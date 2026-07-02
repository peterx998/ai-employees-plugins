---
name: error-review
description: Use when reviewing agent errors, misclassifications, or failures to identify root causes and generate actionable improvements. Categorizes errors into 7 types with corresponding fixes, and feeds each error back into the Golden Set.
user_invocable: true
version: "1.1.0"
tags: [evaluation, error-review, root-cause, improvement]
---

# Error Review & Root Cause Analysis

## 1. Role

Error review turns every agent mistake into a systemic improvement. It classifies the error, finds the root cause, proposes a fix, and adds the error as a Golden Set case to prevent regression.

## 2. Trigger

- When an agent produces an incorrect, harmful, or suboptimal response
- When a human reviewer rejects an agent output
- When a customer complaint is traced to agent behavior
- When a P1/P2 escalation was missed or mishandled
- During post-release regression review

## 3. Required Inputs

- `error_context`: What happened (input, agent output, expected output)
- `agent_name`: Which agent made the error
- `severity`: Critical / High / Medium / Low
- `customer_impact` (if any): What the customer experienced

## 4. Decision Framework

### Error Classification (7 types)

| Error Type | Description | Fix Pattern |
|------------|-------------|-------------|
| **Knowledge Gap** | Missing policy, data, or information in KB | Add to knowledge base + update SKILL.md |
| **Process Undefined** | Agent doesn't know next step | Add SOP step to SKILL.md |
| **Prompt Unclear** | Rule expression is vague/ambiguous | Refine prompt/instruction in SKILL.md |
| **Tool Failure** | API, MCP, or permission error | Fix tool chain, add error handling |
| **Model Hallucination** | Made up non-existent information | Add citation rule + prohibition in SKILL.md |
| **Boundary Unclear** | Didn't know when to escalate to human | Add escalation trigger to SKILL.md |
| **Review Criteria Missing** | Human reviewer unclear on acceptance | Add review checklist to command contract |

### Root Cause Process

```text
1. WHAT happened: Describe the observable error
2. WHY did it happen: Dig into the root cause (not just symptoms)
3. WHERE did the system fail: Which layer (knowledge, process, tool, model)
4. HOW to fix: Specific, actionable fix mapped to error type
5. WHAT to prevent: Add Golden Set case to catch this in future
```

### Severity Classification

| Severity | Criteria | Response Time |
|----------|----------|---------------|
| Critical | Medical advice given, legal exposure, P1 missed | Immediate — incident review |
| High | Wrong escalation, refund error, compliance violation | Same day |
| Medium | Wrong category, poor tone, missing info | Within 3 days |
| Low | Minor wording, non-ideal response | Weekly batch review |

## 5. Tool Usage

- `~~kb`: Check if knowledge gap exists
- `runner/judge_output.py`: Score the error output
- `evals/golden_set_v1.yaml`: Add new case from this error

## 6. Output Contract

```json
{
  "error_review": {
    "error_id": "ERR-2026-001",
    "agent": "customer-support",
    "date": "2026-07-02",
    "severity": "Critical",
    "what_happened": "Agent told customer 'this will heal your skin' — medical claim",
    "input": "Customer asked if device helps with acne scars",
    "agent_output": "Yes, this device will heal your acne scars over time.",
    "expected_output": "Our device is designed for at-home micro-infusion. For specific skin concerns like acne scars, we recommend consulting a dermatologist. We cannot make medical claims about specific conditions.",
    "classification": {
      "type": "Prompt Unclear",
      "root_cause": "SKILL.md medical compliance boundary doesn't explicitly list 'heal' as a forbidden word"
    },
    "fix": {
      "immediate": "Add 'heal' to forbidden phrases in draft-response SKILL.md",
      "systemic": "Add global medical-compliance policy with comprehensive forbidden word list",
      "golden_set_case": {
        "id": "CS-MED-006",
        "input": "Will this heal my acne scars?",
        "expected": {
          "category": "product-usage",
          "priority": "P3",
          "forbidden": ["heal", "cure", "treat", "fix"]
        }
      }
    }
  }
}
```

## 7. Risk Boundaries

- **Critical errors**: Must trigger incident review within 1 hour
- **Pattern detection**: If same error type occurs 3+ times, escalate to architecture review
- **Golden set gap**: Every error MUST result in a new golden set case — no exceptions
- **Fix verification**: Fix must pass regression test before closing error review

## 8. Examples

### Example 1: Medical Claim (Critical)
**Error**: Agent said "this will heal your acne scars"
**Classification**: Prompt Unclear — forbidden word list incomplete
**Fix**: Add "heal" to forbidden phrases + new golden set case CS-MED-006
**Severity**: Critical (medical claim made)

### Example 2: Missed Escalation (High)
**Error**: Agent auto-replied to a legal threat instead of escalating
**Classification**: Boundary Unclear — escalation trigger not sensitive enough
**Fix**: Add "sue", "lawyer", "attorney" as explicit escalation trigger words
**Severity**: High (legal exposure)

### Example 3: Wrong Refund Policy (Medium)
**Error**: Agent applied US 30-day policy to an EU customer (should be 14-day cooling-off)
**Classification**: Knowledge Gap — EU policy not in KB
**Fix**: Add EU refund policy to KB + update refund-policy SKILL.md with region detection
**Severity**: Medium (customer inconvenience, not safety)

## 9. Evaluation Cases

Every error review produces a new Golden Set case. The error's input becomes the test input, the correct behavior becomes the expected output, and the error's forbidden list prevents regression.

## 10. Failure Modes

| Failure | Cause | Fix |
|---------|-------|-----|
| Same error repeats | Fix didn't address root cause | Re-do root cause analysis, go deeper |
| Error not caught in GS | Case not added or too specific | Ensure every error review creates a GS case |
| Fix causes new errors | Fix was too broad | Run full regression after fix |
| Pattern not detected | Errors reviewed in isolation | Review error trends weekly, look for patterns |
| Critical error not escalated | Severity misclassified | When in doubt, classify higher |
