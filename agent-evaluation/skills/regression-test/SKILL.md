---
name: regression-test
description: Use when running regression tests after updating an AI agent's skills, prompts, knowledge base, or model. Ensures new changes do not break previously correct behavior by running the Golden Set and comparing results.
user_invocable: true
version: "1.1.0"
tags: [evaluation, regression, testing, quality]
---

# Regression Testing

## 1. Role

Regression testing is the safety net that prevents agent updates from breaking working behavior. It runs the Golden Set before and after a change, then compares results to detect degradation.

## 2. Trigger

- After any skill update (SKILL.md modification)
- After prompt changes
- After model swap or provider change
- After knowledge base update
- After tool/API connection change
- After new automation added
- On every PR via CI

## 3. Required Inputs

- `agent_name`: Which agent was updated
- `change_description`: What was changed (for the report)
- `baseline_results` (optional): Previous golden set results to compare against

## 4. Decision Framework

### When to Run Regression Tests

| Trigger | Scope | Blocking? |
|---------|-------|-----------|
| Skill update | Full Golden Set for that agent | ✅ Yes |
| Prompt change | Full Golden Set + tone evaluation | ✅ Yes |
| Model change | Full Golden Set + boundary cases | ✅ Yes |
| Knowledge base update | Policy-specific test cases | ✅ Yes |
| Tool/API change | Integration test cases | ✅ Yes |
| New automation added | Escalation bypass tests | ✅ Yes |
| Cosmetic doc fix | None | ❌ No |

### Regression Process

```text
1. Baseline: Run current Golden Set, record scores
2. Update: Apply the change (skill edit, prompt change, model swap)
3. Re-run: Run same Golden Set against updated agent
4. Compare: Compare baseline vs. new results
5. Decide: Pass, Review, or Block
``### Comparison Thresholds

| Result | Criteria | Action |
|--------|----------|--------|
| Same or better | All case scores ≥ baseline | ✅ Safe to proceed |
| Minor degradation | 1-2 cases dropped by 1 point | ⚠️ Review affected cases individually |
| Significant degradation | 3+ cases dropped OR any case dropped by 2+ points | ❌ Roll back, fix root cause, re-test |
| New failure pattern | Category of cases failing that passed before | ❌ Block release, investigate |
| P1 case failure | Any medical-risk case fails | ❌ Block immediately, incident review |

### Common Regression Risks

| Change | Risk | Mitigation |
|--------|------|------------|
| Updated policy → old policy misapplied | Old policy cases fail | Test old + new policy cases |
| Changed prompt → tone becomes cold/rigid | Tone evaluation cases fail | Include tone-checking cases |
| Swapped model → compliance boundaries soften | Medical compliance cases fail | Run all high-risk medical cases |
| New tool → incorrect API calls | Integration cases fail | Test tool calling paths |
| Added automation → human review bypassed | Escalation cases fail | Test all escalation trigger paths |

## 5. Tool Usage

- `runner/run_eval.py --agent <name> --compare baseline.json`: Run with comparison
- `runner/judge_output.py`: Score individual outputs
- CI pipeline (`.github/workflows/eval.yml`): Automated on PR

## 6. Output Contract

```json
{
  "regression_report": {
    "agent": "customer-support",
    "version_old": "1.0.0",
    "version_new": "1.1.0",
    "change_description": "Updated refund policy skill for EU region",
    "total_cases": 50,
    "results": {
      "passed": 48,
      "degraded": 1,
      "failed": 1,
      "new_passes": 0
    },
    "verdict": "REVIEW",
    "degraded_cases": [
      {
        "id": "CS-REF-003",
        "category": "refund-return",
        "old_score": 5,
        "new_score": 4,
        "delta": -1,
        "issue": "Slight tone change in EU refund response"
      }
    ],
    "new_failures": [
      {
        "id": "CS-POL-002",
        "category": "policy-boundary",
        "issue": "EU 14-day policy not applied correctly",
        "root_cause": "Policy update missed EU cooling-off period"
      }
    ]
  }
}
```

## 7. Risk Boundaries

- **Any P1 medical case fails**: Block release immediately, trigger incident review
- **3+ cases degrade**: Block release, investigate root cause
- **Escalation bypass detected**: Block release, fix escalation logic before re-test
- **Pass rate drops below 90%**: Block release

## 8. Examples

### Example 1: Skill Update Regression
**Change**: Updated `refund-policy` SKILL.md to add EU 14-day cooling-off period
**Baseline**: 50/50 passed
**After update**: 48/50 passed, 1 degraded (EU refund tone), 1 failed (EU policy edge case)
**Verdict**: REVIEW — investigate the failed EU case, fix, re-test

### Example 2: Model Swap Regression
**Change**: Switched from Model A to Model B
**Baseline**: 50/50 passed, avg score 4.8
**After swap**: 46/50 passed, 2 medical cases failed (compliance boundaries softened)
**Verdict**: FAIL — block release, add stronger compliance instructions or revert model

### Example 3: Clean Regression
**Change**: Fixed typo in shipping-policy SKILL.md
**Baseline**: 50/50 passed
**After fix**: 50/50 passed, no degradation
**Verdict**: PASS — safe to release

## 9. Evaluation Cases

Regression tests use the same golden set cases defined in `evals/golden_set_v1.yaml`. The difference is the comparison against a baseline.

## 10. Failure Modes

| Failure | Cause | Fix |
|---------|-------|-----|
| No baseline recorded | First run or baseline lost | Always save baseline results in `reports/` |
| Flaky tests | Non-deterministic model output | Run 3 times, use majority vote |
| Cases too strict | Expected output is overly specific | Loosen expected to category+priority level |
| Missing new edge case | New error type discovered in production | Add as golden set case immediately |
| CI not running | Workflow misconfigured | Verify `.github/workflows/eval.yml` triggers on PR |
