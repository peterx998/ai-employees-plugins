---
name: customer-support:summarize-thread
description: Summarize a long customer support email thread for quick human review
argument-hint: "<thread_id>"
required_connectors: ["~~email"]
risk_level: low
human_review: optional
---

## Inputs

| Field | Required | Description |
|-------|----------|-------------|
| thread_id | Yes | Email thread ID (Gmail thread ID) |
| max_messages | No | Maximum messages to include (default: all) |

## Steps

1. Fetch full thread from ~~email → read_thread
2. Extract all messages chronologically
3. Identify key events:
   - Initial customer concern
   - Agent responses sent
   - Customer follow-ups or escalations
   - Resolution or pending status
4. Generate structured summary:
   - Customer issue (1-2 sentences)
   - Actions taken by agent
   - Current status
   - Outstanding items
   - Recommended next step
5. Include sentiment trend (improving / neutral / deteriorating)

## Output

```json
{
  "thread_id": "...",
  "message_count": 7,
  "customer_issue": "Customer received defective device, requested replacement on July 1st.",
  "actions_taken": [
    "Triage: categorized as warranty-defect P3",
    "Draft sent: replacement instructions + prepaid return label",
    "Customer replied: device still not working after troubleshooting"
  ],
  "current_status": "pending — customer's 2nd contact, risk of escalation",
  "outstanding_items": [
    "Verify if replacement was shipped",
    "Consider upgrading to P2 due to repeated contact"
  ],
  "sentiment_trend": "deteriorating",
  "recommended_next_step": "Human review — check replacement order status and proactively contact customer"
}
```

## Risk Boundaries

- Summaries should never include medical advice given by agent (flag if found).
- If sentiment is "deteriorating" and contact count ≥ 3, recommend P2 upgrade.

## Failure Modes

| Failure | Cause | Fix |
|---------|-------|-----|
| Summary too verbose | No length limit | Cap at 200 words for issue + actions |
| Missed escalation signal in thread | Sentiment analysis too shallow | Add keyword detection for frustration markers |
