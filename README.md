# GTM Skills

Claude Code skills for GTM (Go-To-Market) engineering and outbound sales automation.

## Skills

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

## About

Built by [Nitesh Dhande](https://github.com/Nitesh-AI-Wizard) at [Zevenue](https://zevenue.com) — a GTM Engineering Partner for B2B startups.
