# GTM Skills

Claude Code skills for GTM (Go-To-Market) engineering and outbound sales automation.

## Skills

### prospeo-discover
B2B company discovery and list building using Prospeo's 30M+ company database with 33 search filters. Handles five user types — from full ICP experts to users who only have seed company domains.

**User Types:**
- **Type 1 — Expert**: Full ICP provided, maps directly to filters
- **Type 2 — Partial**: Vague input, guides user through filter selection with smart defaults
- **Type 3 — Expert + Lookalike**: Full ICP + seed domains
- **Type 4 — Partial + Lookalike**: Partial filters + seed domains, discovers patterns from lookalike results
- **Type 5 — Lookalike Only**: Only seed domains, builds full ICP from lookalike analysis

**Features:**
- Auto-detects Prospeo plan (Free/Starter/Growth/Pro) and only offers available filters
- 5 mandatory filters with smart defaults (location, size, industry, status, revenue)
- Lookalike as discovery-only — never stacked in final search (narrows results to single digits)
- Smart, data-driven optional filter recommendations from 4 context sources
- Python export script for large lists (3,000-5,000+ companies) with batch writing to Google Sheets
- Enum cache for 256 industries, 27 subtypes, 23 funding stages, and more
- Credit tracking and cost guards before every export

**Export:**
```bash
# Dry run (no credits spent on export)
python3 prospeo-discover/scripts/sheets_export.py --filters filters.json --dry-run

# Export to new spreadsheet
python3 prospeo-discover/scripts/sheets_export.py --filters filters.json

# Export to existing spreadsheet with custom tab
python3 prospeo-discover/scripts/sheets_export.py --filters filters.json --spreadsheet-id SHEET_ID --tab-name "my-search"

# Limit pages
python3 prospeo-discover/scripts/sheets_export.py --filters filters.json --max-pages 10
```

**Requirements:**
```bash
pip install requests gspread google-auth
```

**Auth:**
- Prospeo: `PROSPEO_API_KEY` (set in script or env)
- Google Sheets: OAuth2 token at `~/.google/token.json`

---

### firecrawl-research
Extract LLM-ready markdown from company websites using Firecrawl. Scrapes homepage, about, careers, blog, pricing, customers, integrations, and product pages. Supports batch processing, customer/partner extraction from content, and Google Sheets output.

**Modes:**
- **Standard** (5-8 credits) — Homepage + About + Careers + Blog + Pricing + Customers + Integrations + Product
- **Deep** (5-11 credits) — Standard + Changelog + Leadership
- **Minimal** (3 credits) — Homepage + About only
- **Extract** (~20+ credits) — Structured JSON fields via LLM extraction

**Features:**
- Credit-efficient map-then-scrape approach (1 credit to discover URLs, 1 per page scraped)
- Accurate credit tracking (reads actual credits from Firecrawl response, including stealth proxy costs)
- Post-scrape customer/partner extraction from markdown content (more reliable than screenshot-based logo detection)
- Batch processing with resume capability
- Google Sheets writer (gspread + OAuth2)
- Multilingual URL matching (EN, TR, BG, RO, GR, DE)
- Prefix URL matching for variant patterns (e.g. `about-us`, `about-company`, `careers-at-acme`)

**Usage:**
```bash
# Single domain
python3 firecrawl-research/scripts/firecrawl_scrape.py --domain acme.com --mode standard

# Batch
python3 firecrawl-research/scripts/firecrawl_scrape.py --batch domains.txt --mode standard

# Write to Google Sheet
python3 firecrawl-research/scripts/sheets_writer.py --run-dir <run-folder> --spreadsheet-id <SHEET_ID>
```

**Requirements:**
```bash
pip install firecrawl-py python-dotenv gspread google-auth
```

**Auth:**
- Firecrawl: `FIRECRAWL_API_KEY` in `.env`
- Google Sheets: OAuth2 token at `~/.google/token.json`

### 04-crustdata-signals
Enrich a list of company domains with structured signals from CrustData — funding rounds, headcount growth, department growth, and recent hires (people who joined in last N days). Writes results across 5 Google Sheets tabs.

**Features:**
- Enriches domains via CrustData's company enrichment + person search APIs
- 5 output tabs: Signal Summary, Funding Rounds, Headcount Growth, Department Growth, Recent Hires
- Configurable hire window (90, 180, or 365 days)
- Accepts domains from Google Sheet or raw list
- Google Sheets writer with OAuth2 auth

**Usage:**
```bash
# Set API key
export CRUSTDATA_API_KEY=<your-key>

# Run enrichment
python3 04-crustdata-signals/scripts/crustdata_signals.py --domains domains.txt --hire-window 180

# Write to Google Sheet
python3 04-crustdata-signals/scripts/sheets_writer.py --run-dir <run-folder> --spreadsheet-id <SHEET_ID>
```

**Requirements:**
```bash
pip install requests gspread google-auth
```

**Auth:**
- CrustData: `CRUSTDATA_API_KEY` env var
- Google Sheets: OAuth2 token at `~/.google/token.json`

---

## About

Built by [Nitesh Dhande](https://github.com/Nitesh-AI-Wizard) at [Zevenue](https://zevenue.com) — a GTM Engineering Partner for B2B startups.
