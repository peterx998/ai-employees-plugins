---
name: influencer:usage-rights-check
description: Review collaboration agreement for usage rights, Spark Ads, and whitelisting terms
argument-hint: "<agreement_text>"
required_connectors: []
risk_level: medium
human_review: recommended
---

## Inputs

| Field | Required | Description |
|-------|----------|-------------|
| agreement_text | Yes | Collaboration agreement or contract text |
| creator_handle | Yes | Creator handle for reference |

## Steps

1. Parse agreement for key clauses: usage rights, Spark Ads, exclusivity, content ownership, disclosure, termination
2. Flag missing or ambiguous clauses
3. Generate checklist with pass/warn/fail for each clause

## Output

```json
{
  "clauses": {
    "usage_rights": {"status": "pass", "detail": "Organic + paid, 6 months, TikTok + Instagram"},
    "spark_ads": {"status": "warn", "detail": "Not mentioned - cannot amplify"},
    "exclusivity": {"status": "fail", "detail": "No exclusivity clause"},
    "disclosure": {"status": "pass", "detail": "#ad required, paid partnership tag specified"}
  },
  "overall_risk": "medium",
  "human_review_required": true,
  "recommended_actions": ["Add Spark Ads clause", "Add 30-day category exclusivity"]
}
```

## Risk Boundaries

- This is a review tool, not legal advice. Always recommend human/legal review.
- Flag any agreement without disclosure clause as FTC compliance risk.

## Failure Modes

| Failure | Cause | Fix |
|---------|-------|-----|
| Missed hidden clause | Agreement too long | Chunk into sections before parsing |
