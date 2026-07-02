# Notion KB Connector Contract

**Version:** 1.0.0  
**Last Updated:** 2026-07-02  
**Owner:** Platform Team  
**Connector Type:** Knowledge Base (Notion API)  

---

## 1. Overview

The Notion connector enables AI agents to search and read the internal knowledge base, and to create or update KB articles as drafts (for human review before publishing). It integrates with the Notion API using an integration API key.

---

## 2. Capabilities

| Capability | Description | Permission Level | Human Approval Required? |
|---|---|---|---|
| `search_kb` | Search the KB database for articles by keyword/query | **Read-Only (RO)** | No |
| `read_page` | Read a specific KB article by page ID | **Read-Only (RO)** | No |
| `create_page` | Create a new KB article as a draft | **Write-Draft (WD)** | No (draft only) |
| `update_page` | Update an existing draft KB article | **Write-Draft (WD)** | No (draft only) |
| `delete_page` | Delete a KB article | **PROHIBITED** | **Never — not available** |

---

## 3. Permission Levels

### 3.1 Read-Only Operations

```yaml
search_kb:
  permission: RO
  description: "Search the Notion KB database for articles matching a query."
  input:
    query: string (required)     # Search query (e.g., "refund policy")
    filter: object (optional)    # Notion filter object (e.g., by tag, category)
    max_results: integer (optional, default: 10, max: 50)
  output:
    results: array<PageSummary>
      - id: string
        title: string
        url: string
        last_edited_time: string (ISO 8601)
        tags: array<string>
  rate_limit: "3 requests per second (Notion rate limit)"
  human_approval: false

read_page:
  permission: RO
  description: "Read the full content of a KB article by page ID."
  input:
    page_id: string (required)
  output:
    page:
      id: string
      title: string
      blocks: array<Block>       # Notion block objects (paragraphs, headings, lists, etc.)
      properties: object          # Page properties (tags, category, status)
      last_edited_time: string (ISO 8601)
      url: string
  rate_limit: "3 requests per second (Notion rate limit)"
  human_approval: false
```

### 3.2 Write-Draft Operations

```yaml
create_page:
  permission: WD
  description: "Create a new KB article as a DRAFT. Drafts are NOT published to the live KB."
  input:
    parent_database_id: string (required)   # Defaults to NOTION_KB_DATABASE_ID
    title: string (required)
    blocks: array<Block> (required)          # Content blocks
    properties: object (optional)            # Tags, category, etc.
    status: string (default: "draft")        # Always "draft" — agents cannot set "published"
  output:
    page_id: string
    url: string
    status: string  # Always "draft"
  rate_limit: "3 requests per second (Notion rate limit)"
  human_approval: false  # Draft is NOT published — human reviews before publishing
  notes: |
    - All created pages have status "draft" — agents CANNOT set status to "published".
    - Drafts appear in the human review queue for KB moderation.
    - Human reviewer can edit, approve (publish), or reject drafts.
    - Agents must NOT attempt to publish pages directly.

update_page:
  permission: WD
  description: "Update an existing DRAFT KB article. Cannot update published articles."
  input:
    page_id: string (required)
    blocks: array<Block> (optional)          # Updated content blocks
    properties: object (optional)            # Updated properties
  output:
    page_id: string
    updated_at: string (ISO 8601)
    status: string  # Always remains "draft"
  rate_limit: "3 requests per second (Notion rate limit)"
  human_approval: false
  notes: |
    - Agents may only update pages with status "draft".
    - Updating a "published" page is PROHIBITED — requires human admin action.
    - Agents must NOT change page status from "draft" to "published".
```

### 3.3 Prohibited Operations

```yaml
delete_page:
  permission: PROHIBITED
  description: "Delete a KB article. THIS OPERATION IS NOT AVAILABLE TO AGENTS."
  notes: |
    - Page deletion is NOT available through this connector.
    - Deletion requires admin access to the Notion workspace directly.
    - Agents must NOT attempt to delete or archive pages.
    - If a page needs to be removed, escalate to human admin.
```

---

## 4. Required Environment Variables

| Variable | Description | Required? | Example |
|---|---|---|---|
| `NOTION_API_KEY` | Notion integration API key (secret_xxx) | Yes | `secret_xxxxxxxxxxxxxxxxxxxxxxxxx` |
| `NOTION_KB_DATABASE_ID` | Database ID for the KB article collection | Yes | `abc123def456...` |

### 4.1 Required Integration Capabilities

The Notion integration must be granted the following capabilities on the KB database:

```
Read content      # search_kb, read_page
Update content    # create_page, update_page (drafts only)
Insert content    # create_page (new drafts)
```

The integration must NOT be granted:
```
Delete pages      # Prohibited
Admin access      # Prohibited
```

### 4.2 Environment Setup

```bash
# .env or environment configuration
NOTION_API_KEY=secret_your_integration_key
NOTION_KB_DATABASE_ID=your_database_id
```

---

## 5. Safety Rules

### 5.1 Never Delete Pages

```
SAFETY RULE: NEVER DELETE PAGES
- Agents MUST NOT delete, archive, or trash any Notion pages.
- The delete_page capability is NOT available through this connector.
- If a page needs to be removed or updated beyond draft scope,
  escalate to human admin.
- Violation of this rule results in immediate agent suspension.
```

### 5.2 All Creates Go to Draft Queue

```
SAFETY RULE: ALL CREATES ARE DRAFTS
- All pages created by agents have status "draft" — no exceptions.
- Agents CANNOT set page status to "published".
- Drafts are automatically routed to the human review queue for KB moderation.
- Human reviewers can:
  - APPROVE → publish the draft to the live KB
  - EDIT → modify content, then approve/reject
  - REJECT → discard the draft
- Published KB content is always human-approved.
```

### 5.3 No Direct Publishing

```
SAFETY RULE: NO DIRECT PUBLISHING
- Agents must NOT attempt to change a page's status from "draft" to "published".
- Agents must NOT use any workaround to publish content directly.
- All published content must go through the human review workflow.
- This rule CANNOT be overridden by any plugin or agent configuration.
```

### 5.4 Content Safety

| Rule | Enforcement |
|---|---|
| No PII in KB articles | Agent-created drafts must not contain real customer PII |
| No medical claims | Drafts must pass medical compliance check before submission |
| No unverified claims | Drafts containing factual claims must cite sources |
| No copyrighted content | Agents must not reproduce copyrighted material in KB articles |
| Compliance tagging | Drafts must be tagged with relevant compliance categories |

### 5.5 Rate Limit Awareness

| Limit | Value | Handling |
|---|---|---|
| Requests per second | 3 | Implement rate limiter with 3 RPS cap |
| Request size limit | 1 MB | Chunk large page content into multiple block appends |
| Search results limit | 100 per request | Paginate using start_cursor |

**Rate Limit Error Handling:**
```python
# Pseudocode for Notion rate limit handling
def handle_notion_api_error(response):
    if response.status_code == 429:
        # Rate limited
        retry_after = float(response.headers.get('Retry-After', 1.0))
        time.sleep(retry_after)
        return retry(response)
    elif response.status_code == 404:
        # Page or database not found
        log_error("NOTION_NOT_FOUND", detail=response.json())
        return None
```

---

## 6. Data Handling

### 6.1 What Agents May Read

- KB article content (text blocks, headings, lists, tables)
- Article metadata (tags, category, status, last edited time)
- Article URLs (internal KB links)

### 6.2 What Agents Must NOT Do

- Access databases other than the configured KB database
- Read pages outside the KB (e.g., internal HR docs, financial pages)
- Export KB content to external systems
- Store KB content in agent state beyond the active task
- Include real customer PII in draft articles

---

## 7. Integration with Human Review

### 7.1 Search → Read → Draft/Escalate Workflow

```
1. Agent searches KB for relevant articles (search_kb)
2. Agent reads the full article content (read_page)
3. Agent uses KB content to inform its response:
   - If KB answers the question → draft response via Gmail/Feishu connector
   - If KB is outdated or missing info → create/update draft KB article
   - If KB content conflicts with policy → escalate to compliance
4. For new/updated KB articles:
   - Agent creates draft (create_page or update_page)
   - Draft is routed to human review queue
   - Human reviewer edits, approves, or rejects
   - If approved → published to live KB
```

### 7.2 Draft Review Queue

KB draft reviews include:
- Draft title and content
- Reason for creation/update (e.g., "customer inquiry revealed missing KB article")
- Source references (e.g., customer conversation, product docs)
- Compliance check results
- Suggested category and tags

---

## 8. Mock Data

For testing and development, use the mock KB data at:
```
connectors/mock/mock-kb.json
```

This file contains 5 sample KB articles (refund policy, shipping policy, warranty, product usage guide, medical compliance FAQ) for testing agent workflows.

---

## 9. Error Codes

| Error Code | Description | Agent Action |
|---|---|---|
| `NOTION_AUTH_FAILED` | API key invalid or integration not authorized | Log error, alert ops, stop processing |
| `NOTION_RATE_LIMITED` | Rate limit exceeded (429) | Backoff per Retry-After, retry |
| `NOTION_PAGE_NOT_FOUND` | Page ID does not exist | Log, return "page not found" to agent |
| `NOTION_DATABASE_NOT_FOUND` | Database ID does not exist or no access | Log, alert ops, stop processing |
| `NOTION_DRAFT_CREATE_FAILED` | Draft creation failed | Log error, retry once, escalate if persistent |
| `NOTION_PUBLISH_BLOCKED` | Agent attempted to publish directly | Log violation, block, alert security |
| `NOTION_DELETE_BLOCKED` | Agent attempted to delete a page | Log violation, block, alert security |

---

## 10. References

- Notion API Documentation: https://developers.notion.com/
- Notion API Rate Limits: https://developers.notion.com/reference/request-limits
- policies/tool-permissions.md — Permission level definitions
- policies/medical-compliance.md — Content compliance for KB articles
- policies/human-review.md — Human review workflow for drafts
