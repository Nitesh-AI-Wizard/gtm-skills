---
name: prospeo-discover
description: >
  B2B company discovery and list building via Prospeo search API. Activate when
  the user wants to find companies, build a prospect list, discover TAM, search
  for companies by ICP, find lookalike companies, or size a market. Also triggers
  on: "find companies", "build a list", "company search", "how many companies
  match", "find companies similar to", "TAM sizing", "ICP search", "prospect
  list", "discover companies", "run prospeo", "company discovery", "lookalike
  search", or any combination of industry + location + headcount + funding filters.
---

# Prospeo Discover — B2B Company List Builder

Build targeted company lists from Prospeo's 30M+ company database using 33 search filters.
Handles five user types — from full ICP experts to users who only have seed company domains.

## API Connection

All Prospeo calls use direct HTTP requests via curl in Bash. Do NOT use MCP tools for Prospeo.

```
Base URL: https://api.prospeo.io
Auth header: X-KEY: YOUR_PROSPEO_API_KEY
Content-Type: application/json
```

**Endpoints used by this skill:**
- `GET /account-information` — plan detection (free)
- `POST /search-company` — company search (1 credit/page)
- `POST /search-suggestions` — resolve locations, technologies, industries (free)

### Exact Curl Formats (verified & tested)

#### 1. GET /account-information (free)

```bash
curl -s -H "X-KEY: $KEY" "https://api.prospeo.io/account-information"
```

Response: `{"error": false, "response": {"current_plan": "PRO", "remaining_credits": 64523, ...}}`

#### 2. POST /search-company (1 credit/page)

```bash
curl -s -X POST "https://api.prospeo.io/search-company" \
  -H "X-KEY: $KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "filters": {
      "company_location_search": {"include": ["United States"]},
      "company_headcount_range": ["11-20", "21-50"],
      "company_industry": {"include": ["Software Development"]},
      "company_type": {"status": "Private", "business_model": "b2b"}
    },
    "page": 1
  }'
```

**Critical**: Filters go inside a `"filters": {}` wrapper. `"page"` is a sibling of `"filters"`, NOT inside it.

Response: `{"results": [...], "pagination": {"current_page": 1, "total_page": 80, "total_count": 1991}}`

#### 3. POST /search-suggestions (free, 15 req/sec rate limit)

**Each search type uses its own body key.** Send exactly ONE key per request.

| To resolve | Body key | Response key |
|-----------|----------|-------------|
| Locations | `"location_search"` | `location_suggestions` → `[{"name": "...", "type": "COUNTRY/STATE/CITY/ZONE"}]` |
| Technologies | `"technology_search"` | `technology_suggestions` → `["HubSpot", "HubSpot Analytics", ...]` |
| Industries | `"industry_search"` | `industry_suggestions` → `["Software Development", ...]` |
| Job titles | `"job_title_search"` | `job_title_suggestions` → `["sales development representative", ...]` |
| NAICS codes | `"naics_search"` | `naics_suggestions` → `[{"code": "5132", "label": "Software Publishers"}]` |
| SIC codes | `"sic_search"` | `sic_suggestions` → `[{"code": "7371", "label": "..."}]` |
| Integrations | `"company_integrations_search"` | `company_integrations_suggestions` → `["Salesforce", ...]` |
| Awards | `"company_awards_search"` | `company_awards_suggestions` |
| Compliance | `"company_awards_compliance_search"` | `company_awards_compliance_suggestions` |
| Key customers | `"company_key_customers_search"` | `company_key_customers_suggestions` |
| Investors | `"company_funding_investors_search"` | `company_funding_investors_suggestions` |
| Accelerators | `"company_funding_accelerator_search"` | `company_funding_accelerator_suggestions` |
| Operating languages | `"company_operating_languages_search"` | `company_operating_languages_suggestions` |
| SEO keywords | `"company_google_discovery_search"` | `company_google_discovery_suggestions` |
| Products | `"company_products_services_products_search"` | `company_products_services_products_suggestions` |
| Services | `"company_products_services_services_search"` | `company_products_services_services_suggestions` |
| ICP titles | `"company_icp_titles_search"` | `company_icp_titles_suggestions` |
| ICP industries | `"company_icp_industries_search"` | `company_icp_industries_suggestions` |
| ICP geo markets | `"company_icp_geographic_markets_search"` | `company_icp_geographic_markets_suggestions` |
| ICP departments | `"company_icp_other_departments_search"` | `company_icp_other_departments_suggestions` |
| Headcount by location | `"company_headcount_by_location_search"` | `company_headcount_by_location_suggestions` |
| Traffic countries | `"company_website_traffic_countries_search"` | `company_website_traffic_countries_suggestions` |

**Examples:**

```bash
# Location
curl -s -X POST "https://api.prospeo.io/search-suggestions" \
  -H "X-KEY: $KEY" -H "Content-Type: application/json" \
  -d '{"location_search": "united states"}'

# Technology
curl -s -X POST "https://api.prospeo.io/search-suggestions" \
  -H "X-KEY: $KEY" -H "Content-Type: application/json" \
  -d '{"technology_search": "hubspot"}'

# Industry
curl -s -X POST "https://api.prospeo.io/search-suggestions" \
  -H "X-KEY: $KEY" -H "Content-Type: application/json" \
  -d '{"industry_search": "software"}'

# Job title
curl -s -X POST "https://api.prospeo.io/search-suggestions" \
  -H "X-KEY: $KEY" -H "Content-Type: application/json" \
  -d '{"job_title_search": "sales development"}'

# NAICS (by code prefix or label text)
curl -s -X POST "https://api.prospeo.io/search-suggestions" \
  -H "X-KEY: $KEY" -H "Content-Type: application/json" \
  -d '{"naics_search": "5132"}'

# Company filter field (integrations, investors, etc.)
curl -s -X POST "https://api.prospeo.io/search-suggestions" \
  -H "X-KEY: $KEY" -H "Content-Type: application/json" \
  -d '{"company_funding_investors_search": "sequoia"}'
```

**Common mistakes — do NOT use these formats:**
- ~~`{"type": "location", "query": "..."}`~~ — wrong, this is the MCP abstraction
- ~~`{"filter_id": "company_location_search", "query": "..."}`~~ — wrong, this is the local MCP server format
- ~~`{"filter": "location", "query": "..."}`~~ — wrong field names
- Must send exactly ONE search key per request, min 2 characters

### API docs reference

- Search suggestions: https://prospeo.io/api-docs/search-suggestions
- Search company: https://prospeo.io/api-docs/search-company
- Filters documentation: https://prospeo.io/api-docs/filters-documentation
- Enum values: https://prospeo.io/api-docs/enum

### Enum Values Reference

All valid filter values are stored in `references/prospeo-enums.json` (refreshed every 21 days via `references/enum-refresh.md`).
Do NOT guess or invent values — always check the enum cache or resolve via search-suggestions curl.

- **Cached in `prospeo-enums.json`**: industries (256), subtypes (27), funding stages (23), employee ranges (11), revenue ranges (14), seniorities (10), business models (8), company statuses (4), email providers (5), news categories (10), exec events (24), ICP departments (15), ICP company sizes (5), headcount growth departments (19), headcount by department (14)
- **Resolve at runtime via curl**: technologies (4,946) → `{"technology_search": "..."}`, locations → `{"location_search": "..."}`, plus all company filter fields (integrations, investors, awards, etc.)
- **API docs for all enums**: https://prospeo.io/api-docs/enum

**Critical rule — Lookalike filter:**
- **NEVER include `company_lookalike` in the final search.** Stacking lookalike + ICP filters narrows results to single digits.
- Lookalike is **discovery-only** — use it to analyze patterns and recommend ICP filters, then drop it before the final search.
- Always warn the user that lookalike was removed and why. If they insist on adding it, allow it but warn about the dramatically smaller result set.

---

## Step 0 — Plan Detection & Cache Check

Run these two checks before anything else. They gate which filters and flows are available.

### 0A — Detect Prospeo Plan

Call `GET https://api.prospeo.io/account-information` with the `X-KEY` header.

Read from the response:
- `plan` — Free, Starter, Growth, or Pro
- `credits_remaining` — current balance
- `renewal_date` — when credits reset

Store as `PLAN`, `CREDITS`, `RENEWAL`.

If `CREDITS` < 10, warn the user:
> You have {CREDITS} credits remaining (renews {RENEWAL}). Each search page costs 1 credit. Proceed carefully or top up first.

Map the plan to available filters. Read `references/plan-filter-map.md` for the full mapping. Key rules:
- **Free**: 17 filters (no revenue, funding, technology, lookalike, job postings)
- **Starter**: 23 filters (adds revenue, funding, technology, lookalike, job postings)
- **Growth**: 29 filters (adds ICP, integrations, awards, key customers, headcount by location)
- **Pro**: all 33 filters (adds exec changes, website traffic, website search, SEO keywords)

Only offer filters the user's plan supports. Never ask about unavailable filters.

### 0B — Check Enum Cache

Read `references/prospeo-enums.json`. Check the `last_updated` field.

- If file is missing or `last_updated` is older than 21 days: refresh the cache. Read `references/enum-refresh.md` for the refresh procedure.
- If fresh: proceed with cached values.

The enum cache contains all valid values for industries (256), subtypes (27), funding stages (23), employee ranges (11), revenue ranges (14), departments, seniorities, business models, news categories, exec events, and more.

Technologies (4,946) and locations are too large to cache — use `POST /search-suggestions` at runtime when the user mentions specific tech or locations.

---

## Step 1 — Classify the User

Read the user's input and classify into one of five types based on what they provided.

**Parse the input for**:
- ICP filters (industry, headcount, location, funding, revenue, keywords, company type, etc.)
- Lookalike signals (seed domains, "similar to", "like X", company names to match)
- Vague terms that need mapping ("tech", "healthcare", "fintech", etc.)

**Classification logic**:

| Provided ICP filters | Provided lookalike domains | Type | Mode |
|---------------------|---------------------------|------|------|
| 4-5 mandatory filters covered | No | Type 1 — Expert | `build` |
| 1-3 filters, or vague terms | No | Type 2 — Partial | `guide` |
| 4-5 mandatory filters covered | Yes | Type 3 — Expert + Lookalike | `build+lookalike` |
| 1-3 filters, or vague terms | Yes | Type 4 — Partial + Lookalike | `guide+lookalike` |
| None | Yes (2+ domains) | Type 5 — Lookalike Only | `lookalike` |

### Mandatory Filters (5 for Starter+, 3 for Free)

These filters produce a usable list. The skill ensures they're all covered before running the final search.

**Starter/Growth/Pro (5 mandatory)**:
1. **Location** — no safe default, always ask
2. **Company size** (headcount) — default: `["11-20", "21-50", "51-100", "101-200", "201-500"]`
3. **Industry OR keywords OR subtype** — at least one definition of company type
4. **Company status** — default: `"Private"`
5. **Revenue** — smart default based on headcount: 11-50 emp = `"1M"-"10M"`, 51-200 = `"5M"-"50M"`, 201-500 = `"10M"-"100M"`

**Free plan (3 mandatory)** — revenue not available:
1. Location
2. Company size
3. Industry OR keywords OR subtype
(Status defaults to Private)

If the user gives 3-4 of 5, recommend the missing ones with defaults. If 1-2, enter guide mode for the rest.

---

## Step 2 — Execute by Type

### Type 1 — Expert (build mode)

1. Parse the user's plain English into Prospeo filter JSON
2. Map every term to exact Prospeo enum values — read `references/prospeo-enums.json` for valid values
3. For location and technology terms, call `POST /search-suggestions` to resolve valid values
4. If a term is ambiguous (e.g., "tech"), show matching options from the enum cache and ask the user to pick
5. Build the complete filter JSON
6. Show the assembled filters to the user for confirmation
7. Proceed to Step 2.5 (recommend optional filters), then Step 3 (Search)

### Type 2 — Partial (guide mode)

The skill becomes a recommendation engine. For each vague or missing input:

1. **Interpret vague terms**. When the user says something like "tech" or "healthcare":
   - Read `references/prospeo-enums.json` for industries, subtypes, business models, and attribute flags
   - Find all matching values across multiple filter types
   - Present them grouped by filter type, let the user pick

   Example — user says "tech":
   > Matching Prospeo filters for "tech":
   >
   > **Industries**: Software Development, IT Services and IT Consulting, Technology Information and Internet, Computer Hardware Manufacturing, Computer Networking Products
   >
   > **Subtypes**: SaaS, Platform, AI/ML, Data/Analytics, Hardware
   >
   > **Attributes**: uses_ai, has_api
   >
   > Which of these match your target?

2. **Ask for missing mandatory filters one at a time**. Only ask about filters available on the user's plan. Offer smart defaults:
   > You've set industry and location. Still need:
   > - **Company size** — typical outbound range is 11-500 employees. Sound right?
   > - **Revenue** — based on that size, I'd suggest $1M-$50M. Adjust?

3. Build filters incrementally. After each answer, add to the running filter set.

4. Once all mandatory filters are covered, show the complete filter JSON and proceed to Step 2.5 (recommend optional filters), then Step 3.

### Type 3 — Expert + Lookalike (build+lookalike mode)

1. Parse the full ICP into filters (same as Type 1)
2. **Drop the lookalike filter from the final search** — do NOT stack `company_lookalike` with ICP filters. Combining them produces extremely narrow results (often <10 companies).
3. **Warn the user**:
   > Note: I'm using the seed domain(s) for reference only — not adding lookalike to the search filters. Stacking lookalike + ICP filters together narrows results dramatically (often to single digits). Your ICP filters alone will produce a much better list.
   >
   > If you still want to add the lookalike filter, I can — but expect a much smaller result set.
4. Build the search with ICP filters only
5. Proceed to Step 2.5 (recommend optional filters), then Step 3

### Type 4 — Partial + Lookalike (guide+lookalike mode)

Lookalike is used **only for discovery** — to analyze patterns and recommend missing filters. It is **never included in the final search**.

1. **Keep the user's known filters** (location, headcount, whatever they gave)
2. **Run a discovery-only lookalike search** with `company_lookalike` (domain mode) + known filters. Fetch page 1 only (25 results, 1 credit)
3. **Analyze the 25 results** to discover what's missing from the mandatory filters:
   - Count industries — which ones dominate?
   - Count headcount ranges — what's the typical size?
   - Count locations — where are they concentrated?
   - Note revenue ranges, funding stages, common keywords
4. **Present findings and recommend additions**:
   > You gave: location (US, Germany), size (50-500)
   > From 25 similar companies I found:
   > - Top industries: Software Development (60%), Motor Vehicle Manufacturing (20%)
   > - Funding: mostly Series A-C
   > - Keywords: autonomous, ML, robotics
   > - Revenue: $5M-$100M range
   >
   > Want to add these filters? Or pick specific ones?
5. **Merge** user-confirmed additions with their original filters
6. **Drop the lookalike filter** from the final search. **Warn the user**:
   > Note: Lookalike filter removed from the final search. Stacking lookalike + ICP filters together narrows results dramatically. Your ICP filters alone will produce a much better list.
   >
   > If you still want to add it, I can — but expect a much smaller result set.
7. Proceed to Step 2.5 (recommend optional filters), then Step 3 with the merged ICP filters only

### Type 5 — Lookalike Only (lookalike mode)

Lookalike is used **only for discovery** — to build an ICP from scratch. It is **never included in the final search**.

1. **Get seed company IDs**: search `company.websites.include` with all seed domains (1 credit)
2. **Run lookalike**: `company_lookalike` with `company_oids`, `match_all: false`, `minimum_tier: "T2"` (1 credit)
3. **Analyze all 25 results** — the search response includes name, domain, industry, headcount, location, funding, revenue, keywords, LinkedIn. No export needed.
4. **Extract patterns** for ALL mandatory filters:
   - Location distribution
   - Headcount distribution
   - Top industries + keywords
   - Revenue ranges
   - Funding stages
   - Company status (mostly Private?)
5. **Present the full ICP recommendation** built from patterns
6. **User confirms or adjusts**
7. **Build the filter package** from confirmed patterns — **without the lookalike filter**
8. **Warn the user**:
   > Note: Lookalike filter removed from the final search. Stacking lookalike + ICP filters together narrows results dramatically. The ICP filters I built from the lookalike analysis will produce a much better list.
   >
   > If you still want to add it, I can — but expect a much smaller result set.
9. Proceed to Step 2.5 with ICP filters only

---

## Step 2.5 — Recommend Optional Filters (Smart, Data-Driven)

After all mandatory filters are covered (for ANY user type), **always recommend relevant optional filters** before running the search. The skill has 33 filters — use them. Don't just stop at the 5 mandatory ones.

**Be smart, not generic.** Use ALL context available to make specific, data-driven recommendations with actual values — not just filter category names.

### Context Sources (use all that apply)

1. **Lookalike discovery data** (Types 4 & 5) — you already analyzed 25 companies. Use the patterns:
   - If most had funding → recommend specific stages you saw (e.g., "60% were Series A-C, want to filter to funded companies only?")
   - If common tech stacks appeared → recommend those specific technologies
   - If most were founded after 2015 → recommend a founded year filter
   - If you saw common keywords → suggest adding them as keyword filters

2. **User's input language** — what they said reveals intent:
   - "funded", "raised", "VC-backed" → funding filters with specific values
   - Technology names → `company_technology` with those exact tools
   - "growing", "scaling" → headcount growth with suggested %
   - "hiring" → job posting filters
   - "new companies" → founded year range

3. **ICP context** — what the selected industry/type implies:
   - SaaS/software → has_api, has_sso, public_pricing, free_trial, uses_ai, subscription model
   - B2B → business_model, self_serve, sales_led, enterprise_plan
   - Compliance-heavy (healthcare, fintech) → SOC 2, GDPR, HIPAA
   - Hardware/manufacturing → has_physical_offices, specific NAICS codes

4. **Plan capabilities** — recommend premium filters the user's plan supports:
   - Starter+: technology, funding, job postings
   - Growth+: ICP, integrations, awards, key customers
   - Pro: exec changes, website traffic, SEO keywords

### How to Recommend

Present **3-5 specific, actionable recommendations** with actual suggested values. Each recommendation should explain WHY it's relevant to their search.

**Example for Type 4 (after lookalike discovery of AV/robotics companies):**

> **Optional filters to sharpen your list:**
>
> 1. **Funding** — 40% of similar companies had no funding data. Want to filter to only funded companies? I'd suggest Series A through Series D based on the AV space.
> 2. **Technology** — common tech in this space includes AWS, Python, TensorFlow. Want to target companies using specific tools?
> 3. **Headcount growth** — filter to companies growing 20%+ in the last 12 months to find scaling AV companies
> 4. **Founded year** — most similar companies were founded 2010-2020. Want to exclude older legacy companies?
> 5. **Company attributes** — since these are AI/ML companies: `uses_ai = true` would ensure they're genuinely AI-focused
>
> Pick any, or skip to run the search?

**Example for Type 1 (B2B SaaS search):**

> **Optional filters to sharpen your list:**
>
> 1. **Technology** — target companies using HubSpot, Salesforce, or Intercom to find your competitor's customers
> 2. **Attributes** — has_api = true, has_public_pricing = true to find product-led companies
> 3. **Hiring** — companies hiring for "sales" or "SDR" roles are actively building outbound teams
> 4. **Growth** — 20%+ headcount growth in 12 months to find fast-scaling companies
>
> Pick any, or skip to run the search?

### Rules

- **Be specific** — "Series A-C funding in the last 12 months" not "you could add a funding filter"
- **Explain why** — tie each recommendation to their search context
- **Use discovered data** — if you ran a lookalike or analysis, reference what you found
- **Max 5 recommendations** — pick the most impactful, don't dump all 33
- **Don't repeat** — if the user already set a filter (e.g., funding), don't recommend it again
- **Quick exit** — if user says "skip", "no", "just run it" → proceed immediately to Step 3. Don't push.

---

## After Step 0 — Prompt the User

All of Step 0 is internal. Do NOT show the user plan detection steps, cache checks, or any internal process. No "Running Step 0", no "checking cache", no step numbers.

Present a clean, professional status and ask what they need:

```
Prospeo Discovery ready.
Plan: {PLAN} | Credits: {CREDITS} | Renews: {RENEWAL}
{filter_count} filters available.

What companies are you looking for?
```

Wait for the user's input before proceeding. Do NOT show examples, sample company names, or tutorial prompts.

---

## Step 3 — Search & Present Results

Run `POST /search-company` with the assembled filters via curl in Bash, `page: 1`.

Present results in a clean format:

```
Found {total_count} companies matching your filters.

Filters applied:
- Location: {locations}
- Industry: {industries}
- Size: {headcount_ranges}
- Status: {status}
- Revenue: {revenue_range}
{any additional filters}

Preview (top 25):
| # | Company | Domain | Industry | Employees | Location | Revenue | Funding |
|---|---------|--------|----------|-----------|----------|---------|---------|
| 1 | ... | ... | ... | ... | ... | ... | ... |

Credits used: 1 | Full export: {total_pages} credits | Balance: {CREDITS - 1}

Next steps:
1. Export full list
2. Narrow down
3. Adjust filters
```

If `total_count` > 2,000: recommend narrowing down before full export.

If `total_count` < 10: suggest loosening filters (broader headcount range, more industries, higher tier for lookalike).

---

## Step 4 — Export (on user request only)

Only export when the user explicitly asks. **Always use the Python export script** — never use MCP tools or manual API pagination for exports.

### Export Script

**Script location**: `scripts/sheets_export.py`
**Dependencies**: `pip install requests gspread google-auth`

### Export Procedure

1. **Save the current filter JSON to a temp file**:
   ```bash
   cat > /tmp/prospeo_filters.json << 'EOF'
   {filters JSON here}
   EOF
   ```

2. **Run the export script**:
   ```bash
   # New spreadsheet (auto-created):
   python3 scripts/sheets_export.py --filters /tmp/prospeo_filters.json

   # Existing spreadsheet (user provided URL/ID):
   python3 scripts/sheets_export.py --filters /tmp/prospeo_filters.json --spreadsheet-id SHEET_ID

   # Custom tab name:
   python3 scripts/sheets_export.py --filters /tmp/prospeo_filters.json --tab-name "my-search"

   # Cap pages (for very large result sets):
   python3 scripts/sheets_export.py --filters /tmp/prospeo_filters.json --max-pages 20

   # Dry run (preview count without spending credits):
   python3 scripts/sheets_export.py --filters /tmp/prospeo_filters.json --dry-run
   ```

3. **Share the spreadsheet URL** with the user from the script output.

### What the Script Does

- Fetches all pages from Prospeo `/search-company` automatically
- Creates two tabs: **Results** (15-column company data) + **Search Info** (filters & metadata)
- Writes in batches of 50 rows with retry on error
- Rate-limits both Prospeo API (0.5s) and Google Sheets API (1s between batches)
- Built-in cost guard: confirms with user before fetching >10 pages
- Handles 3,000-5,000+ company exports that MCP tools cannot

### Results Tab Columns

| Column | Prospeo Response Field |
|--------|----------------------|
| Company | `name` |
| Domain | `website` or `primary_domain` |
| Industry | `industry` |
| Employees | `employee_count` |
| Employee Range | `employee_range` |
| HQ City | `city` |
| HQ State | `state` |
| Country | `country` |
| Revenue | `revenue_range_printed` |
| Funding Stage | `last_funding_type` |
| Total Funding | `total_funding` |
| Latest Funding Date | `last_funding_date` |
| LinkedIn URL | `linkedin_url` |
| Keywords | `keywords` (first 15, comma-joined) |
| Founded | `founded` |

### Cost Guard

Before running export, tell the user:
> Full export: {total_pages} pages = {total_pages} credits. Your balance: {CREDITS} credits. Proceed?

If `total_count` > 2,000: recommend `--dry-run` first, then confirm.

Default to displaying first 25 (already done in Step 3) if user doesn't specify export.

---

## Filter Mapping Reference

When mapping user input to Prospeo filters, read `references/filters-full.md` for the complete 33-filter reference with all accepted values and types.

Key mappings for common plain-English terms:

| User says | Maps to |
|-----------|---------|
| "US", "America" | `company_location_search.include: ["United States"]` |
| "B2B SaaS" | `company_type: {business_model: "b2b", subtypes: {include: ["SaaS"]}}` |
| "AI company" | `company_type: {is_mainly_ai: true}` |
| "50-200 employees" | `company_headcount_range: ["51-100", "101-200"]` |
| "Series A" | `company_funding: {stage: ["Series A"]}` |
| "raised recently" | `company_funding: {funding_date: 365}` |
| "growing fast" | `company_headcount_growth: {timeframe_month: 12, min: 20}` |
| "hiring engineers" | `company_job_posting_hiring_for: {include: ["engineer"], match_type: "contains"}` |
| "similar to X.com" | `company_lookalike: {domain: "X.com", minimum_tier: "T2"}` |
| "exclude consulting" | `company_industry: {exclude: ["Management Consulting"]}` |

For ambiguous terms, always check the enum cache first, then present matching options to the user.

---

## Examples

### Type 1 — Expert (full ICP)
> User provides: industry, location, headcount, funding, status, revenue, exclusions

Skill maps all terms to Prospeo filter JSON, confirms with user, runs search, shows count + 25-row preview.

### Type 2 — Partial (vague input)
> User provides: a broad category + one location, nothing else

Skill interprets the vague term against enum cache, shows matching industries/subtypes/attributes, asks for missing mandatory filters one at a time with smart defaults. Builds filters incrementally.

### Type 3 — Expert + Lookalike
> User provides: full ICP filters + a seed domain

Skill parses ICP into filters, uses seed domain for reference only. Lookalike is NOT added to the final search — warns user that stacking narrows results to single digits. Runs search with ICP filters only.

### Type 4 — Partial + Lookalike
> User provides: partial filters (e.g., location + headcount) + seed domain(s)

Skill keeps known filters, runs lookalike for discovery only (1 credit, 25 results), analyzes patterns, recommends missing filters, merges on confirmation. Drops lookalike from final search, runs with ICP filters only.

### Type 5 — Lookalike Only
> User provides: 2+ seed domains, no ICP filters

Skill gets company IDs, runs lookalike for discovery only (1-2 credits), analyzes 25 results for patterns across all mandatory filters, builds full ICP recommendation. Drops lookalike from final search, runs with ICP filters only.
