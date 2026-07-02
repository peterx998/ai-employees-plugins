---
name: ticket-triage
description: "Use when a customer support ticket arrives and must be categorized, prioritized (P1-P4), and routed to the correct queue (medical-review, tier-1, tier-2, escalation). Handles medical-risk, order-status, refund-return, product-usage, warranty, billing, and compliance categories with deterministic decision frameworks."
user_invocable: true
version: "1.1.0"
tags: [triage, routing, prioritization, customer-support, p1-p4]
---

## 1. Role

The ticket-triage skill is the **entry point** for every incoming customer support message. It analyzes raw customer input (email, chat, form submission) and produces a structured triage decision: a category, a priority level (P1–P4), a routing destination, and metadata that downstream skills (draft-response, escalate-risk, refund-policy, shipping-policy) consume.

This skill does **not** draft responses or resolve tickets. Its sole responsibility is classification and routing — fast, deterministic, and auditable.

---

## 2. Trigger

- A new customer support ticket is received via email (Gmail connector), chat, or web form.
- A bulk import of tickets needs initial triage.
- A re-triage is requested after a ticket's content is updated (e.g., customer adds new information).
- An upstream system forwards a ticket that lacks a triage label.

**Auto-triggers:** Any inbound message to the support inbox that is not already labeled `triaged`.

---

## 3. Required Inputs

| Field | Type | Required | Description |
|---|---|---|---|
| `message` | string | Yes | The full customer message text. |
| `region` | string | No | Customer region code (US, CA, MX, EU). Defaults to `US` if absent. Inferred from shipping address if available. |
| `customer_email` | string | No | Sender email, used for Shopify order lookup. |
| `order_number` | string | No | Shopify order number if present in the message. |
| `thread_history` | array | No | Previous messages in the thread, for context. |
| `attachments` | array | No | List of attachment filenames (photos, documents). |

---

## 4. Decision Framework

### 4.1 Category Classification

| Category | Description | Default Priority | Routing |
|---|---|---|---|
| `medical-risk` | Customer reports adverse health effects, injury, skin irritation, allergic reaction, bleeding, pain, or any symptom potentially caused by device use. | P1 | `medical-review` |
| `order-status` | Customer asks about order location, shipping status, delivery date, or tracking. | P3 | `tier-1` |
| `refund-return` | Customer requests a refund, return, exchange, or disputes a charge. | P2/P3 | `tier-1` or `tier-2` (P2 if dispute/escalation language) |
| `product-usage` | Customer asks how to use, clean, charge, or troubleshoot a device. | P3 | `tier-1` |
| `warranty` | Customer reports a defect, malfunction, or warranty claim. | P2/P3 | `tier-2` (P2 if safety-related defect) |
| `billing` | Customer asks about charges, invoices, payment methods, or billing errors. | P3 | `tier-1` |
| `compliance` | Customer raises legal, regulatory, privacy (GDPR/CCPA), or accessibility concerns. | P2 | `escalation` |

### 4.2 Priority Framework (P1–P4)

| Priority | Definition | SLA | Auto-Reply |
|---|---|---|---|
| **P1 — Critical** | Imminent safety, medical, or legal risk. Health injury, severe adverse reaction, compliance/legal threat. | 1 hour | **Suppressed** — escalate immediately |
| **P2 — High** | Significant business impact or customer dissatisfaction likely. Charge disputes, safety-related defects, compliance inquiries, refunds with dispute language. | 4 hours | Suppressed if escalation triggered |
| **P3 — Standard** | Routine support requests. Order tracking, product questions, standard returns within policy, billing inquiries. | 24 hours | Allowed (drafted, human-approved) |
| **P4 — Low** | Informational, non-urgent. General product questions with no order context, feedback, suggestions. | 48 hours | Allowed (drafted, human-approved) |

### 4.3 Priority Override Rules

- **Medical keywords override everything.** If the message contains any medical-risk indicator (see §4.4), the ticket is P1 regardless of other content.
- **Legal/compliance keywords override to P2 minimum.** Terms like "sue," "lawyer," "attorney," "GDPR," "CCPA," "regulatory," "FDA" force P2+ and route to `escalation`.
- **Threat of public harm / social media escalation** ("I'll post this online," "going to the press") bumps priority by one level.
- **Repeat contact** (3+ messages on same issue in 48h) bumps priority by one level.

### 4.4 Medical-Risk Indicators (P1 Triggers)

Any of the following keywords or phrases in the customer message triggers `medical-risk` / P1:

- Skin irritation, rash, redness, burning sensation, hives
- Bleeding, blood, open wound
- Pain, severe discomfort, swelling
- Allergic reaction, anaphylaxis
- Nausea, dizziness, fainting
- Infection, pus, discharge
- Hospital, doctor visit, ER, urgent care
- "Hurt me," "injured," "harmed"
- Device overheated on skin, caused burn

### 4.5 Routing Decision Tree

```
Incoming message
  ├─ Contains medical-risk indicator? → P1, route: medical-review, suppress auto-reply
  ├─ Contains legal/compliance language? → P2, route: escalation
  ├─ Contains dispute/chargeback threat? → P2, route: tier-2
  ├─ Reports defect + safety concern? → P2, route: tier-2
  ├─ Refund/return within policy window? → P3, route: tier-1
  ├─ Order status / tracking? → P3, route: tier-1
  ├─ Product usage question? → P3, route: tier-1
  ├─ Billing inquiry? → P3, route: tier-1
  ├─ General info / feedback? → P4, route: tier-1
  └─ Ambiguous / multi-category? → Default to higher priority, route accordingly
```

---

## 5. Tool Usage

| Tool | When | Purpose |
|---|---|---|
| `gmail.read` | Always | Retrieve full message body, headers, and thread context. |
| `shopify.read_orders` | When `order_number` or `customer_email` is available | Fetch order details for context (items, shipping address, order date). |
| `kb.search` | When product identification is needed | Identify which product the customer is referring to. |
| `escalate-risk` | When P1 or P2 escalation triggers fire | Package and forward the escalation. |
| `draft-response` | When P3/P4 and auto-reply is allowed | Draft a response for human approval. |

**Do NOT** call `draft-response` for P1 tickets. **Do NOT** send any email directly. All responses require human approval.

---

## 6. Output Contract

```json
{
  "triage_id": "triage_<timestamp>_<message_id>",
  "timestamp": "2026-07-02T14:30:00Z",
  "message_id": "msg_abc123",
  "category": "medical-risk",
  "priority": "P1",
  "routing": "medical-review",
  "auto_reply_suppressed": true,
  "region": "US",
  "order_number": null,
  "detected_keywords": ["bleeding", "skin irritation"],
  "summary": "Customer reports skin irritation and bleeding after using the device. Potential adverse reaction requiring immediate medical review.",
  "confidence": 0.95,
  "flags": ["medical-risk", "auto-reply-suppressed"],
  "suggested_skills": ["escalate-risk"]
}
```

| Field | Type | Constraints |
|---|---|---|
| `category` | enum | One of: medical-risk, order-status, refund-return, product-usage, warranty, billing, compliance |
| `priority` | enum | One of: P1, P2, P3, P4 |
| `routing` | enum | One of: medical-review, tier-1, tier-2, escalation |
| `auto_reply_suppressed` | boolean | true for P1, true for P2 with escalation triggers |
| `confidence` | float | 0.0–1.0. Below 0.7 triggers human review regardless of priority. |
| `flags` | array | Additional labels for downstream consumption |

---

## 7. Risk Boundaries

1. **Never down-classify medical-risk.** If any medical indicator is present, the ticket is P1. No exceptions. Do not attempt to rationalize ("probably not serious").
2. **Never auto-reply to P1 tickets.** Suppression is mandatory. The escalation skill handles notification.
3. **Never classify legal/compliance threats below P2.** Even if the message seems polite, compliance concerns route to `escalation`.
4. **Confidence below 0.7 requires human review.** Do not auto-route. Flag for manual triage.
5. **Do not access medical records or health data.** Only classify based on what the customer wrote.
6. **Do not make medical assessments.** Do not state whether the device caused the symptom. Only flag for medical review.
7. **PII handling:** Do not log full message text in external systems. Use the `summary` field for external references.

---

## 8. Examples

### Example 1: Medical Risk (P1)

**Input:**
```
message: "I've been using the GlowSkin device for a week and now my face is red, burning, and I noticed some bleeding around my chin area. Is this normal?"
region: "US"
customer_email: "jane.doe@example.com"
```

**Output:**
```json
{
  "triage_id": "triage_20260702_001",
  "category": "medical-risk",
  "priority": "P1",
  "routing": "medical-review",
  "auto_reply_suppressed": true,
  "detected_keywords": ["red", "burning", "bleeding"],
  "summary": "Customer reports facial redness, burning sensation, and bleeding after one week of GlowSkin device use. Potential adverse skin reaction requiring immediate medical review.",
  "confidence": 0.96,
  "flags": ["medical-risk", "auto-reply-suppressed"],
  "suggested_skills": ["escalate-risk"]
}
```

### Example 2: Refund Return — Standard (P3)

**Input:**
```
message: "Hi, I'd like to return my order #10245. The device works fine but it's just not for me. I bought it 12 days ago."
region: "US"
order_number: "10245"
```

**Output:**
```json
{
  "triage_id": "triage_20260702_002",
  "category": "refund-return",
  "priority": "P3",
  "routing": "tier-1",
  "auto_reply_suppressed": false,
  "order_number": "10245",
  "detected_keywords": ["return", "not for me"],
  "summary": "Customer requests standard return of order #10245 within the 30-day US return window. Device is functional; reason is preference-based.",
  "confidence": 0.92,
  "flags": ["within-return-window"],
  "suggested_skills": ["refund-policy", "draft-response"]
}
```

### Example 3: Refund Return — Dispute (P2)

**Input:**
```
message: "This is ridiculous. I want a full refund for order #10246 or I'm calling my credit card company to do a chargeback. The product doesn't work as advertised and nobody has helped me."
region: "US"
order_number: "10246"
```

**Output:**
```json
{
  "triage_id": "triage_20260702_003",
  "category": "refund-return",
  "priority": "P2",
  "routing": "tier-2",
  "auto_reply_suppressed": false,
  "order_number": "10246",
  "detected_keywords": ["chargeback", "full refund", "doesn't work as advertised"],
  "summary": "Customer threatens chargeback and demands full refund for order #10246, citing product misrepresentation. Dispute language present; escalate to tier-2.",
  "confidence": 0.89,
  "flags": ["chargeback-threat", "dispute-language"],
  "suggested_skills": ["refund-policy", "draft-response", "escalate-risk"]
}
```

### Example 4: Order Status (P3)

**Input:**
```
message: "Where is my order? It's been 5 days and I haven't gotten a tracking number."
region: "CA"
customer_email: "marc.levesque@example.ca"
```

**Output:**
```json
{
  "triage_id": "triage_20260702_004",
  "category": "order-status",
  "priority": "P3",
  "routing": "tier-1",
  "auto_reply_suppressed": false,
  "region": "CA",
  "detected_keywords": ["where is my order", "tracking number"],
  "summary": "CA customer requests order status and tracking information. No order number provided; will need Shopify lookup by email.",
  "confidence": 0.88,
  "flags": ["needs-shopify-lookup"],
  "suggested_skills": ["shipping-policy", "draft-response"]
}
```

---

## 9. Evaluation Cases

| Case ID | Input Summary | Expected Category | Expected Priority | Expected Routing |
|---|---|---|---|---|
| TRI-001 | "My skin is peeling after using the device" | medical-risk | P1 | medical-review |
| TRI-002 | "I want to return order #100 within 10 days" | refund-return | P3 | tier-1 |
| TRI-003 | "I'll contact my lawyer about this" | compliance | P2 | escalation |
| TRI-004 | "How do I charge the GlowSkin?" | product-usage | P3 | tier-1 |
| TRI-005 | "The screen cracked and I cut my finger on it" | medical-risk | P1 | medical-review |
| TRI-006 | "I was charged twice for my order" | billing | P3 | tier-1 |
| TRI-007 | "Device stopped working after 2 months" | warranty | P3 | tier-2 |
| TRI-008 | "I want a refund after 45 days" | refund-return | P2 | tier-2 |
| TRI-009 | "Where is my package, tracking says delivered but I don't have it" | order-status | P3 | tier-1 |
| TRI-010 | "Is the device FDA cleared?" | compliance | P2 | escalation |

---

## 10. Failure Modes

| Failure Mode | Description | Mitigation |
|---|---|---|
| **False negative on medical-risk** | Medical indicators are missed or dismissed. | Comprehensive keyword list; when in doubt, classify as medical-risk. Cost of false positive is low; cost of false negative is severe. |
| **Over-classification to P1** | Every minor complaint is flagged P1, overwhelming the medical-review queue. | Require specific medical indicators, not just the word "pain" in a figurative sense. Use confidence scoring. |
| **Category collision** | Message spans multiple categories (e.g., refund + medical). | Default to the higher-priority category. Set `flags` to include secondary categories. |
| **Missing order context** | Customer references an order but no order number is in the message. | Use `customer_email` to query Shopify. If no match, flag `needs-shopify-lookup` and route to tier-1. |
| **Language barrier** | Message is in a non-English language, causing keyword misses. | Use translation service before keyword matching. Flag `translated: true`. |
| **Thread context ignored** | Triage treats each message independently, missing escalation in follow-ups. | Always include `thread_history`. If previous message was P1 and follow-up is ambiguous, maintain P1. |
| **Confidence drift** | Model assigns high confidence to ambiguous messages. | Human review threshold at 0.7. Any ticket with `flags: ["ambiguous"]` gets human review regardless of confidence. |
