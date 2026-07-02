---
name: follow-up-inquiry
description: Use when scheduling and drafting follow-up messages for B2B inquiries. Manages the B2B follow-up cadence (3/7/14 day) with professional tone.
user_invocable: true
version: "1.0.0"
tags: [b2b-sales, lead-qualification]
---

# Follow Up Inquiry

## Usage
```
/follow-up-inquiry <inquiry context or lead info>
```

## Workflow
1. **Parse**: Extract key information from the inquiry
2. **Evaluate**: Apply the qualification/assessment framework
3. **Act**: Determine recommended action and produce structured output

## Output Format
```
## Follow Up Inquiry

### Recommendation
[Clear action recommendation with reasoning]

### Next Steps
1. [Step 1]
2. [Step 2]
```
