---
name: eval:regression-test
description: Compare agent performance between two versions to detect regressions
argument-hint: "<agent_name> --old <version> --new <version>"
required_connectors: []
risk_level: low
human_review: recommended
output_schema: "schemas/evaluation/regression_report.schema.json"
---

## Inputs

| Field | Required | Description |
|-------|----------|-------------|
| agent_name | Yes | Agent to test |
| old_version | Yes | Previous stable version tag |
| new_version | Yes | New version tag to compare |
| golden_set | No | Path to golden set (default: agent's standard) |

## Steps

1. Run eval:golden-set against old_version, save results as baseline
2. Run eval:golden-set against new_version, save results as candidate
3. Compare case-by-case:
   - Cases that passed before but fail now → degraded
   - Cases that failed before but pass now → improved
   - Cases that failed before and still fail → persistent
   - New failures not in old run → new_failures
4. Generate regression report:
   - Overall: IMPROVED / NO_CHANGE / DEGRADED
   - If any case degraded → verdict = BLOCK_MERGE

## Output

```json
{
  "agent": "customer-support",
  "version_old": "v1.0.0",
  "version_new": "v1.1.0",
  "total_cases": 50,
  "passed_old": 44,
  "passed_new": 45,
  "degraded": 1,
  "improved": 2,
  "new_failures": 0,
  "verdict": "WARN",
  "degraded_cases": [
    {"case_id": "CS-REF-007", "old_result": "pass", "new_result": "fail", "reason": "category changed from refund-return to policy-question"}
  ]
}
```

## Risk Boundaries

- Any degraded case should block merge in CI.
- Human review recommended to investigate degraded cases before re-running.

## Failure Modes

| Failure | Cause | Fix |
|---------|-------|-----|
| Old version unavailable | Version not cached | Re-run old version evaluation first |
| Inconsistent results | Non-deterministic agent output | Run each case 3 times, use majority vote |
