# Roadmap

## v0.1 — Architecture Seed (2026-07-02) ✅

- [x] 6 plugin directories created
- [x] 33 SKILL.md files with `user_invocable: true`
- [x] 32 namespaced commands
- [x] `.mcp.json` + `CONNECTORS.md` per plugin
- [x] Dual-runtime install scripts
- [x] README (Chinese + English bilingual)

## v0.2 — Customer Support Production Sample (in progress)

Goal: prove one plugin can run, be evaluated, have human review, and be rolled back.

- [ ] Upgrade all customer-support SKILL.md to 10-section standard
- [ ] Add command contracts with input/output schema references
- [ ] Add `schemas/` for support_ticket, triage_result, draft_response, escalation_package
- [ ] Add `evals/golden_set_v1.yaml` with 50 test cases
- [ ] Add `examples/` with 3 real-world scenarios (P1 medical, P2 refund, P3 tracking)
- [ ] Add `policies/medical-compliance.md` as global policy
- [ ] Add `connectors/gmail.connector.md` with permission levels
- [ ] Enhanced `plugin.json` with runtime, risk_level, permissions

**Completion criteria**: 50 golden set cases, every command has I/O schema, P1/P2 must human review, email only create_draft, regression runnable.

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
