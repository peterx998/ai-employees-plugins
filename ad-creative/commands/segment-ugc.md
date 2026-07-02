---
name: ad-creative:segment-ugc
description: Segment UGC video into semantic creative segments (hook, proof, demo, objection, CTA)
argument-hint: "<evidence_index>"
required_connectors: []
risk_level: low
human_review: optional
output_schema: "schemas/ad-creative/video_segment.schema.json"
---

## Inputs

| Field | Required | Description |
|-------|----------|-------------|
| evidence_index | Yes | Output from ad-creative:analyze-video |
| segment_granularity | No | fine (3-5s) or coarse (10-15s), default: adaptive |

## Steps

1. Load evidence index (transcript + visual + OCR per timestamp)
2. Classify each segment into semantic role:
   - `hook` — Opening 0-3s, attention grabber
   - `problem` — Pain point or before-state
   - `demo` — Product demonstration, how-to
   - `proof` — Results, testimonial, before/after
   - `objection` — Addressing concerns or FAQs
   - `cta` — Call to action, discount, link
3. Merge adjacent segments with same role
4. Apply creative tags: {product_visible, face_visible, text_overlay, music_type}
5. Flag risk segments (medical claims, before/after, exaggerated language)

## Output

```json
{
  "segments": [
    {
      "segment_id": "seg_001",
      "start_time": "00:00",
      "end_time": "00:03",
      "transcript": "So I've been using this microneedling pen...",
      "semantic_role": "hook",
      "creative_tags": ["face_visible", "product_visible"],
      "risk_flags": [],
      "score": 0,
      "recommended_use": "opening"
    }
  ]
}
```

## Risk Boundaries

- Flag any segment with medical claims for compliance review before use.
- Before/after segments require disclosure overlay.

## Failure Modes

| Failure | Cause | Fix |
|---------|-------|-----|
| All segments tagged as demo | Classification threshold too broad | Use LLM-based semantic classification with role definitions |
| Missing hook segment | Video starts mid-demo | Flag as incomplete creative structure |
