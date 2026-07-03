---
name: crustdata-signals
description: >
  Enrich a list of company domains with structured signals from CrustData -
  funding rounds, headcount growth, department growth, and recent hires
  (people who joined in last N days). Use when the user wants to pull company
  signals, enrich domains with funding/growth/hiring data, run CrustData on a
  list, check who recently joined a company, find new hires at a domain, get
  headcount trends, or anything involving CrustData enrichment. Also triggers
  on: "run crustdata signals", "enrich these domains", "pull funding data",
  "who joined recently", "headcount growth for these companies",
  "department growth", "recent hires at", "crustdata enrich".
---

# CrustData Signals

You are the CrustData signal enrichment engine. You take a list of company
domains and produce structured signal data (funding, growth, departments,
recent hires) written to Google Sheets across 5 tabs.

## How to invoke

The user provides:
1. **Domains** - either a Google Sheet link/ID with a domain column, or a raw list of domains
2. **Hire window** (optional) - how far back to search for recent hires: 90, 180, or 365 days (default: 180)

If the user provides a sheet link, extract the spreadsheet ID and ask which tab and column contain the domains.

## Prerequisites

- **CrustData API key**: must be set as `CRUSTDATA_API_KEY` environment variable
  - Key is in `tech-stack/crustdata.md`
  - To set: `export CRUSTDATA_API_KEY=<your-key>`
- **Python packages**: `requests`, `gspread`, `google-auth`
- **Google Sheets auth**: OAuth2 token at `~/.google/token.json` (same as all other skills)

## Process

### Step 1: Collect inputs

Ask the user for:
- Domain source (sheet link or list)
- If sheet: which tab and which column has domains
- Hire window: 90, 180, or 365 days (default 180 if not specified)
- Where to write results: same sheet (new tabs), different sheet ID, or create new

### Step 2: Run the enrichment script

```bash
export CRUSTDATA_API_KEY=<your-key>

# From a list of domains
python3 .claude/skills/crustdata-signals/scripts/crustdata_signals.py \
  --domains domain1.com,domain2.com \
  --hire-days 180

# From a Google Sheet
python3 .claude/skills/crustdata-signals/scripts/crustdata_signals.py \
  --sheet-id <SHEET_ID> --tab "Sheet1" --domain-col A \
  --hire-days 180
```

The script:
- Calls `/company/enrich` for each domain (ALL 19 field groups, 2 credits each)
- Calls `/person/search` for recent hires per domain (0.03 credits/result)
- Saves per-domain JSON files to `outputs/{run-id}/`
- Maintains a `tracker.json` for resume capability
- If it fails mid-run, resume with: `--resume --output-dir outputs/{run-id}`

> **Note:** The `outputs/` and `runs/` directories do not exist by default. The script creates them automatically on first run.

### Step 3: Write to Google Sheets

```bash
# Write to existing sheet (adds 5 new tabs)
python3 .claude/skills/crustdata-signals/scripts/sheets_writer.py \
  --run-dir .claude/skills/crustdata-signals/outputs/{run-id} \
  --spreadsheet-id <SHEET_ID>

# Or create a new sheet
python3 .claude/skills/crustdata-signals/scripts/sheets_writer.py \
  --run-dir .claude/skills/crustdata-signals/outputs/{run-id} \
  --create-new --title "CrustData Signals - Client Name"
```

This writes 5 tabs:

| Tab | Structure | Content |
|---|---|---|
| **Signal Summary** | 1 row per domain | Company info + key metrics + signal analysis columns (Funding Signal, Growth Signal, Dept Signal, Hiring Signal, Signal Summary) |
| **Recent Hires** | 1 row per person | Name, title, start date, days since joining, seniority, function |
| **Funding** | 1 row per round | Date, round type, amount, lead investors, all investors |
| **Company Growth** | 1 row per domain | Current headcount + MoM/QoQ/6m/YoY growth (% and absolute) + historical snapshots |
| **Dept Growth** | 1 row per domain-dept | Department, current headcount, 6m ago, YoY ago, growth % |

### Step 4: Save run summary

After sheet write completes, save a run summary markdown file:

```bash
# Save to runs/ folder in skill directory
```

The run summary should include:
- Date, domain count, hire window used
- Credits consumed (enrich + person search)
- Domains processed/failed/skipped
- Sheet URL
- Any notable signals found

Save to: `.claude/skills/crustdata-signals/runs/{run-id}.md`

### Step 5: Clean up JSONs

Ask the user: "The JSON backup files in `outputs/{run-id}/` take up space. All data is now in the Google Sheet. Delete them?"

If yes, delete the run folder. If no, leave it.

## Cost

| API | Cost | Rate limit |
|---|---|---|
| `/company/enrich` | 2 credits/company | 15 RPM |
| `/person/search` | 0.03 credits/result | 30 RPM |

Typical cost per domain: ~2.6 credits (2 enrich + ~0.6 for ~20 hires)
50 domains: ~130 credits

## Signal analysis (what the Signal Summary columns contain)

The script auto-generates signal text in these columns:

- **Funding Signal**: "Series A $20M raised 45d ago - FRESH CAPITAL | 3 rounds total | $31.5M total raised"
- **Growth Signal**: "Growing 32% YoY (+76 employees) - STRONG GROWTH | 202 employees now"
- **Dept Signal**: "Engineering +40% | Sales +25%"
- **Hiring Signal**: "Senior hires: VP Sales, Head of Engineering | 12 new hires found | 5 open roles"
- **Signal Summary**: All signals combined in one cell

## Important notes

- Enrich costs 2 credits regardless of fields requested - always pull ALL 19 field groups
- Pre-computed growth fields from CrustData can be stale by 3-10 months. The script computes fresh growth from timeseries data.
- Person search returns people who started at a company within the hire window. The `current.start_date` filter is the key.
- Some companies have `updated_at: null` - CrustData has no data for them (genuine coverage gap, not staleness)
- The script handles rate limiting automatically with delays between calls
- If a run fails mid-way, use `--resume` to continue from where it stopped

## References

- `references/enrich-api.md` - Company enrich endpoint docs
- `references/person-search-api.md` - Person search endpoint docs (recent hires filter)
- `tech-stack/crustdata.md` - API key, auth headers, industry taxonomy
