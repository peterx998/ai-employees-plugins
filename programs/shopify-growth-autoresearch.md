# Shopify Growth Autoresearch Program

## Goal

Improve shopify-growth skills (product-page-review, seo-audit, faq-generate) on the Golden Set. Focus: page audit accuracy and FAQ quality.

## Architecture

```text
prepare.py  →  policies/ + schemas/ + connectors/     (READ-ONLY)
train.py    →  skills/*/SKILL.md + commands/*.md       (AGENT EDITS)
program.md  →  this file                                (HUMAN EDITS)
results.tsv →  experiments/shopify-growth-results.tsv   (AGENT LOGS)
```

## Editable Files

- `shopify-growth/skills/brand-voice/SKILL.md`
- `shopify-growth/skills/product-positioning/SKILL.md`
- `shopify-growth/skills/shopify-conversion-rules/SKILL.md`
- `shopify-growth/skills/medical-beauty-compliance/SKILL.md`
- `shopify-growth/skills/content-structure/SKILL.md`
- `shopify-growth/commands/product-page-review.md`
- `shopify-growth/commands/seo-audit.md`
- `shopify-growth/commands/landing-page-brief.md`
- `shopify-growth/commands/clarity-session-analysis.md`
- `shopify-growth/commands/faq-generate.md`
- `shopify-growth/commands/review-import-check.md`

## Read-Only Files

- `policies/*.md`
- `schemas/common/*.schema.json`
- `connectors/shopify.connector.md`
- `connectors/clarity.connector.md`
- `connectors/notion.connector.md`
- `connectors/mock/*.json`
- `shopify-growth/.claude-plugin/plugin.json`
- `shopify-growth/.mcp.json`

## Evaluation Metric

```
shopify_score =
  30% × audit_accuracy             (correct identification of page issues)
+ 25% × faq_quality                (relevant, accurate, compliant answers)
+ 20% × seo_score_accuracy         (correct SEO findings vs human baseline)
+ 15% × compliance_flag_rate       (medical claims on product pages caught)
+ 10% × brief_usability            (landing page brief quality)
```

**Hard constraint**: Medical claims on product pages must be flagged at 100% recall.

## Budget Control

| Parameter | Value |
|-----------|-------|
| Max pages per experiment | 5 |
| Max skill files modified | 1 |
| Max experiments per session | 20 |
| Max API cost per session | $4.00 |
| Timeout per experiment | 5 min |

## Safety Boundaries

### Agent CAN:
- Edit SKILL.md and command files
- Run page audit evaluation
- Generate FAQ drafts and landing page briefs

### Agent CANNOT:
- Modify Shopify store pages
- Publish FAQ entries directly
- Change SEO settings
- Access real customer session data (use mock data only)

## results.tsv Format

```tsv
commit	agent	skill_modified	score	compliance_flag_rate	cost	status	description
```
