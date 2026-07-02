---
name: grayscale-release
description: Use when planning or executing a grayscale (canary) release for an AI agent update. Manages phased rollout from internal testing through 10% to full production, with monitoring checkpoints and automatic rollback criteria.
user_invocable: true
version: "1.1.0"
tags: [evaluation, grayscale, release, deployment]
---

# Grayscale Release Management

## 1. Role

Grayscale release is the deployment safety mechanism that prevents bad agent updates from reaching all customers at once. It controls the rollout from 0% to 100% traffic with checkpoints and automatic rollback.

## 2. Trigger

- After regression tests pass and release is approved
- When promoting an agent update from staging to production
- When rolling back a failed release

## 3. Required Inputs

- `agent_name`: Which agent is being released
- `version`: New version number
- `golden_set_results`: Must show PASS before starting grayscale
- `feature_flags_path`: Path to feature flag config

## 4. Decision Framework

### Release Stages

| Stage | Traffic % | Duration | Exit Criteria | Blocking? |
|-------|-----------|----------|---------------|-----------|
| 0 — Internal | 0% (dev only) | Until Golden Set passes | All GS tests pass (100%) | ✅ |
| 1 — Shadow | 0% (log only, no customer reply) | 1 day | No critical errors in shadow mode | ✅ |
| 2 — Low-risk only | 5% (P3/P4 only) | 2 days | HR pass rate ≥ baseline, 0 complaints | ✅ |
| 3 — 10% grayscale | 10% (all priorities, P1/P2 with HR) | 3 days | Complaint rate ≤ baseline, error rate ≤ baseline | ✅ |
| 4 — 50% grayscale | 50% | 5 days | All metrics stable, no rollback triggers | ✅ |
| 5 — Full (HR on high-risk) | 100% (P1/P2 still human review) | 7 days | HR pass rate ≥ 95% | ✅ |
| 6 — Full production | 100% | Ongoing | Continuous monitoring | — |

### Monitoring Metrics (checked at every stage)

| Metric | Source | Alert Threshold |
|--------|--------|----------------|
| Human review pass rate | Review queue | Drop >10% from baseline |
| Customer complaint rate | Support tickets | Increase >20% from baseline |
| Error/incorrect response rate | Error logs | Any P1 category error |
| Escalation accuracy | Escalation queue | Drop >5% from baseline |
| Response time | APM | Increase >50% from baseline |
| Cost per interaction | Billing | Increase >30% from baseline |

### Automatic Rollback Criteria

| Condition | Action | Speed |
|-----------|--------|-------|
| Human review pass rate drops >10% | Rollback to previous stage | Within 1 hour |
| Complaint rate increases >20% | Rollback immediately | Within 30 min |
| Critical error (medical advice given) | Rollback + incident review | Immediate |
| Escalation bypass detected | Rollback + fix escalation logic | Immediate |
| 3+ regression cases found post-release | Rollback + re-test | Within 1 hour |

## 5. Tool Usage

- `release/feature_flags.yaml`: Feature flag configuration for traffic control
- `release/rollback_playbook.md`: Step-by-step rollback procedure
- CI pipeline: Auto-run golden set before any stage advancement

## 6. Output Contract

```json
{
  "release_status": {
    "agent": "customer-support",
    "version": "1.1.0",
    "current_stage": "3 — 10% grayscale",
    "stage_started_at": "2026-07-02T10:00:00Z",
    "metrics": {
      "human_review_pass_rate": 0.94,
      "complaint_rate": 0.02,
      "error_rate": 0.01,
      "escalation_accuracy": 0.97
    },
    "rollback_triggers_hit": 0,
    "next_stage_eligible": true,
    "next_stage": "4 — 50% grayscale"
  }
}
```

## 7. Risk Boundaries

- **Never skip stages**: Each stage must complete its duration and exit criteria
- **Never advance with active alerts**: All monitoring metrics must be green
- **P1/P2 always human review**: Even at full production, P1/P2 cases require human approval
- **Rollback is always available**: Any stage can be rolled back to previous

## 8. Examples

### Example 1: Successful 10% Grayscale
**Stage**: 3 — 10% grayscale
**Duration**: 3 days complete
**Metrics**: HR pass rate 94% (baseline 92%), complaint rate 2% (baseline 3%), 0 critical errors
**Decision**: ✅ Advance to Stage 4 — 50% grayscale

### Example 2: Rollback at 50%
**Stage**: 4 — 50% grayscale
**Day**: 2 of 5
**Event**: Human review pass rate dropped from 92% to 78% (>10% drop)
**Decision**: ❌ Automatic rollback to Stage 3. Investigate root cause.

### Example 3: Critical Error Rollback
**Stage**: 3 — 10% grayscale
**Event**: Agent gave medical advice on a P1 case ("this will heal your skin")
**Decision**: ❌ Immediate rollback to Stage 0. Incident review required. Add golden set case.

## 9. Evaluation Cases

Grayscale release is validated by:
- Golden Set must pass before Stage 0 exit
- Shadow mode must show 0 critical errors before Stage 1 exit
- Each stage's metrics are compared against baseline

## 10. Failure Modes

| Failure | Cause | Fix |
|---------|-------|-----|
| Stuck at stage | Metrics never reach threshold | Investigate agent quality, may need skill update |
| Rollback loop | Update keeps failing at same stage | Root cause analysis, may need architecture change |
| Metrics not collected | Monitoring not set up | Configure metrics pipeline before starting grayscale |
| Feature flag not working | Traffic not actually split | Verify flag configuration, test with synthetic traffic |
| Stage duration too short | Issues appear after advancement | Respect minimum durations, don't rush |
