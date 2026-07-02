# Ad Creative Autoresearch Program

## Goal

Improve ad-creative skills (segment-ugc, score-segments, compliance-review) on the Golden Set. Focus: semantic segmentation accuracy and compliance risk detection.

## Architecture

```text
prepare.py  →  policies/ + schemas/ + connectors/     (READ-ONLY)
train.py    →  skills/*/SKILL.md + commands/*.md       (AGENT EDITS)
program.md  →  this file                                (HUMAN EDITS)
results.tsv →  experiments/ad-creative-results.tsv      (AGENT LOGS)
```

## Editable Files

- `ad-creative/skills/hook-framework/SKILL.md`
- `ad-creative/skills/segment-taxonomy/SKILL.md`
- `ad-creative/skills/compliance-risk-rules/SKILL.md`
- `ad-creative/skills/meta-ad-creative-rules/SKILL.md`
- `ad-creative/skills/tiktok-ugc-patterns/SKILL.md`
- `ad-creative/commands/analyze-video.md`
- `ad-creative/commands/segment-ugc.md`
- `ad-creative/commands/score-segments.md`
- `ad-creative/commands/compliance-review.md`
- `ad-creative/commands/build-ad-brief.md`

## Read-Only Files

- `policies/*.md`
- `schemas/ad-creative/*.schema.json`
- `schemas/common/*.schema.json`
- `connectors/*.connector.md`
- `connectors/mock/*.json`
- `ad-creative/.claude-plugin/plugin.json`
- `ad-creative/.mcp.json`

## Evaluation Metric

```
creative_score =
  30% × segmentation_accuracy       (correct semantic role classification)
+ 25% × compliance_detection        (medical claims, before/after, exaggerated language)
+ 20% × hook_quality                (hook segment scoring vs human-labeled baseline)
+ 15% × evidence_completeness       (timestamp + transcript + visual + OCR all present)
+ 10% × brief_usability             (ad brief quality for human review)
```

**Hard constraint**: Compliance-critical segments (medical claims, before/after without disclosure) must be detected at 100% recall. Any miss → auto-discard.

## Budget Control

| Parameter | Value |
|-----------|-------|
| Max videos per experiment | 3 |
| Max segments per video | 20 |
| Max skill files modified | 1 |
| Max experiments per session | 20 |
| Max API cost per session | $6.00 |
| Timeout per experiment | 8 min |

## Experiment Loop

Key differences from support:

1. Each experiment processes 3 sample videos (not text cases)
2. Evaluation requires multimodal analysis (transcript + visual + OCR)
3. Compliance detection is binary hard gate (must catch all critical risks)
4. Hook scoring calibrated against human-labeled baseline

## Safety Boundaries

### Agent CAN:
- Edit SKILL.md and command files
- Run video analysis evaluation
- Generate ad briefs for human review

### Agent CANNOT:
- Publish ads
- Render final videos without human approval
- Modify compliance policies
- Auto-approve any ad creative

## results.tsv Format

```tsv
commit	agent	skill_modified	score	compliance_recall	cost	status	description
```
