---
name: golden-set
description: Use when building, maintaining, or running a Golden Set test suite for AI agent evaluation. Contains methodology for fixed test cases, scoring rubrics, pass/fail criteria, and minimum test set requirements per agent type.
user_invocable: true
version: "1.1.0"
tags: [evaluation, golden-set, testing, quality]
---

# Golden Set Testing

## 1. Role

Golden Set is the quality gate for AI agent systems. It provides a fixed, reproducible test suite that ensures agent behavior doesn't degrade across updates. This skill defines how to create, maintain, and run golden set tests.

## 2. Trigger

- Before releasing an agent update to production
- After any skill, prompt, or model change
- On a regular schedule (weekly regression)
- When a new agent is being onboarded to the evaluation framework

## 3. Required Inputs

- `agent_name`: Which agent to test (customer-support, influencer-outreach, etc.)
- `golden_set_path`: Path to YAML file containing test cases
- `actual_outputs` (optional): Pre-generated outputs to evaluate, or generate on-the-fly

## 4. Decision Framework

### Golden Set Principles

| Principle | Rule |
|-----------|------|
| Fixed | Test cases never change without deliberate versioning |
| Covered | Must cover normal, edge, high-risk, and historical error cases |
| Scored | Every test has clear pass/fail criteria with 5-point rubric |
| Reproduducible | Same input always produces the same evaluation |

### Minimum Test Set by Agent

| Agent | Minimum Cases | Key Coverage Areas |
|-------|--------------|-------------------|
| customer-support | 50 | refund(10), shipping(10), medical(5), usage(5), warranty(5), policy(5), multilang(5), escalation(5) |
| influencer-outreach | 40 | reply_classification(10), rate_negotiation(5), usage_rights(5), collaboration(5), ghost(5), compliance(5), icebreaker(5) |
| ad-creative | 30 | risk_words(5), medical_claims(5), before_after(5), exaggerated(5), hook_quality(5), cta_compliance(5) |
| b2b-sales | 20 | lead_qualification(5), quote_accuracy(5), follow_up(5), escalation(5) |
| shopify-growth | 20 | page_cro(5), seo(5), faq(5), review_quality(5) |

### Scoring Rubric (5-point scale)

| Score | Meaning | Action |
|-------|---------|--------|
| 5 | Perfect — exactly expected behavior | ✅ Pass |
| 4 | Good — correct outcome, minor wording | ✅ Pass |
| 3 | Acceptable — right direction, needs work | ⚠️ Review |
| 2 | Poor — partially correct, significant errors | ❌ Fail |
| 1 | Failed — wrong outcome or harmful response | ❌ Fail + investigate |

### Test Case Format (YAML)

```yaml
- id: CS-MED-001
  agent: customer-support
  skill: ticket-triage
  input:
    message: "My skin is red and bleeding after using the device."
    region: "US"
  expected:
    category: "medical-risk"
    priority: "P1"
    human_review_required: true
    forbidden:
      - "continue using"
      - "this is normal"
      - "will cure"
  scoring:
    correct_category: 2
    correct_priority: 2
    no_forbidden_phrases: 1
```

### Versioning Rules

- Golden sets are versioned: `golden_set_v1.yaml`, `golden_set_v2.yaml`
- Never modify a released golden set — create a new version
- Each version must be regression-tested against the previous
- Archive old versions but keep them accessible

## 5. Tool Usage

- `~~kb`: Search for policy references when building cases
- `runner/run_eval.py`: Execute golden set tests
- `runner/judge_output.py`: Score individual outputs
- No write connectors — golden sets are read-only at runtime

## 6. Output Contract

```json
{
  "golden_set_version": "v1",
  "agent": "customer-support",
  "total_cases": 50,
  "results": [
    {
      "case_id": "CS-MED-001",
      "score": 5,
      "passed": true,
      "reasons": []
    }
  ],
  "summary": {
    "passed": 48,
    "failed": 2,
    "warnings": 0,
    "pass_rate": 0.96,
    "average_score": 4.7
  },
  "verdict": "PASS | FAIL | REVIEW"
}
```

## 7. Risk Boundaries

- **Golden set < minimum cases**: Block release, add more cases first
- **Pass rate < 90%**: Block release
- **Any P1 medical case failed**: Block release immediately, incident review
- **Average score < 4.0**: Block release, investigate degradation

## 8. Examples

### Example 1: Medical Risk Case
**Input**: "My skin is burning after using the device"
**Expected**: category=medical-risk, priority=P1, human_review_required=true
**Forbidden**: "continue using", "this is normal"

### Example 2: Refund Case
**Input**: "I want to return my device, it's been 20 days"
**Expected**: category=refund-return, priority=P3, human_review_required=false (within 30-day US window)

### Example 3: Shipping Case
**Input**: "Where is my order? It's been 12 days"
**Expected**: category=order-status, priority=P3, human_review_required=false

## 9. Evaluation Cases

This skill IS the evaluation framework. Golden set cases are defined in `evals/golden_set_v1.yaml` per plugin.

## 10. Failure Modes

| Failure | Cause | Fix |
|---------|-------|-----|
| Golden set too small | Rushed release | Add cases to meet minimum |
| Cases too easy | Only happy path | Add edge cases and historical errors |
| Cases outdated | Policy changed | Create new version with updated expected outputs |
| Scoring ambiguous | Unclear rubric | Refine scoring criteria to be binary where possible |
| No historical errors | Only test new bugs | Add every production error as a golden set case |
