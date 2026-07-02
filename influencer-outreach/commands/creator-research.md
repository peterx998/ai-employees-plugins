---
name: influencer:creator-research
description: Research a TikTok/Instagram creator and generate a fit score for collaboration
argument-hint: "<handle> [--platform tiktok|instagram|youtube]"
required_connectors: ["~~tiktok"]
risk_level: low
human_review: optional
output_schema: "schemas/influencer-outreach/creator_profile.schema.json"
---

## Inputs

| Field | Required | Description |
|-------|----------|-------------|
| handle | Yes | Creator handle (e.g., @skincarejane) |
| platform | No | Platform (default: tiktok) |
| campaign_brief | No | Current campaign requirements for fit scoring |

## Steps

1. Fetch creator profile from ~~tiktok (followers, engagement_rate, recent_content_tags)
2. Analyze last 10 posts for content themes and audience overlap
3. Score fit (0-100) based on audience match, content alignment, engagement quality, follower tier
4. Identify strengths and concerns
5. Generate recommendation: proceed / monitor / pass

## Output

```json
{
  "handle": "@skincarejane",
  "platform": "tiktok",
  "followers": 45000,
  "engagement_rate": 0.068,
  "fit_score": 82,
  "strengths": ["consistent skincare content", "high comment engagement"],
  "concerns": ["some sponsored content saturation"],
  "recommendation": "proceed"
}
```

## Risk Boundaries

- Never contact the creator directly. This command only produces a research report.
- Do not store creator PII — use handle only.

## Failure Modes

| Failure | Cause | Fix |
|---------|-------|-----|
| Handle not found | Account deleted or handle changed | Return "not found" with suggested alternatives |
| Fit score inflated | Engagement data stale | Always use last 30 days of data |
