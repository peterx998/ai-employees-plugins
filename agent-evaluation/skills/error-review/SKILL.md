---
name: error-review
description: Use when reviewing agent errors, misclassifications, or failures to identify root causes and generate actionable improvements. Categorizes errors into 7 types with corresponding fixes.
user_invocable: true
version: "1.0.0"
tags: [evaluation, error-review, root-cause]
---

# Error Review & Root Cause Analysis

## Error Classification

| Error Type | Description | Fix |
|------------|-------------|-----|
| **Knowledge Gap** | Missing policy, data, or information | Add to knowledge base |
| **Process Undefined** | Agent doesn't know next step | Add SOP step |
| **Prompt Unclear** | Rule expression is vague | Refine instruction |
| **Tool Failure** | API, MCP, or permission error | Fix tool chain |
| **Model Hallucination** | Made up non-existent information | Add citation rule |
| **Boundary Unclear** | Didn't know when to escalate | Add escalation trigger |
| **Review Criteria Missing** | Human reviewer unclear on acceptance | Add review checklist |

## Process
1. **Collect**: Gather error sample (input, output, expected, context)
2. **Classify**: Assign error type(s)
3. **Root Cause**: Dig into WHY, not just WHAT
4. **Fix**: Propose specific, actionable fix
5. **Add to Golden Set**: Prevent regression

## Output Format
```
## Error Review: [ID]
**Agent:** [name] | **Severity:** [Critical/High/Medium/Low]

### What Happened / Root Cause / Fix
**Immediate:** [quick fix]
**Systemic:** [process/knowledge change]
**Golden Set Entry:** [test case to add]
```
