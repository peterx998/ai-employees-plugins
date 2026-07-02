---
name: review-import-check
description: Use when checking imported reviews for quality, authenticity, and compliance. Flags fake reviews, reviews with medical claims, and reviews needing responses.
user_invocable: true
version: "1.0.0"
tags: [shopify, cro, e-commerce]
---

# Review Import Check

## Usage
```
/review-import-check <page URL or context>
```

## Workflow
1. **Collect**: Gather data from ~~store, ~~analytics, ~~seo, ~~session
2. **Analyze**: Run the analysis checklist
3. **Report**: Output structured findings

## Output Format
```
## Review Import Check Report

### Summary
[2-3 sentence assessment]

### Findings
| Area | Status | Detail | Priority |
|------|--------|--------|----------|

### Recommendations
1. [Actionable recommendation]
```
