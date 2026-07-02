---
name: shopify:landing-page-brief
description: Generate a landing page brief with structure, copy, and CTA recommendations
argument-hint: "<product_info> [--campaign_type launch|sale|evergreen]"
required_connectors: []
risk_level: low
human_review: recommended
---

## Inputs

| Field | Required | Description |
|-------|----------|-------------|
| product_info | Yes | Product name, key benefits, target audience |
| campaign_type | No | launch, sale, or evergreen (default: evergreen) |
| region | No | Target market for compliance |

## Steps

1. Analyze product info and campaign type
2. Generate landing page structure:
   - Hero section (headline + subheadline + CTA + hero image)
   - Social proof bar (review count, rating, logos)
   - Problem-solution section
   - Feature-benefit grid (3-5 features)
   - How-to-use section
   - FAQ section (from product-page-review gaps)
   - Final CTA section
3. Generate copy variants for headline and CTA
4. Recommend image requirements per section
5. Include compliance checklist for medical/beauty products

## Output

```json
{
  "brief_id": "LP-2026-001",
  "structure": [
    {"section": "hero", "headline": "Professional Microneedling at Home", "cta": "Shop Now", "image_req": "Product hero shot, clean background"},
    {"section": "social_proof", "content": "4.8★ from 2,300+ reviews", "image_req": "Review screenshots"},
    {"section": "problem_solution", "headline": "Tired of expensive salon treatments?", "image_req": "Before/after with disclosure"},
    {"section": "features", "items": ["Adjustable needle depth", "Cordless design", "Professional-grade results"]},
    {"section": "faq", "questions": ["Is it safe for sensitive skin?", "How often should I use it?", "What's included?"]},
    {"section": "final_cta", "headline": "Start your skincare journey", "cta": "Get Yours Today"}
  ],
  "compliance_checklist": ["No medical claims in headlines", "Before/after requires disclosure", "Add patch test recommendation"],
  "human_review_recommended": true
}
```

## Risk Boundaries

- All copy must pass compliance check before publishing.
- Before/after imagery requires "Results may vary" disclosure.

## Failure Modes

| Failure | Cause | Fix |
|---------|-------|-----|
| Copy too generic | Product info too sparse | Require min 3 key benefits in input |
