---
name: summarize-buyer
description: Use when compiling a buyer profile summary for sales team handoff. Aggregates company info, contact details, inquiry history, lead score, and recommended approach.
user_invocable: true
version: "1.0.0"
tags: [b2b-sales, lead-qualification]
---

# Summarize Buyer

## Usage
```
/summarize-buyer <inquiry context or lead info>
```

## Workflow
1. **Parse**: Extract key information from the inquiry
2. **Evaluate**: Apply the qualification/assessment framework
3. **Act**: Determine recommended action and produce structured output

## Output Format
```
## Summarize Buyer

### Recommendation
[Clear action recommendation with reasoning]

### Next Steps
1. [Step 1]
2. [Step 2]
```
