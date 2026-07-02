---
name: shopify:seo-audit
description: Audit Shopify product page SEO: meta tags, schema, page speed, keyword coverage
argument-hint: "<product_url> [--target_keyword <keyword>]"
required_connectors: []
risk_level: low
human_review: optional
---

## Inputs

| Field | Required | Description |
|-------|----------|-------------|
| product_url | Yes | Shopify product page URL |
| target_keyword | No | Primary keyword to optimize for |

## Steps

1. Fetch page HTML and extract SEO elements:
   - Title tag, meta description, H1, H2-H6 structure
   - Image alt texts, canonical URL, robots meta
   - Schema.org structured data (Product, Offer, Review)
2. Check page speed signals (Core Web Vitals if available)
3. Analyze keyword coverage in title, description, headings, body
4. Generate SEO score and recommendations

## Output

```json
{
  "url": "...",
  "seo_score": 68,
  "findings": {
    "title_tag": {"status": "warn", "current": "Dr. Pen A1 Microneedling Pen", "recommendation": "Add benefit keyword: 'Professional Microneedling Pen at Home'"},
    "meta_description": {"status": "fail", "current": "", "recommendation": "Add 155-char meta description with primary keyword"},
    "schema": {"status": "pass", "types": ["Product", "Offer"]},
    "image_alts": {"status": "warn", "missing_count": 3}
  },
  "recommendations": [
    {"priority": "high", "action": "Add meta description with primary keyword"},
    {"priority": "medium", "action": "Add alt text to 3 missing images"}
  ]
}
```

## Risk Boundaries

- Read-only audit. Do not modify store settings.

## Failure Modes

| Failure | Cause | Fix |
|---------|-------|-----|
| Structured data not detected | Theme uses non-standard markup | Check for JSON-LD vs microdata format |
