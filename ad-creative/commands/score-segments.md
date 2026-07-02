---
name: ad-creative:score-segments
description: Score each video segment 0-100 for creative quality and ad suitability
argument-hint: "<segments>"
required_connectors: []
risk_level: low
human_review: recommended
output_schema: "schemas/ad-creative/video_segment.schema.json"
---

## Inputs

| Field | Required | Description |
|-------|----------|-------------|
| segments | Yes | Output from ad-creative:segment-ugc |
| scoring_criteria | No | Custom weights (default: standard) |

## Steps

1. Load segmented video data
2. Score each segment (0-100) on:
   - Hook strength (for hook segments): emotional pull, curiosity gap, visual impact
   - Demo clarity (for demo segments): clear product visible, easy to follow
   - Proof credibility (for proof segments): authentic, specific results
   - CTA effectiveness (for CTA segments): clear action, urgency, incentive
3. Apply compliance penalty: -20 for medical claims, -15 for before/after without disclosure
4. Rank segments by score within each role
5. Recommend top segments for montage

## Output

```json
{
  "scored_segments": [
    {
      "segment_id": "seg_001",
      "semantic_role": "hook",
      "score": 87,
      "score_breakdown": {"emotional_pull": 9, "curiosity_gap": 8, "visual_impact": 9},
      "compliance_penalty": 0,
      "recommended_use": "opening",
      "rank_in_role": 1
    }
  ],
  "top_picks": {
    "hook": "seg_001",
    "demo": "seg_003",
    "proof": "seg_005",
    "cta": "seg_007"
  }
}
```

## Risk Boundaries

- Segments with compliance penalty > 30 should not be recommended for ads.
- Human review recommended for all segments scoring 60-80 (borderline).

## Failure Modes

| Failure | Cause | Fix |
|---------|-------|-----|
| All segments score high | Scoring too lenient | Calibrate against historical performance data |
| Hook segment scores low | Hook criteria too strict | Ensure hook scoring accounts for niche audience appeal |
