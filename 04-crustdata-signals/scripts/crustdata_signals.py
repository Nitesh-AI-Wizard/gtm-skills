#!/usr/bin/env python3
"""
crustdata_signals.py - Pull company signals from CrustData APIs

Enriches a list of domains via /company/enrich (ALL fields, 2 credits each)
and /person/search (recent hires, 0.03 credits/result). Saves per-domain
JSON files + tracker for resume capability.

Usage:
  # From CLI domains
  python3 crustdata_signals.py --domains serverobotics.com,prenosis.com --hire-days 180

  # From Google Sheet
  python3 crustdata_signals.py --sheet-id <SHEET_ID> --tab "Sheet1" --domain-col A --hire-days 180

  # Resume a failed run
  python3 crustdata_signals.py --resume --output-dir outputs/run-20260702-143000

Environment:
  CRUSTDATA_API_KEY - Required. CrustData API key.
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: Missing requests. Run: pip install requests")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

BASE_URL = "https://api.crustdata.com"
API_VERSION = "2025-11-01"

# All 19 field groups - cost is 2 credits regardless, so always pull everything
ALL_ENRICH_FIELDS = [
    "basic_info", "headcount", "funding", "hiring", "revenue",
    "locations", "taxonomy", "followers", "people", "web_traffic",
    "seo", "employee_reviews", "competitors", "social_profiles",
    "news", "software_reviews", "reviews", "public_launches", "market_intel",
]

# Rate limits (requests per minute)
ENRICH_RPM = 15
PERSON_SEARCH_RPM = 30

# Delays between calls (seconds) - conservative to stay under limits
ENRICH_DELAY = 60.0 / ENRICH_RPM + 0.5     # ~4.5s
PERSON_SEARCH_DELAY = 60.0 / PERSON_SEARCH_RPM + 0.5  # ~2.5s

# Person search fields to return
PERSON_FIELDS = [
    "basic_profile.name",
    "basic_profile.first_name",
    "basic_profile.last_name",
    "basic_profile.headline",
    "basic_profile.location",
    "experience.employment_details.current.title",
    "experience.employment_details.current.start_date",
    "experience.employment_details.current.seniority_level",
    "experience.employment_details.current.company_name",
    "experience.employment_details.current.function_category",
    "experience.employment_details.current.employment_type",
]

SKILL_DIR = Path(__file__).resolve().parent.parent


def get_headers() -> dict:
    api_key = os.environ.get("CRUSTDATA_API_KEY")
    if not api_key:
        print("ERROR: CRUSTDATA_API_KEY environment variable not set.")
        print("  export CRUSTDATA_API_KEY=cd_xxx...")
        sys.exit(1)
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "x-api-version": API_VERSION,
    }


# ---------------------------------------------------------------------------
# API calls
# ---------------------------------------------------------------------------

def enrich_company(domain: str, headers: dict) -> dict | None:
    """Enrich a single domain. Returns the raw API response or None on error."""
    payload = {
        "domains": [domain],
        "fields": ALL_ENRICH_FIELDS,
    }
    try:
        resp = requests.post(
            f"{BASE_URL}/company/enrich",
            headers=headers,
            json=payload,
            timeout=90,
        )
        if resp.status_code == 200:
            data = resp.json()
            if data and len(data) > 0:
                return data[0]
            return {"matched_on": domain, "match_type": "domain", "matches": []}
        elif resp.status_code == 429:
            print(f"    Rate limited on enrich. Waiting 60s...")
            time.sleep(60)
            return enrich_company(domain, headers)  # retry once
        else:
            print(f"    Enrich error {resp.status_code}: {resp.text[:200]}")
            return None
    except requests.exceptions.Timeout:
        print(f"    Enrich timeout for {domain} (90s)")
        return None
    except Exception as e:
        print(f"    Enrich exception for {domain}: {e}")
        return None


def search_recent_hires(domain: str, hire_days: int, headers: dict) -> list:
    """Search for people who joined a company in the last N days. Returns list of profiles."""
    cutoff_date = (datetime.now() - timedelta(days=hire_days)).strftime("%Y-%m-%d")

    payload = {
        "filters": {
            "op": "and",
            "conditions": [
                {
                    "field": "experience.employment_details.current.company_website_domain",
                    "type": "=",
                    "value": domain,
                },
                {
                    "field": "experience.employment_details.current.start_date",
                    "type": ">",
                    "value": cutoff_date,
                },
            ],
        },
        "fields": PERSON_FIELDS,
        "sorts": [{"field": "experience.employment_details.start_date", "order": "desc"}],
        "limit": 100,
    }

    all_profiles = []
    cursor = None

    while True:
        if cursor:
            payload["cursor"] = cursor

        try:
            resp = requests.post(
                f"{BASE_URL}/person/search",
                headers=headers,
                json=payload,
                timeout=60,
            )
            if resp.status_code == 200:
                data = resp.json()
                profiles = data.get("profiles", [])
                all_profiles.extend(profiles)
                cursor = data.get("next_cursor")
                if not cursor or not profiles:
                    break
                time.sleep(PERSON_SEARCH_DELAY)
            elif resp.status_code == 429:
                print(f"    Rate limited on person search. Waiting 60s...")
                time.sleep(60)
                continue  # retry same page
            else:
                print(f"    Person search error {resp.status_code}: {resp.text[:200]}")
                break
        except requests.exceptions.Timeout:
            print(f"    Person search timeout for {domain}")
            break
        except Exception as e:
            print(f"    Person search exception for {domain}: {e}")
            break

    return all_profiles


# ---------------------------------------------------------------------------
# Sheet reading (optional - only when --sheet-id provided)
# ---------------------------------------------------------------------------

def read_domains_from_sheet(sheet_id: str, tab: str, domain_col: str) -> list[str]:
    """Read domains from a Google Sheet column using gspread."""
    try:
        import gspread
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
    except ImportError:
        print("ERROR: Missing gspread. Run: pip install gspread google-auth")
        sys.exit(1)

    token_path = os.path.expanduser("~/.google/token.json")
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]

    creds = Credentials.from_authorized_user_file(token_path, scopes)
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            Path(token_path).write_text(creds.to_json())
        else:
            print("ERROR: Google token expired. Re-authenticate:")
            print(f"  rm {token_path}")
            print("  mcp-google-sheets --auth")
            sys.exit(1)

    gc = gspread.authorize(creds)
    sh = gc.open_by_key(sheet_id)
    ws = sh.worksheet(tab)

    # Determine column index
    if domain_col.isalpha():
        col_idx = 0
        for c in domain_col.upper():
            col_idx = col_idx * 26 + (ord(c) - ord("A") + 1)
    else:
        # Try to find column by header name
        headers = ws.row_values(1)
        try:
            col_idx = headers.index(domain_col) + 1
        except ValueError:
            print(f"ERROR: Column '{domain_col}' not found. Available: {headers}")
            sys.exit(1)

    values = ws.col_values(col_idx)
    # Skip header row, filter empties
    domains = [v.strip().lower() for v in values[1:] if v.strip()]
    # Remove protocol prefixes
    cleaned = []
    for d in domains:
        d = d.replace("https://", "").replace("http://", "").replace("www.", "")
        d = d.rstrip("/")
        if d:
            cleaned.append(d)
    return cleaned


# ---------------------------------------------------------------------------
# Tracker
# ---------------------------------------------------------------------------

def load_tracker(output_dir: Path) -> dict:
    tracker_path = output_dir / "tracker.json"
    if tracker_path.exists():
        return json.loads(tracker_path.read_text())
    return {
        "status": "in_progress",
        "started_at": datetime.now().isoformat(),
        "domains": {},
        "credits_used": {"enrich": 0, "person_search": 0, "total": 0},
        "counts": {"total": 0, "done": 0, "failed": 0, "skipped": 0},
    }


def save_tracker(output_dir: Path, tracker: dict):
    tracker_path = output_dir / "tracker.json"
    tracker_path.write_text(json.dumps(tracker, indent=2))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def process_domain(domain: str, hire_days: int, headers: dict, output_dir: Path, tracker: dict):
    """Process a single domain: enrich + person search, save JSON."""
    domain_status = tracker["domains"].get(domain, {})
    if domain_status.get("status") == "done":
        print(f"  [{domain}] Already done, skipping")
        tracker["counts"]["skipped"] = tracker["counts"].get("skipped", 0) + 1
        return

    print(f"  [{domain}] Enriching...")
    enrich_data = enrich_company(domain, headers)
    time.sleep(ENRICH_DELAY)

    if enrich_data is None:
        print(f"  [{domain}] Enrich FAILED")
        tracker["domains"][domain] = {"status": "failed", "error": "enrich_failed"}
        tracker["counts"]["failed"] += 1
        save_tracker(output_dir, tracker)
        return

    matches = enrich_data.get("matches", [])
    has_match = len(matches) > 0 and matches[0].get("company_data")
    enrich_credits = 2 if has_match else 0

    # Person search for recent hires
    print(f"  [{domain}] Searching recent hires (last {hire_days} days)...")
    hires = search_recent_hires(domain, hire_days, headers)
    hire_credits = round(len(hires) * 0.03, 2)
    print(f"  [{domain}] Found {len(hires)} recent hires ({hire_credits} credits)")

    # Build combined result
    result = {
        "domain": domain,
        "timestamp": datetime.now().isoformat(),
        "hire_days": hire_days,
        "enrich": enrich_data,
        "recent_hires": hires,
        "credits": {
            "enrich": enrich_credits,
            "person_search": hire_credits,
            "total": enrich_credits + hire_credits,
        },
    }

    # Save JSON
    json_path = output_dir / f"{domain.replace('.', '_')}.json"
    json_path.write_text(json.dumps(result, indent=2, default=str))
    print(f"  [{domain}] Saved to {json_path.name}")

    # Update tracker
    tracker["domains"][domain] = {
        "status": "done",
        "has_match": has_match,
        "hires_found": len(hires),
        "credits": result["credits"],
    }
    tracker["credits_used"]["enrich"] += enrich_credits
    tracker["credits_used"]["person_search"] += hire_credits
    tracker["credits_used"]["total"] += enrich_credits + hire_credits
    tracker["counts"]["done"] += 1
    save_tracker(output_dir, tracker)


def main():
    parser = argparse.ArgumentParser(description="Pull company signals from CrustData")
    # Input sources
    input_group = parser.add_mutually_exclusive_group(required=False)
    input_group.add_argument("--domains", help="Comma-separated domains")
    input_group.add_argument("--sheet-id", help="Google Sheet ID to read domains from")

    # Sheet options
    parser.add_argument("--tab", default="Sheet1", help="Sheet tab name (default: Sheet1)")
    parser.add_argument("--domain-col", default="A", help="Domain column letter or header name (default: A)")

    # Signal options
    parser.add_argument("--hire-days", type=int, default=180, choices=[90, 180, 365],
                        help="How many days back to search for recent hires (default: 180)")

    # Output
    parser.add_argument("--output-dir", help="Output directory (default: auto-generated in skill outputs/)")
    parser.add_argument("--resume", action="store_true", help="Resume a previous run (requires --output-dir)")

    args = parser.parse_args()

    # Resolve output directory
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        run_id = f"run-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        output_dir = SKILL_DIR / "outputs" / run_id
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load or create tracker
    tracker = load_tracker(output_dir)

    # Get domains
    if args.resume:
        if not (output_dir / "tracker.json").exists():
            print(f"ERROR: No tracker.json in {output_dir} to resume from")
            sys.exit(1)
        # Get all domains from tracker, process undone ones
        domains = [d for d, info in tracker["domains"].items() if info.get("status") != "done"]
        if not domains:
            print("All domains already processed. Nothing to resume.")
            sys.exit(0)
        print(f"Resuming {len(domains)} remaining domains from {output_dir}")
    elif args.domains:
        domains = [d.strip().lower() for d in args.domains.split(",") if d.strip()]
    elif args.sheet_id:
        print(f"Reading domains from sheet {args.sheet_id}, tab '{args.tab}', column '{args.domain_col}'...")
        domains = read_domains_from_sheet(args.sheet_id, args.tab, args.domain_col)
    else:
        print("ERROR: Provide --domains, --sheet-id, or --resume")
        sys.exit(1)

    if not domains:
        print("ERROR: No domains found")
        sys.exit(1)

    # Initialize tracker counts for new run
    if not args.resume:
        tracker["counts"]["total"] = len(domains)
        tracker["hire_days"] = args.hire_days
        if args.sheet_id:
            tracker["source"] = {"type": "sheet", "sheet_id": args.sheet_id, "tab": args.tab}
        else:
            tracker["source"] = {"type": "cli", "count": len(domains)}
        # Pre-populate domain entries
        for d in domains:
            if d not in tracker["domains"]:
                tracker["domains"][d] = {"status": "pending"}
        save_tracker(output_dir, tracker)

    headers = get_headers()

    print(f"\nCrustData Signals")
    print(f"  Domains: {len(domains)}")
    print(f"  Hire window: {args.hire_days} days")
    print(f"  Output: {output_dir}")
    print(f"  Est. credits: ~{len(domains) * 2.6:.0f} (2 enrich + ~0.6 hires per domain)")
    print()

    for i, domain in enumerate(domains, 1):
        print(f"[{i}/{len(domains)}] {domain}")
        process_domain(domain, args.hire_days, headers, output_dir, tracker)

    # Final summary
    tracker["status"] = "completed"
    tracker["completed_at"] = datetime.now().isoformat()
    save_tracker(output_dir, tracker)

    c = tracker["counts"]
    cr = tracker["credits_used"]
    print(f"\n{'='*50}")
    print(f"Run complete")
    print(f"  Done: {c['done']} | Failed: {c['failed']} | Skipped: {c.get('skipped', 0)}")
    print(f"  Credits: {cr['total']:.2f} (enrich: {cr['enrich']:.0f}, person search: {cr['person_search']:.2f})")
    print(f"  Output: {output_dir}")
    print(f"\nNext step: run sheets_writer.py to write results to Google Sheets")
    print(f"  python3 {SKILL_DIR}/scripts/sheets_writer.py --run-dir {output_dir} --spreadsheet-id <SHEET_ID>")


if __name__ == "__main__":
    main()
