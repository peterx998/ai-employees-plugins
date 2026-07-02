---
name: eval:error-review
description: Review and classify errors from failed golden set cases into 7-type taxonomy
argument-hint: "<failed_cases> [--agent <name>]"
required_connectors: []
risk_level: low
human_review: recommended
---

## Inputs

| Field | Required | Description |
|-------|----------|-------------|
| failed_cases | Yes | List of failed case IDs from eval:golden-set or eval:regression-test |
| agent | No | Agent name for context |

## Steps

1. Load failed case details (input, expected, actual)
2. For each failed case, classify error type:
   - `knowledge_gap` — Agent lacked information (no KB article)
   - `process_undefined` — Agent didn't know next step (no SOP)
   - `prompt_unclear` — Instructions ambiguous (rules unclear)
   - `tool_failure` — API/MCP/connector error
   - `model_hallucination` — Agent fabricated information
   - `boundary_unclear` — Agent didn't escalate when it should have
   - `review_criteria_missing` — Human reviewer didn't know how to verify
3. Determine root cause for each error (dig beyond symptom)
4. Recommend fix:
   - knowledge_gap → add KB article
   - process_undefined → add SOP step
   - prompt_unclear → revise instruction
   - tool_failure → fix connector
   - model_hallucination → add anti-hallucination rule
   - boundary_unclear → add escalation trigger
   - review_criteria_missing → add verification checklist
5. Suggest new golden set cases from the error pattern

## Output

```json
{
  "total_errors_reviewed": 5,
  "classification": {
    "knowledge_gap": 2,
    "boundary_unclear": 1,
    "prompt_unclear": 1,
    "model_hallucination": 1
  },
  "cases": [
    {
      "case_id": "CS-ESC-003",
      "error_type": "boundary_unclear",
      "root_cause": "Agent didn't recognize 'I'll take this to small claims' as legal threat",
      "recommended_fix": "Add 'small claims', 'court', 'sue' to escalation trigger keywords in skills/escalation-rules/SKILL.md",
      "new_golden_set_case_suggested": "CS-ESC-006: message containing 'small claims court'"
    }
  ],
  "human_review_recommended": true
}
```

## Risk Boundaries

- Error review is for improvement, not blame. Frame as system learning.
- All recommended fixes must be verified by human before applying.

## Failure Modes

| Failure | Cause | Fix |
|---------|-------|-----|
| Error misclassified | Insufficient context | Include full agent output in analysis |
| Fix too vague | Root cause analysis too shallow | Require specific file/line reference in fix recommendation |
