---
name: ad-creative:render-template-plan
description: Generate a rendering plan for Shotstack or FFmpeg montage from ad brief
argument-hint: "<ad_brief>"
required_connectors: []
risk_level: low
human_review: optional
---

## Inputs

| Field | Required | Description |
|-------|----------|-------------|
| ad_brief | Yes | Output from ad-creative:build-ad-brief |
| render_engine | No | shotstack | ffmpeg (default: shotstack) |

## Steps

1. Load ad brief (segment sequence, hooks, CTA)
2. Map segments to source video timestamps
3. Generate render timeline:
   - For each segment: source video, start time, duration, transition
4. Add text overlays (hook copy, CTA copy)
5. Add music track recommendation (if no audio in segments)
6. Output render plan JSON for Shotstack API or FFmpeg command

## Output

```json
{
  "render_engine": "shotstack",
  "timeline": {
    "tracks": [
      {
        "type": "video",
        "clips": [
          {"source": "video_url", "start": 0, "duration": 3, "transition": "fade"},
          {"source": "video_url", "start": 5, "duration": 7, "transition": "cut"}
        ]
      },
      {
        "type": "text",
        "clips": [
          {"text": "This changed my skin...", "start": 0, "duration": 3, "position": "bottom"}
        ]
      }
    ]
  },
  "music_track": "upbeat_lifestyle_01",
  "output_format": "mp4",
  "resolution": "1080x1920"
}
```

## Risk Boundaries

- This is a render plan only. Actual rendering requires human approval and API credentials.
- Do not include any compliance-failed segments in the render timeline.

## Failure Modes

| Failure | Cause | Fix |
|---------|-------|-----|
| FFmpeg command too long | Too many segments | Split into multiple render passes |
| Source video URL expired | Temporary URL | Re-fetch source video before rendering |
