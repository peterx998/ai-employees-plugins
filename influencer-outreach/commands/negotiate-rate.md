---
name: influencer:negotiate-rate
description: Prepare a rate negotiation brief for human review (agent does NOT negotiate)
argument-hint: "<thread_id> <creator_profile>"
required_connectors: ["~~email"]
risk_level: high
human_review: always
---

## Inputs

| Field | Required | Description |
|-------|----------|-------------|
| thread_id | Yes | Email thread with creator fee request |
| creator_profile | Yes | Creator research profile with fit score |
| budget_range | No | Available budget for this creator tier |

## Steps

1. Fetch creator fee request from thread
2. Analyze rate vs benchmarks: micro $50-$300, mid $300-$1500, macro $1500-$5000+
3. Prepare brief: requested rate, benchmark range, fit score, recommended counter range, non-monetary alternatives
4. Route to human via ~~collab notification

## Output

```json
{
  "creator_requested_rate": "$800 per TikTok post",
  "benchmark_range": "$300-$1,500 (mid-tier)",
  "fit_score": 82,
  "recommended_counter_range": "$400-$600 per post + product bundle",
  "non_monetary_alternatives": ["3-month product supply", "affiliate code 15% commission", "long-term partnership"],
  "human_review_required": true,
  "agent_action": "none - brief prepared for human"
}
```

## Risk Boundaries

- Agent never sends negotiation emails. Only prepares a brief.
- Agent never commits to any rate or payment terms.

## Failure Modes

| Failure | Cause | Fix |
|---------|-------|-----|
| Agent sent negotiation email | Boundary not enforced | Hard block: this command only outputs a brief, never calls create_draft |
