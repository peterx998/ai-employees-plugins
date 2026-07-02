---
name: eval:grayscale-release
description: Manage grayscale release stages for an agent update
argument-hint: "<agent_name> [--stage 0|1|2|3|4|5] [--action promote|hold|rollback]"
required_connectors: []
risk_level: high
human_review: always
---

## Inputs

| Field | Required | Description |
|-------|----------|-------------|
| agent_name | Yes | Agent to manage release for |
| stage | No | Target stage (0-5) |
| action | Yes | promote, hold, or rollback |

## Steps

1. Load current feature flag state from agent-evaluation/release/feature_flags.yaml
2. Validate action:
   - promote: Check if current stage metrics meet promotion criteria
   - hold: Pause at current stage
   - rollback: Revert to previous stable version
3. For promote, check gate criteria:
   - Stage 0→1: Golden set PASS (100%)
   - Stage 1→2: Internal testing, 0 critical errors
   - Stage 2→3: 10% traffic, human review pass rate ≥90%
   - Stage 3→4: 50% traffic, complaint rate ≤ baseline
   - Stage 4→5: 80% traffic, all metrics stable for 48h
4. Update feature_flags.yaml with new stage
5. Log stage transition with timestamp and metrics snapshot

## Output

```json
{
  "agent": "customer-support",
  "previous_stage": 2,
  "new_stage": 3,
  "action": "promote",
  "gate_check": {
    "golden_set_pass_rate": 1.0,
    "human_review_pass_rate": 0.92,
    "complaint_delta": "-5%",
    "verdict": "PASS"
  },
  "traffic_percentage": 10,
  "feature_flag_updated": true,
  "human_review_required": true
}
```

## Risk Boundaries

- Stage promotion always requires human approval.
- Rollback can be triggered automatically by monitoring (see rollback_playbook.md).
- Never skip stages. No exceptions even under time pressure.

## Failure Modes

| Failure | Cause | Fix |
|---------|-------|-----|
| Gate check bypassed | Feature flag edited manually | Enforce programmatic gate check in CI |
| Traffic split misconfigured | Feature flag syntax error | Validate YAML schema before applying |
