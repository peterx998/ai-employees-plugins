---
name: b2b:draft-quote
description: Draft a B2B quote based on lead qualification and pricing rules
argument-hint: "<lead_profile>"
required_connectors: []
risk_level: medium
human_review: required
output_schema: "schemas/b2b-sales/quote.schema.json"
---

## Inputs

| Field | Required | Description |
|-------|----------|-------------|
| lead_profile | Yes | Output from b2b:qualify-lead |
| product_models | Yes | Requested product models and quantities |
| discount_tier | No | Pre-approved discount tier (default: standard) |

## Steps

1. Load lead profile (buyer type, MOQ, pricing tier)
2. Apply pricing rules by buyer type:
   - Retail partner: 20-30% off MSRP, MOQ 10
   - Clinic: 30-40% off MSRP, MOQ 10
   - Distributor: 40-50% off MSRP, MOQ 50
   - Procurement: custom pricing, MOQ 100+
3. Generate line items with quantities, unit prices, discounts
4. Calculate subtotal, discount, total
5. Set quote validity (30 days) and payment terms
6. Include certification and compliance information
7. Route to human sales rep for approval before sending

## Output

```json
{
  "quote_id": "QT-2026-001",
  "lead_id": "LEAD-2026-001",
  "line_items": [
    {"model": "A1", "quantity": 25, "unit_price": 45.00, "discount": 0.35, "line_total": 731.25}
  ],
  "subtotal": 731.25,
  "discount": 393.75,
  "total": 731.25,
  "currency": "USD",
  "valid_until": "2026-08-01",
  "terms": "Net 30, 50% deposit on order confirmation",
  "human_review_required": true
}
```

## Risk Boundaries

- Quotes must be approved by human sales rep before sending to buyer.
- Agent never sends quotes directly. Draft only.
- Custom pricing below 50% off MSRP requires sales manager approval.

## Failure Modes

| Failure | Cause | Fix |
|---------|-------|-----|
| Discount exceeds max tier | Pricing rules misconfigured | Enforce hard cap on discount percentage |
| Wrong currency | Buyer region not detected | Add region-based currency selection |
