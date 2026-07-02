---
name: eval:golden-set
description: Run the Golden Set evaluation suite against an agent and generate a scorecard
argument-hint: "<agent_name> [--golden_set <path>] [--version <tag>]"
required_connectors: []
risk_level: low
human_review: optional
output_schema: "schemas/evaluation/eval_result.schema.json"
---

## Inputs

| Field | Required | Description |
|-------|----------|-------------|
| agent_name | Yes | Agent to evaluate (e.g., customer-support) |
| golden_set | No | Path to golden set YAML (default: agent's evals/golden_set_v1.yaml) |
| version | No | Version tag for comparison (default: current) |

## Steps

1. Load golden set YAML for the specified agent
2. For each test case:
   a. Send the input to the agent
   b. Capture the agent's output
   c. Compare against expected output:
      - Category match (2 points)
      - Priority match (2 points)
      - No forbidden phrases (1 point)
      - Human review flag correctness (1 point)
   d. Score: 6 = full pass, 4-5 = partial pass, <4 = fail
3. Aggregate results:
   - Total cases, passed, failed, pass rate
   - Score breakdown by category
   - Failed case details
4. Generate verdict: PASS (≥90%), WARN (75-89%), FAIL (<75%)

## Output

```json
{
  "agent": "customer-support",
  "version": "v1.1.0",
  "total_cases": 50,
  "passed": 45,
  "partial": 3,
  "failed": 2,
  "pass_rate": 0.90,
  "score_breakdown": {
    "refund-return": {"total": 10, "passed": 10},
    "shipping-logistics": {"total": 10, "passed": 9},
    "medical-risk": {"total": 5, "passed": 5},
    "escalation": {"total": 5, "passed": 4}
  },
  "failed_cases": [
    {"case_id": "CS-ESC-003", "reason": "missed legal threat keyword", "expected": "P1 escalation", "actual": "P3 policy-question"}
  ],
  "verdict": "PASS"
}
```

## Risk Boundaries

- Golden set results are for internal quality assurance. Do not expose to customers.
- A FAIL verdict blocks production deployment.

## Failure Modes

| Failure | Cause | Fix |
|---------|-------|-----|
| Agent timeout | Agent took too long | Set 30s timeout per case, mark as fail |
| Golden set malformed | YAML syntax error | Validate YAML before running |
''',
