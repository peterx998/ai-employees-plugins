# Influencer Outreach Autoresearch Program

## Goal

Improve influencer-outreach skills (creator-research, draft-first-touch, classify-reply) on the Golden Set without violating compliance boundaries.

## Architecture

```text
prepare.py  →  policies/ + schemas/ + connectors/     (READ-ONLY)
train.py    →  skills/*/SKILL.md + commands/*.md       (AGENT EDITS)
program.md  →  this file                                (HUMAN EDITS)
results.tsv →  experiments/influencer-results.tsv       (AGENT LOGS)
```

## Editable Files

- `influencer-outreach/skills/creator-fit-score/SKILL.md`
- `influencer-outreach/skills/outreach-tone-guide/SKILL.md`
- `influencer-outreach/skills/collaboration-policy/SKILL.md`
- `influencer-outreach/skills/compliance-claims-boundary/SKILL.md`
- `influencer-outreach/commands/creator-research.md`
- `influencer-outreach/commands/draft-first-touch.md`
- `influencer-outreach/commands/follow-up.md`
- `influencer-outreach/commands/classify-reply.md`
- `influencer-outreach/commands/negotiate-rate.md`
- `influencer-outreach/commands/usage-rights-check.md`

## Read-Only Files

- `policies/*.md` (all 5 global policies)
- `schemas/influencer-outreach/*.schema.json`
- `schemas/common/*.schema.json`
- `connectors/*.connector.md`
- `connectors/mock/*.json`
- `influencer-outreach/.claude-plugin/plugin.json`
- `influencer-outreach/.mcp.json`
- `agent-evaluation/runner/*.py`

## Evaluation Metric

```
influencer_score =
  30% × reply_classification_accuracy
+ 25% × personalization_score        (anti-pattern check pass rate)
+ 20% × usage_rights_detection       (correct clause identification)
+ 15% × compliance_boundary          (no medical claims, no payment in first-touch)
+ 10% × human_usability              (draft quality for human review)
```

**Hard constraint**: Fee-request replies must ALWAYS be classified as "fee-request" with human_review_required: true. Any miss → auto-discard.

## Budget Control

| Parameter | Value |
|-----------|-------|
| Max cases per experiment | 40 |
| Max skill files modified | 1 |
| Max experiments per session | 25 |
| Max API cost per session | $4.00 |
| Timeout per experiment | 5 min |

## Experiment Loop

Same structure as customer-support. Key differences:

1. Focus areas: personalization quality, reply classification accuracy
2. Anti-pattern detection: no generic greetings, no payment in first-touch
3. Fee-request classification is a hard gate (like P1 medical for support)

## Safety Boundaries

### Agent CAN:
- Edit SKILL.md and command files
- Run evaluation
- Generate drafts for human review

### Agent CANNOT:
- Send emails (create_draft only)
- Negotiate rates or commit to payments
- Contact creators directly
- Modify exclusion lists without human approval
- Exceed budget

## results.tsv Format

```tsv
commit	agent	skill_modified	score	fee_reply_pass_rate	cost	status	description
```
