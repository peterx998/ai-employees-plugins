---
name: b2b:escalate-high-value
description: Escalate a high-value B2B lead to senior sales rep with full context
argument-hint: "<lead_id> [--reason high_value|strategic|complex]"
required_connectors: ["~~email"]
risk_level: high
human_review: always
---

## Inputs

| Field | Required | Description |
|-------|----------|-------------|
| lead_id | Yes | B2B lead ID |
| reason | Yes | Escalation reason: high_value, strategic, complex |
| lead_profile | Yes | Full lead qualification profile |
| quote_id | No | Associated quote if exists |

## Steps

1. Verify escalation criteria:
   - high_value: potential order $10K+ or 100+ units
   - strategic: distributor/enterprise with multi-region potential
   - complex: custom requirements, certification needs, legal review
2. Compile escalation package:
   - Lead profile and qualification score
   - Communication history summary
   - Quote details (if exists)
   - Recommended action for senior rep
3. Route to senior sales rep via ~~collab notification
4. Log escalation with timestamp

## Output

```json
{
  "escalation_id": "B2B-ESC-2026-001",
  "lead_id": "LEAD-2026-001",
  "reason": "high_value",
  "lead_summary": {
    "company": "Glow Clinic Chain",
    "buyer_type": "clinic",
    "potential_value": "$15,000",
    "lead_score": 85
  },
  "quote_ref": "QT-2026-001",
  "recommended_action": "Senior rep to schedule call within 48h. Prepare FDA docs and bulk pricing matrix.",
  "escalated_to": "senior_sales_rep",
  "human_review_required": true
}
```

## Risk Boundaries

- All high-value escalations require senior rep response within 48 hours.
- Agent does not negotiate or commit to terms. Only prepares context.

## Failure Modes

| Failure | Cause | Fix |
|---------|-------|-----|
| Escalated non-qualifying lead | Threshold check failed | Enforce $10K+ or 100+ units minimum |
''',
