---
name: shopify:review-import-check
description: Check Judge.me review import status and flag missing or filtered reviews
argument-hint: "[--product_id <id>]"
required_connectors: ["~~store"]
risk_level: low
human_review: optional
---

## Inputs

| Field | Required | Description |
|-------|----------|-------------|
| product_id | No | Specific product to check (default: all products) |

## Steps

1. Fetch product review data from ~~store
2. Check Judge.me import status:
   - Total reviews imported vs source count
   - Filtered/pending reviews
   - Reviews with missing fields (rating, date, author)
3. Flag anomalies:
   - Sudden drop in review count (import failure)
   - Reviews pending > 7 days
   - Rating distribution anomalies
4. Generate import health report

## Output

```json
{
  "product_id": "all",
  "import_status": "healthy",
  "total_reviews": 2300,
  "imported_reviews": 2280,
  "pending_reviews": 15,
  "filtered_reviews": 5,
  "anomalies": [
    {"type": "pending_overdue", "count": 3, "detail": "3 reviews pending > 7 days"},
    {"type": "missing_fields", "count": 2, "detail": "2 reviews missing author name"}
  ],
  "recommendations": [
    {"priority": "medium", "action": "Re-run Judge.me import for 15 pending reviews"},
    {"priority": "low", "action": "Update 2 reviews with missing author names"}
  ]
}
```

## Risk Boundaries

- Read-only check. Do not modify review data.

## Failure Modes

| Failure | Cause | Fix |
|---------|-------|-----|
| Judge.me API unavailable | Connector misconfigured | Check SHOPIFY_ACCESS_TOKEN and Judge.me API key |
