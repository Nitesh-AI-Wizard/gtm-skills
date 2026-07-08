---
name: prospeo-discover
description: >
  B2B company discovery and list building via the Prospeo search API. Use when the
  user wants to find companies, build a prospect or TAM list, search by ICP, find
  lookalike companies, or size a market - e.g. "find companies like X", "build a list
  of B2B SaaS in the US", "how many companies match this ICP", "TAM sizing", "company
  search", or any mix of industry + location + headcount + funding filters.
---

# Prospeo Discover — B2B Company List Builder

Turn a plain-English ICP into Prospeo filter JSON, run a company search against Prospeo's
30M+ company database (33 filters), present the result, and export to Google Sheets on request.

## Your job

1. Work out what the user has given you and what's still missing.
2. Map their language to exact Prospeo filter values. Resolve anything you're unsure of via the API rather than inventing enum values.
3. Cover the mandatory filters, using the smart defaults below for anything they skip.
4. Recommend a few high-impact optional filters, then stop.
5. Run the search, show the count plus a 25-row preview, and export only when asked.

Credits are real money: each search page costs 1 credit; account and suggestion calls are free. Guard spend, especially on export.

## Setup

Auth reads from environment variables. Nothing is hardcoded.

- `PROSPEO_API_KEY` - required for every Prospeo call.
- Google Sheets export reads OAuth credentials from `GOOGLE_TOKEN_PATH` (default `~/.google/token.json`). Only needed when exporting.

The curl examples use `$PROSPEO_API_KEY` as the key.

## API basics

```
Base URL: https://api.prospeo.io
Auth header: X-KEY: $PROSPEO_API_KEY
Content-Type: application/json
```

Three endpoints:

- `GET /account-information` - plan and credit balance (free)
- `POST /search-company` - the search (1 credit per page)
- `POST /search-suggestions` - resolve locations, technologies, industries, and other open-ended values (free)

The one body-shape rule that breaks searches when you get it wrong: filters go inside a `"filters": {}` wrapper, and `"page"` is a sibling of `"filters"`, not inside it.

```bash
curl -s -X POST "https://api.prospeo.io/search-company" \
  -H "X-KEY: $PROSPEO_API_KEY" -H "Content-Type: application/json" \
  -d '{"filters": { ...filter JSON... }, "page": 1}'
```

`search-suggestions` takes exactly one search key per request (min 2 chars) and is how you resolve any value you are not certain of. The full table of search keys and response keys, the worked curl examples, and the wrong formats to avoid live in `references/api-curl.md` - read it before resolving values for the first time in a session.

## Step 0 — Plan and enum check (internal, run once)

Do this silently before prompting the user. Don't narrate it or show step numbers.

**Plan and credits.** Call `GET /account-information` and read `current_plan` and `remaining_credits` from the `response` object (plus the renewal date if the response carries one). Store them. If `remaining_credits` is under 10, tell the user their balance and that each page costs 1 credit before spending anything.

Gate filters by plan. Only offer what the plan supports, and don't ask about filters it lacks. Full mapping in `references/plan-filter-map.md`:

- **Free**: 18 filters (no revenue, funding, technology, lookalike, or job postings)
- **Starter**: adds revenue, funding, technology, lookalike, job postings
- **Growth**: adds ICP, integrations, awards, key customers, headcount-by-location
- **Pro**: all 33 (adds exec changes, website traffic/search, SEO keywords)

**Enum cache.** Read `references/prospeo-enums.json` and check `last_updated`. If it's missing or older than 21 days, refresh it with `references/enum-refresh.md`; otherwise use the cached values. The cache holds valid values for industries (256), subtypes, funding stages, employee and revenue ranges, departments, and more. Technologies (4,946) and locations are too large to cache - resolve those at runtime via `search-suggestions`.

Then present a clean prompt and wait for input. Don't show examples or sample company names.

```
Prospeo Discovery ready.
Plan: {plan} | Credits: {credits} | {n} filters available.

What companies are you looking for?
```

## Step 1 — Read the input, pick the approach

Sort what the user gave you into three buckets:

- **ICP filters** - industry, size, location, funding, revenue, keywords, company type
- **Lookalike signals** - seed domains, "similar to X", named companies to match
- **Vague terms** that need mapping - "tech", "healthcare", "fintech"

That tells you how to proceed. You don't need to announce a "type" to the user, just route:

| What they gave | Approach |
|---|---|
| A full ICP (4-5 mandatory filters covered) | Map it to filter JSON and confirm |
| A partial or vague ICP | Guide them: interpret vague terms against the enum cache, then ask for missing mandatory filters one at a time with smart defaults |
| Seed domains or "similar to" | Use lookalike for discovery only (see below), then build an ICP from the patterns |

These combine. A user can hand you a partial ICP and a seed domain - run lookalike to fill the gaps, then merge what you find with what they already gave.

### Mandatory filters and smart defaults

A usable list needs these covered. Fill anything the user skips with the default, and tell them what you defaulted to:

1. **Location** - no safe default, always ask.
2. **Company size** - default `["11-20","21-50","51-100","101-200","201-500"]`.
3. **Industry / keywords / subtype** - at least one definition of the company.
4. **Status** - default `"Private"`.
5. **Revenue** (Starter+ only) - default by size: 11-50 employees → `"1M"`-`"10M"`, 51-200 → `"5M"`-`"50M"`, 201-500 → `"10M"`-`"100M"`.

On Free, revenue isn't available, so only the first three are mandatory.

For vague terms, read the enum cache, show the matching industries, subtypes, and attributes grouped by filter type, and let the user pick rather than guessing for them. `references/mapping-examples.md` has 20+ worked plain-English → filter JSON mappings - use it instead of inventing mappings.

### Lookalike is discovery-only

Lookalike is strong for *finding* an ICP and weak as a *filter* to search on. Stacking `company_lookalike` with ICP filters narrows results to single digits, so use it to analyze patterns and then drop it before the final search.

When the user gives seed domains:

1. For multiple domains, resolve them to Prospeo company IDs first (search `company.websites.include`, 1 credit), then run lookalike with `company_oids`, `match_all: false`, `minimum_tier: "T2"`. A single domain can use `{"domain": "..."}` directly.
2. Fetch page 1 only (25 results, 1 credit). The response already carries industry, headcount, location, funding, revenue, and keywords, so no export is needed to analyze.
3. Read the 25 for patterns across the mandatory filters: dominant industries, typical size, location concentration, funding stages, common keywords.
4. Present the pattern-built ICP, let the user confirm or adjust, and merge with anything they already gave.
5. Build the final search from the confirmed ICP **without** `company_lookalike`, and say so once:

> I used the seed domain(s) to find the pattern, not as a search filter. Stacking lookalike with ICP filters collapses the result set to single digits, so the ICP I built from them will give you a fuller list. I can add the lookalike filter back if you want, but expect far fewer results.

If the user insists on keeping the lookalike filter, allow it and restate the trade-off.

## Step 2 — Recommend optional filters, then stop

Once the mandatory filters are covered, recommend a few optional filters before running. The skill has 33 filters - use the ones that fit, don't stop at the mandatory five and don't dump all 33.

Draw recommendations from whatever context you have:

- **Lookalike discovery data** - if you analyzed 25 companies, reuse the patterns (funding stages you saw, common tech, founding years, recurring keywords).
- **The user's own language** - "funded"/"raised"/"VC-backed" → funding filters; named tools → `company_technology`; "growing"/"scaling" → headcount growth; "hiring" → job postings; "new companies" → founded year.
- **What the industry implies** - SaaS → `has_api`, `uses_ai`, subscription model; compliance-heavy (healthcare, fintech) → SOC 2, GDPR, HIPAA; hardware → physical offices, specific NAICS.
- **Plan capabilities** - only premium filters the plan supports.

Present 3-5 specific, actionable recommendations with real values, each tied to why it fits their search. "Series A-C funding in the last 12 months" beats "you could add a funding filter."

**Example (after lookalike discovery of AV/robotics companies):**

> Optional filters to sharpen your list:
> 1. **Funding** - 40% of the similar companies had no funding data. Filter to funded only? Series A-D fits the AV space.
> 2. **Technology** - common here: AWS, Python, TensorFlow. Target a specific stack?
> 3. **Headcount growth** - 20%+ over 12 months to catch the scaling ones.
> 4. **Founded year** - most were 2010-2020; exclude legacy players?
> 5. **Attributes** - `uses_ai = true` to keep it genuinely AI-focused.
>
> Pick any, or skip to run the search.

Rules: be specific, explain why, reuse anything you discovered, cap at 5, don't recommend a filter the user already set, and if they say "skip" or "just run it" go straight to the search without pushing.

## Step 3 — Search and present

Run `POST /search-company` with the assembled filters, `page: 1`. Present:

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
| 1 | ...     | ...    | ...      | ...       | ...      | ...     | ...     |

Credits used: 1 | Full export: {total_pages} credits | Balance: {credits - 1}

Next steps:
1. Export full list
2. Narrow down
3. Adjust filters
```

If `total_count` is over 2,000, suggest narrowing before a full export. If it's under 10, suggest loosening - a broader headcount range, more industries, or a broader lookalike tier.

## Step 4 — Export (only when asked)

Export uses the Python script, which paginates and writes to Google Sheets with batching and retries. Don't paginate the API by hand for exports.

**Script**: `scripts/sheets_export.py` · **Deps**: `pip install -r ../_shared/requirements.txt` (Sheets export needs the optional `gspread`/`google-auth` extras in that file)

```bash
# Preview count without spending export credits
python3 scripts/sheets_export.py --filters /tmp/prospeo_filters.json --dry-run

# New spreadsheet (auto-created)
python3 scripts/sheets_export.py --filters /tmp/prospeo_filters.json

# Existing spreadsheet, custom tab
python3 scripts/sheets_export.py --filters /tmp/prospeo_filters.json --spreadsheet-id SHEET_ID --tab-name "my-search"

# Cap pages for very large result sets
python3 scripts/sheets_export.py --filters /tmp/prospeo_filters.json --max-pages 20
```

Save the current filter JSON to the path you pass in `--filters`, then run the script and share the spreadsheet URL it prints.

**Before exporting**, show the cost and confirm:

> Full export: {total_pages} pages = {total_pages} credits. Your balance: {credits}. Proceed?

The script also asks for confirmation itself before fetching more than 10 pages, and `--dry-run` previews the count for free. It writes a **Results** tab (15 columns of company data) and a **Search Info** tab (filters and metadata), and handles 3,000-5,000+ company exports that the MCP tools can't.

## Shared output (records.jsonl)

After export, the script writes a `records.jsonl` file alongside the filters JSON.
Each line is one company in the shared record format consumed by downstream skills
(signal-builder, resolution):

```jsonl
{"company": "Acme Corp", "domain": "acme.com", "person": null, "filters_matched": ["Industry: Software Development", "Headcount Range: 51-100, 101-200"]}
```

This file is additive - existing Sheet and API outputs are unchanged.

## References

- `references/api-curl.md` - exact curl formats, the full search-suggestions key table, formats to avoid
- `references/filters-full.md` - all 33 filters with accepted values and types
- `references/plan-filter-map.md` - which filters each plan supports
- `references/mapping-examples.md` - 20+ plain-English → filter JSON examples
- `references/enum-refresh.md` - how to refresh the enum cache
- `references/prospeo-enums.json` - cached valid enum values
