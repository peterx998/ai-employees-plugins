---
name: ad-creative:build-ad-brief
description: Build a montage ad brief from top-scored segments with hook variants and CTA options
argument-hint: "<scored_segments>"
required_connectors: []
risk_level: medium
human_review: recommended
output_schema: "schemas/ad-creative/ad_brief.schema.json"
---

## Inputs

| Field | Required | Description |
|-------|----------|-------------|
| scored_segments | Yes | Output from ad-creative:score-segments |
| target_platform | No | tiktok | meta | both (default: both) |
| ad_duration | No | Target ad duration in seconds (default: 15-30) |

## Steps

1. Load top-scored segments by role (hook, demo, proof, CTA)
2. Generate 3 hook variants (emotional, curiosity, benefit-led)
3. Create segment sequence for each duration variant:
   - 15s: hook(3s) + demo(7s) + cta(5s)
   - 30s: hook(3s) + problem(5s) + demo(10s) + proof(7s) + cta(5s)
4. Generate copy variants (3 headline + 3 caption options)
5. Recommend CTA options: shop_now, learn_more, get_offer
6. Include compliance status from compliance-review

## Output

```json
{
  "brief_id": "BRIEF-2026-001",
  "hook_options": [
    {"id": "H1", "type": "emotional", "segment_ref": "seg_001", "copy": "This changed my skin..."},
    {"id": "H2", "type": "curiosity", "segment_ref": "seg_002", "copy": "I wish I knew this sooner"}
  ],
  "segment_sequence": {
    "15s": ["seg_001", "seg_003", "seg_007"],
    "30s": ["seg_001", "seg_002", "seg_003", "seg_005", "seg_007"]
  },
  "copy_variants": [
    {"headline": "Professional microneedling at home", "caption": "See real results in 2 weeks"},
    {"headline": "The skincare tool everyone's talking about", "caption": "Limited time offer"}
  ],
  "cta_recommendations": ["shop_now", "learn_more"],
  "platform": "both",
  "compliance_status": "pending_review"
}
```

## Risk Boundaries

- Ad brief is a recommendation, not final creative. Human creative review required.
- Compliance status must be "passed" before brief is used for production.

## Failure Modes

| Failure | Cause | Fix |
|---------|-------|-----|
| Not enough segments for 30s variant | Source video too short | Fall back to 15s only and flag |
| Hook variants too similar | Template diversity low | Use 3 distinct hook frameworks |
