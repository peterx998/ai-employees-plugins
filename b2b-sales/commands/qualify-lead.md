---
name: b2b:qualify-lead
description: Qualify a B2B lead by buyer type, order volume, and fit score
argument-hint: "<inquiry_text> [--company <name>]"
required_connectors: []
risk_level: low
human_review: recommended
output_schema: "schemas/b2b-sales/b2b_lead.schema.json"
---

## Inputs

| Field | Required | Description |
|-------|----------|-------------|
| inquiry_text | Yes | The B2B inquiry email or form submission |
| company | No | Company name if provided |
| contact_email | Yes | Contact email for the lead |

## Steps

1. Parse inquiry text for key signals:
   - Buyer type: retail, clinic, distributor, procurement, drop-shipper
   - Product interest (which device model, quantity)
   - Budget indicators (MOQ mention, price inquiry)
   - Urgency (timeline, deadline)
   - Certification awareness (FDA, CE, ISO)
2. Score lead (0-100) based on:
   - Fit: buyer type matches distribution strategy
   - Volume: MOQ meets minimum (50+ units for distributor, 10+ for clinic)
   - Authority: decision-maker vs researcher
   - Budget: explicit budget or price discussion
   - Timeline: clear purchase timeline
3. Classify: hot / warm / cold / unqualified
4. Recommend next action: immediate-quote / send-catalog / nurture / decline

## Output

```json
{
  "lead_id": "LEAD-2026-001",
  "company": "Glow Clinic Chain",
  "contact": "buyer@glowclinic.com",
  "buyer_type": "clinic",
  "moq_indicated": 25,
  "pricing_tier": "clinic-bulk",
  "lead_score": 78,
  "classification": "hot",
  "recommendation": "immediate-quote",
  "human_review_recommended": true
}
```

## Risk Boundaries

- Do not quote prices directly. Lead qualification only.
- High-value leads ($10K+ potential) must go to human sales rep.

## Failure Modes

| Failure | Cause | Fix |
|---------|-------|-----|
| Consumer misclassified as B2B | Personal email with product question | Check email domain and inquiry signals |
| Lead score inflated | No budget verification | Discount score if no budget signal present |
