---
name: regression-test
description: Use when running regression tests after updating an AI agent's skills, prompts, knowledge base, or model. Ensures new changes don't break previously correct behavior.
user_invocable: true
version: "1.0.0"
tags: [evaluation, regression, testing]
---

# Regression Testing

## When to Run

| Trigger | Scope |
|---------|-------|
| Skill update | Full Golden Set for that agent |
| Prompt change | Full Golden Set + tone evaluation |
| Model change | Full Golden Set + boundary cases |
| Knowledge base update | Policy-specific test cases |
| New automation added | Escalation bypass tests |

## Process

### 1. Baseline → 2. Update → 3. Re-run → 4. Compare

| Result | Action |
|--------|--------|
| Same or better | ✅ Safe to proceed |
| Minor degradation (1-2 cases) | ⚠️ Review case-by-case |
| Significant degradation (3+ cases) | ❌ Roll back, fix, re-test |

## Common Regression Risks

| Change | Risk |
|--------|------|
| Updated policy | Old policy misapplied |
| Changed prompt | Tone becomes cold/rigid |
| Swapped model | Compliance boundaries soften |
| New tool | Incorrect API calls |
| Added automation | Human review bypassed |
