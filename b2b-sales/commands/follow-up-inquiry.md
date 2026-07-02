---
name: b2b:follow-up-inquiry
description: Draft a follow-up email to a B2B lead who hasn't responded to quote
argument-hint: "<quote_id> [--day 3|7|14]"
required_connectors: ["~~email"]
risk_level: low
human_review: optional
output_schema: "schemas/influencer-outreach/outreach_email.schema.json"
---

## Inputs

| Field | Required | Description |
|-------|----------|-------------|
| quote_id | Yes | Quote ID from b2b:draft-quote |
| day | Yes | Follow-up day (3, 7, or 14) |
| lead_profile | Yes | Lead qualification profile |

## Steps

1. Fetch original quote and thread from ~~email
2. Check if lead already responded (if yes, abort)
3. Select tone by day:
   - Day 3: Check-in, offer to answer questions
   - Day 7: Value-add (share catalog or case study)
   - Day 14: Final check-in, create urgency (quote expiry)
4. Draft follow-up email referencing the quote
5. Create as Gmail draft

## Output

```json
{
  "subject": "Re: Quote QT-2026-001 - Glow Clinic Chain",
  "body": "Hi, following up on the quote we sent...",
  "human_review_recommended": false,
  "follow_up_stage": "day-3",
  "draft_id": "gmail_draft_id"
}
```

## Risk Boundaries

- Maximum 3 follow-ups. No contact after day 14 if no response.
- Do not pressure or use aggressive sales language.

## Failure Modes

| Failure | Cause | Fix |
|---------|-------|-----|
| Followed up after response | Thread scan missed reply | Always check for new messages before drafting |
