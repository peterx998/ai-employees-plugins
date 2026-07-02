# Example Walk-Through: P2 Refund Dispute

## Overview

This walk-through demonstrates the complete flow when a customer requests a refund 35 days after delivery — past the US 30-day return window — with mild dispute language. It covers triage, policy lookup, draft response with a workaround, and human review flagging.

---

## Customer Message

> **From:** jennifer.smith@example.com
> **Subject:** Refund request — order #10246
> **Date:** July 2, 2026, 10:00 AM ET
>
> Hi, I want a full refund for order #10246. I've had the GlowSkin device for about 5 weeks now and it just doesn't work the way it was described on your website. I've been patient but I'm not satisfied and I'd like my money back. If this isn't resolved I may have to dispute the charge with my credit card company.

---

## Step 1: Ticket Triage

### Input to ticket-triage

```json
{
  "message": "Hi, I want a full refund for order #10246. I've had the GlowSkin device for about 5 weeks now and it just doesn't work the way it was described on your website. I've been patient but I'm not satisfied and I'd like my money back. If this isn't resolved I may have to dispute the charge with my credit card company.",
  "region": "US",
  "customer_email": "jennifer.smith@example.com",
  "order_number": "10246"
}
```

### Triage Output

```json
{
  "triage_id": "triage_20260702_005",
  "timestamp": "2026-07-02T10:05:00Z",
  "message_id": "msg_def456",
  "category": "refund-return",
  "priority": "P2",
  "routing": "tier-2",
  "auto_reply_suppressed": false,
  "region": "US",
  "order_number": "10246",
  "detected_keywords": ["full refund", "doesn't work as described", "dispute the charge"],
  "summary": "Customer requests full refund for order #10246 after ~5 weeks (past 30-day window). Cites product expectations mismatch. Mild chargeback threat present. Dispute language triggers P2 routing to tier-2.",
  "confidence": 0.89,
  "flags": ["chargeback-threat", "dispute-language", "past-return-window"],
  "suggested_skills": ["refund-policy", "draft-response", "escalate-risk"]
}
```

### Why P2 / refund-return?

The message is clearly a refund request, placing it in the `refund-return` category. The priority is elevated to **P2** (instead of the default P3) because:

1. **Dispute language detected:** "dispute the charge with my credit card company" is a chargeback threat — an explicit P2 trigger.
2. **Past return window:** ~5 weeks = ~35 days, which exceeds the US 30-day standard return window, creating a potential conflict scenario.
3. **Product expectations mismatch:** "doesn't work the way it was described" could indicate a misrepresentation claim, which has legal/compliance implications.

Routing is set to `tier-2` (not tier-1) because dispute language and potential chargeback require a more experienced agent.

Auto-reply is **not suppressed** because this is P2 (not P1), and the escalation triggers for full suppression (medical-risk, legal/compliance, safety defect) are not met. However, the draft-response will be flagged for tier-2 + support lead co-approval.

---

## Step 2: Policy Lookup

### Input to refund-policy

```json
{
  "triage_output": { "...": "see above" },
  "region": "US",
  "order_number": "10246",
  "order_data": {
    "order_number": "10246",
    "purchase_date": "2026-05-25",
    "delivery_date": "2026-05-28",
    "items": [
      {
        "sku": "GLOW-SKIN-01",
        "name": "GlowSkin Facial Device",
        "price": 149.00
      }
    ],
    "total": 149.00,
    "currency": "USD"
  },
  "defect_reported": false,
  "message": "Hi, I want a full refund for order #10246..."
}
```

### Policy Output

```json
{
  "policy_id": "pol_20260702_10246",
  "order_number": "10246",
  "region": "US",
  "decision": "eligible_with_exception",
  "decision_reason": "Request is 5 days past the 30-day US standard return window. No membership on file for extended window. Customer cites product expectations mismatch — not a defect. Exception possible with human approval. Chargeback threat present — do not auto-deny.",
  "eligible_for": ["refund", "store_credit"],
  "refund_amount": 149.00,
  "refund_currency": "USD",
  "refund_method": "original_payment",
  "shipping_cost_refund": false,
  "restocking_fee": 0,
  "return_window_days": 30,
  "days_since_delivery": 35,
  "return_label_cost": "pending_exception_approval",
  "refund_processing_time": "5-7 business days post-approval",
  "process_steps": [
    "Submit exception request to support lead for review",
    "Support lead evaluates: purchase history, reason, product condition, chargeback risk",
    "If approved: generate return label and process as standard return",
    "If denied: offer store credit or discount on future purchase as goodwill",
    "Communicate decision to customer within 48 hours"
  ],
  "exception_flag": true,
  "human_review_required": true,
  "notes": "5 days past window. Customer cites expectations mismatch — not defective. Chargeback threat present — prioritize review. Do not auto-deny. Offer exception review and goodwill options."
}
```

### Key Policy Decisions

1. **Not automatically eligible:** 35 days > 30-day US window. No membership on file (which would extend to 45 days).
2. **Not automatically denied:** The refund-policy skill's risk boundary #1 states: *"Never auto-deny a refund without human review if dispute language is present."* The chargeback threat requires human review.
3. **Exception possible:** The `eligible_with_exception` decision means the refund *can* be processed if a human approves it. The skill does not make the final call.
4. **No defect:** The customer says the product "doesn't work as described" but doesn't report a malfunction. This is an expectations mismatch, not a warranty claim.

---

## Step 3: Draft Response

### Input to draft-response

```json
{
  "triage_output": { "priority": "P2", "category": "refund-return", "routing": "tier-2" },
  "policy_context": { "decision": "eligible_with_exception", "human_review_required": true },
  "order_data": { "order_number": "10246", "total": 149.00 }
}
```

### Draft Output

```json
{
  "draft_id": "draft_20260702_005",
  "triage_id": "triage_20260702_005",
  "to": "jennifer.smith@example.com",
  "subject": "Re: Refund request — order #10246",
  "body": "Hi Jennifer,\n\nI understand your frustration, and I want to thank you for reaching out to us directly rather than pursuing other options. I've reviewed your order and your concerns carefully.\n\nOur standard return window is 30 days from the delivery date, and your order was delivered 35 days ago. While this places your request outside our standard window, I want to find a solution that works for you. I've submitted a review request to our support lead who can evaluate exceptions on a case-by-case basis. You can expect to hear back from us within 48 hours with a decision.\n\nIn the meantime, if you'd like to share any additional details about your experience with the product, it would help us review your request more thoroughly.\n\nThank you for your patience, and I'm committed to helping resolve this for you.\n\n— Alex, Customer Support Team",
  "tone": "warm_professional",
  "structure": ["acknowledge", "answer", "help", "close"],
  "word_count": 143,
  "medical_disclaimer_included": false,
  "compliance_checked": true,
  "forbidden_phrases_scan": "passed",
  "approval_required_from": "tier-2",
  "status": "pending_human_approval"
}
```

### Draft Analysis

| Check | Result | Notes |
|---|---|---|
| Acknowledge | ✅ | "I understand your frustration" + "thank you for reaching out directly" |
| Answer | ✅ | Explains 30-day window, states 35 days, doesn't auto-deny |
| Help | ✅ | Submitted exception request to support lead, 48-hour timeline |
| Close | ✅ | "committed to helping resolve this for you" |
| Forbidden phrases | ✅ Passed | No "refund denied," no "too late," no "nothing we can do" |
| Dispute de-escalation | ✅ | Thanks customer for not pursuing chargeback — validates their choice |
| Human review flag | ✅ | `approval_required_from: "tier-2"` + `human_review_required: true` |
| Over-promise check | ✅ | No "I promise" or "you will definitely" — uses "expect to hear back" |

### Why This Draft Works

1. **Doesn't auto-deny:** The draft acknowledges the policy window but immediately offers an exception review path. This prevents the customer from feeling dismissed and reduces chargeback risk.

2. **De-escalates the dispute:** By thanking the customer for "reaching out directly rather than pursuing other options," the agent acknowledges the chargeback threat without confronting it, reinforcing the customer's choice to work with support.

3. **Sets clear expectations:** 48-hour response timeline. No vague "we'll get back to you."

4. **Requests additional context:** Asking for more details about the product experience serves two purposes: (a) gives the support lead more information for the exception decision, and (b) engages the customer in the process, reducing the likelihood of an immediate chargeback.

5. **Human review required:** The draft cannot be sent without tier-2 + support lead approval, ensuring that the exception decision is made by a human with authority.

---

## Step 4: Human Review and Resolution

### Support Lead Review

The support lead reviews the exception request and considers:

| Factor | Assessment |
|---|---|
| Days past window | 5 days (minor overrun) |
| Customer history | First-time customer, no prior returns |
| Reason | Expectations mismatch, not defect |
| Chargeback risk | Moderate — customer mentioned it but hasn't acted |
| Product condition | Unknown — customer hasn't confirmed if device is functional |
| Goodwill value | $149 refund vs. potential chargeback cost ($25 fee + loss) |

### Decision: Approve Exception

The support lead approves the exception with conditions:
- Full refund of $149.00
- Customer must return the device (free return label provided)
- Refund processed within 5-7 business days of warehouse receipt

### Final Response Sent to Customer (Human-Approved)

> Hi Jennifer,
>
> Thank you for your patience. I've reviewed your request and I'm happy to let you know that we've approved an exception to our standard return window for your order.
>
> Here's what happens next:
>
> 1. I've attached a prepaid return label to this email. Please use it to ship the GlowSkin device back to us.
> 2. Once we receive and inspect the device at our warehouse, your refund of $149.00 will be processed to your original payment method within 5-7 business days.
> 3. You'll receive a confirmation email when the refund is processed.
>
> Please ship the device within 14 days of receiving this email. If you have any questions or need assistance, I'm here to help.
>
> Thank you for giving us the opportunity to make this right.
>
> — Maria, Support Lead

---

## Summary

| Step | Skill | Key Decision | Outcome |
|---|---|---|---|
| Triage | ticket-triage | P2, refund-return, chargeback-threat flag | Routed to tier-2 |
| Policy lookup | refund-policy | eligible_with_exception, human_review_required | No auto-deny, exception submitted |
| Draft response | draft-response | Empathetic draft, no forbidden phrases, de-escalation | Pending tier-2 + support lead approval |
| Human review | (manual) | Exception approved with return condition | Full refund approved, return label sent |
| Resolution | (manual) | Customer receives prepaid label, refund upon return | Chargeback prevented, customer retained |
