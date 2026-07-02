# Experiments Directory

This directory stores all autoresearch experiment data. It is the **knowledge compound interest** layer of the system.

## Structure

```
experiments/
├── customer-support-results.tsv    # Experiment log (TSV, untracked by git)
├── influencer-outreach-results.tsv
├── ad-creative-results.tsv
├── shopify-growth-results.tsv
├── b2b-sales-results.tsv
├── scorecards/                     # JSON scorecards per experiment
│   ├── customer-support/
│   ├── influencer-outreach/
│   ├── ad-creative/
│   ├── shopify-growth/
│   └── b2b-sales/
├── reports/                        # Regression and session reports
│   ├── regression-report.md
│   └── session-report.md
└── sessions/                       # Per-session summary (human review)
    └── session-<tag>.md
```

## TSV Format

All results TSVs follow this format (tab-separated):

```
commit	agent	skill_modified	score	hard_constraint_pass	cost	status	description
```

| Column | Description |
|--------|-------------|
| commit | Git short hash (7 chars) |
| agent | Agent name (e.g., customer-support) |
| skill_modified | Which SKILL.md or command was changed |
| score | Overall score (0.000-1.000) |
| hard_constraint_pass | Did the hard constraint pass? (1.0 or 0.0) |
| cost | API cost in USD for this experiment |
| status | keep, discard, or crash |
| description | Short description of what was tried |

## Git Tracking

- `*.tsv` files are **untracked** (added to .gitignore) — they are local experiment logs
- `scorecards/*.json` are tracked — they are evaluation artifacts for regression comparison
- `reports/*.md` are tracked — they are human-readable summaries
- `sessions/*.md` are tracked — they are session records for human review

## How to Use

After an autoresearch session:

```bash
# View experiment history
cat experiments/customer-support-results.tsv | column -t

# Compare scores across sessions
python scripts/compare_regression.py --agent customer-support

# Generate session report
python scripts/run_autoresearch.py --agent customer-support --report-only
```
