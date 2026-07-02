---
name: shopify:product-page-review
description: Audit a Shopify product page for conversion, clarity, FAQ gaps, and mobile UX
argument-hint: "<product_url>"
required_connectors: ["~~store"]
risk_level: low
human_review: recommended
---

## Inputs

| Field | Required | Description |
|-------|----------|-------------|
| product_url | Yes | Shopify product page URL |
| region | No | Target market for compliance check |

## Steps

1. Fetch product page HTML and parse key elements:
   - Title, description, bullet points, images, FAQ section
   - Price, compare-at price, reviews count
   - Add to Cart button visibility and placement
2. Score page on conversion criteria:
   - Above-the-fold clarity (value proposition visible in 3s)
   - Image quality and quantity (min 5 images, zoom available)
   - FAQ completeness (shipping, returns, usage, safety)
   - Mobile responsiveness (tap targets, load speed)
   - Trust signals (reviews, badges, guarantees)
3. Generate improvement recommendations ranked by impact

## Output

```json
{
  "url": "...",
  "overall_score": 72,
  "scores": {
    "above_fold_clarity": 80,
    "image_quality": 65,
    "faq_completeness": 50,
    "mobile_ux": 85,
    "trust_signals": 70
  },
  "recommendations": [
    {"priority": "high", "area": "faq_completeness", "action": "Add FAQ entries for: needle depth guide, skin sensitivity, cleaning instructions"},
    {"priority": "medium", "area": "image_quality", "action": "Add lifestyle images showing product in use, add zoom for product detail"}
  ],
  "human_review_recommended": true
}
```

## Risk Boundaries

- Do not modify the Shopify store. Read-only audit.
- Flag any medical claims on the product page for compliance review.

## Failure Modes

| Failure | Cause | Fix |
|---------|-------|-----|
| Page not accessible | URL invalid or geo-blocked | Try alternative user-agent or proxy |
| FAQ section missing | Theme doesn't support FAQ | Flag as critical gap in recommendations |
