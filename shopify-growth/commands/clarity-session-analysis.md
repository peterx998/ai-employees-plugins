---
name: shopify:clarity-session-analysis
description: Analyze Microsoft Clarity session recordings for UX issues and conversion barriers
argument-hint: "<session_id> [--metric rage_clicks|dead_clicks|quick_exits]"
required_connectors: ["~~clarity"]
risk_level: low
human_review: recommended
---

## Inputs

| Field | Required | Description |
|-------|----------|-------------|
| session_id | Yes | Clarity session ID |
| metric_focus | No | Specific metric to analyze (default: all) |

## Steps

1. Fetch session data from ~~clarity (get_session)
2. Fetch page metrics (get_metrics: rage_clicks, dead_clicks, quick_exits, scroll_depth)
3. Identify UX issues:
   - Rage clicks on non-interactive elements
   - Dead clicks (clicking nothing)
   - Quick exits from key pages (product, cart, checkout)
   - Excessive scrolling without engagement
4. Correlate issues with conversion funnel stage
5. Generate improvement recommendations

## Output

```json
{
  "session_id": "...",
  "duration_seconds": 120,
  "pages_visited": 3,
  "issues_found": [
    {"type": "rage_click", "element": "size-chart-link", "page": "/products/a1", "severity": "high"},
    {"type": "dead_click", "element": "review-star-image", "page": "/products/a1", "severity": "medium"},
    {"type": "quick_exit", "page": "/cart", "severity": "high"}
  ],
  "funnel_stage": "cart",
  "recommendations": [
    {"priority": "high", "action": "Fix size chart link — currently non-clickable on mobile"},
    {"priority": "high", "action": "Investigate cart abandonment — check shipping cost display"}
  ],
  "human_review_recommended": true
}
```

## Risk Boundaries

- Clarity data may contain PII (cursor patterns, IP). Do not log raw session data.
- Focus on aggregate patterns, not individual user identification.

## Failure Modes

| Failure | Cause | Fix |
|---------|-------|-----|
| Session not found | Session expired or ID invalid | Return "not found" and suggest recent session list |
| No issues detected | Session too short | Set minimum session duration of 30s |
