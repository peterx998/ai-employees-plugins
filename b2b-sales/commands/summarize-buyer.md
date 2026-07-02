---
name: b2b:summarize-buyer
description: Generate a buyer summary profile from inquiry, quote history, and communication thread
argument-hint: "<lead_id>"
required_connectors: ["~~email"]
risk_level: low
human_review: optional
---

## Inputs

| Field | Required | Description |
|-------|----------|-------------|
| lead_id | Yes | B2B lead ID |
| thread_id | No | Email thread for communication history |

## Steps

1. Fetch lead profile and quote history
2. Fetch communication thread from ~~email
3. Summarize:
   - Company background and buyer type
   - Product interest and volume
   - Budget and pricing discussions
   - Timeline and urgency
   - Objections or concerns raised
   - Decision-making process signals
4. Generate actionable summary for sales team

## Output

```json
{
  "lead_id": "LEAD-2026-001",
  "company": "Glow Clinic Chain",
  "buyer_type": "clinic",
  "products_interest": ["A1 (25 units)"],
  "budget_range": "$1,500-$2,000",
  "timeline": "Q3 2026 purchase",
  "key_objections": ["wants FDA documentation", "comparing with competitor brand"],
  "decision_status": "evaluating",
  "communication_count": 4,
  "recommended_next_step": "Send FDA compliance documentation + schedule demo call"
}
```

## Risk Boundaries

- Do not include personal contact info in summaries shared externally.
- Summary is for internal sales team use only.

## Failure Modes

| Failure | Cause | Fix |
|---------|-------|-----|
| Summary too long | No length constraint | Cap at 300 words |
| Missing objection data | Thread scan incomplete | Include all messages in analysis |
