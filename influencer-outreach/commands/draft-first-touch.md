---
name: influencer:draft-first-touch
description: Draft a personalized first-touch outreach email to a creator
argument-hint: "<creator_profile> [--template A|B|C]"
required_connectors: ["~~email"]
risk_level: medium
human_review: recommended
output_schema: "schemas/influencer-outreach/outreach_email.schema.json"
---

## Inputs

| Field | Required | Description |
|-------|----------|-------------|
| creator_profile | Yes | Output from influencer:creator-research |
| template | No | A/B/C variant (default: weighted 40/30/30) |
| product_info | Yes | Product name and key benefit |
| sender_name | Yes | Who the email is from |

## Steps

1. Load creator profile (handle, strengths, content themes)
2. Select template variant (A=product-first, B=audience-first, C=collaboration-first)
3. Personalize: use handle in subject only, reference specific recent post, acknowledge audience niche, offer product as gift, keep under 150 words
4. Run anti-pattern checks: no generic greetings, no payment mention, no unrealistic promises
5. Create as Gmail draft (~~email create_draft), do NOT send

## Output

```json
{
  "subject": "@skincarejane",
  "body": "Hi @skincarejane, loved your recent video about...",
  "personalization_hooks": ["referenced post about vitamin C serum"],
  "anti_pattern_check": {"passed": true, "violations": []},
  "human_review_recommended": true,
  "draft_id": "gmail_draft_id"
}
```

## Risk Boundaries

- Never auto-send. Draft only.
- Subject line must contain ONLY the handle.
- No payment terms in first-touch emails.

## Failure Modes

| Failure | Cause | Fix |
|---------|-------|-----|
| Generic greeting | Template not personalized | Enforce personalization hook from creator_profile |
| Payment mentioned | Template leaked compensation language | Remove all payment references from templates |
