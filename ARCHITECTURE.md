# Architecture

## Overview

AI Employees Plugins combines four architectural paradigms:

1. **[knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins)** — Role capability encapsulation (plugin manifest → skills → commands → connectors)
2. **[karpathy/autoresearch](https://github.com/karpathy/autoresearch)** — Autonomous experiment loop (modify → evaluate → keep/discard → log → repeat)
3. **[kunchenguid/no-mistakes](https://github.com/kunchenguid/no-mistakes)** — Quality gate pipeline (intent → findings → auto-fix / ask-user → PR body)
4. **[kunchenguid/treehouse](https://github.com/kunchenguid/treehouse)** — Worktree isolation (leased worktree → disposable experiment → safe prune)

Together they create a system where enterprise AI agents don't just execute SOPs — they **continuously improve SOPs within safe boundaries, with structured quality gates and isolated execution environments**.

## Layered Architecture

```text
L0  Business Goals / KPIs
        ↓
L1  Role Process Decomposition (6 roles: support, influencer, ad, shopify, b2b, eval)
        ↓
L2  SOP / Knowledge / Templates / Rules / Tag Taxonomy
        ↓
L3  Plugin Encapsulation (knowledge-work-plugins standard)
    ├── .claude-plugin/plugin.json    → Plugin identity, version, permissions
    ├── .mcp.json                     → MCP server connections
    ├── CONNECTORS.md                 → Tool connector documentation
    ├── commands/                     → Executable workflow contracts
    ├── skills/                       → Domain SOP + knowledge (SKILL.md)
    ├── schemas/                      → Input/output JSON Schema
    ├── evals/                        → Golden Set test cases
    └── examples/                     → Real-world usage examples
        ↓
L3.5  Autoresearch Loop (karpathy/autoresearch adapted)
    ├── programs/                     → Experiment "constitution" per agent (human edits)
    │   ├── customer-support-autoresearch.md
    │   ├── influencer-outreach-autoresearch.md
    │   └── ... (5 total)
    ├── scripts/                      → Evaluation harness
    │   ├── run_eval.py               → Golden Set scorer (deterministic)
    │   ├── run_autoresearch.py       → Experiment loop runner
    │   └── compare_regression.py     → Version comparison + regression report
    └── experiments/                  → Experiment logs (knowledge compound interest)
        ├── *-results.tsv             → Per-agent experiment log (untracked)
        ├── scorecards/               → JSON scorecards per experiment
        ├── reports/                  → Regression + session reports
        ├── runs/                     → Isolated run directory (active/archived/failed)
        └── sessions/                 → Human review summaries
        ↓
L3.7  Gate Layer (kunchenguid/no-mistakes adapted)
    ├── scripts/agent_gate.py         → Local pre-push quality pipeline
    │   intent → contract → schema → eval → mock-batch → findings → pr-body
    ├── scripts/findings_report.py    → Structured findings from all stages
    ├── scripts/generate_pr_body.py   → Auto-generated PR body from gate results
    ├── schemas/common/finding.schema.json → Finding schema (severity/action)
    └── experiments/runs/             → Per-agent gate run artifacts
        ├── findings.json             → Structured findings output
        └── pr_body.md               → Generated PR body
        ↓
L3.8  Isolation Layer (kunchenguid/treehouse adapted)
    ├── scripts/run_in_treehouse.sh   → Worktree-based isolation
    │   acquire worktree → run command → return/prune
    ├── experiments/runs/disposable/  → Symlinks to treehouse worktrees
    └── Safe prune: only idle/clean/merged worktrees removed
        ↓
L4  Shared Infrastructure (READ-ONLY for agents)
    ├── schemas/                      → Cross-plugin business entity models
    ├── policies/                     → Global compliance + risk policies
    ├── connectors/                   → Connector contracts + mock data
    └── evals/                        → Cross-agent evaluation runner
        ↓
L5  Runtime Adapters
    ├── Hermes (~/.hermes/skills/ + ~/.hermes/plugins/)
    └── Codex (~/.codex/skills/ + ~/.codex/plugins/)
        ↓
L6  Real Business Execution
        ↓
L7  Human Review / Permissions / Grayscale / Rollback / Logs
        ↓
L8  Golden Set / Regression Test / Error Review (CI-enforced)
        ↓
L9  Asset Accumulation / Component Reuse / Commercial Delivery
```

## Autoresearch Loop Design

Adapted from karpathy/autoresearch's three-file pattern:

| autoresearch | ai-employees-plugins | Who edits |
|-------------|---------------------|-----------|
| `prepare.py` (fixed eval) | `policies/` + `schemas/` + `connectors/` + `evals/` | **Nobody** (read-only) |
| `train.py` (agent modifies) | `skills/*/SKILL.md` + `commands/*.md` | **Agent** (within boundaries) |
| `program.md` (human sets org) | `programs/*-autoresearch.md` | **Human** (experiment constitution) |
| `results.tsv` (experiment log) | `experiments/*-results.tsv` | **Agent** (auto-logged) |

### Experiment Loop

```text
1. Human creates branch: autoresearch/<tag>
2. Agent reads program.md → understands editable/read-only boundaries
3. Agent runs baseline evaluation → records in results.tsv
4. LOOP (max N experiments, max $M cost):
   a. Agent identifies improvement hypothesis (from failed cases)
   b. Agent modifies ONE skill/command file
   c. Agent commits change
   d. Agent runs evaluation: python scripts/run_eval.py --agent <name>
   e. Agent compares score to baseline:
      - If improved AND hard constraint passed → KEEP
      - If worse OR hard constraint failed → DISCARD (git reset)
   f. Agent logs result to results.tsv
5. Agent generates session report + creates PR
6. Human reviews PR → merge → grayscale release
```

### Hard Constraints (Binary Gates)

Each agent has a hard constraint that auto-discards experiments if violated:

| Agent | Hard Constraint | Auto-discard Trigger |
|-------|----------------|---------------------|
| customer-support | P1 medical cases must escalate | Any P1 case missed |
| influencer-outreach | Fee-request replies need human review | Any fee-reply auto-answered |
| ad-creative | Compliance-critical segments detected | Any medical claim missed |
| shopify-growth | Medical claims on pages flagged | Any claim missed |
| b2b-sales | High-value leads escalated | Any $10K+ lead missed |

### Budget Control

| Agent | Max Experiments | Max Cost | Timeout |
|-------|----------------|----------|---------|
| customer-support | 30 | $5.00 | 5 min |
| influencer-outreach | 25 | $4.00 | 5 min |
| ad-creative | 20 | $6.00 | 8 min |
| shopify-growth | 20 | $4.00 | 5 min |
| b2b-sales | 20 | $3.00 | 5 min |

### Safety: What Agent CAN vs CANNOT Do

```text
Agent CAN autonomously:              Agent CANNOT autonomously:
- Edit SKILL.md drafts               - Send emails (draft only)
- Edit command .md files             - Issue refunds
- Run golden set evaluation          - Modify Shopify pages
- Generate scorecards                - Publish ads
- Create git commits on branch       - Modify compliance policies
- Create PR for human review         - Merge PR without human
- Log experiments to results.tsv     - Exceed budget
```

## Plugin Anatomy

Every plugin follows this structure:

```
{plugin-name}/
├── .claude-plugin/
│   └── plugin.json              # Manifest: name, version, runtime, risk_level, permissions
├── .mcp.json                    # MCP server connections (Gmail, Shopify, TikTok, etc.)
├── CONNECTORS.md                # Connector categories + placeholders (~~email, ~~store)
├── .hermes.md                   # Hermes runtime adapter
├── AGENTS.md                    # Codex runtime adapter
├── commands/                    # Executable command contracts
│   └── {namespace}:{command}.md # Namespaced: /customer-support:triage, /eval:golden-set
├── skills/                      # Domain knowledge + SOP
│   └── {skill-name}/SKILL.md    # 10-section structured skill
├── schemas/                     # JSON Schema for inputs/outputs
│   ├── triage_result.schema.json
│   └── draft_response.schema.json
├── evals/                       # Golden Set test cases
│   ├── golden_set_v1.yaml
│   └── expected_outputs.jsonl
└── examples/                    # Real-world usage examples
    ├── p1_medical_risk.md
    └── p3_order_tracking.md
```

## SKILL.md 10-Section Standard

Every SKILL.md follows this structure for production-grade consistency:

| Section | Purpose |
|---------|---------|
| 1. Role | What problem this skill solves in which role |
| 2. Trigger | When should this skill be invoked |
| 3. Required Inputs | Mandatory fields, how to ask for missing ones |
| 4. Decision Framework | Specific judgment rules and scoring criteria |
| 5. Tool Usage | Which connectors are allowed/prohibited |
| 6. Output Contract | Required JSON/Markdown/table output format |
| 7. Risk Boundaries | When to escalate to human |
| 8. Examples | At least 3 input-output samples |
| 9. Evaluation Cases | Which golden set cases cover this skill |
| 10. Failure Modes | Common errors and correction rules |

## Command Contract Standard

Every command includes:

```yaml
---
name: {namespace}:{command}
description: One-line description
argument-hint: "<args>"
required_connectors: ["~~email", "~~store"]
risk_level: low | medium | high
human_review: optional | recommended | required_for_p1_p2 | always
output_schema: "schemas/{output}.schema.json"
---
```

Plus: Inputs, Steps, Output (JSON), Risk Boundaries, Failure Modes.

## Connector Abstraction

Plugins use `~~placeholder` syntax for tool-agnostic references:

| Placeholder | Default | Alternatives |
|-------------|---------|-------------|
| `~~email` | Gmail | Outlook, Microsoft 365 |
| `~~store` | Shopify | WooCommerce, BigCommerce |
| `~~kb` | Notion | Obsidian, Dify, Confluence |
| `~~collab` | Feishu | Slack, Teams |
| `~~tiktok` | TikTok API | — |

Each connector has a contract in `connectors/` defining capabilities, permission levels, required env vars, and safety rules.

## Evaluation Pipeline

```text
Golden Set (fixed test cases)
    → Regression Test (compare before/after update)
    → Grayscale Release (0% → 5% → 10% → 50% → 100%)
    → Error Review (root cause → fix → add to Golden Set)
    → CI Gate (PR must pass golden set to merge)
```

## Install Modes

| Mode | Command | What it installs |
|------|---------|-----------------|
| Skill-only | `install-skills-only.sh hermes\|codex` | SKILL.md files only |
| Full plugin | `install-full-plugin.sh hermes\|codex` | Complete plugin structure |
| Validate | `validate-plugin.sh` | Check structure integrity |
| Sync adapters | `sync-runtime-adapters.sh` | Generate .hermes.md + AGENTS.md |
