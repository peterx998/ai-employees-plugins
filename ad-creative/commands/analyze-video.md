---
name: ad-creative:analyze-video
description: Extract transcript, key frames, OCR text, and audio from a video for creative analysis
argument-hint: "<video_url> [--language auto]"
required_connectors: []
risk_level: low
human_review: optional
output_schema: "schemas/ad-creative/video_segment.schema.json"
---

## Inputs

| Field | Required | Description |
|-------|----------|-------------|
| video_url | Yes | URL or path to the video file |
| language | No | Audio language for transcription (default: auto-detect) |

## Steps

1. Extract audio track and generate timestamped transcript (Whisper or equivalent)
2. Extract key frames at scene change points (PySceneDetect)
3. Run OCR on key frames to capture on-screen text
4. Generate visual description for each key frame
5. Build timestamped evidence index: {time, transcript, visual, ocr_text}
6. Return raw data for downstream segmentation command

## Output

```json
{
  "video_url": "...",
  "duration_seconds": 45,
  "language_detected": "en",
  "evidence_index": [
    {
      "timestamp": "00:00-00:03",
      "transcript": "So I've been using this microneedling pen for two weeks...",
      "visual_description": "Creator holding device, bathroom setting",
      "ocr_text": "Dr. Pen A1"
    }
  ]
}
```

## Risk Boundaries

- Do not store video files permanently. Process and discard.
- OCR text may contain errors — flag low-confidence readings.

## Failure Modes

| Failure | Cause | Fix |
|---------|-------|-----|
| Transcript empty | No audio track | Fall back to visual-only analysis |
| Scene detection too aggressive | Threshold too low | Use adaptive threshold (VP_SCENE_ADAPTIVE_THRESHOLD=3.0) |
