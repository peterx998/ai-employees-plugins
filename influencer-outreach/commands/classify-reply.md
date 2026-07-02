---
name: influencer:classify-reply
description: Classify a creator reply to outreach and determine next action
argument-hint: "<thread_id>"
required_connectors: ["~~email"]
risk_level: medium
human_review: required_for_fee_replies
output_schema: "schemas/influencer-outreach/reply_classification.schema.json"
---

## Inputs

| Field | Required | Description |
|-------|----------|-------------|
| thread_id | Yes | Email thread containing creator reply |
| creator_profile | Yes | Creator research profile |

## Steps

1. Fetch creator reply from ~~email read_thread
2. Classify: interested / interested-with-questions / fee-request / declined / unclear
3. If fee-request, flag for human review (agents cannot negotiate fees)
4. Next action: interested→send product info, fee-request→escalate, declined→exclusion list, unclear→clarification
5. Set follow-up timing

## Output

```json
{
  "category": "fee-request|interested|interested-with-questions|declined|unclear",
  "next_action": "escalate-fee|send-product-info|answer-questions|add-to-exclusion|send-clarification",
  "human_review_required": true,
  "follow_up_timing": "immediate|3-days|none"
}
```

## Risk Boundaries

- Fee requests must always go to human review. Agents cannot negotiate or approve payments.
- Declined creators go to exclusion list permanently.

## Failure Modes

| Failure | Cause | Fix |
|---------|-------|-----|
| Fee reply auto-answered | Missed fee language | Add keywords: rate, compensation, paid, budget |
