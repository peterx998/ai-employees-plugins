---
name: customer-support:escalate-risk
description: Escalate a high-risk ticket to human support lead with full context package
argument-hint: "<ticket_id> [--reason medical|legal|social|regulatory|high-value]"
required_connectors: ["~~email", "~~store"]
risk_level: high
human_review: always
output_schema: "schemas/customer-support/escalation_package.schema.json"
---

## Inputs

| Field | Required | Description |
|-------|----------|-------------|
| ticket_id | Yes | The ticket/case identifier |
| reason | Yes | Escalation reason: medical, legal, social, regulatory, high-value |
| customer_message | Yes | Original customer message |
| triage_result | Yes | Output from triage command |
| agent_actions | No | List of actions already taken by the agent |
| order_id | No | Associated order for context |

## Steps

1. Verify escalation reason matches P1/P2 criteria:
   - medical → customer reports adverse reaction, skin irritation, bleeding
   - legal → customer threatens legal action ("sue", "lawyer", "attorney")
   - social → customer threatens social media exposure ("post this", "review", "tweet")
   - regulatory → inquiry about FDA, CE, regulatory compliance
   - high-value → dispute involving $500+ or bulk order
2. Suppress all auto-replies for this ticket
3. Compile escalation package:
   - Customer profile (from ~~store → get_customer)
   - Order history (from ~~store → search_orders)
   - Full message thread
   - Triage result and risk flags
   - Agent actions taken (if any)
   - Recommended action for human reviewer
4. Route to support lead via ~~collab (Feishu/Slack) or email notification
5. Log escalation with timestamp and reason

## Output

```json
{
  "escalation_id": "ESC-2026-001",
  "priority": "P1",
  "trigger": "medical",
  "customer": {
    "id": "cust_123",
    "name": "...",
    "email": "...",
    "order_count": 3,
    "total_spent": 450.00
  },
  "issue_history": [
    {"timestamp": "...", "message": "...", "category": "..."}
  ],
  "agent_actions_taken": [
    {"action": "triage", "result": "medical-risk P1"}
  ],
  "recommended_action": "Contact customer within 1 hour. Review medical history. Offer refund + product replacement.",
  "auto_reply_suppressed": true
}
```

## Risk Boundaries

- **Never** draft a response for escalated tickets. Auto-reply must be suppressed.
- Escalation SLA: P1 = 1 hour, P2 = 4 hours.
- All escalated tickets remain in human queue until explicitly closed by support lead.

## Failure Modes

| Failure | Cause | Fix |
|---------|-------|-----|
| Auto-reply sent before escalation processed | Race condition between draft and escalate | Add suppression flag check before any draft creation |
| Escalation package missing order history | ~~store connector failed | Retry with fallback to cached data |
| Wrong escalation reason | Agent misclassified trigger | Run triage first, then escalate based on triage risk_flags |
