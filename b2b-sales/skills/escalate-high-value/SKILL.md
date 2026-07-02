---
name: escalate-high-value
description: Use when a B2B inquiry meets high-value criteria and needs human sales team attention. Packages the lead with full context and opportunity sizing.
user_invocable: true
version: "1.0.0"
tags: [b2b-sales, lead-qualification]
---

# Escalate High Value

## Usage
```
/escalate-high-value <inquiry context or lead info>
```

## Workflow
1. **Parse**: Extract key information from the inquiry
2. **Evaluate**: Apply the qualification/assessment framework
3. **Act**: Determine recommended action and produce structured output

## Output Format
```
## Escalate High Value

### Recommendation
[Clear action recommendation with reasoning]

### Next Steps
1. [Step 1]
2. [Step 2]
```
