#!/usr/bin/env python3
"""
sheets_export.py — Export Prospeo company search results to Google Sheets

Fetches all pages from Prospeo /search-company API and writes them to a
Google Sheet with two tabs: Results (company data) and Search Info (metadata).

Usage:
  # New spreadsheet (auto-created):
  python3 sheets_export.py --filters filters.json

  # Existing spreadsheet:
  python3 sheets_export.py --filters filters.json --spreadsheet-id SHEET_ID

  # With custom tab name:
  python3 sheets_export.py --filters filters.json --spreadsheet-id SHEET_ID --tab-name "my-search"

  # Max pages limit:
  python3 sheets_export.py --filters filters.json --max-pages 10

filters.json example:
  {
    "company_location_search": {"include": ["United States"]},
    "company_industry": {"include": ["Software Development"]},
    "company_headcount_range": ["51-100", "101-200"],
    "company_type": {"status": "Private"},
    "company_revenue": {"min": "1M", "max": "50M"}
  }
"""

import argparse
import json
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

PROSPEO_API_KEY = "YOUR_PROSPEO_API_KEY"
PROSPEO_BASE_URL = "https://api.prospeo.io"
TOKEN_PATH = "~/.google/token.json"
CREDS_PATH = "~/.google/credentials.json"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

RESULTS_HEADER = [
    "Company", "Domain", "Industry", "Employees", "Employee Range",
    "HQ City", "HQ State", "Country", "Revenue", "Funding Stage",
    "Total Funding", "Latest Funding Date", "LinkedIn URL", "Keywords", "Founded"
]


def prospeo_request(endpoint: str, method: str = "GET", body: dict = None) -> dict:
    """Make a request to the Prospeo API."""
    url = f"{PROSPEO_BASE_URL}{endpoint}"
    headers = {
        "X-KEY": PROSPEO_API_KEY,
        "Content-Type": "application/json",
    }
    try:
        if method == "POST":
            resp = requests.post(url, headers=headers, json=body, timeout=30)
        else:
            resp = requests.get(url, headers=headers, timeout=30)
        return resp.json()
    except Exception as e:
        print(f"  ERROR: API request failed: {e}")
        return {"error": True, "error_code": str(e)}


def get_account_info() -> dict:
    """Get Prospeo account info."""
    return prospeo_request("/account-information")


def search_companies(filters: dict, page: int = 1) -> dict:
    """Search companies with given filters."""
    return prospeo_request("/search-company", method="POST", body={
        "page": page,
        "filters": filters,
    })


def extract_company_row(company: dict) -> list:
    """Extract a single company into a row matching RESULTS_HEADER."""
    loc = company.get("location", {}) or {}
    fund = company.get("funding", {}) or {}
    keywords = company.get("keywords", []) or []

    return [
        company.get("name", ""),
        company.get("domain", "") or company.get("website", ""),
        company.get("industry", ""),
        company.get("employee_count", ""),
        company.get("employee_range", ""),
        loc.get("city", "") or "",
        loc.get("state", "") or "",
        loc.get("country", "") or "",
        company.get("revenue_range_printed", ""),
        fund.get("last_funding_type", "") if isinstance(fund, dict) else "",
        fund.get("total_funding", "") if isinstance(fund, dict) else "",
        fund.get("last_funding_date", "") if isinstance(fund, dict) else "",
        company.get("linkedin_url", "") or "",
        ", ".join(keywords[:15]),
        company.get("founded", "") or "",
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

    mapping = {
        "company_location_search": "Location",
        "company_industry": "Industries",
        "company_headcount_range": "Headcount Range",
        "company_headcount_custom": "Headcount Custom",
        "company_type": "Company Type",
        "company_keywords": "Keywords",
        "company_revenue": "Revenue",
        "company_funding": "Funding",
        "company_technology": "Technology",
        "company_lookalike": "Lookalike",
        "company_headcount_growth": "Headcount Growth",
        "company_job_posting_hiring_for": "Hiring For",
        "company_job_posting_quantity": "Job Posting Count",
        "company_attributes": "Attributes",
        "company_founded": "Founded",
        "company_news": "News",
        "company_email_provider": "Email Provider",
        "company_products_services": "Products/Services",
        "company_icp": "ICP",
        "company_key_execs": "Key Execs",
        "company_website_traffic": "Website Traffic",
    }

    for key, val in filters.items():
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
            # Retry one by one
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
                      pages_exported: int, credits_used: int, credits_remaining: int,
                      gc: gspread.Client):
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
    info_rows.append(["Credits Used", str(credits_used)])
    info_rows.append(["Export Date", datetime.now().strftime("%Y-%m-%d %H:%M")])
    info_rows.append(["Credits Remaining", str(credits_remaining)])

    worksheet.update(range_name="A1", values=info_rows)
    print(f"  Search Info tab written ({len(info_rows)} rows)")


def main():
    parser = argparse.ArgumentParser(description="Export Prospeo search results to Google Sheets")
    parser.add_argument("--filters", required=True, help="Path to filters JSON file")
    parser.add_argument("--spreadsheet-id", help="Existing spreadsheet ID (creates new if omitted)")
    parser.add_argument("--tab-name", help="Custom Results tab name (default: Results)")
    parser.add_argument("--max-pages", type=int, default=1000, help="Max pages to fetch (default: 1000)")
    parser.add_argument("--dry-run", action="store_true", help="Preview filters and count without exporting")
    args = parser.parse_args()

    # Load filters
    filters_path = Path(args.filters)
    if not filters_path.exists():
        print(f"ERROR: Filters file not found: {filters_path}")
        sys.exit(1)
    filters = json.loads(filters_path.read_text())

    # Account check
    print("\nProspeo Sheets Export")
    print("=" * 50)
    acct = get_account_info()
    if acct.get("error"):
        print(f"ERROR: Could not get account info: {acct}")
        sys.exit(1)
    resp = acct["response"]
    credits_start = resp["remaining_credits"]
    print(f"  Plan: {resp['current_plan']} | Credits: {credits_start}")

    # First page to get total count
    print(f"\nFetching page 1...")
    result = search_companies(filters, page=1)
    if result.get("error"):
        print(f"ERROR: Search failed: {result.get('error_code', result)}")
        if result.get("filter_error"):
            print(f"  Filter error: {result['filter_error']}")
        sys.exit(1)

    pagination = result["pagination"]
    total_count = pagination["total_count"]
    total_pages = pagination["total_page"]
    pages_to_fetch = min(total_pages, args.max_pages)

    print(f"  Found {total_count} companies across {total_pages} pages")
    print(f"  Will fetch {pages_to_fetch} pages ({pages_to_fetch} credits)")

    if args.dry_run:
        print("\n  [DRY RUN] No export performed.")
        sys.exit(0)

    # Cost guard
    if pages_to_fetch > 10:
        confirm = input(f"\n  Export {pages_to_fetch} pages = {pages_to_fetch} credits. Proceed? (y/n): ")
        if confirm.lower() != "y":
            print("  Cancelled.")
            sys.exit(0)

    # Collect all rows
    all_rows = []
    for company_data in result["results"]:
        all_rows.append(extract_company_row(company_data["company"]))
    print(f"  Page 1: {len(result['results'])} companies")

    for page in range(2, pages_to_fetch + 1):
        time.sleep(0.5)  # Rate limit Prospeo
        print(f"  Fetching page {page}/{pages_to_fetch}...")
        result = search_companies(filters, page=page)
        if result.get("error"):
            print(f"    ERROR on page {page}: {result.get('error_code')}")
            break
        for company_data in result["results"]:
            all_rows.append(extract_company_row(company_data["company"]))
        print(f"  Page {page}: {len(result['results'])} companies (total: {len(all_rows)})")

    credits_used = pages_to_fetch
    print(f"\n  Fetched {len(all_rows)} companies using {credits_used} credits")

    # Google Sheets auth
    print(f"\nConnecting to Google Sheets...")
    gc = get_gspread_client()

    # Create or open spreadsheet
    if args.spreadsheet_id:
        spreadsheet_id = args.spreadsheet_id
        print(f"  Using existing spreadsheet: {spreadsheet_id}")
    else:
        # Build a short summary for the title
        loc = filters.get("company_location_search", {}).get("include", [""])[0] if isinstance(filters.get("company_location_search"), dict) else ""
        ind = filters.get("company_industry", {}).get("include", [""])[0][:20] if isinstance(filters.get("company_industry"), dict) else ""
        hc = ", ".join(filters.get("company_headcount_range", [])) if isinstance(filters.get("company_headcount_range"), list) else ""
        title = f"Prospeo Discovery — {ind} {loc} {hc} — {datetime.now().strftime('%Y-%m-%d')}".strip()
        sh = gc.create(title)
        spreadsheet_id = sh.id
        print(f"  Created spreadsheet: {title}")
        print(f"  ID: {spreadsheet_id}")

    # Write Search Info tab first
    print(f"\nWriting Search Info tab...")
    acct_after = get_account_info()
    credits_remaining = acct_after.get("response", {}).get("remaining_credits", credits_start - credits_used)
    write_search_info(spreadsheet_id, filters, total_count, pages_to_fetch, credits_used, credits_remaining, gc)

    # Write Results tab
    tab_name = args.tab_name or "Results"
    print(f"\nWriting {len(all_rows)} companies to '{tab_name}' tab...")
    total_written = write_results(spreadsheet_id, tab_name, all_rows, gc)

    # Summary
    print(f"\n{'=' * 50}")
    print(f"Export complete!")
    print(f"  Companies: {total_written}/{len(all_rows)}")
    print(f"  Credits used: {credits_used}")
    print(f"  Credits remaining: {credits_remaining}")
    print(f"  Sheet: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")


if __name__ == "__main__":
    main()
