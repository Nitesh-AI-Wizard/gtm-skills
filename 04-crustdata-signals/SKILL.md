---
name: crustdata-signals
description: >
  Enriches company domains with structured signals from CrustData — funding
  rounds, headcount growth, department growth, and recent hires. Use when the
  user wants to pull company signals, enrich domains with funding/growth/hiring
  data, check who recently joined a company, find new hires at a domain, get
  headcount trends, or anything involving CrustData enrichment. Also triggers
  on: "run crustdata signals", "enrich these domains", "pull funding data",
  "who joined recently", "headcount growth for these companies", "department
  growth", "recent hires at", "crustdata enrich".
---

# CrustData Signals

Enrich company domains with structured signal data (funding, growth,
departments, recent hires) and write results to Google Sheets across 5 tabs.

## Inputs

1. **Domains** — a Google Sheet link/ID with a domain column, or a raw list
2. **Hire window** (optional) — 90, 180, or 365 days back for recent hires (default: 180)
3. **Output destination** — same sheet (new tabs), different sheet ID, or create new

If the user provides a sheet link, extract the spreadsheet ID and ask which tab
and column contain the domains.

## Prerequisites

- `CRUSTDATA_API_KEY` env var — get your API key from the [CrustData dashboard](https://crustdata.com)
- Python packages: `pip install -r ../_shared/requirements.txt` (Sheets export uses the optional `gspread`/`google-auth` extras)
- Google Sheets OAuth2 token at `~/.google/token.json`

## Credit rules

Each API call costs real credits. Treat them like money.

| API | Cost | Rate limit |
|-----|------|------------|
| `/company/enrich` | 2 credits/company | 15 RPM |
| `/person/search` | 0.03 credits/result | 30 RPM |

Typical cost: ~2.6 credits per domain (2 enrich + ~0.6 for ~20 hires).

**JSON files are the source of truth.** Every API call saves a per-domain JSON
to `outputs/{run-id}/`. Before calling the API for any domain, check whether a
JSON already exists in any prior run folder. If it does, reuse it — do not
spend credits again. The sheets writer can combine multiple run folders.

## Process

### 1. Collect inputs

Ask the user for domain source, hire window, and output destination. Default to
180-day hire window if not specified.

### 2. Run enrichment

```bash
export CRUSTDATA_API_KEY=<your-crustdata-api-key>

# From a list of domains
python3 .claude/skills/crustdata-signals/scripts/crustdata_signals.py \
  --domains domain1.com,domain2.com \
  --hire-days 180

# From a Google Sheet
python3 .claude/skills/crustdata-signals/scripts/crustdata_signals.py \
  --sheet-id <SHEET_ID> --tab "Sheet1" --domain-col B \
  --hire-days 180
```

The script saves per-domain JSON files to `outputs/{run-id}/` and maintains a
`tracker.json` for resume. If it fails mid-run, resume with
`--resume --output-dir outputs/{run-id}`.

### 3. Write to Google Sheets

```bash
# Single run folder
python3 .claude/skills/crustdata-signals/scripts/sheets_writer.py \
  --run-dir .claude/skills/crustdata-signals/outputs/{run-id} \
  --spreadsheet-id <SHEET_ID>

# Combine multiple run folders (dedupes by domain)
python3 .claude/skills/crustdata-signals/scripts/sheets_writer.py \
  --run-dir outputs/run-A outputs/run-B outputs/run-C \
  --spreadsheet-id <SHEET_ID>

# Create a new sheet
python3 .claude/skills/crustdata-signals/scripts/sheets_writer.py \
  --run-dir outputs/{run-id} \
  --create-new --title "CrustData Signals - Jul 2026"
```

The writer accepts multiple `--run-dir` paths and deduplicates by domain. This
means you can enrich domains across separate sessions and combine them into one
sheet without re-running the API.

### Output tabs

| Tab | Grain | Key columns |
|-----|-------|-------------|
| Signal Summary | 1 row/domain | Company info, key metrics, signal analysis (Funding/Growth/Dept/Hiring/Summary) |
| Recent Hires | 1 row/person | Name, title, start date, days since joining, seniority, function |
| Funding | 1 row/round | Date, round type, amount, lead investors, all investors |
| Company Growth | 1 row/domain | Headcount + MoM/QoQ/6m/YoY growth (% and absolute) |
| Dept Growth | 1 row/domain-dept | Department, current headcount, 6m ago, YoY ago, growth % |

### 4. Save run summary

After writing to sheets, save a markdown summary to
`.claude/skills/crustdata-signals/runs/{run-id}.md` with: date, domain count,
hire window, credits consumed, domains processed/failed/skipped, sheet URL.

### 5. Clean up (ask first)

Ask the user whether to keep or delete the JSON backup files. They can always
be regenerated but that costs credits again.

## Signal analysis columns

The sheets writer auto-generates signal text:

- **Funding Signal**: "Series A $20M raised 45d ago - FRESH CAPITAL | 3 rounds total"
- **Growth Signal**: "Growing 32% YoY (+76 employees) - STRONG GROWTH | 202 employees"
- **Dept Signal**: "Engineering 23% | Operations 23%"
- **Hiring Signal**: "Senior hires: VP Sales, Head of Eng | 42 new hires | 5 open roles"
- **Signal Summary**: All signals combined

## Key behaviors

- Enrich costs 2 credits regardless of fields requested — always pull all 19 field groups.
- Pre-computed growth fields from CrustData lag by 3–10 months. The script computes fresh growth from timeseries data.
- `basic_info.industries` is often null. The writer falls back to `taxonomy.categories` then `taxonomy.professional_network_industries`.
- Department keys from CrustData are Title Case with spaces (e.g. "Engineering", "Human Resources"). The writer handles this automatically.
- Department timeseries uses `employee_count` as the key (not `headcount`).
- Some companies return `updated_at: null` — a genuine coverage gap, not staleness.
- Rate limiting is handled automatically with conservative delays.

## Shared output (records.jsonl)

After enrichment completes, the script writes a `records.jsonl` file to the output
directory. Each line is one domain in the shared record format consumed by
downstream skills (signal-builder, resolution):

```jsonl
{"company": "Serve Robotics", "domain": "serverobotics.com", "person": null, "filters_matched": ["Series B $56M", "350 employees", "42% YoY growth", "18 recent hires"]}
```

The `filters_matched` field summarizes the key signals found. This file is
additive - existing per-domain JSONs, tracker, and Sheet outputs are unchanged.

## References

- `references/enrich-api.md` — company enrich endpoint docs
- `references/person-search-api.md` — person search endpoint docs
- [CrustData API docs](https://crustdata.com/docs) — API keys, auth headers, industry taxonomy
