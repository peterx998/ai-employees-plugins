---
name: customer-support:draft-response
description: Draft a compliant customer support reply based on triage result and KB lookup
argument-hint: "<triage_result> [--tone empathetic|professional|friendly]"
required_connectors: ["~~email", "~~kb"]
risk_level: medium
human_review: recommended
output_schema: "schemas/customer-support/draft_response.schema.json"
---

## Inputs

| Field | Required | Description |
|-------|----------|-------------|
| triage_result | Yes | Output from customer-support:triage command |
| customer_message | Yes | Original customer message for context |
| thread_history | No | Previous messages for conversation continuity |
| tone | No | Response tone (default: empathetic) |
| region | No | Customer region for policy-specific responses |

## Steps

1. Load the triage result (category, priority, risk_flags)
2. Query knowledge base (`~~kb`) for relevant policy/procedure:
   - refund-return → refund_policy + return_procedure
   - shipping-logistics → shipping_policy + carrier_tracking
   - product-usage → product_manual + faq
   - warranty-defect → warranty_policy + defect_procedure
3. If KB returns no match → flag as KB gap (use customer-support:kb-gap command)
4. Draft response following tone guide:
   - Acknowledge the customer's concern first
   - Provide accurate policy/procedure information
   - Include next steps or timeline
   - Close with appropriate sign-off
5. Run compliance checks:
   - No medical claims (cure, fix, treat, heal)
   - No guaranteed results
   - No forbidden phrases (see skills/compliance-boundary/SKILL.md)
6. Set send_ready flag:
   - P3/P4 → send_ready: true (but still recommended for human review)
   - P1/P2 → send_ready: false (human review required)
7. Create as Gmail draft (~~email → create_draft), do NOT send

## Output

```json
{
  "draft_text": "Dear [Customer],\n\nThank you for reaching out...",
  "subject": "Re: Your inquiry about [topic]",
  "tone": "empathetic",
  "language": "en",
  "compliance_checks": {
    "medical_claims": false,
    "guaranteed_results": false,
    "forbidden_phrases": []
  },
  "human_review_required": true,
  "send_ready": false,
  "draft_id": "gmail_draft_id_if_created"
}
```

## Risk Boundaries

- Never auto-send. Drafts go to `~~email → create_draft` only.
- If triage priority is P1, refuse to draft and return escalation notice.
- If compliance check fails, return error with specific violations.

## Failure Modes

| Failure | Cause | Fix |
|---------|-------|-----|
| Draft contains medical claim | KB article had medical language | Clean KB article + add compliance check |
| Wrong policy for region | KB didn't filter by region | Add region parameter to KB query |
| Tone too formal for upset customer | Default tone not adapted | Use thread sentiment to adjust tone |
