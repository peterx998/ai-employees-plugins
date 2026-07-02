---
name: ad-creative:compliance-review
description: Review video segments and ad copy for platform compliance (Meta, TikTok, FTC)
argument-hint: "<segments> [--platform meta|tiktok|both]"
required_connectors: []
risk_level: high
human_review: always
---

## Inputs

| Field | Required | Description |
|-------|----------|-------------|
| segments | Yes | Video segments from ad-creative:segment-ugc |
| ad_copy | No | Ad text/caption to review |
| platform | No | Target platform (default: both) |

## Steps

1. Check for prohibited claims:
   - Medical efficacy claims (cure, treat, heal, fix)
   - Guaranteed results
   - Before/after without disclosure
   - Exaggerated language ("miracle", "instant", "permanent")
2. Check platform-specific rules:
   - Meta: personal attributes policy, misleading claims
   - TikTok: restricted health content, minor safety
3. Check FTC endorsement compliance:
   - Disclosure present (#ad, paid partnership)
   - No deceptive endorsements
4. Check ASA (UK) if applicable:
   - No misleading advertising
   - Substantiation required for claims
5. Generate compliance report with pass/fail/warn per item

## Output

```json
{
  "overall_status": "fail",
  "platform": "both",
  "findings": [
    {
      "segment_id": "seg_005",
      "issue": "before/after without disclosure",
      "severity": "high",
      "platform": "both",
      "required_action": "Add disclosure overlay: 'Results may vary'"
    },
    {
      "segment_id": "seg_003",
      "issue": "medical claim: 'cures acne scars'",
      "severity": "critical",
      "platform": "both",
      "required_action": "Remove or rephrase to 'may help improve appearance of acne scars'"
    }
  ],
  "human_review_required": true
}
```

## Risk Boundaries

- Critical findings must be fixed before ad submission. No exceptions.
- This command does NOT approve ads. It only flags issues for human review.

## Failure Modes

| Failure | Cause | Fix |
|---------|-------|-----|
| Missed medical claim | OCR didn't catch text overlay | Combine transcript + OCR + visual analysis |
| False positive on common phrase | Keyword match too aggressive | Use context-aware classification, not just keyword match |
