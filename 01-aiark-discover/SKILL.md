---
name: aiark-discover
description: >
  B2B company discovery and list building via AI Ark's 72M+ company database
  with 921 industries. Activate when the user wants to find companies using AI Ark,
  build a prospect list from AI Ark, discover TAM, search for companies by ICP,
  find lookalike companies, or size a market using AI Ark. Also triggers on:
  "find companies (ai ark)", "ai ark company search", "build a list with ai ark",
  "ai ark discover", "run ai ark", "company discovery ai ark", "lookalike search
  ai ark", or any combination of industry + location + headcount + funding filters
  when AI Ark is specified.
---

# AI Ark Discover — B2B Company List Builder

Build targeted company lists from AI Ark's 72M+ company database with 921 industries,
geo-location search, growth metrics, and lookalike discovery.

## API Connection

All AI Ark calls use direct HTTP requests via curl in Bash.

```
Base URL: https://api.ai-ark.com
Endpoint: POST /api/developer-portal/v1/companies
Auth header: X-TOKEN: <your-ai-ark-token>
Content-Type: application/json
Rate limit: 5 req/sec, 300/min, 18,000/hr
```

### Base Curl Format

```bash
curl -s -X POST \
  'https://api.ai-ark.com/api/developer-portal/v1/companies' \
  -H 'X-TOKEN: <your-ai-ark-token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "page": 0,
    "size": 25,
    "account": {
      <filters here>
    }
  }'
```

All filters go inside an `account` object. Placing them at top level returns the entire 72M database unfiltered. `page` is 0-based. `size` max is 100.

### Response Shape

```json
{
  "content": [<company objects>],
  "totalElements": 23583,
  "totalPages": 23583,
  "number": 0,
  "size": 25
}
```

Each company object has: `id`, `summary` (name, description, type, industry, staff, founded_year), `link` (website, domain, linkedin), `contact`, `financial` (revenue, funding), `location` (headquarter with country/state/city/coordinates), `technologies`, `industries`, `keywords`, `languages`, `sic`, `naics`, `last_updated`.

### Enum Values Reference

All valid filter values are stored in `references/aiark-enums.json` (refreshed every 30 days via `references/enum-refresh.md`).
Do not guess or invent values — always check the enum cache first.

- **Cached in `aiark-enums.json`**: industries (921), technologies (16,041), languages (48), continents (23), countries (262), company types (8), funding types (19), social media platforms (6), metric timeframes (5), metric departments (27), keyword sources (5), keyword modes (3)
- **Resolve at runtime**: states/regions (4,919) — use country filter or geoLocation instead. For technologies not in the cache, use `technologies` AdvanceFilter with SMART mode as fallback.

### Cache Check

Read `references/aiark-enums.json`. Check the `last_updated` field.
- If file is missing or `last_updated` is older than 30 days: refresh the cache. Read `references/enum-refresh.md` for the procedure.
- If fresh: proceed with cached values.

---

## Step 0 — Quick Validation

No plan detection needed — AI Ark has a single API key with all filters available.

Run a minimal search to confirm the API is responding:

```bash
curl -s -X POST 'https://api.ai-ark.com/api/developer-portal/v1/companies' \
  -H 'X-TOKEN: <your-ai-ark-token>' \
  -H 'Content-Type: application/json' \
  -d '{"page": 0, "size": 1}' | python3 -c "import sys,json; d=json.load(sys.stdin); print('OK' if d.get('content') else 'ERROR:', d)"
```

Then present a clean status:

```
AI Ark Discovery ready.
Database: 72M+ companies | 921 industries
All filters available.

What companies are you looking for?
```

Wait for the user's input before proceeding.

---

## Step 1 — Classify the User

Read the user's input and classify into one of four types.

**Parse the input for**:
- ICP filters (industry, headcount, location, revenue, company type, keywords, etc.)
- Lookalike signals (seed domains, LinkedIn URLs, "similar to", "like X")
- Vague terms that need mapping ("tech", "healthcare", "fintech")

| Provided ICP filters | Provided lookalike | Type | Mode |
|---------------------|-------------------|------|------|
| 3+ core filters covered | No | Type 1 — Expert | `build` |
| 1-2 filters, or vague terms | No | Type 2 — Partial | `guide` |
| 1+ filters | Yes | Type 3 — Filtered + Lookalike | `build+lookalike` |
| None or minimal | Yes | Type 4 — Lookalike Discovery | `lookalike` |

### Core Filters (4 recommended)

These produce a usable list. Ensure they're all covered before the final search:

1. **Location** — no safe default, always ask
2. **Company size** (employeeSize) — default: `{"start": 11, "end": 500}`
3. **Industry or keywords** — at least one definition of company type
4. **Company type** — default: `privately_held`

**Revenue** is optional but recommended. Use exact USD amounts (not string ranges).

---

## Step 2 — Execute by Type

### Type 1 — Expert (build mode)

1. Parse plain English into AI Ark filter JSON
2. Map every term to exact AI Ark values — read `references/aiark-enums.json` for valid values, `references/filters-full.md` for format, `references/mapping-examples.md` for examples
3. For ambiguous terms (e.g., "tech"), search the 921-industry catalog in `aiark-enums.json` and show matching options
4. Build the complete filter JSON
5. **Show assembled filters to the user for confirmation** (see "Show Filters" format below)
6. Proceed to Step 2.5 (recommend optional filters), then Step 3

### Type 2 — Partial (guide mode)

Act as a recommendation engine for missing filters:

1. **Interpret vague terms** — search the industry catalog with SMART mode and present matching industries grouped by relevance. AI Ark has 921 industries vs Prospeo's 256, so there are usually 5-20+ matches for broad terms.

2. **Ask for missing core filters one at a time** with smart defaults:
   > You've set industry and location. Still need:
   > - **Company size** — typical outbound range is 11-500 employees. Sound right?
   > - **Company type** — default to privately held. Change?

3. Build filters incrementally. After each answer, add to the running filter set.

4. Once all core filters are covered, **show assembled filters for confirmation** (see "Show Filters" format below), then proceed to Step 2.5, then Step 3.

### Type 3 — Filtered + Lookalike

AI Ark lookalike requires at least one account filter alongside it — can't run standalone.

1. Parse ICP filters from user input
2. Add `lookalikeDomains` at top level (outside `account`) with LinkedIn URLs preferred (higher accuracy) or domains
3. Keep account filters alongside — lookalike alone returns 0 results or times out
4. **Show assembled filters for confirmation** (see "Show Filters" format below)
5. Proceed to Step 3

Unlike Prospeo, AI Ark lookalike stacking with filters works well and is required. Don't drop it.

### Type 4 — Lookalike Discovery

The user only has seed companies, no ICP filters. Before running the AI Ark lookalike, Claude Code researches the domain to suggest relevant industry tags.

**Step A — Claude Code Industry Research (automatic, before AI Ark):**

1. Get the seed domain from the user (e.g., una.ai)
2. **Fetch the company website** using WebFetch — read homepage, about page, product page
3. From the website content, understand what the company does, who they serve, what space they're in
4. **Search `references/aiark-enums.json` industries list** for all matching tags based on that understanding
5. **Suggest the matching industries** to the user:
   > I researched **una.ai** — they're an FP&A and financial planning platform for mid-market companies.
   >
   > **Suggested AI Ark industry tags:**
   > - software development
   > - financial services
   > - fintech
   > - saas
   > - analytics
   > - business intelligence
   > - enterprise software
   >
   > These are suggestions — you can pick any, all, or skip them entirely.

This step is a suggestion only — the user can use these tags, modify them, or ignore them completely.

**Step B — Ask for required filters:**

6. **Ask for location and employee size** — minimum required for AI Ark lookalike:
   > I also need:
   > - **Location** — which countries? (e.g., United States)
   > - **Company size** — what employee range? Default is 11-500.

**Step C — Run the lookalike search:**

7. Build the search with:
   - `lookalikeDomains` at top level (LinkedIn URL preferred)
   - Location + employee size + type in `account`
   - If user picked industry tags from Step A, add them to the `industries` filter as well
8. Show filters for confirmation (see "Show Filters" format)
9. Run the search, present results (Step 3)
10. Analyze the results — show industry/funding/revenue patterns from the returned companies

**Step D — Optional refined search (if user wants):**

11. After seeing lookalike results, user can choose to run a **second search without lookalike** — using the discovered industry tags + any patterns from the results as ICP filters for a broader, cleaner list

---

## Show Filters (before every search)

Before running any search, always show the user exactly what filters will be applied. This applies to all types. Use this format:

```
Here's what I'm searching:

Filters:
- Location: United States
- Industry: software development (mode: WORD)
- Employee size: 50-200
- Company type: privately_held
- Revenue: $1M-$50M
- Funding: Series A, Series B
{if lookalike:}
- Lookalike seeds: hubspot.com, stripe.com

Run this search?
```

Wait for confirmation before executing. If the user says "yes", "go", "run it", or similar — proceed. If they want changes, adjust and show again.

---

## Step 2.5 — Recommend Optional Filters

After core filters are set, recommend 3-5 relevant optional filters with specific values. Use context from the user's input and any lookalike discovery data.

**Available optional filters** (read `references/filters-full.md` for full details):

- **Funding** — type (seed, series_a, etc.), total/last amounts, duration since last round
- **Revenue** — exact USD range
- **Founded year** — min/max year
- **Technology** — specific tech stack tools
- **Keywords** — free-text with SMART/WORD/STRICT modes across multiple sources
- **Growth metrics** — employee change or % growth by department over 1-24 months
- **Geo-location** — lat/lng/radius for hyper-local targeting
- **Products & services** — free-text product/service search
- **Language** — company operating language
- **NAICS/SIC** — industry classification codes
- **Social media** — filter by platform presence
- **Retail size** — number of retail locations

### Rules

- Be specific: "Series A-B funding with $1M-$10M last round" not "you could add funding"
- Explain why: tie each recommendation to their search context
- Max 5 recommendations
- Quick exit: if user says "skip" or "just run it", proceed to Step 3

---

## Step 3 — Search & Present Results

Run `POST /api/developer-portal/v1/companies` with assembled filters, `page: 0`, `size: 25`.

Present results:

```
Found {totalElements} companies matching your filters.

Filters applied:
- Location: {locations}
- Industry: {industries}
- Size: {employee range}
- Type: {company type}
{any additional filters}

Preview (top 25):
| # | Company | Domain | Industry | Employees | Location | Revenue | Founded |
|---|---------|--------|----------|-----------|----------|---------|---------|
| 1 | ... | ... | ... | ... | ... | ... | ... |

Pages: {totalPages} (100 results/page max)

Next steps:
1. Export full list to Google Sheets
2. Narrow down filters
3. Adjust and re-search
```

If `totalElements` > 5,000: recommend narrowing before full export.
If `totalElements` < 10: suggest loosening filters.

---

## Step 4 — Export (on user request only)

Only export when the user explicitly asks. Use the Python export script.

### Export Script

**Script location**: `scripts/sheets_export.py`
**Dependencies**: `pip install requests gspread google-auth`

### Export Procedure

1. **Save the current filter JSON to a temp file**:
   ```bash
   cat > /tmp/aiark_filters.json << 'EOF'
   {full request body JSON here, including account wrapper}
   EOF
   ```

2. **Run the export script**:
   ```bash
   # New spreadsheet:
   python3 scripts/sheets_export.py --filters /tmp/aiark_filters.json

   # Existing spreadsheet:
   python3 scripts/sheets_export.py --filters /tmp/aiark_filters.json --spreadsheet-id SHEET_ID

   # Custom tab name:
   python3 scripts/sheets_export.py --filters /tmp/aiark_filters.json --tab-name "my-search"

   # Cap pages:
   python3 scripts/sheets_export.py --filters /tmp/aiark_filters.json --max-pages 20

   # Dry run:
   python3 scripts/sheets_export.py --filters /tmp/aiark_filters.json --dry-run
   ```

3. **Share the spreadsheet URL** from the script output.

### Results Tab Columns

| Column | Response Field Path |
|--------|-------------------|
| Company | `summary.name` |
| Domain | `link.domain` |
| Website | `link.website` |
| Industry | `summary.industry` |
| Employees | `summary.staff.total` |
| Employee Range | `summary.staff.range.start`-`summary.staff.range.end` |
| Type | `summary.type` |
| HQ City | `location.headquarter.city` |
| HQ State | `location.headquarter.state` |
| Country | `location.headquarter.country` |
| Revenue | `financial.revenue.annual.amount` |
| Founded | `summary.founded_year` |
| LinkedIn | `link.linkedin` |
| Keywords | `keywords` (first 15, comma-joined) |
| Technologies | `technologies` (names, first 10, comma-joined) |

### Cost Guard

AI Ark doesn't charge per-page credits, but respect rate limits (5 req/sec, 300/min). The script handles rate limiting automatically.

Before large exports, tell the user:
> Full export: {totalPages} pages at 100 results/page. This will take ~{estimate} minutes. Proceed?

---

## Filter Mapping Reference

Read `references/filters-full.md` for the complete filter reference and `references/mapping-examples.md` for plain-English mapping examples.

Key quick-reference:

| User says | Maps to |
|-----------|---------|
| "US" / "America" | `location: {"any": {"include": ["United States"]}}` |
| "private companies" | `type.include: ["privately_held"]` |
| "50-200 employees" | `employeeSize: {"type": "RANGE", "range": [{"start": 50, "end": 200}]}` |
| "Series A" | `funding: {"type": ["series_a"]}` |
| "$1M-$10M revenue" | `revenue: {"type": "RANGE", "range": [{"start": 1000000, "end": 10000000}]}` |
| "SaaS" / "software" | `industries` with SMART mode, matching against 921 catalog |
| "similar to X" | `lookalikeDomains: ["linkedin.com/company/x"]` at top level |
| "growing fast" | Not available via direct HTTP — use MCP `mcp__ai-ark__company_search` with `minMetricGrowthChange` |
| "uses Salesforce" | `technology.any.include: ["salesforce"]` |
| "founded after 2015" | Not available via direct HTTP — use MCP `mcp__ai-ark__company_search` with `minFoundedYear` |
