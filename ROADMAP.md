# Roadmap

## v0.1 — Architecture Seed (2026-07-02) ✅

- [x] 6 plugin directories created
- [x] 33 SKILL.md files with `user_invocable: true`
- [x] 32 namespaced commands
- [x] `.mcp.json` + `CONNECTORS.md` per plugin
- [x] Dual-runtime install scripts
- [x] README (Chinese + English bilingual)

## v0.2-alpha — Architecture Sample (2026-07-02) ✅

- [x] 6 plugin directories created
- [x] 33 SKILL.md files with `user_invocable: true`
- [x] 33 namespaced commands (plugin:command format)
- [x] `.mcp.json` + `CONNECTORS.md` per plugin
- [x] Dual-runtime install scripts (4 scripts in install/)
- [x] README (Chinese + English bilingual)
- [x] Apache-2.0 license + NOTICE
- [x] ARCHITECTURE.md + ROADMAP.md + CHANGELOG.md
- [x] 18 JSON Schemas + 5 global policies + 7 connector contracts
- [x] 50-case golden set for customer-support
- [x] Autoresearch Loop layer (programs/ + scripts/ + experiments/)
- [x] CI workflow with schema consistency check

## v0.2-beta — Contract Alignment + Real Eval (current)

Goal: Make customer-support a real, testable, fail-closeable evaluation loop.

- [x] Unified taxonomy (schemas/enums/customer_support_taxonomy.yaml)
- [x] Schema priority enum: P1/P2/P3/P4 (was low/medium/high/urgent)
- [x] SKILL.md output contract: route_to/risk_flags (was routing/flags)
- [x] CI gate: removed `|| true`, PENDING = FAIL, schema validation added
- [x] Eval runner: no actual output = FAIL (was using expected as baseline)
- [x] Autoresearch: git diff detection, skill_modified tracking, base_commit reset
- [x] Autoresearch: no-op experiments discarded (no changes = discard)
- [x] Actual output fixtures: 50 baseline JSON files
- [x] Deep validator (validate-contracts.py + validate-evals.py)
- [x] MCP template cleanup (remove placeholders from .mcp.json)
- [x] Agent Batch Runner (mock/codex/hermes adapters + run_agent_batch.py)
- [x] Runtime MCP servers (gmail, shopify, kb, human_review)
- [x] P2 hard constraints + enhanced regression comparison
- [x] actual_outputs metadata upgrade (_meta on all baselines)

## v0.3 — Evaluation Framework CI (planned)

- [ ] `evals/` directory with golden sets for customer-support
- [ ] `agent-evaluation/runner/run_eval.py` — automated test runner
- [ ] `agent-evaluation/runner/judge_output.py` — output scoring
- [ ] `.github/workflows/eval.yml` — CI gate on every PR
- [ ] Regression report generation
- [ ] Scorecard JSON output
- [ ] Score threshold blocks merge

## v0.4 — Influencer Outreach Deep Build (planned)

- [ ] `schemas/creator_profile.schema.json`
- [ ] `schemas/outreach_thread.schema.json`
- [ ] Classify-reply output enum validation
- [ ] Fee reply → human handoff contract
- [ ] Usage rights review checklist
- [ ] 40 golden set cases
- [ ] Desensitized real email examples

## v0.5 — Ad Creative Deep Build (planned)

- [ ] `schemas/video_segment.schema.json` with timestamp evidence index
- [ ] Semantic segmentation rules (hook | proof | demo | objection | cta)
- [ ] Compliance risk detection (medical claims, before/after, exaggerated)
- [ ] Hook scoring framework (0-100)
- [ ] Montage brief builder
- [ ] 30 golden set cases

## v0.6 — Shopify + B2B + Full Connector Layer (planned)

- [ ] Real Gmail connector with OAuth scope documentation
- [ ] Real Shopify connector with API permissions
- [ ] Real Clarity connector for session analysis
- [ ] Shopify golden set (20 cases)
- [ ] B2B golden set (20 cases)

## v1.0 — Production Release (planned)

- [ ] All 6 plugins at production depth
- [ ] 150+ golden set cases across all agents
- [ ] CI-enforced regression testing
- [ ] Feature flags for grayscale release
- [ ] Complete connector permission matrix
- [ ] Full documentation in Chinese + English
- [ ] Apache-2.0 license with NOTICE
