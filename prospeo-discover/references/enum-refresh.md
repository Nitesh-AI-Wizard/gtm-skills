# Enum Cache Refresh Procedure

How to refresh `prospeo-enums.json` when it's older than 21 days or missing.

## When to Refresh

- File `references/prospeo-enums.json` does not exist
- `last_updated` field is older than 21 days from today

## What Gets Refreshed

### Hardcoded values (from Prospeo API schema — rarely change)

Write these directly — no API call needed:

- `employee_ranges` — 11 values
- `revenue_ranges` — 14 values
- `funding_stages` — 23 values
- `subtypes` — 27 values
- `departments` — 14 values
- `headcount_growth_departments` — 19 values
- `seniorities` — 10 values
- `business_models` — 8 values
- `news_categories` — 10 values
- `exec_events` — 24 values
- `email_providers` — 5 values
- `icp_departments` — 15 values
- `icp_company_sizes` — 5 values
- `company_statuses` — 4 values

### Fetched via API (may grow over time)

Use `mcp__prospeo__search_suggestions` with `type: "industry"` to refresh industries.

**Procedure for industries** (target: 256 values):

1. Run search_suggestions with these 2-char prefixes to maximize coverage:
   ```
   ac, ad, ae, ag, ai, al, am, an, ap, ar, as, au, av
   bi, bl, bo, br, bu
   ca, ch, ci, cl, co, cr, cu
   da, de, di, do
   ed, el, en, ev, ex
   fa, fi, fo, fr, fu
   ga, ge, gl, go, gr, gu
   he, hi, ho, hu
   in, it
   la, le, li, lo, lu
   ma, me, mi, mo, mu
   na, no, nu
   of, oi, op, ou
   pa, pe, ph, pl, po, pr, pu
   ra, re, ri, ro, ru
   sa, sc, se, si, so, sp, st, su
   te, th, to, tr, tu
   ut
   ve, vo
   wa, wh, wi, wo
   ```

2. Collect all unique values from all responses
3. Sort alphabetically
4. Write to `industries` array in the JSON file

**Rate limit**: 15 requests/second. No credit cost.

### NOT cached (fetched at runtime)

- **Technologies** (4,946 values) — use `search_suggestions` with `type: "technology"` when user mentions a specific tech
- **Locations** — use `search_suggestions` with `type: "location"` when user mentions a place
- **Job titles** — use `search_suggestions` with `type: "job_title"` when needed

## After Refresh

Update `last_updated` to today's date in ISO format: `"2026-06-22"`.
