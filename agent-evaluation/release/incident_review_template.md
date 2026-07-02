# Incident Review Template

## Incident Information

| Field | Value |
|-------|-------|
| Incident ID | INC-[YYYY]-[NNN] |
| Date | [YYYY-MM-DD] |
| Time (UTC) | [HH:MM] |
| Severity | Critical / High / Medium / Low |
| Agent | [agent name] |
| Version | [version that caused the issue] |
| Detected by | [monitoring / human reviewer / customer complaint] |
| Incident Commander | [name] |
| Status | Open / Investigating / Resolved / Closed |

---

## Summary

**One-sentence description:**
> [What happened in plain language]

**Impact:**
- Customers affected: [number]
- Cases affected: [number]
- Duration: [time from detection to rollback]
- Severity rationale: [why this severity level]

---

## Timeline

| Time (UTC) | Event |
|------------|-------|
| [HH:MM] | [Event description] |
| [HH:MM] | [Event description] |
| [HH:MM] | Rollback executed |
| [HH:MM] | [Event description] |

---

## Root Cause

### What Happened
[Detailed description of what the agent did wrong]

### Why It Happened
[Root cause — dig deeper than surface symptom]

### System Layer That Failed
- [ ] Knowledge base (missing or incorrect information)
- [ ] Process/SOP (undefined workflow)
- [ ] Prompt/Instructions (unclear or incomplete rules)
- [ ] Tool/API (connector failure or wrong call)
- [ ] Model (hallucination or capability gap)
- [ ] Boundary (escalation trigger missing)
- [ ] Review criteria (human reviewer unclear)

### Error Classification
- **Type:** [Knowledge Gap / Process Undefined / Prompt Unclear / Tool Failure / Model Hallucination / Boundary Unclear / Review Criteria Missing]
- **Root Cause:** [Specific root cause description]

---

## Actions Taken

| Action | Owner | Status | Timestamp |
|--------|-------|--------|-----------|
| Rollback to v[old] | [name] | ✅ Done | [HH:MM] |
| Customer notification | [name] | ✅ Done | [HH:MM] |
| Evidence preserved | [name] | ✅ Done | [HH:MM] |
| Root cause analysis | [name] | 🔄 In Progress | [HH:MM] |
| Fix applied | [name] | ⏳ Pending | — |
| Regression test | [name] | ⏳ Pending | — |

---

## Prevention Measures

### Immediate Fix
- [What was changed to fix the immediate issue]

### Systemic Fix
- [What process/architecture change prevents this class of error]

### Golden Set Case Added
```yaml
- id: [CASE-ID]
  agent: [agent]
  skill: [skill]
  input:
    message: "[the input that triggered the error]"
    region: "[region]"
  expected:
    category: "[correct category]"
    priority: "[correct priority]"
    human_review_required: [true/false]
    forbidden:
      - "[phrase that was incorrectly used]"
  scoring:
    correct_category: 2
    correct_priority: 2
    no_forbidden_phrases: 1
```

---

## Lessons Learned

1. **What went well:** [e.g., monitoring caught it within 5 minutes]
2. **What went wrong:** [e.g., golden set didn't cover this edge case]
3. **What to improve:** [e.g., add more edge case coverage to golden set]

---

## Sign-off

| Role | Name | Date |
|------|------|------|
| Incident Commander | | |
| Agent Owner | | |
| Engineering Lead | | |
