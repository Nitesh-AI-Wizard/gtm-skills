# Enum Cache Refresh Procedure

How to refresh `aiark-enums.json` when it's older than 30 days or missing.

## When to Refresh

- File `references/aiark-enums.json` does not exist
- `last_updated` field is older than 30 days from today

## What Gets Refreshed

### Fetched from MCP resources (may grow over time)

These are pulled from AI Ark MCP resources. Use `ReadMcpResourceTool` with server `ai-ark`.

| Field | MCP Resource URI | Current Count |
|-------|-----------------|---------------|
| `industries` | `ark://reference/industries` | 921 |
| `languages` | `ark://reference/languages` | 48 |
| `countries_by_continent` + `continents` + `countries` | `ark://reference/locations` | 23 continents, 262 countries, 4,919 states |
| `technologies` | `ark://reference/technologies` | 16,041 (all, sorted alphabetically) |

**Refresh procedure:**

1. Read all 4 MCP resources in parallel
2. Parse each JSON response:
   - **Industries**: Direct array, sort alphabetically
   - **Languages**: Direct array, keep as-is
   - **Locations**: Hierarchical `continent > country > states`. Extract continents (top-level keys), countries (second-level keys), and build `countries_by_continent` mapping. States are available but too numerous to cache — resolve at runtime.
   - **Technologies**: Array of `{"key": "...", "doc_count": N}` objects sorted by popularity. Extract all keys, sort alphabetically.
3. Write updated values to `aiark-enums.json`
4. Update `last_updated` to today's date

### Hardcoded values (from API docs — rarely change)

Write these directly — no API call needed:

- `company_types` — 8 values: privately_held, public_company, self_owned, self_employed, partnership, non_profit, educational, government_agency
- `funding_types` — 19 values: pre_seed, seed, angel, venture, series_a through series_f, series_unknown, debt, grant, equity, convertible_note, private_equity, ipo, post_ipo, undisclosed
- `social_media_platforms` — 6 values: TWITTER, FACEBOOK, LINKEDIN, INSTAGRAM, YOUTUBE, GITHUB
- `metric_timeframes` — 5 values: one (1mo), three (3mo), six (6mo), twelve (12mo), twenty_four (24mo)
- `metric_departments` — 27 values (engineering, sales, marketing, etc.)
- `keyword_sources` — 5 values: NAME, KEYWORD, SEO, DESCRIPTION, INDUSTRY
- `keyword_modes` — 3 values: SMART, WORD, STRICT
- `range_filter_types` — 3 values: NONE, ALL, RANGE

### NOT cached (resolve at runtime)

These are too large or dynamic to cache:

- **States/regions** (4,919) — Use `location.country` filter with the country name; AI Ark handles state-level matching. Or use `geoLocation` for radius search.
- **All 16,041 technologies** — Top 500 are cached. For others, use `technologies` AdvanceFilter with SMART mode, which does fuzzy matching.

## After Refresh

Update `last_updated` to today's date in ISO format: `"2026-06-29"`.
