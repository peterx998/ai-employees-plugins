---
name: customer-support:triage
description: Classify a customer support ticket by category, priority, and risk level
argument-hint: "<customer_message> [--region US|CA|MX|EU]"
required_connectors: ["~~email", "~~store"]
risk_level: medium
human_review: required_for_p1_p2
output_schema: "schemas/customer-support/triage_result.schema.json"
---

## Inputs

| Field | Required | Description |
|-------|----------|-------------|
| customer_message | Yes | The raw customer email or chat message |
| region | No | Customer region (default: infer from message) |
| order_id | No | Associated order ID if available |
| thread_history | No | Previous messages in the conversation thread |

## Steps

1. Parse the customer message and extract key entities (order number, product name, concern type)
2. Classify into one of these categories:
   - `refund-return` — Refund requests, return initiation, exchange
   - `shipping-logistics` — Tracking, delivery delays, customs, lost packages
   - `medical-risk` — Skin irritation, adverse reaction, safety questions
   - `product-usage` — How-to questions, needle depth, frequency, maintenance
   - `warranty-defect` — Device malfunction, defective product, warranty claims
   - `policy-question` — Discount stacking, price match, international policy
   - `escalation` — Legal threats, social media threats, regulatory inquiries
3. Assign priority:
   - **P1** — Medical risk, legal threat, regulatory inquiry → immediate escalation
   - **P2** — High-value dispute ($500+), repeated unresolved contact, complaint escalation
   - **P3** — Standard refund, shipping inquiry, product usage question
   - **P4** — General policy question, FAQ-type inquiry
4. Check for risk flags (medical claims, forbidden phrases, escalation triggers)
5. Generate suggested initial response (acknowledgment only, not full resolution)
6. Determine if human review is required (P1/P2 → always required)

## Output

```json
{
  "category": "refund-return|shipping-logistics|medical-risk|product-usage|warranty-defect|policy-question|escalation",
  "priority": "P1|P2|P3|P4",
  "risk_flags": [
    {"type": "medical", "severity": "high", "description": "..."}
  ],
  "route_to": "auto-draft|human-review|immediate-escalation",
  "human_review_required": true,
  "suggested_initial_response": "Thank you for reaching out...",
  "internal_notes": "Customer mentions skin irritation after first use."
}
```

## Risk Boundaries

- **P1 medical-risk**: Always escalate to human immediately. Never draft a medical response.
- **P1 escalation (legal/social/regulatory)**: Suppress auto-reply entirely. Route to support lead.
- **P2 high-value disputes**: Draft must be reviewed before sending.

## Failure Modes

| Failure | Cause | Fix |
|---------|-------|-----|
| Miscategorized medical as product-usage | Agent missed subtle medical language | Add more medical trigger phrases to skill |
| Priority too low for escalation case | Agent didn't detect legal/social threat keywords | Enhance escalation detection rules |
| Auto-drafted response for P1 case | human_review flag not set correctly | Enforce P1 → human_review_required: true at schema level |
