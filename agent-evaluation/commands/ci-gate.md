---
name: eval:ci-gate
description: CI gate check — run golden set and block merge if quality threshold not met
argument-hint: "[--agent <name>] [--blocking_threshold 0.90]"
required_connectors: []
risk_level: high
human_review: always
---

## Inputs

| Field | Required | Description |
|-------|----------|-------------|
| agent | No | Agent to check (default: all agents with golden sets) |
| blocking_threshold | No | Minimum pass rate to allow merge (default: 0.90) |

## Steps

1. Detect which agents have golden sets (scan */evals/golden_set_v1.yaml)
2. For each agent:
   a. Run eval:golden-set
   b. Check pass rate against blocking_threshold
   c. If below threshold → set CI gate to FAIL
3. Run regression test if previous version results exist
4. Check for degraded cases (any case that passed before but fails now)
5. Generate CI gate decision:
   - PASS: All agents ≥ threshold, no regressions
   - FAIL: Any agent < threshold OR any degraded case
6. Output machine-readable gate decision for CI pipeline

## Output

```json
{
  "ci_gate": "FAIL",
  "agents_checked": ["customer-support"],
  "results": [
    {
      "agent": "customer-support",
      "pass_rate": 0.88,
      "threshold": 0.90,
      "regression": true,
      "degraded_cases": 2,
      "verdict": "FAIL"
    }
  ],
  "block_reason": "customer-support pass rate 88% below threshold 90%. 2 degraded cases detected.",
  "action_required": "Fix degraded cases CS-REF-007 and CS-ESC-003 before merge.",
  "human_review_required": true
}
```

## Risk Boundaries

- CI gate is mandatory. No bypass without human approval from tech lead.
- Degraded cases always block merge, regardless of overall pass rate.

## Failure Modes

| Failure | Cause | Fix |
|---------|-------|-----|
| Gate bypassed | CI workflow misconfigured | Ensure eval.yml runs on all PRs to main/master |
| False fail | Non-deterministic agent output | Run each case 3 times with majority vote |
