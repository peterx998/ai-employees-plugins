# STATUS — Project Component Status

> **Single source of truth** for what is actually done, partial, or not started.
> README.md, ROADMAP.md, and ARCHITECTURE.md should not contradict this file.
>
> Source: `docs/status.yaml` · Last updated: 2026-07-03

---

## Summary Table

| Component | Status | Notes |
|-----------|--------|-------|
| customer-support SOP | ✅ DONE | Sample-grade ticket-triage SKILL.md |
| influencer-outreach SOP | 🟡 PARTIAL | creator-research has fit-score; others template-level |
| ad-creative SOP | ⬜ NOT_STARTED | Template-level only |
| shopify-growth SOP | ⬜ NOT_STARTED | Template-level only |
| b2b-sales SOP | ⬜ NOT_STARTED | Template-level only |
| Golden Set (single-turn) | ✅ DONE | 50 cases, 8 categories |
| Golden Set (multi-turn) | 🟡 PARTIAL | 10 conversations + runner + state-diff evaluator; not in CI |
| Unified Evaluator | ✅ DONE | Schema + hard constraints + rubric + EvalSummary |
| Regression Comparison | ✅ DONE | Unified accessor, old/new format compat |
| Tool Trace Evaluation | 🟡 PARTIAL | Evaluator + 10 traces; not in main pipeline |
| State Diff Evaluation | 🟡 PARTIAL | Evaluator implemented; not in CI |
| Permission Gateway | ✅ DONE | P1 write-deny, send_email always-deny, PII redaction |
| Audit Logger | ✅ DONE | tool_calls.jsonl + permission_violations.jsonl |
| PII Redaction | ✅ DONE | Email, phone, order, CC, IP |
| Human Review Gateway | ✅ DONE | Submit/approve/reject queue |
| Mock MCP Servers | ✅ DONE | Gmail, Shopify, KB, Human Review stubs |
| Real MCP Servers | ⬜ NOT_STARTED | Mock only |
| CI Workflow | ✅ DONE | Schema + pipeline integrity + gate + findings |
| CI Regression Gate | ✅ DONE | Phase 3 regression compare in batch runner |
| CI Tool Trace Gate | ⬜ NOT_STARTED | Not wired into workflow |
| CI Multi-turn Gate | ⬜ NOT_STARTED | Not wired into workflow |
| Autoresearch Harness | 🟡 PARTIAL | Eval harness works; no LLM-driven file modification |
| Autoresearch Autonomous | ⬜ NOT_STARTED | No autonomous agent loop |
| Worktree Isolation | 🟡 PARTIAL | Basic worktree; no lease lock or run_id binding |
| Mock Adapter | ✅ DONE | Pipeline integrity testing |
| Codex Adapter | 🟡 PARTIAL | Exists, untested in CI |
| Hermes Adapter | ✅ DONE | Fail-closed, no silent fallback |
| Findings Report | ✅ DONE | Auto-fix / ask-user classification |
| Tool Call Logging | ✅ DONE | JSONL audit trail |
| Agent Run Logging | ⬜ NOT_STARTED | No latency/cost/trace_id metrics |

---

## Status Definitions

- **✅ DONE** — Feature is implemented, tested, and functional
- **🟡 PARTIAL** — Core implementation exists but incomplete or not integrated
- **⬜ NOT_STARTED** — Not yet implemented
- **🚫 BLOCKED** — Blocked by external dependency

---

## Key Architectural Boundaries Enforced

| Rule | Enforcement |
|------|-------------|
| P1 cases suppress auto-reply | Evaluator hard constraint + mock adapter |
| P1 cases deny write tools | PermissionGateway |
| `send_email` always denied | PermissionGateway (no override) |
| `create_draft` requires human review | PermissionGateway (P2+ only) |
| `shopify.update_page` agent-deny | PermissionGateway |
| PII auto-redacted | Redactor on all tool call arguments |
| All tool calls logged | AuditLogger → tool_calls.jsonl |
| Permission violations logged | AuditLogger → permission_violations.jsonl |
| No expected fallback in eval | run_eval.py returns FAIL, not expected |
| Hermes CLI fail-closed | No dry-run fallback, explicit `hermes-dry-run` only |
| CI blocks on regression | run_agent_batch.py Phase 3, BLOCK_MERGE → exit 1 |

---

## What's Next (Priority Order)

1. **Integrate ToolTraceEvaluator into main evaluator pipeline** — wire tool_calls.jsonl into evaluator scoring
2. **Wire multi-turn runner + state-diff into CI** — add as separate CI job
3. **Agent run logging** — agent_run.jsonl with latency/cost/trace_id
4. **Worktree run_id binding** — lease.json + commit_before/after + artifacts
5. **Autoresearch autonomous loop** — LLM-driven hypothesis → modify → eval → keep/discard
6. **Influencer-outreach deep build** — replicate customer-support pattern
