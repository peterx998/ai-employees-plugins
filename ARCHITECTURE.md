# Architecture

## Overview

AI Employees Plugins is built on the [knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins) architecture, adapted for **Hermes Agent** and **Codex CLI** dual runtime. Each plugin bundles skills (domain knowledge + SOP), commands (executable workflow entry points), connectors (MCP tool connections), and evaluation suites (Golden Set + regression tests).

## Layered Architecture

```text
L0  Business Goals / KPIs
        ↓
L1  Role Process Decomposition (6 roles: support, influencer, ad, shopify, b2b, eval)
        ↓
L2  SOP / Knowledge / Templates / Rules / Tag Taxonomy
        ↓
L3  Plugin Encapsulation (this repo — knowledge-work-plugins standard)
    ├── .claude-plugin/plugin.json    → Plugin identity, version, permissions
    ├── .mcp.json                     → MCP server connections
    ├── CONNECTORS.md                 → Tool connector documentation
    ├── commands/                     → Executable workflow contracts
    ├── skills/                       → Domain SOP + knowledge (SKILL.md)
    ├── schemas/                      → Input/output JSON Schema
    ├── evals/                        → Golden Set test cases
    └── examples/                     → Real-world usage examples
        ↓
L4  Shared Infrastructure
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
