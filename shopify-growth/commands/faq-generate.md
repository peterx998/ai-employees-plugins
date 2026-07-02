---
name: shopify:faq-generate
description: Generate FAQ entries from product info, customer questions, and KB gaps
argument-hint: "<product_id> [--source reviews|support_tickets|kb_gaps]"
required_connectors: ["~~store", "~~kb"]
risk_level: low
human_review: recommended
---

## Inputs

| Field | Required | Description |
|-------|----------|-------------|
| product_id | Yes | Shopify product ID |
| source | No | Data source for FAQ topics (default: all) |

## Steps

1. Fetch product info from ~~store (get_product)
2. Gather FAQ source data:
   - Customer reviews (from ~~store product reviews)
   - Support tickets mentioning this product (from ~~email search)
   - KB gaps (from ~~kb search_kb for unanswered questions)
3. Cluster questions by topic:
   - Usage & instructions
   - Safety & contraindications
   - Shipping & returns
   - Product comparison
   - Technical specs
4. Generate FAQ entry for each cluster (question + answer + category)
5. Run compliance check on answers (no medical claims)

## Output

```json
{
  "product_id": "...",
  "faq_entries": [
    {
      "question": "How often should I use the microneedling pen?",
      "answer": "For beginners, we recommend once every 1-2 weeks. Always follow the included instruction guide and consult a dermatologist if you have sensitive skin.",
      "category": "usage",
      "source": "support_tickets",
      "compliance_check": "passed"
    },
    {
      "question": "Can I use it while pregnant?",
      "answer": "We recommend consulting your healthcare provider before using any skincare device during pregnancy.",
      "category": "safety",
      "source": "kb_gaps",
      "compliance_check": "passed"
    }
  ],
  "total_generated": 8,
  "human_review_recommended": true
}
```

## Risk Boundaries

- Medical/safety answers must include "consult a professional" disclaimer.
- Do not publish FAQ entries directly. Create as draft for human review.

## Failure Modes

| Failure | Cause | Fix |
|---------|-------|-----|
| Answers too generic | Source data insufficient | Require min 5 support tickets or reviews before generating |
| Compliance check failed | Answer contained medical claim | Auto-flag and require human rewrite |
