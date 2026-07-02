# Microsoft Clarity Connector Contract

**Version:** 1.0.0  
**Last Updated:** 2026-07-02  
**Owner:** Platform Team  
**Connector Type:** Analytics (Microsoft Clarity API)  

---

## 1. Overview

The Microsoft Clarity connector enables AI agents to retrieve analytics data including session recordings, metrics, and heatmaps. All operations are **read-only** — agents can retrieve and analyze data but cannot modify any Clarity settings or data.

---

## 2. Capabilities

| Capability | Description | Permission Level | Human Approval Required? |
|---|---|---|---|
| `get_session` | Retrieve session recording data by session ID | **Read-Only (RO)** | No |
| `get_metrics` | Retrieve aggregated analytics metrics | **Read-Only (RO)** | No |
| `get_heatmap` | Retrieve heatmap data for a specific page | **Read-Only (RO)** | No |

---

## 3. Permission Levels

### 3.1 Read-Only Operations

All Clarity connector capabilities are **read-only**. There are no write operations available.

```yaml
get_session:
  permission: RO
  description: "Retrieve session recording metadata and playback data by session ID."
  input:
    session_id: string (required)
    fields: array<string> (optional)  # e.g., ["duration", "pages", "clicks", "scroll_depth"]
  output:
    session:
      id: string
      duration: integer          # seconds
      page_count: integer
      pages: array<PageView>
        - url: string
          duration: integer      # seconds on page
          scroll_depth: float    # percentage 0-100
      clicks: integer
      device: string             # desktop, mobile, tablet
      country: string
      browser: string
      started_at: string (ISO 8601)
      ended_at: string (ISO 8601)
  rate_limit: "Dependent on Clarity API plan"
  human_approval: false
  pii_safety: |
    Clarity masks PII in session recordings by default (text masking, 
    image masking). Agents must verify no unmasked PII is present in
    retrieved session data before using it in any output.

get_metrics:
  permission: RO
  description: "Retrieve aggregated analytics metrics for a date range."
  input:
    start_date: string (required)  # ISO 8601 date (e.g., "2026-06-01")
    end_date: string (required)    # ISO 8601 date
    metrics: array<string> (optional)  # e.g., ["total_sessions", "avg_duration", "bounce_rate"]
    filters: object (optional)     # e.g., {"device": "mobile", "country": "US"}
  output:
    metrics:
      total_sessions: integer
      total_pages: integer
      avg_duration: float          # seconds
      avg_pages_per_session: float
      bounce_rate: float           # percentage
      scroll_depth_avg: float      # percentage
      click_count: integer
      device_breakdown: object     # {desktop: int, mobile: int, tablet: int}
      country_breakdown: object    # {US: int, CA: int, ...}
  rate_limit: "Dependent on Clarity API plan"
  human_approval: false

get_heatmap:
  permission: RO
  description: "Retrieve heatmap data for a specific page URL."
  input:
    page_url: string (required)
    date_range:
      start_date: string (required)  # ISO 8601
      end_date: string (required)
    heatmap_type: string (optional)  # "click", "scroll", "rage" (default: "click")
  output:
    heatmap:
      page_url: string
      type: string                # click, scroll, rage
      total_sessions: integer
      data: object                # Heatmap coordinate data
        - x: float
          y: float
          intensity: float        # 0-1
      hotspots: array<Hotspot>
        - x: float
          y: float
          label: string
          intensity: float
  rate_limit: "Dependent on Clarity API plan"
  human_approval: false
```

---

## 4. Required Environment Variables

| Variable | Description | Required? | Example |
|---|---|---|---|
| `CLARITY_PROJECT_ID` | Microsoft Clarity project ID | Yes | `abc123def456` |
| `CLARITY_API_KEY` | Clarity API key for authentication | Yes | `clarity_xxxxxxxxxxxxxxxxxxxx` |

### 4.1 Required API Permissions

The Clarity API key must have the following permissions:

```
Read project data      # get_session, get_metrics, get_heatmap
Read session recordings # get_session playback data
```

The API key must NOT have:
```
Modify project settings  # Prohibited
Delete data              # Prohibited
Export raw data          # Prohibited (admin only)
```

### 4.2 Environment Setup

```bash
# .env or environment configuration
CLARITY_PROJECT_ID=your_project_id
CLARITY_API_KEY=clarity_your_api_key
```

---

## 5. Safety Rules

### 5.1 No PII in Session Data

```
SAFETY RULE: NO PII IN SESSION DATA
- Clarity masks PII in session recordings by default (text masking,
  image masking). Agents must verify no unmasked PII is present in
  retrieved session data before using it in any output.
- If unmasked PII is detected in session data:
  1. Do NOT include the PII in any output or log.
  2. Escalate to compliance team for Clarity masking configuration review.
  3. Log the incident as a privacy violation.
- Session data must not be shared externally or stored in agent state.
- When referencing session data in reports, use aggregated/anonymized
  summaries only.
```

### 5.2 Read-Only — No Modifications

```
SAFETY RULE: READ-ONLY — NO MODIFICATIONS
- All Clarity connector operations are READ-ONLY.
- Agents CANNOT modify project settings, masking rules, or data.
- Agents CANNOT export raw session data — only aggregated metrics
  and summaries may be used in agent outputs.
- Data export is admin-only and not available through this connector.
```

### 5.3 Data Minimization

| Rule | Enforcement |
|---|---|
| Request only needed metrics | Specify `fields` or `metrics` parameters to limit response scope |
| No raw session export | Agents reference sessions by ID in reports; do not export full recordings |
| No user identification | Agents must not attempt to identify individual users from session data |
| Aggregated reporting | Reports use aggregated metrics, not individual session data |

### 5.4 Rate Limit Awareness

| Limit | Value | Handling |
|---|---|---|
| API requests | Dependent on Clarity plan | Check `X-RateLimit-Remaining` header |
| Concurrent requests | 5 per project | Use connection pooling with max 5 connections |
| Date range limit | 90 days per request | Paginate requests for longer ranges |

**Rate Limit Error Handling:**
```python
# Pseudocode for Clarity rate limit handling
def handle_clarity_api_error(response):
    if response.status_code == 429:
        # Rate limited
        retry_after = int(response.headers.get('Retry-After', 60))
        time.sleep(retry_after)
        return retry(response)
    elif response.status_code == 401:
        # API key invalid
        log_error("CLARITY_AUTH_FAILED")
        alert_ops_team()
        return None
```

---

## 6. Data Handling

### 6.1 What Agents May Read

- Session recording metadata (duration, pages, device, country)
- Aggregated metrics (sessions, bounce rate, scroll depth, etc.)
- Heatmap data (click, scroll, rage click hotspots)

### 6.2 What Agents Must NOT Do

- Identify individual users from session data
- Export raw session recordings or playback data
- Include session data with PII in external outputs or reports
- Access Clarity project settings or masking configurations
- Store session data in agent state beyond the active task
- Share session URLs or session IDs in customer-facing communications

---

## 7. Integration with Agent Workflows

### 7.1 Analytics → Insight → Report Workflow

```
1. Agent retrieves metrics for a date range (get_metrics)
2. Agent retrieves heatmap data for specific pages (get_heatmap)
3. Agent may review specific session recordings for context (get_session)
4. Agent generates an analytics report or insight summary:
   - Use aggregated data only
   - No individual user identification
   - No PII in the report
5. Report is saved as a draft (via Notion connector) for human review
6. Human reviewer reviews and publishes the report
```

### 7.2 Use Cases

| Use Case | Capabilities Used | Output |
|---|---|---|
| Weekly analytics summary | `get_metrics` | Aggregated report (draft via Notion) |
| Page optimization recommendation | `get_heatmap`, `get_metrics` | Recommendation document (draft) |
| User behavior analysis | `get_session`, `get_metrics` | Anonymized behavior summary (draft) |
| Customer support context | `get_session` (if customer provides session ID) | Context for support response |

---

## 8. Error Codes

| Error Code | Description | Agent Action |
|---|---|---|
| `CLARITY_AUTH_FAILED` | API key invalid or expired (401) | Log error, alert ops, stop processing |
| `CLARITY_RATE_LIMITED` | Rate limit exceeded (429) | Backoff per Retry-After, retry |
| `CLARITY_PROJECT_NOT_FOUND` | Project ID does not exist or no access (404) | Log, alert ops, stop processing |
| `CLARITY_SESSION_NOT_FOUND` | Session ID does not exist (404) | Log, return "session not found" to agent |
| `CLARITY_NO_DATA` | No data available for the requested range/filters | Log, return empty result to agent |
| `CLARITY_PII_DETECTED` | Unmasked PII detected in session data | Suppress output, escalate to compliance |

---

## 9. References

- Microsoft Clarity API: https://learn.microsoft.com/en-us/clarity/
- Clarity Data Privacy: https://learn.microsoft.com/en-us/clarity/data-privacy
- policies/tool-permissions.md — Permission level definitions
- policies/privacy-and-pii.md — PII handling rules
