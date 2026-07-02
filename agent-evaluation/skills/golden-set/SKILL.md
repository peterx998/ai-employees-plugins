---
name: golden-set
description: Use when building, maintaining, or running a Golden Set test suite for AI agent evaluation. Contains the methodology for creating fixed test cases, scoring rubrics, and pass/fail criteria for each agent type.
user_invocable: true
version: "1.0.0"
tags: [evaluation, golden-set, testing]
---

# Golden Set Testing

## Golden Set Principles
1. **Fixed**: Test cases never change without deliberate versioning
2. **Covered**: Must cover normal, edge, high-risk, and historical error cases
3. **Scored**: Every test has clear pass/fail criteria
4. **Reproducible**: Same input always produces same evaluation

## Minimum Test Sets

### Customer Support (50 cases minimum)
- 10 refund/return | 10 shipping/logistics | 5 medical risk | 5 usage questions
- 5 warranty/defect | 5 policy boundary | 5 multi-language | 5 escalation triggers

### Influencer Outreach (40 cases minimum)
- 10 reply classification | 5 rate negotiation | 5 usage rights | 5 collaboration policy
- 5 ghost/unresponsive | 5 compliance | 5 icebreaker quality

### Ad Creative (30 cases minimum)
- 5 high-risk word detection | 5 medical efficacy claims | 5 before/after imagery
- 5 exaggerated claims | 5 hook quality | 5 CTA compliance

## Scoring Rubric

| Score | Meaning |
|-------|---------|
| 5 | Perfect — exactly expected behavior |
| 4 | Good — correct outcome, minor wording differences |
| 3 | Acceptable — right direction, room for improvement |
| 2 | Poor — partially correct but significant errors |
| 1 | Failed — wrong outcome or harmful response |
