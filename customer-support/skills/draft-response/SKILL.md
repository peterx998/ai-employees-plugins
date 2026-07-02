---
name: draft-response
description: "Use when a triaged ticket (P2-P4) needs a customer-facing response drafted for human approval. Follows warm-professional tone, acknowledge-answer-help-close structure, and strict medical-compliance boundaries. Never sends email directly — all drafts require human approval before sending."
user_invocable: true
version: "1.1.0"
tags: [drafting, response, tone, compliance, customer-support]
---

## 1. Role

The draft-response skill generates **customer-facing response drafts** based on triage output, policy lookups, and order data. It produces a well-structured, empathetic, compliant draft that a human agent reviews and approves before sending.

This skill **never sends email directly.** All drafts are queued for human approval. The `send_email` permission is `human_approval_required` and this skill respects that boundary absolutely.

---

## 2. Trigger

- A triaged ticket with priority P2, P3, or P4 has been routed to tier-1 or tier-2.
- The `auto_reply_suppressed` flag on the triage output is `false`.
- A human agent or upstream workflow requests a draft for a specific ticket.
- A re-draft is requested after the human reviewer provides feedback.

**Does NOT trigger for P1 tickets.** P1 tickets go to `escalate-risk` and are handled by the medical-review or escalation queue.

---

## 3. Required Inputs

| Field | Type | Required | Description |
|---|---|---|---|
| `triage_output` | object | Yes | The full triage JSON from ticket-triage. |
| `policy_context` | object | No | Output from refund-policy or shipping-policy skills if applicable. |
| `order_data` | object | No | Shopify order details if available. |
| `kb_article` | object | No | Knowledge base article relevant to the customer's question. |
| `thread_history` | array | No | Previous messages for conversation continuity. |
| `human_feedback` | string | No | Feedback from a previous draft rejection, for re-drafting. |
| `language` | string | No | Response language. Defaults to `en` (English). |

---

## 4. Decision Framework

### 4.1 Tone Selection

The default and only approved tone is **`warm_professional`**:

| Attribute | Guideline |
|---|---|
| Warmth | Acknowledge the customer's feelings. Use empathetic language ("I understand," "I'm sorry to hear that"). |
| Professionalism | Clear, concise, no slang, no emoji in formal responses (emoji allowed in chat if customer used them first). |
| Clarity | Plain language. Avoid jargon unless the customer uses it. |
| Brevity | Aim for 150–250 words for standard responses. Max 400 words. |
| Ownership | Use "I" and "we" — never "they" or "the system." Take responsibility. |

### 4.2 Response Structure (Acknowledge → Answer → Help → Close)

Every draft follows this four-part structure:

1. **Acknowledge** (1–2 sentences)
   - Validate the customer's experience.
   - Reference the specific issue.
   - Example: "Hi Sarah, thank you for reaching out. I'm sorry to hear your GlowSkin device isn't holding a charge."

2. **Answer** (2–4 sentences)
   - Directly address the question or concern.
   - Provide the specific information requested (order status, refund status, usage instructions).
   - If the answer requires policy context, state the policy clearly and simply.

3. **Help** (1–3 sentences)
   - Offer the next step or additional assistance.
   - Include relevant links, instructions, or options.
   - Example: "I've initiated a return label for you. You'll receive it via email within 24 hours."

4. **Close** (1 sentence)
   - Warm sign-off.
   - Example: "If you have any other questions, I'm here to help. — Alex, Customer Support Team"

### 4.3 Priority-Based Drafting Rules

| Priority | Tone Adjustment | Structure Adjustment | Approval Path |
|---|---|---|---|
| P2 | Heightened empathy. Acknowledge frustration explicitly. | Add a "what we're doing" paragraph before Help. | Tier-2 agent + support lead co-approval |
| P3 | Standard warm-professional. | Standard 4-part structure. | Tier-1 agent approval |
| P4 | Friendly, brief. | Can compress Acknowledge+Answer. | Tier-1 agent approval |

### 4.4 Medical-Compliance Boundary Rules

When the ticket involves any health, medical, or device-on-skin context (even if not P1):

1. **Never claim the device cures, fixes, treats, heals, or prevents any condition.**
2. **Never guarantee results.** Use "may help with" not "will fix."
3. **Never provide medical advice.** Direct customers to consult a healthcare professional.
4. **Never minimize reported symptoms.** Always validate and escalate if needed.
5. **Never blame the customer** for adverse reactions.
6. **Include safety disclaimer** when discussing device use on skin: "If you experience any discomfort or adverse reaction, please discontinue use and consult a healthcare professional."

---

## 5. Tool Usage

| Tool | When | Purpose |
|---|---|---|
| `kb.search` | Product usage, warranty, or policy questions | Retrieve accurate product information and official guidance. |
| `shopify.read_orders` | Order-status or refund-return tickets | Get order details, shipping status, item information. |
| `refund-policy` | Refund-return tickets | Get region-specific refund policy and eligibility. |
| `shipping-policy` | Order-status tickets | Get shipping options, tracking info, and carrier details. |
| `gmail.draft` | After draft text is finalized | Save the draft in Gmail for human review. **Never send.** |

**Sequencing:** Always gather all context (order data, policy, KB articles) BEFORE drafting. Do not draft based on assumptions.

---

## 6. Output Contract

```json
{
  "draft_id": "draft_<timestamp>_<message_id>",
  "triage_id": "triage_20260702_002",
  "to": "customer@example.com",
  "subject": "Re: Return request for order #10245",
  "body": "Hi Sarah,\n\nThank you for reaching out...",
  "tone": "warm_professional",
  "structure": ["acknowledge", "answer", "help", "close"],
  "word_count": 187,
  "medical_disclaimer_included": false,
  "compliance_checked": true,
  "forbidden_phrases_scan": "passed",
  "approval_required_from": "tier-1",
  "status": "pending_human_approval"
}
```

| Field | Type | Constraints |
|---|---|---|
| `body` | string | The full email body. Plain text. No HTML. |
| `word_count` | integer | Must be between 50 and 400. |
| `medical_disclaimer_included` | boolean | Must be `true` if ticket touches health/skin/device-on-body topics. |
| `forbidden_phrases_scan` | string | Must be `"passed"`. If `"failed"`, draft is rejected and not queued. |
| `status` | string | Always `"pending_human_approval"`. Never `"sent"`. |

---

## 7. Risk Boundaries

### 7.1 Forbidden Phrases

The following phrases must **never** appear in any draft response:

| Category | Forbidden Phrase | Why | Safe Alternative |
|---|---|---|---|
| Medical | "cure" / "cures" / "cured" | Implies medical treatment | "may help support" |
| Medical | "treat" / "treats" / "treated" (in health context) | Implies medical treatment | "designed for" |
| Medical | "heal" / "heals" / "healed" | Implies medical outcome | "support your skin's natural process" |
| Medical | "guarantee" / "guaranteed results" | Cannot guarantee outcomes | "designed to" / "formulated to" |
| Medical | "side effects are normal" | Minimizes adverse reactions | "If you experience discomfort, please discontinue use and consult a healthcare professional" |
| Medical | "this happens to everyone" | Dismissive | "I understand your concern" |
| Dismissive | "that's just how it works" | Dismissive | "Let me explain how the device functions" |
| Dismissive | "there's nothing we can do" | Definitive refusal | "Let me explore what options are available" |
| Legal | "we are not responsible for" | Admits/denies liability inappropriately | Use policy language from refund/shipping skills |
| Legal | "you should have read the terms" | Blames customer | "As noted in our policy..." |
| Tone | "obviously" / "clearly" / "as you should know" | Condescending | Omit or rephrase |
| Tone | "per my last email" / "as previously stated" | Passive-aggressive | "To recap our earlier conversation" |
| Commitment | "I promise" / "I guarantee personally" | Over-commits | "I'll do my best to" |
| Commitment | "you will definitely receive" | Over-commits | "You should receive" |

### 7.2 Additional Boundaries

1. **Never send email directly.** Draft only. The `gmail.draft` tool saves to drafts; `gmail.send` is never called.
2. **Never provide tracking numbers unless verified via Shopify.** Do not guess or fabricate.
3. **Never quote refund amounts unless calculated via refund-policy skill.**
4. **Never reference internal systems, ticket IDs, or agent names** unless the customer already knows them.
5. **Never include personal opinions about products.**
6. **Language matching:** If the customer writes in French, draft in French (if language capability exists). Otherwise, draft in English and note `language_mismatch: true`.

---

## 8. Examples

### Example 1: P3 — Order Status

**Input (triage output):**
```json
{
  "category": "order-status",
  "priority": "P3",
  "routing": "tier-1",
  "summary": "Customer asks where their order is. Order #10247 shipped 3 days ago via UPS."
}
```

**Draft output:**
```
Subject: Re: Where is my order?

Hi Michael,

Thank you for reaching out about your order! I completely understand wanting to know exactly when to expect your package.

Your order #10247 shipped on June 30th via UPS Ground, and the estimated delivery date is July 5th. You can track your package anytime using this link: [UPS Tracking Link]. Your tracking number is 1Z999AA10123456784.

If you don't see the package by July 6th, please let me know and I'll look into it right away.

Thanks for your patience, and please reach out if you have any other questions!

— Alex, Customer Support Team
```

### Example 2: P2 — Refund Dispute

**Input (triage output + policy context):**
```json
{
  "category": "refund-return",
  "priority": "P2",
  "routing": "tier-2",
  "summary": "Customer wants refund after 35 days, past US 30-day window. Threatening chargeback.",
  "policy_context": {
    "region": "US",
    "return_window_days": 30,
    "days_since_purchase": 35,
    "eligible_for_refund": false,
    "exception_possible": true
  }
}
```

**Draft output:**
```
Subject: Re: Refund request for order #10246

Hi Jennifer,

I understand your frustration, and I want to thank you for reaching out to us directly rather than pursuing other options. I've reviewed your order and your concerns carefully.

Our standard return window is 30 days from the delivery date, and your order was delivered 35 days ago. While this places your request outside our standard window, I want to find a solution that works for you. I've submitted a review request to our support lead who can evaluate exceptions on a case-by-case basis. You can expect to hear back from us within 48 hours with a decision.

In the meantime, if you'd like to share any additional details about your experience with the product, it would help us review your request more thoroughly.

Thank you for your patience, and I'm committed to helping resolve this for you.

— Alex, Customer Support Team
```

**Note:** This draft includes `human_review_required: true` flag for tier-2 + support lead co-approval.

### Example 3: P3 — Product Usage with Medical Disclaimer

**Input (triage output + KB article):**
```json
{
  "category": "product-usage",
  "priority": "P3",
  "routing": "tier-1",
  "summary": "Customer asks how to use GlowSkin device on sensitive skin."
}
```

**Draft output:**
```
Subject: Re: How to use GlowSkin on sensitive skin

Hi Emma,

Thank you for your question! I'm happy to help you get the most out of your GlowSkin device.

For sensitive skin, we recommend starting with the lowest intensity setting (Level 1) and using the device for no more than 5 minutes per session, 2-3 times per week. Always cleanse your skin before use and apply the provided conductive gel in a thin, even layer. You can gradually increase the intensity as your skin adjusts.

If you experience any discomfort, redness, or irritation, please discontinue use immediately and consult a healthcare professional. Your skin's health comes first.

I've also included a link to our full usage guide here: [KB Link]. It includes a sensitive skin routine and FAQs.

Let me know if you have any other questions — I'm here to help!

— Alex, Customer Support Team
```

### Example 4: P4 — General Feedback

**Input (triage output):**
```json
{
  "category": "product-usage",
  "priority": "P4",
  "routing": "tier-1",
  "summary": "Customer suggests adding a battery indicator light to future models."
}
```

**Draft output:**
```
Subject: Re: Product suggestion

Hi David,

Thank you so much for taking the time to share this suggestion! A battery indicator light is a great idea, and I've forwarded your feedback to our product development team for consideration in future iterations.

We genuinely value input from our customers — it helps us build better products.

Thanks again, and please don't hesitate to reach out anytime!

— Alex, Customer Support Team
```

---

## 9. Evaluation Cases

| Case ID | Scenario | Key Check |
|---|---|---|
| DRF-001 | P3 order status, order shipped | Tracking number included, correct carrier, 4-part structure |
| DRF-002 | P2 refund dispute, past return window | Empathy for frustration, no "refund denied," exception language, human review flag |
| DRF-003 | P3 product usage on skin | Medical disclaimer present, no "cure"/"heal"/"guarantee" |
| DRF-004 | P3 warranty claim, defective device | Acknowledges defect, provides RMA instructions, no blame on customer |
| DRF-005 | P4 general feedback | Brief, appreciative, forwarded to product team |
| DRF-006 | P2 compliance question (GDPR) | No legal advice given, routes to escalation, acknowledges concern |
| DRF-007 | P3 billing double charge | Acknowledges error, explains correction process, no "our system did X" |
| DRF-008 | P3 shipping delay, EU customer | Customs disclaimer, updated ETA, empathy for delay |

---

## 10. Failure Modes

| Failure Mode | Description | Mitigation |
|---|---|---|
| **Medical non-compliance** | Draft contains "cure," "heal," "guarantee," or provides medical advice. | Automated forbidden-phrase scan before queuing. Draft rejected if scan fails. |
| **Over-promising** | Draft commits to outcomes the company can't guarantee ("you'll get your refund by Friday"). | Use hedging language ("you should receive," "typically within"). Human reviewer checks commitments. |
| **Tone mismatch** | Draft is too formal for a casual inquiry or too casual for a serious complaint. | Priority-based tone rules. Human reviewer can request re-draft with `human_feedback`. |
| **Missing context** | Draft references wrong order, wrong product, or outdated policy. | All context (order data, policy, KB) must be gathered before drafting. Validation step checks that referenced order numbers exist. |
| **Length violations** | Draft is too long (rambling) or too short (dismissive). | Word count constraint 50–400. Auto-reject if outside range. |
| **Premature sending** | Draft is sent without human approval. | System-level enforcement: `send_email` permission is `human_approval_required`. This skill only calls `gmail.draft`, never `gmail.send`. |
| **Language mismatch** | Customer writes in French, draft is in English. | Language detection on input. If translation capability exists, match language. Otherwise, flag `language_mismatch: true` for human reviewer. |
| **Thread discontinuity** | Draft doesn't reference previous conversation, making the customer repeat themselves. | Always include `thread_history` in input. Acknowledge prior interactions in the Acknowledge section. |
