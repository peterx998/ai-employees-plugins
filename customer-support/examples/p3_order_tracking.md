# Example Walk-Through: P3 Order Tracking

## Overview

This walk-through demonstrates the complete flow when a customer asks about the status of their order. It covers triage, Shopify order lookup, tracking status explanation, and draft response. This is a routine P3 ticket with no escalation triggers.

---

## Customer Message

> **From:** michael.brown@example.com
> **Subject:** Where is my order??
> **Date:** July 2, 2026, 9:00 AM ET
>
> Hey, I placed an order a week ago and still haven't gotten a tracking number. Can someone tell me where my package is? Order number is 10247.

---

## Step 1: Ticket Triage

### Input to ticket-triage

```json
{
  "message": "Hey, I placed an order a week ago and still haven't gotten a tracking number. Can someone tell me where my package is? Order number is 10247.",
  "region": "US",
  "customer_email": "michael.brown@example.com",
  "order_number": "10247"
}
```

### Triage Output

```json
{
  "triage_id": "triage_20260702_010",
  "timestamp": "2026-07-02T09:05:00Z",
  "message_id": "msg_ghi789",
  "category": "order-status",
  "priority": "P3",
  "routing": "tier-1",
  "auto_reply_suppressed": false,
  "region": "US",
  "order_number": "10247",
  "detected_keywords": ["where is my package", "tracking number"],
  "summary": "US customer requests order status for order #10247. Says it's been a week with no tracking number. Routine order-status inquiry.",
  "confidence": 0.94,
  "flags": [],
  "suggested_skills": ["shipping-policy", "draft-response"]
}
```

### Why P3 / order-status?

The message is a straightforward order status inquiry — "where is my package" and "tracking number" are clear order-status keywords. No medical indicators, no dispute language, no compliance triggers. Standard P3 priority, tier-1 routing.

---

## Step 2: Shopify Order Lookup

### Shopify API Response (via shopify.read_orders connector)

```json
{
  "order_number": "10247",
  "customer_email": "michael.brown@example.com",
  "purchase_date": "2026-06-25",
  "fulfillment_status": "fulfilled",
  "shipping_method": "Ground",
  "carrier": "UPS",
  "tracking_number": "1Z999AA10123456784",
  "shipped_date": "2026-06-30",
  "shipping_address": {
    "city": "Austin",
    "state": "TX",
    "country": "US",
    "region": "US"
  },
  "items": [
    {
      "sku": "GLOW-SKIN-01",
      "name": "GlowSkin Facial Device",
      "quantity": 1,
      "price": 149.00
    }
  ],
  "total": 149.00,
  "currency": "USD",
  "shipping_cost": 0.00,
  "estimated_delivery": "2026-07-05"
}
```

### Key Findings

- The order was placed on June 25 and **shipped on June 30** (5 days after purchase — within normal processing time).
- A tracking number **was generated** (1Z999AA10123456784) but the customer says they didn't receive it. This may indicate a missed shipping notification email.
- The package is currently in transit via UPS Ground with an estimated delivery of July 5.
- The customer said "a week ago" but the order was placed 7 days ago and shipped only 2 days ago. The perception of delay is due to the 5-day processing time before shipping.

---

## Step 3: Shipping Policy Context

### Input to shipping-policy

```json
{
  "triage_output": { "...": "see above" },
  "region": "US",
  "order_number": "10247",
  "order_data": { "...": "see Shopify response above" },
  "tracking_number": "1Z999AA10123456784",
  "message": "Hey, I placed an order a week ago and still haven't gotten a tracking number..."
}
```

### Shipping Policy Output

```json
{
  "shipping_id": "shp_20260702_10247",
  "order_number": "10247",
  "region": "US",
  "carrier": "UPS",
  "shipping_method": "Ground",
  "tracking_number": "1Z999AA10123456784",
  "tracking_url": "https://www.ups.com/track?tracknum=1Z999AA10123456784",
  "tracking_status": "In Transit",
  "last_update": "2026-07-01T08:15:00Z",
  "last_location": "Louisville, KY, US",
  "estimated_delivery": "2026-07-05",
  "shipped_date": "2026-06-30",
  "shipping_cost_paid": 0.00,
  "customs_info": {
    "applicable": false,
    "duties_owed": 0,
    "ddp": false
  },
  "status_meaning": "Your package is moving through the UPS network and is on schedule for delivery by July 5th.",
  "action_needed": "none",
  "customer_instructions": "Track your package anytime at the UPS link. Your delivery is estimated for July 5th.",
  "issue_flag": null,
  "process_steps": null
}
```

### Tracking Status Interpretation

The tracking status is `In Transit` with the last scan in Louisville, KY. This is normal for UPS Ground — the package left the warehouse, passed through a major UPS hub, and is en route to Austin, TX. No exceptions, no delays, no customs issues. The package is on schedule.

The customer's concern ("no tracking number") is likely because the shipping notification email was missed or went to spam. The tracking number exists and is active.

---

## Step 4: Draft Response

### Input to draft-response

```json
{
  "triage_output": {
    "priority": "P3",
    "category": "order-status",
    "routing": "tier-1"
  },
  "policy_context": {
    "shipping_id": "shp_20260702_10247",
    "carrier": "UPS",
    "tracking_number": "1Z999AA10123456784",
    "tracking_url": "https://www.ups.com/track?tracknum=1Z999AA10123456784",
    "tracking_status": "In Transit",
    "estimated_delivery": "2026-07-05",
    "status_meaning": "Your package is moving through the UPS network and is on schedule for delivery by July 5th."
  },
  "order_data": {
    "order_number": "10247",
    "shipped_date": "2026-06-30",
    "items": [{ "name": "GlowSkin Facial Device" }]
  }
}
```

### Draft Output

```json
{
  "draft_id": "draft_20260702_010",
  "triage_id": "triage_20260702_010",
  "to": "michael.brown@example.com",
  "subject": "Re: Where is my order??",
  "body": "Hi Michael,\n\nThank you for reaching out about your order! I completely understand wanting to know exactly when to expect your package.\n\nYour order #10247 shipped on June 30th via UPS Ground, and the estimated delivery date is July 5th. You can track your package anytime using this link: https://www.ups.com/track?tracknum=1Z999AA10123456784. Your tracking number is 1Z999AA10123456784.\n\nIt looks like the shipping confirmation email with your tracking number may have ended up in your spam folder — I'd recommend checking there just in case. I've also included it here so you have it handy.\n\nIf you don't see the package by July 6th, please let me know and I'll look into it right away.\n\nThanks for your patience, and please reach out if you have any other questions!\n\n— Alex, Customer Support Team",
  "tone": "warm_professional",
  "structure": ["acknowledge", "answer", "help", "close"],
  "word_count": 139,
  "medical_disclaimer_included": false,
  "compliance_checked": true,
  "forbidden_phrases_scan": "passed",
  "approval_required_from": "tier-1",
  "status": "pending_human_approval"
}
```

### Draft Analysis

| Check | Result | Notes |
|---|---|---|
| Acknowledge | ✅ | "Thank you for reaching out" + "I completely understand wanting to know" |
| Answer | ✅ | Shipping date, carrier, tracking number, estimated delivery — all from verified Shopify data |
| Help | ✅ | Tracking link provided, spam folder suggestion, follow-up offer if not received by July 6th |
| Close | ✅ | "Thanks for your patience" + "reach out if you have any other questions" |
| Forbidden phrases | ✅ Passed | No "obviously," no "as you should know," no blaming customer |
| Tracking verified | ✅ | Number from Shopify, not fabricated |
| Word count | ✅ | 139 words (within 50–400 range) |
| Approval path | ✅ | Tier-1 agent approval (standard for P3) |

### Why This Draft Works

1. **Provides all information upfront:** The customer gets the tracking number, carrier, link, and estimated delivery in one response — no back-and-forth needed.

2. **Explains the missing notification:** The spam folder suggestion is a helpful, non-accusatory explanation for why the customer didn't receive the tracking number. It doesn't blame the customer or the system.

3. **Sets a clear follow-up trigger:** "If you don't see the package by July 6th" gives the customer a specific action point. This prevents premature "where is my package" follow-ups while still offering help if there's a real delay.

4. **Verifies all data:** The tracking number, shipping date, and delivery estimate all come from the Shopify API response — nothing is guessed or fabricated.

5. **Appropriate tone:** Friendly, helpful, not overly formal. Matches the customer's casual tone ("Hey") while maintaining professionalism.

---

## Step 5: Human Review and Send

### Tier-1 Agent Review

The tier-1 agent reviews the draft and checks:

- [x] Tracking number matches Shopify order data
- [x] Estimated delivery date is correct
- [x] No forbidden phrases
- [x] Tone is appropriate
- [x] No medical or compliance concerns
- [x] No over-promises

### Decision: Approve and Send

The agent approves the draft. The email is sent to michael.brown@example.com.

---

## Summary

| Step | Skill | Key Decision | Outcome |
|---|---|---|---|
| Triage | ticket-triage | P3, order-status, tier-1 routing | Standard inquiry, no escalation |
| Order lookup | shopify.read_orders | Order fulfilled, shipped June 30, tracking exists | Package in transit, on schedule |
| Shipping context | shipping-policy | In Transit, no issues, ETA July 5 | No action needed beyond providing info |
| Draft response | draft-response | Full tracking info + spam folder suggestion | Draft pending tier-1 approval |
| Human review | (manual) | Agent verifies data and approves | Email sent to customer |

### Timeline

| Time | Event |
|---|---|
| 9:00 AM | Customer sends message |
| 9:05 AM | Triage completes (P3, order-status) |
| 9:06 AM | Shopify order lookup completes |
| 9:07 AM | Shipping policy context assembled |
| 9:08 AM | Draft response generated |
| 9:15 AM | Tier-1 agent reviews and approves draft |
| 9:16 AM | Email sent to customer |
| **Total** | **~16 minutes from customer message to response sent** |
