# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `programs/` directory with 5 agent autoresearch constitutions (customer-support, influencer-outreach, ad-creative, shopify-growth, b2b-sales)
- `scripts/` directory with 3 evaluation scripts: `run_eval.py`, `run_autoresearch.py`, `compare_regression.py`
- `experiments/` directory with 5 results.tsv templates, scorecards/, reports/, sessions/ structure
- Autoresearch Loop layer (L3.5) in ARCHITECTURE.md — adapted from karpathy/autoresearch
- Budget control per agent ($3-$6/session, 20-30 experiments max)
- Hard constraints (binary gates) per agent — auto-discard on violation
- Safety boundaries: agent can edit skills/commands but cannot send emails, issue refunds, modify policies, or exceed budget
- `install/` directory with 4 scripts: `install-skills-only.sh`, `install-full-plugin.sh`, `validate-plugin.sh`, `sync-runtime-adapters.sh`
- All commands namespaced: `/customer-support:triage`, `/influencer:creator-research`, `/eval:golden-set`, etc.
- Command contracts with inputs, steps, output JSON, risk boundaries, failure modes
- `ARCHITECTURE.md` — full layered architecture documentation
- `ROADMAP.md` — v0.1 through v1.0 plan
- `NOTICE` file — attribution to upstream `anthropics/knowledge-work-plugins`
- Apache-2.0 license (changed from MIT to match upstream)

### Changed
- License changed from MIT to Apache-2.0
- Install scripts moved from repo root to `install/` directory
- Commands renamed from `/triage` to `/customer-support:triage` (namespaced)
- Install scripts split into skill-only mode and full-plugin mode

### Fixed
- Command → skill path references corrected (e.g., `skills/triage/SKILL.md` → `skills/ticket-triage/SKILL.md`)
- Missing `user_invocable: true` validation added to `validate-plugin.sh`

## [0.1.0] — 2026-07-02

### Added
- Initial commit: 6 plugin directories (customer-support, influencer-outreach, ad-creative, shopify-growth, b2b-sales, agent-evaluation)
- 33 SKILL.md files with `user_invocable: true` frontmatter
- 32 command files (original non-namespaced, fixed in Unreleased)
- 5 `.mcp.json` files with MCP server connections
- 5 `CONNECTORS.md` files with tool category documentation
- `marketplace.json` with plugin registry
- `README.md` in Chinese + English bilingual format
- `.hermes.md` and `AGENTS.md` for runtime context
- `.gitignore`, `LICENSE`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`
