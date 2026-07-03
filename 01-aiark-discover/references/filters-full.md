# AI Ark Company Search — Complete Filter Reference

All filters for `POST /api/developer-portal/v1/companies`. Filters go inside the `account` object in the request body.

## Table of Contents

1. [Filter Type Formats](#filter-type-formats)
2. [Identification Filters](#identification-filters)
3. [Location Filters](#location-filters)
4. [Industry Filters](#industry-filters)
5. [Company Size & Type](#company-size--type)
6. [Financial Filters](#financial-filters)
7. [Keyword & Content Filters](#keyword--content-filters)
8. [Technology Filters](#technology-filters)
9. [Growth Metrics](#growth-metrics)
10. [Classification Codes](#classification-codes)
11. [Social & Language](#social--language)
12. [Lookalike](#lookalike)
13. [List Exclusion](#list-exclusion)

---

## Filter Type Formats

AI Ark uses three filter shapes. Use the right one for each field.

### SimpleFilter
For enum fields (location, type, technology, socialMedia, domain, linkedin, etc.):
```json
{"any": {"include": ["value1", "value2"], "exclude": ["value3"]}}
```
Use `"all"` instead of `"any"` to require ALL values match.

**Special case — `type` field**: uses a simpler format (verified by testing):
```json
{"include": ["privately_held"]}
```

### AdvanceFilter
For text-searchable fields (industries, name, url, nameOrDomain, productAndServices):
```json
{"any": {"include": {"mode": "SMART", "content": ["value"]}, "exclude": {"mode": "WORD", "content": ["value"]}}}
```
Modes:
- `SMART` — fuzzy/semantic matching (recommended default)
- `WORD` — whole word matching
- `STRICT` — exact string matching

### RangeFilter
For numeric fields (employeeSize, revenue, foundedYear, retailSize):
```json
{"type": "RANGE", "range": [{"start": 100, "end": 1000}]}
```
Type values: `RANGE` (filter by range), `ALL` (any value), `NONE` (no value / unknown)

---

## Identification Filters

| Field | Format | Description |
|-------|--------|-------------|
| `id` | SimpleFilter | Company UUID(s) |
| `domain` | SimpleFilter | Website domain, e.g. `"google.com"` |
| `linkedin` | SimpleFilter | LinkedIn company URL |
| `url` | AdvanceFilter | Company website URL |
| `name` | AdvanceFilter | Company name |
| `nameOrDomain` | AdvanceFilter | Search by name or domain together |
| `phoneNumber` | SimpleFilter | Company phone number |
| `socialMediaLink` | SimpleFilter | Social media profile URLs |

### Example — Search by domain
```json
{
  "account": {
    "domain": {"any": {"include": ["hubspot.com", "salesforce.com"]}}
  }
}
```

---

## Location Filters

### Standard Location Filter — SimpleFilter
Uses the standard SimpleFilter format (verified working — the `country` nested format does NOT filter correctly):
```json
{
  "location": {"any": {"include": ["United States"]}}
}
```

Values must be exact enum names from `aiark-enums.json`:
- **Continents**: `Northern America` (NOT "North America"), `Western Europe`, `Northern Europe`, `Eastern Asia`, `Southern Asia`, `Oceania`, etc.
- **Countries**: `United States`, `Germany`, `United Kingdom`, `Canada`, `India`, etc.
- **States/Regions**: `California`, `New York`, `Texas`, `Bavaria`, `Ontario`, etc.

Can mix levels (continent, country, state) in a single filter.

### Multiple locations
```json
{
  "location": {"any": {"include": ["United States", "Germany", "United Kingdom"]}}
}
```

### Exclude locations
```json
{
  "location": {"any": {"include": ["United States"], "exclude": ["California"]}}
}
```

### Geo-Location (radius search)
```json
{
  "geoLocation": {
    "position": {"lat": 37.7749, "lng": -122.4194},
    "radius": 50,
    "unit": "km"
  }
}
```
Units: `km` (default), `mi`

---

## Industry Filters

AI Ark has **921 industries** (vs Prospeo's 256). Two approaches:

### `industries` — AdvanceFilter (recommended)
Uses mode/content for flexible matching:
```json
{
  "industries": {
    "any": {
      "include": {
        "mode": "WORD",
        "content": ["Software Development"]
      }
    }
  }
}
```

Use `SMART` mode for fuzzy matching when you're not sure of exact values:
```json
{
  "industries": {
    "any": {
      "include": {
        "mode": "SMART",
        "content": ["artificial intelligence"]
      }
    }
  }
}
```

### `industry` — SimpleFilter
For exact enum values only:
```json
{
  "industry": {
    "any": {
      "include": ["software development", "information technology"]
    }
  }
}
```

### Common Industry Values (verified)

| Category | Industry Values |
|----------|----------------|
| Software/Tech | software development, information technology, computer software, internet, saas |
| Healthcare | health care, medical devices, hospital & health care, pharmaceuticals, biotechnology |
| Finance | financial services, banking, insurance, investment management, venture capital |
| Manufacturing | manufacturing, automotive, industrial automation, machinery, electronics |
| Services | professional services, consulting, business services, outsourcing |
| Marketing | marketing, advertising, digital marketing, public relations |
| Education | education, e-learning, higher education |
| Real Estate | real estate, construction, architecture |
| Retail/E-commerce | retail, e-commerce, consumer goods, food & beverages |

For the full 921-industry list, search with SMART mode or check the API.

---

## Company Size & Type

### employeeSize — RangeFilter
Exact employee count range (not string brackets like Prospeo):
```json
{
  "employeeSize": {
    "type": "RANGE",
    "range": [{"start": 51, "end": 200}]
  }
}
```

Common ranges:
| Segment | Start | End |
|---------|-------|-----|
| Micro | 1 | 10 |
| Small | 11 | 50 |
| SMB | 51 | 200 |
| Mid-market | 201 | 1000 |
| Enterprise | 1001 | 10000 |
| Large enterprise | 10001 | 999999 |

### type — Special format
Company legal type. Uses a flat `include` array (not nested in `any`):
```json
{
  "type": {"include": ["privately_held"]}
}
```

Valid values (lowercase):
- `privately_held`
- `public_company`
- `self_owned`
- `self_employed`
- `partnership`
- `non_profit`
- `educational`
- `government_agency`

### retailSize — RangeFilter
Number of retail locations:
```json
{
  "retailSize": {
    "type": "RANGE",
    "range": [{"start": 5, "end": 100}]
  }
}
```

---

## Financial Filters

### revenue — RangeFilter
Annual revenue in USD (exact amounts, not string labels):
```json
{
  "revenue": {
    "type": "RANGE",
    "range": [{"start": 1000000, "end": 50000000}]
  }
}
```

Common revenue ranges:
| Segment | Start | End |
|---------|-------|-----|
| Pre-revenue / early | 0 | 1000000 |
| $1M-$10M | 1000000 | 10000000 |
| $10M-$50M | 10000000 | 50000000 |
| $50M-$100M | 50000000 | 100000000 |
| $100M-$500M | 100000000 | 500000000 |
| $500M+ | 500000000 | 10000000000 |

### funding — Complex object
```json
{
  "funding": {
    "type": ["series_a", "series_b"],
    "totalAmount": {"start": 1000000, "end": 50000000},
    "lastAmount": {"start": 500000, "end": 10000000},
    "duration": {"start": 0, "end": 5},
    "notReceived": false
  }
}
```

All sub-fields are optional — use only what you need.

**funding.type values** (lowercase):
`pre_seed`, `seed`, `angel`, `venture`, `series_a`, `series_b`, `series_c`, `series_d`, `series_e`, `series_f`, `debt`, `grant`, `equity`, `convertible_note`, `series_unknown`, `private_equity`, `ipo`, `post_ipo`, `undisclosed`

**funding.notReceived**: `true` = companies with NO funding, `false` = companies WITH funding

**funding.totalAmount / lastAmount**: `start` and `end` in USD

**funding.duration**: years since last funding round (`start` and `end` as integers)

### foundedYear — NOT WORKING via direct HTTP
The `foundedYear` filter is silently ignored when using the direct HTTP API. It does not return a 400 error but does not filter results either. This filter only works through the MCP translation layer.

**Workaround**: Skip this filter in direct HTTP searches. If filtering by founded year is critical, use the MCP tool `mcp__ai-ark__company_search` with `minFoundedYear` / `maxFoundedYear` params instead.

---

## Keyword & Content Filters

### keyword — Special format
Free-text search across company data sources:
```json
{
  "keyword": {
    "any": {
      "include": {
        "sources": [
          {"source": "DESCRIPTION", "mode": "SMART"},
          {"source": "KEYWORD", "mode": "SMART"}
        ],
        "content": ["AI", "machine learning", "automation"]
      }
    }
  }
}
```

Valid source values: `NAME`, `KEYWORD`, `SEO`, `DESCRIPTION`, `INDUSTRY`

Valid mode values: `SMART`, `WORD`, `STRICT`

If you omit `sources`, it searches all sources.

### productAndServices — AdvanceFilter
```json
{
  "productAndServices": {
    "any": {
      "include": {
        "mode": "SMART",
        "content": ["cloud computing", "data analytics"]
      }
    }
  }
}
```

---

## Technology Filters

### technology — SimpleFilter
For exact tech stack keys:
```json
{
  "technology": {
    "any": {
      "include": ["salesforce", "hubspot", "aws"]
    }
  }
}
```

### technologies — AdvanceFilter
For fuzzy tech matching:
```json
{
  "technologies": {
    "any": {
      "include": {
        "mode": "SMART",
        "content": ["salesforce"]
      }
    }
  }
}
```

Common technology values: `salesforce`, `hubspot`, `aws`, `google-analytics`, `wordpress`, `shopify`, `marketo`, `intercom`, `segment`, `stripe`, `slack`, `jira`, `github`, `docker`, `kubernetes`, `react`, `angular`, `vue`, `python`, `java`, `ruby`

---

## Growth Metrics

### metric — NOT WORKING via direct HTTP
The `metric` filter (both `employee` and `growth` sub-filters) returns 400 errors when used in the direct HTTP API, regardless of format.

**Workaround**: Use the MCP tool `mcp__ai-ark__company_search` with flat params instead:
- `minMetricGrowthChange` / `maxMetricGrowthChange` + `metricGrowthTimeFrame`
- `minMetricEmployeeChange` / `maxMetricEmployeeChange` + `metricEmployeeTimeFrame`
- `metricGrowthFunction` / `metricEmployeeFunction`

**timeFrame values**: `one` (1 month), `three`, `six`, `twelve`, `twenty_four`

**function values** (department names): `engineering`, `information_technology`, `operations`, `finance`, `marketing`, `sales`, `human_resources`, `legal`, `business_development`, `product_management`, `customer_success_and_support`, `education`, `consulting`, `research`, `arts_and_design`, `healthcare_services`, `media_and_communication`, `administrative`, `accounting`, `quality_assurance`, `purchasing`, `real_estate`, `support`, `program_and_project_management`, `entrepreneurship`, `community_and_social_services`, `military_and_protective_services`

---

## Classification Codes

### naics — SimpleFilter
```json
{
  "naics": {"any": {"include": ["5112", "5415"]}}
}
```

### sic — SimpleFilter
```json
{
  "sic": {"any": {"include": ["7372", "7371"]}}
}
```

---

## Social & Language

### socialMedia — SimpleFilter
Filter by social media platform presence:
```json
{
  "socialMedia": {"any": {"include": ["LINKEDIN", "TWITTER", "GITHUB"]}}
}
```
Values: `TWITTER`, `FACEBOOK`, `LINKEDIN`, `INSTAGRAM`, `YOUTUBE`, `GITHUB`

### language — SimpleFilter (with optional range)
```json
{
  "language": {"any": {"include": ["english"]}}
}
```
Values: `english`, `spanish`, `french`, `portuguese`, `german`, `dutch`, `italian`, `chinese`, `turkish`, `polish`, `russian`, `swedish`, `arabic`, `indonesian`, `danish`, `czech`, `norwegian`, `japanese`, `korean`, `romanian`, `ukrainian`, `thai`, `hindi`, `malay`, `tagalog`, `vietnamese`, `finnish`, `persian`, `greek`, `hungarian`, and more.

---

## Lookalike

`lookalikeDomains` goes at **top level** of the request body, NOT inside `account`:
```json
{
  "page": 0,
  "size": 25,
  "lookalikeDomains": ["https://www.linkedin.com/company/hubspot"],
  "account": {
    "employeeSize": {"type": "RANGE", "range": [{"start": 50, "end": 500}]}
  }
}
```

- Max 5 domains/URLs
- LinkedIn URLs are more accurate than plain domains
- At least one `account` filter is required alongside — lookalike alone returns 0 or times out
- Accepts domains (`hubspot.com`) or LinkedIn URLs (`https://www.linkedin.com/company/hubspot`)

---

## List Exclusion

Exclude companies by ID list (up to 10 lists, each up to 10,000 items):
```json
{
  "lists": {
    "company_id": {
      "exclude": ["uuid1", "uuid2"]
    }
  }
}
```

---

## Complete Example — Full ICP Search

```json
{
  "page": 0,
  "size": 25,
  "account": {
    "industries": {
      "any": {
        "include": {
          "mode": "WORD",
          "content": ["Software Development"]
        }
      }
    },
    "type": {"include": ["privately_held"]},
    "employeeSize": {
      "type": "RANGE",
      "range": [{"start": 51, "end": 200}]
    },
    "revenue": {
      "type": "RANGE",
      "range": [{"start": 1000000, "end": 50000000}]
    },
    "location": {"any": {"include": ["United States"]}},
    "funding": {
      "type": ["series_a", "series_b"],
      "notReceived": false
    }
  }
}
```
