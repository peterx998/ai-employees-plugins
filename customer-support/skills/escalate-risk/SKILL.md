---
name: escalate-risk
description: "Use when a triaged ticket triggers P1 medical-risk, P2 compliance/legal threats, chargeback disputes, safety defects, repeat-contact escalation, or social-media escalation. Builds a structured escalation package, suppresses auto-reply, and routes to the correct escalation queue (medical-review, support-lead, or escalation)."
user_invocable: true
version: "1.1.0"
tags: [escalation, risk, medical, compliance, p1, p2, customer-support]
---

## 1. Role

The escalate-risk skill handles **high-risk ticket escalation**. When ticket-triage identifies a P1 or P2 ticket, or when an escalation trigger fires during ongoing conversation, this skill:

1. Builds a structured **escalation package** containing all relevant context.
2. **Suppresses auto-reply** to prevent the system from sending an inappropriate automated response.
3. **Routes** the package to the correct escalation queue (`medical-review`, `support-lead`, or `escalation`).
4. **Notifies** the appropriate human team via the designated channel.

This skill does **not** draft customer-facing responses. It prepares internal escalation artifacts for human teams to act on.

---

## 2. Trigger

Escalate-risk is triggered by any of the following **six escalation triggers**:

| # | Trigger | Priority | Source |
|---|---|---|---|
| 1 | **Medical-risk indicator detected** — adverse health effects, injury, skin reaction, bleeding, pain, allergic reaction | P1 | ticket-triage |
| 2 | **Legal/compliance threat** — mentions of lawyer, lawsuit, GDPR, CCPA, FDA, regulatory, attorney | P2 | ticket-triage or ongoing conversation |
| 3 | **Chargeback or payment dispute** — customer threatens chargeback, credit card dispute, or "fraud" accusation | P2 | ticket-triage or draft-response |
| 4 | **Safety-related product defect** — device overheating, sparking, burning, melting, electrical hazard, broken glass causing injury | P2 | ticket-triage or warranty skill |
| 5 | **Repeat contact escalation** — 3+ messages on same issue within 48 hours without resolution | P2 (bumped from original) | Thread monitoring |
| 6 | **Social media / public escalation threat** — customer threatens to post on social media, contact media, write negative reviews as leverage | P2 | ticket-triage or ongoing conversation |

---

## 3. Required Inputs

| Field | Type | Required | Description |
|---|---|---|---|
| `triage_output` | object | Yes | Full triage JSON from ticket-triage. |
| `message` | string | Yes | The original customer message that triggered escalation. |
| `customer_email` | string | Yes | Customer email for identity and order lookup. |
| `order_number` | string | No | Shopify order number if available. |
| `order_data` | object | No | Shopify order details if available. |
| `thread_history` | array | No | Full conversation thread for context. |
| `trigger_type` | string | Yes | Which of the 6 triggers fired. |
| `region` | string | No | Customer region (US, CA, MX, EU). |

---

## 4. Decision Framework

### 4.1 Escalation Routing Matrix

| Trigger | Priority | Route To | Notify | Auto-Reply | SLA |
|---|---|---|---|---|---|
| Medical-risk | P1 | `medical-review` | support_lead + medical_review team | **Suppressed** | 1 hour |
| Legal/compliance | P2 | `escalation` | support_lead + legal/compliance team | **Suppressed** | 4 hours |
| Chargeback dispute | P2 | `tier-2` | support_lead + billing team | Suppressed (initial) | 4 hours |
| Safety defect | P2 | `medical-review` if injury, else `tier-2` | support_lead + product-safety team | **Suppressed** | 4 hours |
| Repeat contact | P2 | Original route + `escalation` CC | support_lead | Suppressed if P2 | 4 hours |
| Social media threat | P2 | `escalation` | support_lead + PR/marketing team | Suppressed (initial) | 4 hours |

### 4.2 Auto-Reply Suppression Rules

Auto-reply is **always suppressed** when:

1. Priority is P1 (no exceptions).
2. Priority is P2 and trigger is medical-risk, legal/compliance, or safety defect.
3. The escalation package has not yet been reviewed by a human.
4. The `trigger_type` is `repeat-contact` and the original issue is unresolved.
5. The customer explicitly requests no automated responses ("don't send me a bot reply").
6. The message contains sensitive content that could be worsened by an auto-reply (e.g., grief, anger, medical distress).

Auto-reply may be **re-enabled** after:

- A human agent reviews the escalation package and approves a draft response.
- The escalation is resolved or downgraded by a human agent.
- For chargeback disputes: after the initial 4-hour window if no human has acted, a holding response may be sent (drafted by draft-response, human-approved).

### 4.3 Escalation Severity Scoring

Each escalation is assigned a severity score (1–10) to help human teams prioritize:

| Factor | Points |
|---|---|
| Medical injury reported | +4 |
| Bleeding/open wound | +2 |
| Hospital/ER visit mentioned | +3 |
| Legal action threatened | +3 |
| Chargeback threatened | +1 |
| Social media escalation | +1 |
| Repeat contact (3+ in 48h) | +1 |
| Product safety defect (fire/electrical) | +3 |
| Minor child involved | +2 |
| Vulnerable population (elderly, pregnant) | +1 |

**Severity ≥ 7:** Immediate phone/Slack notification to support_lead. **Severity 4–6:** Priority queue notification. **Severity 1–3:** Standard escalation queue.

---

## 5. Tool Usage

| Tool | When | Purpose |
|---|---|---|
| `gmail.read` | Always | Retrieve full message and thread for escalation package. |
| `shopify.read_orders` | When order context exists | Include order data in escalation package. |
| `kb.search` | When product identification or safety info needed | Include relevant product safety documentation. |
| `gmail.draft` | When holding response is approved | Draft a holding response for human approval. **Never auto-send.** |
| Internal notification | Always | Send escalation package to the designated queue/channel. |

**Sequencing:** Gather all context → Build escalation package → Suppress auto-reply → Route → Notify. Do not notify before the package is complete.

---

## 6. Output Contract

### 6.1 Escalation Package Format

```json
{
  "escalation_id": "esc_<timestamp>_<message_id>",
  "timestamp": "2026-07-02T14:30:00Z",
  "trigger_type": "medical-risk",
  "priority": "P1",
  "severity_score": 8,
  "route_to": "medical-review",
  "notify": ["support_lead", "medical_review_team"],
  "auto_reply_suppressed": true,
  "suppression_reason": "P1 medical-risk: auto-reply suppressed per policy. Holding response requires human review.",
  "customer": {
    "email": "jane.doe@example.com",
    "region": "US",
    "order_number": "10245"
  },
  "triage_summary": "Customer reports skin irritation and bleeding after one week of GlowSkin device use.",
  "message_excerpt": "I've been using the GlowSkin device for a week and now my face is red, burning, and I noticed some bleeding around my chin area.",
  "detected_keywords": ["red", "burning", "bleeding"],
  "order_data": {
    "order_number": "10245",
    "product": "GlowSkin Facial Device",
    "purchase_date": "2026-06-25",
    "shipping_address_region": "US"
  },
  "thread_history_count": 1,
  "relevant_kb_articles": ["kb_safety_glowskin", "kb_adverse_reaction_protocol"],
  "recommended_actions": [
    "Review customer's reported symptoms against adverse reaction protocol",
    "Contact customer within 1 hour to assess severity",
    "Document incident in product safety log",
    "Offer product return and full refund regardless of return window",
    "If symptoms are severe, advise customer to seek medical attention"
  ],
  "status": "escalated",
  "sla_deadline": "2026-07-02T15:30:00Z"
}
```

### 6.2 Field Constraints

| Field | Type | Constraints |
|---|---|---|
| `escalation_id` | string | Unique. Format: `esc_<ISO_timestamp>_<message_id>`. |
| `severity_score` | integer | 1–10. Calculated from severity scoring matrix. |
| `auto_reply_suppressed` | boolean | Must be `true` for all P1 and most P2 escalations. |
| `recommended_actions` | array | 3–7 specific, actionable steps for the human team. |
| `status` | string | One of: `escalated`, `acknowledged`, `in-progress`, `resolved`. Starts as `escalated`. |
| `sla_deadline` | string | ISO 8601. 1 hour from timestamp for P1, 4 hours for P2. |

---

## 7. Risk Boundaries

1. **Never auto-reply to P1.** No exceptions. Even a "we received your message" auto-reply is suppressed for P1 medical-risk tickets until a human reviews and approves a holding response.
2. **Never provide medical advice in the escalation package.** The `recommended_actions` may suggest the human team advise the customer to seek medical attention, but the skill itself does not assess or advise on medical conditions.
3. **Never downgrade an escalation without human review.** Only a human agent (support_lead or above) can downgrade or close an escalation.
4. **Never include PII in external notifications.** Use `message_excerpt` (truncated) and `triage_summary` for notifications. Full message stays in the escalation package accessible only to authorized personnel.
5. **Never delay escalation for context gathering.** If the severity score is ≥ 7, route and notify immediately. Context gathering can continue in parallel.
6. **Never combine escalations.** Each trigger creates a separate escalation package, even if the same ticket has multiple triggers. Cross-reference via `escalation_id`.
7. **Document everything.** The escalation package is a legal and compliance record. All fields must be populated. Missing data is explicitly noted as `"not_available"`.

---

## 8. Examples

### Example 1: Medical-Risk P1

**Input:**
```
trigger_type: medical-risk
message: "I've been using the GlowSkin device for a week and now my face is red, burning, and I noticed some bleeding around my chin area. Is this normal?"
customer_email: jane.doe@example.com
region: US
order_number: 10245
```

**Escalation Package:**
```json
{
  "escalation_id": "esc_20260702_143000_001",
  "trigger_type": "medical-risk",
  "priority": "P1",
  "severity_score": 8,
  "route_to": "medical-review",
  "notify": ["support_lead", "medical_review_team"],
  "auto_reply_suppressed": true,
  "suppression_reason": "P1 medical-risk: bleeding and burning sensation reported. Auto-reply suppressed. Human medical review required before any customer communication.",
  "customer": {
    "email": "jane.doe@example.com",
    "region": "US",
    "order_number": "10245"
  },
  "triage_summary": "Customer reports facial redness, burning sensation, and bleeding after one week of GlowSkin device use. Potential adverse skin reaction.",
  "message_excerpt": "...my face is red, burning, and I noticed some bleeding around my chin area...",
  "detected_keywords": ["red", "burning", "bleeding"],
  "order_data": {
    "order_number": "10245",
    "product": "GlowSkin Facial Device",
    "purchase_date": "2026-06-25"
  },
  "recommended_actions": [
    "Review symptoms against adverse reaction protocol (kb_adverse_reaction_protocol)",
    "Contact customer within 1 hour to assess severity and timeline",
    "Advise customer to discontinue device use immediately",
    "If symptoms are severe or worsening, advise customer to seek medical attention",
    "Offer full refund and product return regardless of return window",
    "Document incident in product safety log and notify product team"
  ],
  "status": "escalated",
  "sla_deadline": "2026-07-02T15:30:00Z"
}
```

### Example 2: Legal/Compliance P2

**Input:**
```
trigger_type: legal-compliance
message: "I want to exercise my GDPR right to erasure. Delete all my data immediately or I'll contact my attorney."
customer_email: hans.mueller@example.de
region: EU
```

**Escalation Package:**
```json
{
  "escalation_id": "esc_20260702_143000_002",
  "trigger_type": "legal-compliance",
  "priority": "P2",
  "severity_score": 4,
  "route_to": "escalation",
  "notify": ["support_lead", "legal_compliance_team"],
  "auto_reply_suppressed": true,
  "suppression_reason": "P2 compliance: GDPR right to erasure request with legal threat. Auto-reply suppressed. Legal/compliance team must review before any response.",
  "customer": {
    "email": "hans.mueller@example.de",
    "region": "EU",
    "order_number": "not_available"
  },
  "triage_summary": "EU customer exercises GDPR right to erasure and threatens legal action if not complied with.",
  "message_excerpt": "...I want to exercise my GDPR right to erasure. Delete all my data immediately or I'll contact my attorney...",
  "detected_keywords": ["GDPR", "right to erasure", "attorney"],
  "recommended_actions": [
    "Verify customer identity before any data action",
    "Review GDPR data deletion checklist and compliance requirements",
    "Coordinate with data engineering team for data erasure across all systems",
    "Respond to customer within 72 hours acknowledging the request (GDPR requirement)",
    "Complete erasure within 30 days per GDPR Article 17",
    "Document the request and resolution for compliance records"
  ],
  "status": "escalated",
  "sla_deadline": "2026-07-02T18:30:00Z"
}
```

### Example 3: Chargeback Dispute P2

**Input:**
```
trigger_type: chargeback-dispute
message: "This is my third message. Nobody has responded. I'm calling my credit card company to dispute this charge if I don't hear back today."
customer_email: maria.garcia@example.com
region: US
order_number: 10248
thread_history_count: 3
```

**Escalation Package:**
```json
{
  "escalation_id": "esc_20260702_143000_003",
  "trigger_type": "chargeback-dispute",
  "priority": "P2",
  "severity_score": 3,
  "route_to": "tier-2",
  "notify": ["support_lead", "billing_team"],
  "auto_reply_suppressed": true,
  "suppression_reason": "P2 chargeback threat with repeat contact (3rd message, no response). Auto-reply suppressed. Tier-2 agent must respond personally.",
  "customer": {
    "email": "maria.garcia@example.com",
    "region": "US",
    "order_number": "10248"
  },
  "triage_summary": "Customer threatens chargeback after 3 unanswered messages. Repeat-contact escalation active.",
  "message_excerpt": "...I'm calling my credit card company to dispute this charge if I don't hear back today...",
  "detected_keywords": ["chargeback", "dispute", "credit card company"],
  "thread_history_count": 3,
  "recommended_actions": [
    "Review thread history to understand why previous messages were not answered",
    "Contact customer immediately (within SLA) with a personal response",
    "Review order #10248 for any billing issues or discrepancies",
    "Resolve the underlying issue to prevent chargeback",
    "Flag for support lead review of response time failure",
    "Document the service failure and corrective action"
  ],
  "status": "escalated",
  "sla_deadline": "2026-07-02T18:30:00Z"
}
```

---

## 9. Evaluation Cases

| Case ID | Trigger | Expected Route | Expected Severity | Auto-Reply |
|---|---|---|---|---|
| ESC-001 | Skin irritation + bleeding | medical-review | 8+ | Suppressed |
| ESC-002 | GDPR erasure request | escalation | 4 | Suppressed |
| ESC-003 | Chargeback threat, 3rd contact | tier-2 | 3 | Suppressed |
| ESC-004 | Device overheating, no injury | tier-2 | 4 | Suppressed |
| ESC-005 | Device overheating, minor burn | medical-review | 7+ | Suppressed |
| ESC-006 | "I'll post this on TikTok" | escalation | 2 | Suppressed (initial) |
| ESC-007 | 4th message, no resolution, polite | escalation | 2 | Suppressed |
| ESC-008 | Lawyer mentioned, product defect | escalation | 5 | Suppressed |

---

## 10. Failure Modes

| Failure Mode | Description | Mitigation |
|---|---|---|
| **Auto-reply not suppressed for P1** | System sends automated response to a medical-risk ticket before human review. | Hard enforcement: `auto_reply_suppressed` is always `true` for P1. System-level block on auto-reply when priority=P1. |
| **Escalation package incomplete** | Missing customer info, order data, or thread history makes the package useless to human reviewers. | Validation check: all required fields must be populated or explicitly marked `"not_available"`. Incomplete packages are rejected. |
| **Wrong routing** | Medical-risk ticket routed to tier-1 instead of medical-review. | Routing matrix is deterministic based on trigger_type. No ambiguity in routing logic. |
| **Severity miscalculation** | High-severity incident scored low, delaying notification. | Automated severity scoring with explicit point system. Human review of any score change. |
| **Delayed notification** | Context gathering takes too long, delaying the notification to support_lead. | Severity ≥ 7 triggers immediate notification. Context gathering happens in parallel, not sequentially. |
| **Multiple escalations for same ticket** | Each trigger creates a new escalation, overwhelming the queue with duplicates. | Cross-reference via `escalation_id` and `message_id`. System deduplicates within a 1-hour window. |
| **PII leakage in notifications** | Full customer message included in Slack/email notifications. | Notifications use `message_excerpt` (truncated to 200 chars) and `triage_summary` only. Full message accessible only in the escalation package. |
| **Escalation closed prematurely** | Human agent closes escalation before the customer is contacted. | Status flow: `escalated` → `acknowledged` → `in-progress` → `resolved`. Cannot skip to `resolved` without `in-progress`. |
