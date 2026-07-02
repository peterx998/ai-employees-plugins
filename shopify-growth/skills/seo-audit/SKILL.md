---
name: seo-audit
description: Use when auditing SEO for a Shopify product or collection page. Checks title tags, meta descriptions, H1-H3 structure, image alt text, URL slugs, and schema markup.
user_invocable: true
version: "1.0.0"
tags: [shopify, cro, e-commerce]
---

# Seo Audit

## Usage
```
/seo-audit <page URL or context>
```

## Workflow
1. **Collect**: Gather data from ~~store, ~~analytics, ~~seo, ~~session
2. **Analyze**: Run the analysis checklist
3. **Report**: Output structured findings

## Output Format
```
## Seo Audit Report

### Summary
[2-3 sentence assessment]

### Findings
| Area | Status | Detail | Priority |
|------|--------|--------|----------|

### Recommendations
1. [Actionable recommendation]
```
