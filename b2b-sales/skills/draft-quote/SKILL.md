---
name: draft-quote
description: Use when drafting a B2B quote or pricing proposal for wholesale/distribution. Applies tiered pricing rules, MOQ requirements, shipping estimates, and certification notes.
user_invocable: true
version: "1.0.0"
tags: [b2b-sales, lead-qualification]
---

# Draft Quote

## Usage
```
/draft-quote <inquiry context or lead info>
```

## Workflow
1. **Parse**: Extract key information from the inquiry
2. **Evaluate**: Apply the qualification/assessment framework
3. **Act**: Determine recommended action and produce structured output

## Output Format
```
## Draft Quote

### Recommendation
[Clear action recommendation with reasoning]

### Next Steps
1. [Step 1]
2. [Step 2]
```
