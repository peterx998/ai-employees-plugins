---
name: qualify-lead
description: Use when a new B2B inquiry comes in and needs lead qualification. Determines whether the inquirer is retail, clinic, distributor, or procurement, scores lead quality, and routes to the appropriate pipeline.
user_invocable: true
version: "1.0.0"
tags: [b2b-sales, lead-qualification]
---

# Qualify Lead

## Usage
```
/qualify-lead <inquiry context or lead info>
```

## Workflow
1. **Parse**: Extract key information from the inquiry
2. **Evaluate**: Apply the qualification/assessment framework
3. **Act**: Determine recommended action and produce structured output

## Output Format
```
## Qualify Lead

### Recommendation
[Clear action recommendation with reasoning]

### Next Steps
1. [Step 1]
2. [Step 2]
```
