#!/usr/bin/env python3
"""
sheets_export.py — Export AI Ark company search results to Google Sheets

Fetches all pages from AI Ark /api/developer-portal/v1/companies and writes
them to a Google Sheet with two tabs: Results (company data) and Search Info
(filters & metadata).

Usage:
  # New spreadsheet (auto-created):
  python3 sheets_export.py --filters filters.json

  # Existing spreadsheet:
  python3 sheets_export.py --filters filters.json --spreadsheet-id SHEET_ID

  # With custom tab name:
  python3 sheets_export.py --filters filters.json --spreadsheet-id SHEET_ID --tab-name "my-search"

  # Max pages limit:
  python3 sheets_export.py --filters filters.json --max-pages 10

  # Dry run (preview count without exporting):
  python3 sheets_export.py --filters filters.json --dry-run

filters.json example (full request body with account wrapper):
  {
    "account": {
      "industries": {"any": {"include": {"mode": "WORD", "content": ["Software Development"]}}},
      "employeeSize": {"type": "RANGE", "range": [{"start": 51, "end": 200}]},
      "location": {"country": {"include": {"mode": "WORD", "content": ["United States"]}}},
      "type": {"include": ["privately_held"]}
    }
  }
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: Missing requests. Run: pip install requests")
    sys.exit(1)

try:
    import gspread
    from google.auth.transport.requests import Request as AuthRequest
    from google.oauth2.credentials import Credentials
except ImportError:
    print("ERROR: Missing dependencies. Run: pip install gspread google-auth")
    sys.exit(1)

AIARK_API_KEY = os.environ.get("AIARK_API_KEY", "")
AIARK_BASE_URL = "https://api.ai-ark.com/api/developer-portal/v1"
TOKEN_PATH = os.path.expanduser("~/.google/token.json")
CREDS_PATH = os.path.expanduser("~/.google/credentials.json")
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

# Rate limit: 5 req/sec, 300/min — use 0.25s between requests
REQUEST_DELAY = 0.25

RESULTS_HEADER = [
    "Company", "Domain", "Website", "Industry", "Employees", "Employee Range",
    "Type", "HQ City", "HQ State", "Country", "Revenue", "Founded",
    "LinkedIn", "Keywords", "Technologies"
]


def aiark_search(body: dict) -> dict:
    """Make a company search request to AI Ark API."""
    url = f"{AIARK_BASE_URL}/companies"
    headers = {
        "X-TOKEN": AIARK_API_KEY,
        "Content-Type": "application/json",
        "accept": "application/json",
    }
    try:
        resp = requests.post(url, headers=headers, json=body, timeout=30)
        if resp.status_code == 400:
            print(f"  ERROR 400: {resp.text[:200]}")
            return {"error": True, "status": 400, "message": resp.text[:200]}
        if resp.status_code == 404:
            return {"error": True, "status": 404, "message": "Data not found"}
        return resp.json()
    except Exception as e:
        print(f"  ERROR: API request failed: {e}")
        return {"error": True, "message": str(e)}


def extract_company_row(company: dict) -> list:
    """Extract a single company into a row matching RESULTS_HEADER."""
    summary = company.get("summary", {}) or {}
    link = company.get("link", {}) or {}
    location = company.get("location", {}) or {}
    hq = location.get("headquarter", {}) or {}
    financial = company.get("financial", {}) or {}
    revenue = financial.get("revenue", {}) or {}
    annual = revenue.get("annual", {}) or {}
    staff = summary.get("staff", {}) or {}
    staff_range = staff.get("range", {}) or {}
    keywords = company.get("keywords", []) or []
    technologies = company.get("technologies", []) or []

    # Format employee range
    range_start = staff_range.get("start", "")
    range_end = staff_range.get("end", "")
    emp_range = ""
    if range_start or range_end:
        emp_range = f"{range_start}-{range_end}" if range_end else f"{range_start}+"

    # Format revenue
    rev_amount = annual.get("amount", "")

    # Format technologies (name only, first 10)
    tech_names = [t.get("name", "") for t in technologies[:10] if isinstance(t, dict)]

    return [
        summary.get("name", ""),
        link.get("domain", ""),
        link.get("website", ""),
        summary.get("industry", ""),
        staff.get("total", ""),
        emp_range,
        summary.get("type", ""),
        hq.get("city", "") or "",
        hq.get("state", "") or "",
        hq.get("country", "") or "",
        rev_amount,
        summary.get("founded_year", "") or "",
        link.get("linkedin", "") or "",
        ", ".join(keywords[:15]) if keywords else "",
        ", ".join(tech_names) if tech_names else "",
    ]


def get_gspread_client() -> gspread.Client:
    """Authenticate and return a gspread client."""
    creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(AuthRequest())
            Path(TOKEN_PATH).write_text(creds.to_json())
        else:
            print("ERROR: Token expired and cannot refresh. Re-authenticate:")
            print(f"  rm {TOKEN_PATH}")
            print(f"  CREDENTIALS_PATH={CREDS_PATH} TOKEN_PATH={TOKEN_PATH} mcp-google-sheets --auth")
            sys.exit(1)
    return gspread.authorize(creds)


def build_filter_summary(filters: dict) -> list[list]:
    """Build human-readable filter summary for Search Info tab."""
    rows = [["Field", "Value"]]

    account = filters.get("account", {})
    if filters.get("lookalikeDomains"):
        rows.append(["Lookalike Domains", json.dumps(filters["lookalikeDomains"])])

    mapping = {
        "location": "Location",
        "industries": "Industries",
        "industry": "Industry",
        "employeeSize": "Employee Size",
        "type": "Company Type",
        "revenue": "Revenue",
        "funding": "Funding",
        "technology": "Technology",
        "technologies": "Technologies",
        "keyword": "Keywords",
        "foundedYear": "Founded Year",
        "metric": "Growth Metrics",
        "geoLocation": "Geo Location",
        "productAndServices": "Products/Services",
        "language": "Language",
        "naics": "NAICS",
        "sic": "SIC",
        "socialMedia": "Social Media",
        "retailSize": "Retail Size",
        "name": "Company Name",
        "domain": "Domain",
        "nameOrDomain": "Name or Domain",
    }

    for key, val in account.items():
        label = mapping.get(key, key)
        if isinstance(val, (dict, list)):
            rows.append([label, json.dumps(val, ensure_ascii=False)])
        else:
            rows.append([label, str(val)])

    return rows


def write_results(spreadsheet_id: str, tab_name: str, rows: list[list], gc: gspread.Client):
    """Write company rows to the Results tab in batches."""
    sh = gc.open_by_key(spreadsheet_id)

    try:
        worksheet = sh.add_worksheet(title=tab_name, rows=len(rows) + 1, cols=len(RESULTS_HEADER))
        print(f"  Created tab: {tab_name}")
    except gspread.exceptions.APIError:
        worksheet = sh.worksheet(tab_name)
        print(f"  Using existing tab: {tab_name}")

    # Write header
    worksheet.update(range_name="A1", values=[RESULTS_HEADER])

    # Write data in batches of 50 rows
    batch_size = 50
    total_written = 0

    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        start_row = i + 2

        try:
            worksheet.update(range_name=f"A{start_row}", values=batch)
            total_written += len(batch)
            print(f"  Rows {start_row}-{start_row + len(batch) - 1} written ({total_written}/{len(rows)})")
        except Exception as e:
            print(f"  ERROR batch at row {start_row}: {e}")
            for j, row in enumerate(batch):
                row_num = start_row + j
                try:
                    worksheet.update(range_name=f"A{row_num}", values=[row])
                    total_written += 1
                except Exception as e2:
                    print(f"    ERROR row {row_num}: {e2}")

        # Rate limit: 60 requests/min for Google Sheets API
        if i + batch_size < len(rows):
            time.sleep(1)

    return total_written


def write_search_info(spreadsheet_id: str, filters: dict, total_companies: int,
                      pages_exported: int, gc: gspread.Client):
    """Write the Search Info metadata tab."""
    sh = gc.open_by_key(spreadsheet_id)

    try:
        worksheet = sh.add_worksheet(title="Search Info", rows=30, cols=2)
    except gspread.exceptions.APIError:
        worksheet = sh.worksheet("Search Info")

    info_rows = build_filter_summary(filters)
    info_rows.append(["", ""])
    info_rows.append(["Total Companies Found", str(total_companies)])
    info_rows.append(["Pages Exported", str(pages_exported)])
    info_rows.append(["Export Date", datetime.now().strftime("%Y-%m-%d %H:%M")])
    info_rows.append(["Source", "AI Ark (72M+ companies)"])

    worksheet.update(range_name="A1", values=info_rows)
    print(f"  Search Info tab written ({len(info_rows)} rows)")


def main():
    parser = argparse.ArgumentParser(description="Export AI Ark search results to Google Sheets")
    parser.add_argument("--filters", required=True, help="Path to filters JSON file (full request body)")
    parser.add_argument("--spreadsheet-id", help="Existing spreadsheet ID (creates new if omitted)")
    parser.add_argument("--tab-name", help="Custom Results tab name (default: Results)")
    parser.add_argument("--max-pages", type=int, default=1000, help="Max pages to fetch (default: 1000)")
    parser.add_argument("--page-size", type=int, default=100, help="Results per page (max 100, default: 100)")
    parser.add_argument("--dry-run", action="store_true", help="Preview count without exporting")
    args = parser.parse_args()

    # Load filters
    filters_path = Path(args.filters)
    if not filters_path.exists():
        print(f"ERROR: Filters file not found: {filters_path}")
        sys.exit(1)
    filters = json.loads(filters_path.read_text())

    # Ensure account wrapper exists
    if "account" not in filters:
        # Assume the entire JSON is the account filters — wrap it
        filters = {"account": filters}

    page_size = min(args.page_size, 100)

    print("\nAI Ark Sheets Export")
    print("=" * 50)

    # First page to get total count
    body = {**filters, "page": 0, "size": page_size}
    print(f"Fetching page 1 (size={page_size})...")
    result = aiark_search(body)
    if result.get("error"):
        print(f"ERROR: Search failed: {result}")
        sys.exit(1)

    total_count = result.get("totalElements", 0)
    total_pages = result.get("totalPages", 0)
    pages_to_fetch = min(total_pages, args.max_pages)

    print(f"  Found {total_count} companies across {total_pages} pages")
    print(f"  Will fetch {pages_to_fetch} pages ({page_size} results/page)")

    if args.dry_run:
        print("\n  [DRY RUN] No export performed.")
        sys.exit(0)

    # Cost guard for large exports
    if pages_to_fetch > 20:
        est_minutes = (pages_to_fetch * REQUEST_DELAY) / 60
        confirm = input(f"\n  Export {pages_to_fetch} pages (~{est_minutes:.0f} min). Proceed? (y/n): ")
        if confirm.lower() != "y":
            print("  Cancelled.")
            sys.exit(0)

    # Collect all rows from page 1
    all_rows = []
    for company in result.get("content", []):
        all_rows.append(extract_company_row(company))
    print(f"  Page 1: {len(result.get('content', []))} companies")

    # Fetch remaining pages
    for page in range(1, pages_to_fetch):
        time.sleep(REQUEST_DELAY)
        body = {**filters, "page": page, "size": page_size}
        print(f"  Fetching page {page + 1}/{pages_to_fetch}...")
        result = aiark_search(body)
        if result.get("error"):
            print(f"    ERROR on page {page + 1}: {result.get('message', result)}")
            break
        content = result.get("content", [])
        if not content:
            print(f"    No more results at page {page + 1}")
            break
        for company in content:
            all_rows.append(extract_company_row(company))
        print(f"  Page {page + 1}: {len(content)} companies (total: {len(all_rows)})")

    print(f"\n  Fetched {len(all_rows)} companies")

    # Google Sheets auth
    print(f"\nConnecting to Google Sheets...")
    gc = get_gspread_client()

    # Create or open spreadsheet
    if args.spreadsheet_id:
        spreadsheet_id = args.spreadsheet_id
        print(f"  Using existing spreadsheet: {spreadsheet_id}")
    else:
        account = filters.get("account", {})
        # Build title from filters
        ind_filter = account.get("industries", {})
        ind_text = ""
        if isinstance(ind_filter, dict):
            any_f = ind_filter.get("any", {})
            inc = any_f.get("include", {})
            if isinstance(inc, dict):
                content = inc.get("content", [])
                ind_text = content[0][:20] if content else ""

        loc_filter = account.get("location", {})
        loc_text = ""
        if isinstance(loc_filter, dict):
            country = loc_filter.get("country", {})
            inc = country.get("include", {})
            if isinstance(inc, dict):
                content = inc.get("content", [])
                loc_text = content[0] if content else ""

        title = f"AI Ark Discovery — {ind_text} {loc_text} — {datetime.now().strftime('%Y-%m-%d')}".strip()
        sh = gc.create(title)
        spreadsheet_id = sh.id
        print(f"  Created spreadsheet: {title}")
        print(f"  ID: {spreadsheet_id}")

    # Write Search Info tab first
    print(f"\nWriting Search Info tab...")
    write_search_info(spreadsheet_id, filters, total_count, pages_to_fetch, gc)

    # Write Results tab
    tab_name = args.tab_name or "Results"
    print(f"\nWriting {len(all_rows)} companies to '{tab_name}' tab...")
    total_written = write_results(spreadsheet_id, tab_name, all_rows, gc)

    # Summary
    print(f"\n{'=' * 50}")
    print(f"Export complete!")
    print(f"  Companies: {total_written}/{len(all_rows)}")
    print(f"  Pages fetched: {pages_to_fetch}")
    print(f"  Sheet: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")


if __name__ == "__main__":
    main()
