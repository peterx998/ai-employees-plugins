# B2B Sales Autoresearch Program

## Goal

Improve b2b-sales skills (qualify-lead, draft-quote, summarize-buyer) on the Golden Set. Focus: lead qualification accuracy and quote correctness.

## Architecture

```text
prepare.py  →  policies/ + schemas/ + connectors/     (READ-ONLY)
train.py    →  skills/*/SKILL.md + commands/*.md       (AGENT EDITS)
program.md  →  this file                                (HUMAN EDITS)
results.tsv →  experiments/b2b-sales-results.tsv        (AGENT LOGS)
```

## Editable Files

- `b2b-sales/skills/mdl-product-policy/SKILL.md`
- `b2b-sales/skills/distributor-fit-score/SKILL.md`
- `b2b-sales/skills/quote-rules/SKILL.md`
- `b2b-sales/skills/clinic-use-case/SKILL.md`
- `b2b-sales/skills/compliance-boundary/SKILL.md`
- `b2b-sales/commands/qualify-lead.md`
- `b2b-sales/commands/draft-quote.md`
- `b2b-sales/commands/follow-up-inquiry.md`
- `b2b-sales/commands/summarize-buyer.md`
- `b2b-sales/commands/escalate-high-value.md`

## Read-Only Files

- `policies/*.md`
- `schemas/b2b-sales/*.schema.json`
- `schemas/common/*.schema.json`
- `connectors/*.connector.md`
- `connectors/mock/*.json`
- `b2b-sales/.claude-plugin/plugin.json`
- `b2b-sales/.mcp.json`

## Evaluation Metric

```
b2b_score =
  30% × lead_classification_accuracy  (correct buyer type: retail/clinic/distributor/procurement)
+ 25% × quote_accuracy                (correct pricing tier and discount applied)
+ 20% × high_value_detection          ($10K+ leads correctly escalated)
+ 15% × compliance_awareness          (certification/registration requirements flagged)
+ 10% × summary_quality               (buyer summary actionable for sales team)
```

**Hard constraint**: High-value leads ($10K+ or 100+ units) must be escalated at 100% accuracy. Any miss → auto-discard.

## Budget Control

| Parameter | Value |
|-----------|-------|
| Max inquiries per experiment | 20 |
| Max skill files modified | 1 |
| Max experiments per session | 20 |
| Max API cost per session | $3.00 |
| Timeout per experiment | 5 min |

## Safety Boundaries

### Agent CAN:
- Edit SKILL.md and command files
- Run lead qualification evaluation
- Generate quote drafts for human review

### Agent CANNOT:
- Send quotes to buyers
- Commit to pricing terms
- Modify pricing rules or discount tiers
- Contact buyers directly
- Approve high-value escalations without human

## results.tsv Format

```tsv
commit	agent	skill_modified	score	high_value_pass_rate	cost	status	description
```
