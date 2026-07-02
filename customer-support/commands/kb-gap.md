---
name: customer-support:kb-gap
description: Record a knowledge base gap when the agent cannot find relevant policy/procedure
argument-hint: "<question> [--suggested_answer <text>]"
required_connectors: ["~~kb"]
risk_level: low
human_review: optional
output_schema: "schemas/customer-support/kb_gap.schema.json"
---

## Inputs

| Field | Required | Description |
|-------|----------|-------------|
| question | Yes | The customer question that couldn't be answered from KB |
| category | No | Ticket category from triage |
| suggested_answer | No | Agent's best-guess answer (to be verified by human) |
| customer_message | No | Original customer message for context |
| frequency | No | Estimated how often this question occurs |

## Steps

1. Check if a KB gap for this question already exists (~~kb → search_kb)
2. If exists, increment frequency count and update last_seen timestamp
3. If new, create a KB gap record:
   - Record the exact customer question
   - Note why the KB couldn't answer it (missing article, outdated policy, ambiguous wording)
   - Capture the agent's suggested answer (if any) for human review
   - Estimate frequency (how often this question type appears)
4. Assign priority for KB update:
   - high → question appears weekly or relates to safety/compliance
   - medium → question appears monthly
   - low — question appears rarely
5. Create as draft page in ~~kb (create_page) for content team to review

## Output

```json
{
  "gap_id": "GAP-2026-001",
  "question": "Can I use the device while pregnant?",
  "why_unanswered": "No KB article covers pregnancy contraindications",
  "suggested_answer": "We recommend consulting your healthcare provider before using any skincare device during pregnancy.",
  "estimated_frequency": "weekly",
  "priority_for_kb_update": "high",
  "kb_draft_page_id": "notion_page_id_if_created"
}
```

## Risk Boundaries

- The suggested_answer is a **draft for human review**, never send to customer directly.
- If the question relates to medical safety, flag priority as "high" regardless of frequency.

## Failure Modes

| Failure | Cause | Fix |
|---------|-------|-----|
| Duplicate gap created | Search didn't match similar existing gap | Improve fuzzy matching in KB search |
| Suggested answer sent to customer | Agent bypassed human review | Enforce: suggested_answer → create_draft only, never send |
