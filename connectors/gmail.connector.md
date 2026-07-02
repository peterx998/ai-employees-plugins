# Gmail Connector Contract

**Version:** 1.0.0  
**Last Updated:** 2026-07-02  
**Owner:** Platform Team  
**Connector Type:** Email (Google Workspace / Gmail API)  

---

## 1. Overview

The Gmail connector enables AI agents to read email threads, search messages, create draft replies, and (with human approval) send emails. It integrates with the Gmail API using OAuth 2.0 credentials.

---

## 2. Capabilities

| Capability | Description | Permission Level | Human Approval Required? |
|---|---|---|---|
| `read_thread` | Read a specific email thread by thread ID | **Read-Only (RO)** | No |
| `search_messages` | Search messages using Gmail search query syntax | **Read-Only (RO)** | No |
| `create_draft` | Create a draft email (saved in Gmail Drafts, NOT sent) | **Write-Draft (WD)** | No (draft only) |
| `send_email` | Send an email to a recipient | **Write-Send (WS)** | **Yes — ALWAYS** |

---

## 3. Permission Levels

### 3.1 Read-Only Operations

```yaml
read_thread:
  permission: RO
  description: "Retrieve a specific thread and its messages."
  input:
    thread_id: string (required)
  output:
    thread:
      id: string
      messages: array<Message>
  rate_limit: "250 requests per second per user"
  human_approval: false

search_messages:
  permission: RO
  description: "Search Gmail messages using query syntax."
  input:
    query: string (required)  # Gmail search query (e.g., "from:support@brand.com subject:refund")
    max_results: integer (optional, default: 20, max: 100)
  output:
    messages: array<MessageSummary>
  rate_limit: "250 requests per second per user"
  human_approval: false
```

### 3.2 Write-Draft Operations

```yaml
create_draft:
  permission: WD
  description: "Create a draft email. The draft is saved in Gmail Drafts folder and is NOT sent."
  input:
    to: string (required)          # Recipient email
    subject: string (required)
    body: string (required)        # Email body (HTML or plaintext)
    thread_id: string (optional)   # Reply to existing thread
    cc: string (optional)
    bcc: string (optional)
  output:
    draft_id: string
    thread_id: string
  rate_limit: "250 requests per second per user"
  human_approval: false  # Draft is NOT sent — human reviews before sending
  notes: |
    - Drafts are created in the Gmail Drafts folder.
    - Human reviewer can edit and send the draft from Gmail or the review queue.
    - Agents must NOT attempt to send drafts directly.
```

### 3.3 Write-Send Operations

```yaml
send_email:
  permission: WS
  description: "Send an email to a recipient. HUMAN APPROVAL IS ALWAYS REQUIRED."
  input:
    to: string (required)
    subject: string (required)
    body: string (required)
    thread_id: string (optional)
    cc: string (optional)
    bcc: string (optional)
  output:
    message_id: string
    thread_id: string
    sent_at: string (ISO 8601)
  rate_limit: "250 requests per second per user"
  human_approval: true  # ALWAYS REQUIRED — NO EXCEPTIONS
  notes: |
    - This operation CANNOT be executed by an agent autonomously.
    - The agent prepares the email content and submits it to the human review queue.
    - A human reviewer must explicitly APPROVE before the email is sent.
    - All sent emails are logged with: agent_id, reviewer_id, timestamp, content hash.
```

---

## 4. Required Environment Variables

| Variable | Description | Required? | Example |
|---|---|---|---|
| `GMAIL_CLIENT_ID` | Google OAuth 2.0 Client ID | Yes | `xxxxx.apps.googleusercontent.com` |
| `GMAIL_CLIENT_SECRET` | Google OAuth 2.0 Client Secret | Yes | `GOCSPX-xxxxxxxxxxxxxxxx` |
| `GMAIL_REFRESH_TOKEN` | OAuth 2.0 Refresh Token for token refresh | Yes | `1//xxxxxxxxxxxxxxxxxxxxxxxx` |

### 4.1 Required OAuth Scopes

```
https://www.googleapis.com/auth/gmail.readonly    # Read threads and search
https://www.googleapis.com/auth/gmail.compose      # Create drafts and send (with approval)
```

### 4.2 Environment Setup

```bash
# .env or environment configuration
GMAIL_CLIENT_ID=your_client_id.apps.googleusercontent.com
GMAIL_CLIENT_SECRET=GOCSPX-your_client_secret
GMAIL_REFRESH_TOKEN=1//your_refresh_token
```

---

## 5. Safety Rules

### 5.1 Never Auto-Send

```
SAFETY RULE: NEVER AUTO-SEND EMAILS
- Agents MUST NOT execute the send_email capability directly.
- All emails must be created as drafts (create_draft) and submitted
  to the human review queue.
- A human reviewer must explicitly approve before the email is sent.
- This rule CANNOT be overridden by any plugin or agent configuration.
- Violation of this rule results in immediate agent suspension.
```

### 5.2 Never Expose Customer Email in Logs

```
SAFETY RULE: NO CUSTOMER EMAIL IN LOGS
- Customer email addresses must be redacted in all logs.
- Redaction format: [REDACTED:EMAIL]
- Logs must not contain the "to", "cc", or "bcc" fields in plaintext.
- If a log must reference a recipient, use a hashed identifier or
  [REDACTED:EMAIL] placeholder.
- This applies to debug logs, error logs, and audit logs.
```

### 5.3 Rate Limit Awareness

| Limit | Value | Handling |
|---|---|---|
| Requests per second per user | 250 | Implement exponential backoff on 429 responses |
| Requests per day per user | 1,000,000,000 | Monitor daily usage; alert at 80% |
| Concurrent requests per user | 250 | Use connection pooling with max 250 connections |
| Push notifications (watch) | Renew every 7 days | Monitor and renew watch subscriptions |

**Rate Limit Error Handling:**
```python
# Pseudocode for rate limit handling
def handle_gmail_api_error(response):
    if response.status_code == 429:
        # Rate limited — exponential backoff
        retry_after = int(response.headers.get('Retry-After', 1))
        wait_time = min(retry_after * (2 ** attempt), 64)
        time.sleep(wait_time)
        return retry(response)
    elif response.status_code == 403:
        # Quota exceeded — log and alert
        log_error("GMAIL_QUOTA_EXCEEDED")
        alert_ops_team()
        return None
```

### 5.4 Additional Safety Rules

| Rule | Enforcement |
|---|---|
| No bulk sending | Agents may create at most 10 drafts per conversation; bulk email requires admin tool |
| No sending to blocklists | Connector checks recipient against internal blocklist before draft creation |
| Subject line validation | Drafts with empty or suspicious subject lines are flagged |
| Attachment safety | Agents may not add attachments to emails — human reviewers add attachments during review |
| Reply-all safety | Agents must not use reply-all without explicit human instruction |

---

## 6. Data Handling

### 6.1 What Agents May Read

- Email thread content (subject, body, headers) for the specific thread being processed
- Sender and recipient addresses (for context and routing)
- Timestamps and labels

### 6.2 What Agents Must NOT Do

- Download or export entire inbox contents
- Store email contents beyond the active task duration
- Include customer email addresses in outputs shared with external systems
- Access emails unrelated to the current customer inquiry
- Read emails from threads the agent was not explicitly assigned to

---

## 7. Integration with Human Review

### 7.1 Draft → Review → Send Workflow

```
1. Agent reads incoming email thread (read_thread)
2. Agent searches for relevant context (search_messages, if needed)
3. Agent queries KB for policy/product info (via Notion connector)
4. Agent creates a draft reply (create_draft)
5. Agent submits draft to human review queue with:
   - Draft ID
   - Original thread context (PII redacted)
   - Compliance check results
   - Suggested action: SEND
6. Human reviewer:
   - Reviews draft content
   - Edits if needed
   - Approves or rejects
7. If approved: system sends the email (send_email) on behalf of the agent
8. If rejected: agent is notified, draft is discarded or revised
```

### 7.2 Escalation Integration

If the email triggers an escalation (see `policies/human-review.md`):

1. Agent does NOT create a draft reply
2. Agent creates an escalation package
3. Auto-reply is suppressed (if P1 trigger)
4. Human reviewer handles the response directly

---

## 8. Mock Data

For testing and development, use the mock Gmail data at:
```
connectors/mock/mock-gmail.json
```

This file contains 3 sample customer support emails (no real PII) for testing agent workflows.

---

## 9. Error Codes

| Error Code | Description | Agent Action |
|---|---|---|
| `GMAIL_AUTH_FAILED` | OAuth credentials invalid or expired | Log error, alert ops, stop processing |
| `GMAIL_RATE_LIMITED` | Rate limit exceeded (429) | Exponential backoff, retry |
| `GMAIL_QUOTA_EXCEEDED` | Daily quota exceeded (403) | Log, alert ops, queue tasks for later |
| `GMAIL_THREAD_NOT_FOUND` | Thread ID does not exist | Log, return "thread not found" to agent |
| `GMAIL_DRAFT_FAILED` | Draft creation failed | Log error, retry once, escalate if persistent |
| `GMAIL_SEND_REJECTED` | Send attempt blocked (no human approval) | Log violation, block, alert security |

---

## 10. References

- Gmail API Documentation: https://developers.google.com/gmail/api
- OAuth 2.0 for Google APIs: https://developers.google.com/identity/protocols/oauth2
- policies/tool-permissions.md — Permission level definitions
- policies/privacy-and-pii.md — PII handling rules
- policies/human-review.md — Human review workflow
