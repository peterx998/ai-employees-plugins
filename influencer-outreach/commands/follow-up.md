---
name: influencer:follow-up
description: Draft a follow-up email to a creator who has not responded
argument-hint: "<thread_id> [--day 5|7|15]"
required_connectors: ["~~email"]
risk_level: low
human_review: optional
output_schema: "schemas/influencer-outreach/outreach_email.schema.json"
---

## Inputs

| Field | Required | Description |
|-------|----------|-------------|
| thread_id | Yes | Original outreach email thread ID |
| day | Yes | Follow-up day (5, 7, or 15) |
| creator_profile | Yes | Creator research profile |

## Steps

1. Fetch original thread from ~~email read_thread
2. Check if creator already replied (if yes, abort and route to classify-reply)
3. Select tone by day: Day 5 gentle nudge, Day 7 value-add, Day 15 final check-in
4. Draft follow-up (under 80 words)
5. Exclude creators who explicitly declined
6. Create as Gmail draft

## Output

```json
{
  "subject": "Re: @skincarejane",
  "body": "Hi @skincarejane, just following up...",
  "personalization_hooks": ["referenced original email"],
  "anti_pattern_check": {"passed": true, "violations": []},
  "human_review_recommended": false,
  "follow_up_stage": "day-5",
  "draft_id": "gmail_draft_id"
}
```

## Risk Boundaries

- Maximum 3 follow-ups (day 5, 7, 15). No further contact after day 15.
- If creator declined, add to exclusion list permanently.

## Failure Modes

| Failure | Cause | Fix |
|---------|-------|-----|
| Followed up after decline | Exclusion check failed | Scan thread for opt-out keywords before drafting |
