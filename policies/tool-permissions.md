# Tool Permission Matrix for All Connectors

> **Applies to:** ALL plugins, ALL agents, ALL connectors. This is a global policy — no plugin may grant permissions beyond those defined here.

**Version:** 1.0.0  
**Last Updated:** 2026-07-02  
**Owner:** Platform / Security Team  
**Review Cadence:** Quarterly  

---

## 1. Purpose

This document defines the permission levels for all connector operations and maps each connector's capabilities to allowed permission levels. It ensures that AI agents can only perform actions appropriate to their role, and that sensitive operations (sending emails, modifying orders) always require human approval.

---

## 2. Permission Levels

| Level | Name | Description | Human Approval Required? |
|---|---|---|---|
| **RO** | Read-Only | Agent may retrieve and read data. No modifications. | No |
| **RW** | Read-Write | Agent may read and modify data autonomously. | No |
| **WD** | Write-Draft | Agent may create draft content for human review. Draft is NOT published/sent. | No (to create draft); Yes (to publish/send) |
| **WS** | Write-Send | Agent may create and send/publish content. **Human approval required before execution.** | **Yes — always** |

### 2.1 Default Permission Rules

```
DEFAULT PERMISSION RULES
1. All connectors start at READ-ONLY by default.
2. Write permissions must be explicitly granted per plugin configuration.
3. WRITE-SEND operations ALWAYS require human approval, no exceptions.
4. WRITE-DRAFT operations create drafts that are reviewed by a human before publishing.
5. READ-WRITE is reserved for internal system operations only (e.g., updating agent state).
6. Agents cannot self-escalate permission levels.
7. Permission changes require admin approval and are logged for audit.
```

---

## 3. Connector Permission Matrix

### 3.1 Gmail Connector

| Capability | Permission Level | Agent Can Execute Autonomously? | Human Approval Required? |
|---|---|---|---|
| `read_thread` | RO | Yes | No |
| `search_messages` | RO | Yes | No |
| `create_draft` | WD | Yes (creates draft only) | No (draft is not sent) |
| `send_email` | WS | **No** | **Yes — always required** |

**Key Rule:** Agents may draft email replies but may NEVER send emails without human approval. Drafts are reviewed in the human review queue before sending.

### 3.2 Shopify Connector

| Capability | Permission Level | Agent Can Execute Autonomously? | Human Approval Required? |
|---|---|---|---|
| `get_order` | RO | Yes | No |
| `search_orders` | RO | Yes | No |
| `get_product` | RO | Yes | No |
| `get_customer` | RO | Yes | No |
| `update_tracking` | WS | **No** | **Yes — always required** |

**Key Rules:**
- Agents may read orders, products, and customer data (data minimization applies).
- Agents may NOT modify orders, issue refunds, cancel orders, or change payment status.
- `update_tracking` requires human approval because incorrect tracking causes customer confusion.

### 3.3 Notion Connector (Knowledge Base)

| Capability | Permission Level | Agent Can Execute Autonomously? | Human Approval Required? |
|---|---|---|---|
| `search_kb` | RO | Yes | No |
| `read_page` | RO | Yes | No |
| `create_page` | WD | Yes (creates as draft) | No (draft is not published) |
| `update_page` | WD | Yes (updates draft only) | No (draft is not published) |
| `delete_page` | **PROHIBITED** | **No** | **Never — not available** |

**Key Rules:**
- All created/updated pages go to a draft queue for human review before publishing to the live KB.
- Agents may NEVER delete KB pages.
- Published KB content requires human approval.

### 3.4 TikTok Connector

| Capability | Permission Level | Agent Can Execute Autonomously? | Human Approval Required? |
|---|---|---|---|
| `get_video_metrics` | RO | Yes | No |
| `get_account_stats` | RO | Yes | No |
| `search_trends` | RO | Yes | No |
| `create_video_draft` | WD | Yes (creates draft) | No (draft is not posted) |
| `post_video` | WS | **No** | **Yes — always required** |
| `post_comment` | WS | **No** | **Yes — always required** |
| `delete_content` | **PROHIBITED** | **No** | **Never — not available** |

**Key Rules:**
- All TikTok content goes through medical compliance and advertising claims review before posting.
- Agents may never post directly — all content is drafted and human-approved.
- Deletion is not available to agents; content removal requires admin action.

### 3.5 Feishu (Lark) Connector

| Capability | Permission Level | Agent Can Execute Autonomously? | Human Approval Required? |
|---|---|---|---|
| `read_message` | RO | Yes | No |
| `search_messages` | RO | Yes | No |
| `create_message_draft` | WD | Yes (creates draft) | No (draft is not sent) |
| `send_message` | WS | **No** | **Yes — always required** |
| `create_doc` | WD | Yes (creates as draft) | No (draft is not published) |
| `update_doc` | WD | Yes (updates draft only) | No (draft is not published) |
| `delete_doc` | **PROHIBITED** | **No** | **Never — not available** |

**Key Rules:**
- Internal communications via Feishu follow the same draft-then-approve pattern as email.
- Agents may read Feishu messages for context but may not send without approval.

### 3.6 Microsoft Clarity Connector

| Capability | Permission Level | Agent Can Execute Autonomously? | Human Approval Required? |
|---|---|---|---|
| `get_session` | RO | Yes | No |
| `get_metrics` | RO | Yes | No |
| `get_heatmap` | RO | Yes | No |
| `get_funnel` | RO | Yes | No |
| `export_data` | **PROHIBITED** | **No** | **Never — not available to agents** |

**Key Rules:**
- Clarity is read-only — agents may retrieve analytics data but cannot modify anything.
- Session data must not contain PII (enforced by Clarity's own masking, verified by agent runtime).
- Data export is admin-only; agents reference data in reports but do not export raw data.

### 3.7 Shotstack Connector (Video Generation)

| Capability | Permission Level | Agent Can Execute Autonomously? | Human Approval Required? |
|---|---|---|---|
| `create_video_draft` | WD | Yes (generates draft render) | No (draft is not published) |
| `render_video` | WD | Yes (renders to staging) | No (render is to staging only) |
| `publish_video` | WS | **No** | **Yes — always required** |
| `delete_video` | **PROHIBITED** | **No** | **Never — not available** |

**Key Rules:**
- All video generation goes through medical compliance review before publishing.
- Renders are created in staging; publishing to any platform requires human approval.
- Agents cannot delete video assets.

---

## 4. Summary Matrix

| Connector | RO | WD | WS | PROHIBITED |
|---|---|---|---|---|
| **Gmail** | read_thread, search_messages | create_draft | send_email | — |
| **Shopify** | get_order, search_orders, get_product, get_customer | — | update_tracking | modify_order, issue_refund, cancel_order |
| **Notion** | search_kb, read_page | create_page, update_page | — | delete_page |
| **TikTok** | get_video_metrics, get_account_stats, search_trends | create_video_draft | post_video, post_comment | delete_content |
| **Feishu** | read_message, search_messages | create_message_draft, create_doc, update_doc | send_message | delete_doc |
| **Clarity** | get_session, get_metrics, get_heatmap, get_funnel | — | — | export_data |
| **Shotstack** | — | create_video_draft, render_video | publish_video | delete_video |

---

## 5. Write-Send Approval Workflow

All WS (Write-Send) operations follow this mandatory workflow:

```
WRITE-SEND APPROVAL WORKFLOW
1. Agent prepares the action (email draft, social post, tracking update, etc.)
2. Agent submits action to human review queue with:
   - Action type and target
   - Full content of what will be sent/published
   - Context (conversation, customer info, reason)
   - Compliance check results
3. Human reviewer receives notification per escalation SLA.
4. Human reviewer can: APPROVE, REJECT, or EDIT+APPROVE.
5. If APPROVED → action is executed by the system (not the agent).
6. If REJECTED → agent is notified, no action taken, case closed.
7. If EDIT+APPROVE → human modifies content, then approves for execution.
8. All WS actions are logged with: agent ID, human reviewer ID, timestamp, action details.
```

---

## 6. Permission Violations

| Violation | Severity | Response |
|---|---|---|
| Agent attempts WS without approval | Critical | Block action, suspend agent workflow, incident report |
| Agent attempts PROHIBITED operation | Critical | Block action, suspend agent, security review |
| Agent accesses RO data beyond task scope | High | Log violation, review connector scopes |
| Draft published without human review | Critical | Immediate rollback, incident report, audit review |
| Permission level changed without admin approval | Critical | Revert change, security incident |

---

## 7. Connector Reference

For detailed connector contracts, see:

| Connector | Contract File |
|---|---|
| Gmail | `connectors/gmail.connector.md` |
| Shopify | `connectors/shopify.connector.md` |
| Notion | `connectors/notion.connector.md` |
| Clarity | `connectors/clarity.connector.md` |
| TikTok | (defined in plugin configurations) |
| Feishu | (defined in plugin configurations) |
| Shotstack | (defined in plugin configurations) |

---

## 8. References

- policies/medical-compliance.md — Compliance checks for content before WS
- policies/human-review.md — Escalation and review queue management
- policies/privacy-and-pii.md — Data access minimization rules
- policies/advertising-claims.md — Ad content compliance before publishing
