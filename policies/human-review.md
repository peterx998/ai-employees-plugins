# Global Human Review and Escalation Policy

> **Applies to:** ALL plugins, ALL agents, ALL workflows. This is a global policy — no plugin or agent may override escalation requirements defined here.

**Version:** 1.0.0  
**Last Updated:** 2026-07-02  
**Owner:** Operations / Compliance Team  
**Review Cadence:** Quarterly  

---

## 1. Purpose

This policy defines when AI agents must escalate to human review, the service level agreements (SLAs) for those escalations, what information must be included in escalation packages, and the rules governing auto-reply suppression and review queue management. It ensures that high-risk situations are always handled by qualified humans, never by autonomous agents.

---

## 2. When Human Review Is Mandatory

### 2.1 Priority Levels

| Priority | Label | Description | SLA |
|---|---|---|---|
| **P1** | Critical | Immediate risk to customer safety, legal exposure, or brand reputation | 15 minutes |
| **P2** | High | Significant risk requiring human judgment before response | 1 hour |
| **P3** | Medium | Standard escalation for review before action | 4 hours |
| **P4** | Low | Informational escalation, no immediate action needed | 24 hours |

### 2.2 Mandatory Escalation Triggers

#### P1 — Immediate Escalation (15 min SLA)

| Trigger | Condition | Auto-Reply? |
|---|---|---|
| **Medical risk** | Customer reports adverse reaction, allergic reaction, or product safety concern | Suppressed |
| **Legal threat** | Customer threatens legal action, mentions attorney, or references lawsuits | Suppressed |
| **Social media threat** | Customer threatens to post negatively, go viral, or contact media | Suppressed |
| **Regulatory inquiry** | Communication from or about a regulatory body (FDA, FTC, ASA, trading standards) | Suppressed |
| **High-value refund** | Refund request exceeding $500 USD (or local equivalent) | Suppressed |
| **Data breach suspected** | Agent detects potential unauthorized data access or PII exposure | Suppressed |
| **Self-harm or safety** | Customer expresses distress, self-harm ideation, or safety concerns | Suppressed |

#### P2 — High Priority Escalation (1 hour SLA)

| Trigger | Condition | Auto-Reply? |
|---|---|---|
| **Customer requests manager** | Explicit request for human supervisor | Allowed (acknowledgment only) |
| **Repeated complaint** | Customer has contacted support 3+ times on same issue | Allowed (with context) |
| **Medical advice request** | Customer asks for diagnosis, treatment recommendation, or medical guidance | Suppressed |
| **Complex refund** | Refund request $100–$500, partial refunds, exchange disputes | Allowed (with context) |
| **Negative sentiment + high-value customer** | Customer with LTV > $1000 expressing dissatisfaction | Allowed (with context) |
| **Product defect report** | Customer reports a product defect or quality issue affecting safety | Suppressed |

#### P3 — Medium Priority Escalation (4 hour SLA)

| Trigger | Condition | Auto-Reply? |
|---|---|---|
| **Non-standard request** | Request outside documented agent capabilities | Allowed |
| **Policy exception request** | Customer requests exception to stated policies | Allowed |
| **International shipping dispute** | Complex customs/duty/shipping issue | Allowed |
| **Warranty claim** | Warranty claim requiring verification | Allowed |

---

## 3. Escalation SLA

### 3.1 SLA Definitions

| Priority | First Response SLA | Resolution Target SLA | After-Hours? |
|---|---|---|---|
| P1 | 15 minutes | 2 hours | Yes — 24/7 coverage required |
| P2 | 1 hour | 8 hours | Yes — during business hours; queued if after hours |
| P3 | 4 hours | 24 hours | Next business day if after hours |
| P4 | 24 hours | 72 hours | Next business day if after hours |

### 3.2 SLA Breach Protocol

```
SLA BREACH PROTOCOL
1. If P1 is not acknowledged within 15 minutes:
   - Auto-page on-call manager
   - Send alert to compliance team
   - Log breach incident
2. If P2 is not acknowledged within 1 hour:
   - Notify team lead
   - Log breach incident
3. If P3 is not acknowledged within 4 hours:
   - Log breach incident
4. Repeated SLA breaches trigger operational review.
```

---

## 4. Escalation Package Requirements

Every escalation must include a structured escalation package. Agents must compile this package before routing to the human review queue.

### 4.1 Escalation Package Structure

```json
{
  "escalation_id": "ESC-2026-0702-001",
  "priority": "P1",
  "trigger": "MEDICAL_RISK",
  "created_at": "2026-07-02T14:30:00Z",
  "customer_context": {
    "customer_id": "[REDACTED]",
    "customer_name": "[REDACTED]",
    "order_id": "ORD-12345",
    "channel": "email"
  },
  "summary": "Customer reports skin irritation after using Product X. Adverse reaction protocol triggered.",
  "conversation_history": "[Full conversation transcript with PII redacted]",
  "relevant_kb_articles": ["kb-medical-compliance-faq", "kb-refund-policy-us"],
  "agent_assessment": "Adverse reaction reported. Advised customer to discontinue use and consult healthcare professional. Refund or replacement pending human decision.",
  "suggested_actions": [
    "Review adverse reaction report",
    "Determine if product recall or safety alert is needed",
    "Approve refund/replacement per policy",
    "File compliance incident report"
  ],
  "attachments": ["product-label-screenshot.png"],
  "compliance_flags": ["MEDICAL_COMPLIANCE", "ADVERSE_REACTION"]
}
```

### 4.2 Required Fields

| Field | Required? | Description |
|---|---|---|
| `escalation_id` | Yes | Auto-generated unique ID |
| `priority` | Yes | P1, P2, P3, or P4 |
| `trigger` | Yes | Categorized trigger (see §2.2) |
| `created_at` | Yes | ISO 8601 timestamp |
| `customer_context` | Yes | Customer/order identifiers (PII redacted per privacy policy) |
| `summary` | Yes | 1-3 sentence summary of the situation |
| `conversation_history` | Yes | Full transcript with PII redacted |
| `relevant_kb_articles` | Yes | KB articles the agent referenced |
| `agent_assessment` | Yes | Agent's analysis and what it has done so far |
| `suggested_actions` | Yes | Recommended next steps for human reviewer |
| `attachments` | No | Relevant files, screenshots, product info |
| `compliance_flags` | Yes | Applicable compliance flag tags |

---

## 5. Auto-Reply Suppression Rules

### 5.1 When to Suppress Auto-Reply

Auto-reply (automated acknowledgment or AI-generated response) must be **suppressed** in the following situations:

| Situation | Suppression | Rationale |
|---|---|---|
| P1 escalation | **Always suppressed** | Human must respond first; auto-reply risks misinformation |
| Adverse reaction report | **Always suppressed** | Medical safety — human must assess |
| Legal threat | **Always suppressed** | Legal risk — human must respond |
| Regulatory inquiry | **Always suppressed** | Compliance risk — human must respond |
| DSR / privacy request | **Always suppressed** | Legal compliance — human must handle |
| Self-harm / safety concern | **Always suppressed** | Safety — trained human required |
| Social media threat | **Always suppressed** | Brand risk — human must strategize |

### 5.2 Permitted Auto-Reply (Acknowledgment Only)

For P2 and P3 escalations where auto-reply is permitted, the auto-reply must:

1. Be an **acknowledgment only** — not a substantive response
2. State: "We've received your message and our team is reviewing it. We'll respond within [SLA timeframe]."
3. **Not** attempt to resolve the issue
4. **Not** make any commitments beyond the SLA timeframe
5. **Not** reference other customers or cases

### 5.3 Suppression Implementation

```
AUTO-REPLY SUPPRESSION LOGIC
1. Before sending any auto-reply, check escalation status.
2. If escalation priority is P1 → SUPPRESS (do not send auto-reply).
3. If escalation trigger is in [ADVERSE_REACTION, LEGAL_THREAT,
   REGULATORY_INQUIRY, DSR_REQUEST, SAFETY_CONCERN] → SUPPRESS.
4. If suppression is active, route directly to human review queue
   with P1 priority.
5. Log suppression event for audit trail.
```

---

## 6. Human Review Queue Management

### 6.1 Queue Structure

| Queue | Priority | Routing | Monitor |
|---|---|---|---|
| **Critical Queue** | P1 | Immediate notification (Slack/pager) to on-call agent | 24/7 |
| **High Priority Queue** | P2 | Notified to support team channel | Business hours |
| **Standard Queue** | P3 | Available in review dashboard | Business hours |
| **Informational Queue** | P4 | Batched daily summary | Daily |

### 6.2 Queue Assignment Rules

```
QUEUE ASSIGNMENT RULES
1. P1 escalations → Page on-call human agent immediately.
   If no acknowledgment within 5 minutes → escalate to manager.
2. P2 escalations → Assign to available support agent.
   Round-robin assignment among active agents.
3. P3 escalations → Available in shared queue, first-come-first-served.
4. P4 escalations → Batched into daily summary report.

Queue reassignment:
- If an agent does not pick up within 50% of SLA → reassign + notify.
- Agents can self-assign from P3/P4 queues.
- P1/P2 must be explicitly accepted/rejected by the assigned agent.
```

### 6.3 Queue Metrics

| Metric | Target |
|---|---|
| P1 acknowledgment time | < 5 minutes |
| P1 resolution time | < 2 hours |
| P2 acknowledgment time | < 30 minutes |
| P2 resolution time | < 8 hours |
| P3 resolution time | < 24 hours |
| Escalation rate (escalations / total tickets) | < 15% |
| Auto-reply suppression compliance | 100% |

---

## 7. Post-Escalation Actions

After a human reviewer resolves an escalation:

1. **Resolution logging:** The human reviewer records the resolution and any policy updates needed.
2. **Feedback to agent system:** If the escalation revealed an agent knowledge gap, the relevant KB article or agent instruction is updated.
3. **Compliance reporting:** P1 escalations are included in monthly compliance reports.
4. **Customer follow-up:** The human reviewer or agent sends a follow-up confirming resolution (agent may draft, human approves).

---

## 8. Escalation Categories (Tags)

All escalations must be tagged with one or more category tags:

| Tag | Description |
|---|---|
| `MEDICAL_RISK` | Adverse reaction, safety concern, medical advice request |
| `LEGAL_THREAT` | Threat of legal action, attorney involvement |
| `SOCIAL_MEDIA_THREAT` | Threat to post negatively, go viral, contact media |
| `REGULATORY` | Communication from/to regulatory body |
| `HIGH_VALUE_REFUND` | Refund request > $500 |
| `DSR_REQUEST` | Data subject request (GDPR/CCPA) |
| `SAFETY_CONCERN` | Self-harm, distress, safety risk |
| `COMPLIANCE_VIOLATION` | Agent detected potential compliance issue |
| `PRODUCT_DEFECT` | Product quality or safety defect report |
| `POLICY_EXCEPTION` | Customer requesting policy exception |
| `MANAGER_REQUEST` | Customer explicitly requested human supervisor |
| `REPEATED_COMPLAINT` | 3+ contacts on same issue |
| `COMPLEX_REFUND` | Refund $100-$500, partial refund, exchange dispute |

---

## 9. References

- policies/medical-compliance.md — Medical escalation triggers
- policies/privacy-and-pii.md — DSR handling protocol
- policies/tool-permissions.md — Write-send approval requirements
- policies/advertising-claims.md — Ad content escalation triggers
