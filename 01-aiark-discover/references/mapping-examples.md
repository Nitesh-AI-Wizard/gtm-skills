# Plain English -> AI Ark Filter Mapping Examples

20+ examples showing how to convert user input to AI Ark filter JSON.
All filters go inside the `account` object in the request body.

## Location Mappings

| User says | Filter JSON |
|-----------|-------------|
| "US" / "America" | `"location": {"any": {"include": ["United States"]}}` |
| "US and UK" | `"location": {"any": {"include": ["United States", "United Kingdom"]}}` |
| "Europe" | `"location": {"any": {"include": ["Europe"]}}` (continent level) |
| "Bay Area" / "SF" | Use geoLocation: `"geoLocation": {"position": {"lat": 37.7749, "lng": -122.4194}, "radius": 50, "unit": "km"}` |
| "California" | `"location": {"any": {"include": ["California"]}}` (state level) |
| "DACH region" | `"location": {"any": {"include": ["Germany", "Austria", "Switzerland"]}}` |

## Company Size Mappings

| User says | Filter JSON |
|-----------|-------------|
| "small companies" / "startups" | `"employeeSize": {"type": "RANGE", "range": [{"start": 1, "end": 50}]}` |
| "50-200 employees" | `"employeeSize": {"type": "RANGE", "range": [{"start": 50, "end": 200}]}` |
| "mid-market" | `"employeeSize": {"type": "RANGE", "range": [{"start": 201, "end": 1000}]}` |
| "enterprise" | `"employeeSize": {"type": "RANGE", "range": [{"start": 1001, "end": 10000}]}` |

## Industry Mappings

| User says | Filter JSON |
|-----------|-------------|
| "tech companies" | Show matching options from 921 catalog using SMART mode. Likely: software development, information technology, computer software, saas, internet |
| "SaaS" | `"industries": {"any": {"include": {"mode": "WORD", "content": ["saas"]}}}` |
| "software" | `"industries": {"any": {"include": {"mode": "WORD", "content": ["Software Development"]}}}` |
| "healthcare" | `"industries": {"any": {"include": {"mode": "SMART", "content": ["healthcare"]}}}` — SMART mode catches variants |
| "AI company" | `"industries": {"any": {"include": {"mode": "SMART", "content": ["artificial intelligence"]}}}` |
| "exclude consulting" | `"industries": {"any": {"exclude": {"mode": "WORD", "content": ["consulting"]}}}` |
| "fintech" | `"industries": {"any": {"include": {"mode": "SMART", "content": ["fintech", "financial technology"]}}}` |

## Company Type Mappings

| User says | Filter JSON |
|-----------|-------------|
| "private companies" | `"type": {"include": ["privately_held"]}` |
| "public companies" | `"type": {"include": ["public_company"]}` |
| "nonprofits" | `"type": {"include": ["non_profit"]}` |
| "exclude government" | `"type": {"include": ["privately_held", "public_company", "self_owned", "partnership"]}` (include everything except gov) |

## Funding Mappings

| User says | Filter JSON |
|-----------|-------------|
| "Series A" | `"funding": {"type": ["series_a"]}` |
| "Series A or B" | `"funding": {"type": ["series_a", "series_b"]}` |
| "seed stage" | `"funding": {"type": ["seed", "pre_seed"]}` |
| "raised $5M-$50M total" | `"funding": {"totalAmount": {"start": 5000000, "end": 50000000}}` |
| "last round $1M-$10M" | `"funding": {"lastAmount": {"start": 1000000, "end": 10000000}}` |
| "VC-backed" | `"funding": {"type": ["venture"], "notReceived": false}` |
| "funded companies" | `"funding": {"notReceived": false}` |
| "bootstrapped" / "no funding" | `"funding": {"notReceived": true}` |
| "funded in last 2 years" | `"funding": {"duration": {"start": 0, "end": 2}}` |

## Revenue Mappings

| User says | Filter JSON |
|-----------|-------------|
| "$1M-$10M revenue" | `"revenue": {"type": "RANGE", "range": [{"start": 1000000, "end": 10000000}]}` |
| "over $100M" | `"revenue": {"type": "RANGE", "range": [{"start": 100000000, "end": 10000000000}]}` |
| "pre-revenue" / "early stage" | `"revenue": {"type": "RANGE", "range": [{"start": 0, "end": 1000000}]}` |

## Growth & Metrics

| User says | Filter JSON |
|-----------|-------------|
| "growing fast" | `"metric": {"growth": [{"start": 20, "end": 1000, "timeFrame": "twelve"}]}` |
| "growing engineering team" | `"metric": {"employee": [{"start": 5, "end": 500, "function": ["engineering"], "timeFrame": "twelve"}]}` |
| "sales team grew 20%+" | `"metric": {"growth": [{"start": 20, "end": 1000, "function": ["sales"], "timeFrame": "twelve"}]}` |
| "shrinking" / "layoffs" | `"metric": {"growth": [{"start": -100, "end": -5, "timeFrame": "six"}]}` |

## Technology Mappings

| User says | Filter JSON |
|-----------|-------------|
| "uses Salesforce" | `"technology": {"any": {"include": ["salesforce"]}}` |
| "uses HubSpot but not Salesforce" | `"technology": {"any": {"include": ["hubspot"], "exclude": ["salesforce"]}}` |
| "AWS stack" | `"technology": {"any": {"include": ["aws"]}}` |
| "Shopify merchants" | `"technology": {"any": {"include": ["shopify"]}}` |

## Founded Year

| User says | Filter JSON |
|-----------|-------------|
| "founded after 2015" | `"foundedYear": {"type": "RANGE", "range": [{"start": 2015, "end": 2026}]}` |
| "established companies" | `"foundedYear": {"type": "RANGE", "range": [{"start": 1900, "end": 2010}]}` |
| "founded 2018-2022" | `"foundedYear": {"type": "RANGE", "range": [{"start": 2018, "end": 2022}]}` |

## Keyword & Content

| User says | Filter JSON |
|-----------|-------------|
| "AI companies" (keyword) | `"keyword": {"any": {"include": {"sources": [{"source": "DESCRIPTION", "mode": "SMART"}, {"source": "KEYWORD", "mode": "SMART"}], "content": ["artificial intelligence", "machine learning"]}}}` |
| "companies selling CRM" | `"productAndServices": {"any": {"include": {"mode": "SMART", "content": ["CRM", "customer relationship management"]}}}` |

## Lookalike Mappings

| User says | Filter JSON (top-level, NOT inside account) |
|-----------|-------------|
| "similar to hubspot.com" | `"lookalikeDomains": ["https://www.linkedin.com/company/hubspot"]` + at least one account filter |
| "companies like Stripe" | `"lookalikeDomains": ["https://www.linkedin.com/company/stripe"]` + account filters |
| "find me companies like these 3" | `"lookalikeDomains": ["linkedin1", "linkedin2", "linkedin3"]` (max 5) + account filters |

LinkedIn URLs are preferred over domains for better accuracy.

## Combined Examples

### Full ICP (Type 1)
User: "Find private software companies in the US, 50-200 employees, Series A or B, $1M-$50M revenue"

```json
{
  "page": 0,
  "size": 25,
  "account": {
    "industries": {"any": {"include": {"mode": "WORD", "content": ["Software Development"]}}},
    "type": {"include": ["privately_held"]},
    "employeeSize": {"type": "RANGE", "range": [{"start": 50, "end": 200}]},
    "location": {"any": {"include": ["United States"]}},
    "funding": {"type": ["series_a", "series_b"]},
    "revenue": {"type": "RANGE", "range": [{"start": 1000000, "end": 50000000}]}
  }
}
```

### Lookalike + Filters (Type 3)
User: "Find companies similar to HubSpot, 50-500 employees, in the US"

```json
{
  "page": 0,
  "size": 25,
  "lookalikeDomains": ["https://www.linkedin.com/company/hubspot"],
  "account": {
    "employeeSize": {"type": "RANGE", "range": [{"start": 50, "end": 500}]},
    "location": {"any": {"include": ["United States"]}}
  }
}
```

### Geo + Growth (advanced)
User: "Find fast-growing software companies within 50km of San Francisco"

```json
{
  "page": 0,
  "size": 25,
  "account": {
    "industries": {"any": {"include": {"mode": "WORD", "content": ["Software Development"]}}},
    "geoLocation": {"position": {"lat": 37.7749, "lng": -122.4194}, "radius": 50, "unit": "km"},
    "metric": {"growth": [{"start": 20, "end": 1000, "timeFrame": "twelve"}]}
  }
}
```
