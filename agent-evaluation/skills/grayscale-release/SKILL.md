---
name: grayscale-release
description: Use when planning or executing a grayscale (canary) release for an AI agent update. Manages phased rollout from internal testing through 10% → 50% → full production with monitoring checkpoints and rollback criteria.
user_invocable: true
version: "1.0.0"
tags: [evaluation, grayscale, release, deployment]
---

# Grayscale Release Management

## Release Stages

| Stage | Traffic % | Duration | Exit Criteria |
|-------|-----------|----------|---------------|
| 0 — Internal | 0% (dev only) | Until Golden Set passes | All tests pass |
| 1 — Shadow | 0% (log only) | 1 day | No critical errors |
| 2 — Low-risk only | 5% (P3/P4 only) | 2 days | Human review pass rate ≥ baseline |
| 3 — 10% grayscale | 10% | 3 days | Complaint rate ≤ baseline |
| 4 — 50% grayscale | 50% | 5 days | All metrics stable |
| 5 — Full (HR on high-risk) | 100% (P1/P2 with human) | 7 days | HR pass rate ≥ 95% |
| 6 — Full production | 100% | Ongoing | Continuous monitoring |

## Rollback Criteria

| Condition | Action |
|-----------|--------|
| Human review pass rate drops >10% | Rollback |
| Complaint rate increases >20% | Rollback immediately |
| Critical error (medical advice given) | Rollback + incident review |
| Escalation bypass detected | Rollback + fix logic |
