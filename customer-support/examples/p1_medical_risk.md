# Example Walk-Through: P1 Medical Risk

## Overview

This walk-through demonstrates the complete flow when a customer reports an adverse skin reaction (irritation and bleeding) after using a device. It covers triage, escalation package generation, and auto-reply suppression.

---

## Customer Message

> **From:** jane.doe@example.com
> **Subject:** Is this normal??
> **Date:** July 2, 2026, 2:15 PM ET
>
> I've been using the GlowSkin device for a week and now my face is red, burning, and I noticed some bleeding around my chin area. Is this normal? I'm really worried.

---

## Step 1: Ticket Triage

### Input to ticket-triage

```json
{
  "message": "I've been using the GlowSkin device for a week and now my face is red, burning, and I noticed some bleeding around my chin area. Is this normal? I'm really worried.",
  "region": "US",
  "customer_email": "jane.doe@example.com",
  "thread_history": []
}
```

### Triage Output

```json
{
  "triage_id": "triage_20260702_001",
  "timestamp": "2026-07-02T14:30:00Z",
  "message_id": "msg_abc123",
  "category": "medical-risk",
  "priority": "P1",
  "routing": "medical-review",
  "auto_reply_suppressed": true,
  "region": "US",
  "order_number": null,
  "detected_keywords": ["red", "burning", "bleeding"],
  "summary": "Customer reports facial redness, burning sensation, and bleeding after one week of GlowSkin device use. Potential adverse skin reaction requiring immediate medical review.",
  "confidence": 0.96,
  "flags": ["medical-risk", "auto-reply-suppressed"],
  "suggested_skills": ["escalate-risk"]
}
```

### Why P1 / medical-risk?

The triage skill detected three medical-risk indicators from its keyword list:

1. **"red"** → Skin irritation / redness indicator
2. **"burning"** → Burning sensation indicator
3. **"bleeding"** → Bleeding indicator (automatic P1 trigger)

Per the priority framework, **any medical-risk indicator forces P1 classification** regardless of other content. The presence of "bleeding" alone is sufficient for P1. The combination of red + burning + bleeding creates a high-confidence (0.96) medical-risk classification.

Routing is set to `medical-review` — the dedicated queue for adverse reaction review by trained specialists.

---

## Step 2: Escalation Package

### Input to escalate-risk

```json
{
  "trigger_type": "medical-risk",
  "triage_output": { "...": "see above" },
  "message": "I've been using the GlowSkin device for a week and now my face is red, burning, and I noticed some bleeding around my chin area. Is this normal? I'm really worried.",
  "customer_email": "jane.doe@example.com",
  "region": "US",
  "order_number": null
}
```

### Escalation Package Output

```json
{
  "escalation_id": "esc_20260702_143000_001",
  "timestamp": "2026-07-02T14:30:00Z",
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
    "order_number": "not_available"
  },
  "triage_summary": "Customer reports facial redness, burning sensation, and bleeding after one week of GlowSkin device use. Potential adverse skin reaction.",
  "message_excerpt": "...my face is red, burning, and I noticed some bleeding around my chin area...",
  "detected_keywords": ["red", "burning", "bleeding"],
  "order_data": {
    "order_number": "not_available",
    "product": "GlowSkin Facial Device (inferred from message)",
    "purchase_date": "not_available"
  },
  "thread_history_count": 1,
  "relevant_kb_articles": ["kb_safety_glowskin", "kb_adverse_reaction_protocol"],
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

### Severity Score Breakdown

| Factor | Points |
|---|---|
| Medical injury reported | +4 |
| Bleeding/open wound | +2 |
| Customer expresses worry ("really worried") | +1 (emotional distress indicator) |
| No hospital/ER visit mentioned | +0 |
| **Total** | **7** → Upgraded to 8 for combined symptom severity |

Severity ≥ 7 triggers **immediate phone/Slack notification** to support_lead in addition to queue routing.

---

## Step 3: Auto-Reply Suppression

### Why was auto-reply suppressed?

Auto-reply suppression is **mandatory** for all P1 tickets. The specific reasons:

1. **Priority P1:** Per the escalation framework, all P1 tickets have `auto_reply_suppressed: true` with no exceptions.

2. **Medical-risk trigger:** The escalation routing matrix specifies that medical-risk triggers always suppress auto-reply. The suppression reason is documented: *"P1 medical-risk: bleeding and burning sensation reported. Auto-reply suppressed. Human medical review required before any customer communication."*

3. **Risk of inappropriate response:** An automated response to a medical-risk ticket could:
   - Minimize the customer's symptoms ("This is normal, don't worry")
   - Provide medical advice the system is not qualified to give
   - Delay escalation by making the customer think their issue is being handled
   - Create legal liability if the response is incorrect

4. **What happens instead:** The escalation package is routed to the medical-review queue. A human agent (or the support_lead) must review the case and approve any communication with the customer. The first human-approved response typically:
   - Acknowledges the customer's concern
   - Advises discontinuing device use
   - Asks follow-up questions about symptom severity and timeline
   - Advises seeking medical attention if symptoms are severe
   - Offers a full refund and product return

### Suppression Enforcement

The suppression is enforced at two levels:

- **Skill level:** `draft-response` is not invoked for this ticket. The triage output's `suggested_skills` array contains only `["escalate-risk"]`, not `["draft-response"]`.
- **System level:** The `send_email` permission is `human_approval_required`. Even if a draft were somehow generated, no email can be sent without explicit human approval.

---

## Step 4: Human Review and Response (Example)

After the medical-review team reviews the escalation package (within 1-hour SLA), a human agent drafts and approves the following response:

> **Subject:** Re: Is this normal??
>
> Hi Jane,
>
> Thank you for reaching out, and I want you to know we take your concerns very seriously.
>
> Based on what you've described — redness, burning, and bleeding — I strongly recommend that you **discontinue use of the GlowSkin device immediately**. These symptoms are not a normal reaction, and your health and safety are our top priority.
>
> I'd like to connect you with our medical review team who can better assess your situation. They may recommend that you consult a healthcare professional, especially given the bleeding you've noticed.
>
> In the meantime, I've processed a full refund for your GlowSkin device — you do not need to return it. The refund will appear on your original payment method within 5-7 business days.
>
> We're also logging this incident in our product safety registry so our product team can investigate further.
>
> Please don't hesitate to reach out if you have any questions or if your symptoms worsen. We're here to support you.
>
> — Dr. Sarah Chen, Medical Review Team

**Note:** This response was drafted by a human agent (not the draft-response skill) because P1 medical-risk tickets bypass the automated drafting pipeline. The response includes:
- ✅ Medical disclaimer (discontinue use, consult healthcare professional)
- ✅ No forbidden phrases (no "cure," "heal," "guarantee," "normal reaction")
- ✅ Empathetic tone with ownership
- ✅ Immediate action (refund processed)
- ✅ Escalation to medical review team
- ✅ Safety documentation

---

## Summary

| Step | Skill | Key Decision | Outcome |
|---|---|---|---|
| Triage | ticket-triage | Category: medical-risk, Priority: P1 | Routed to medical-review, auto-reply suppressed |
| Escalation | escalate-risk | Severity score: 8, immediate notification | Escalation package sent to medical-review + support_lead |
| Auto-reply | escalate-risk | Suppressed (P1 mandatory) | No automated response sent to customer |
| Human response | (manual) | Human agent reviews and responds | Customer contacted within 1 hour with safety guidance and refund |
