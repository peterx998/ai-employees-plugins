# Rollback Playbook

## Overview

This playbook defines the step-by-step procedure for rolling back an AI agent update when issues are detected during grayscale release or production.

## When to Rollback

### Automatic Triggers
- Human review pass rate drops >10% from baseline
- Customer complaint rate increases >20% from baseline
- Critical error: agent gives medical advice or misses P1 escalation
- Escalation bypass detected (agent auto-replies to P1/P2 case)
- 3+ regression test cases fail post-release

### Manual Triggers
- Support team reports pattern of incorrect responses
- Compliance team flags regulatory risk
- Engineering discovers data corruption or tool failure

## Rollback Procedure

### Step 1: Detect & Confirm (within 5 minutes)
```text
1. Alert triggered by monitoring or reported by team
2. Confirm the issue is caused by the new agent version (not external)
3. Assign incident commander (on-call support lead)
4. Log incident in #incident-response channel
```

### Step 2: Execute Rollback (within 15 minutes)
```text
1. Switch feature flag to previous version:
   - Edit agent-evaluation/release/feature_flags.yaml
   - Set version to previous stable version
   - Set rollout stage to "0 — Internal"

2. If using traffic routing:
   - Route 100% traffic to previous version
   - Stop all traffic to new version

3. Verify rollback:
   - Run Golden Set against previous version → must PASS
   - Check live monitoring → complaint rate returning to baseline
   - Confirm no new auto-replies from the failed version
```

### Step 3: Notify (within 30 minutes)
```text
1. Notify support team: "Agent [name] rolled back to v[old] due to [reason]"
2. Notify affected customers if any were impacted:
   - Draft apology + correction for any wrong advice given
   - Human review any responses sent by the failed version
3. Log timeline: what happened, when, impact, actions taken
```

### Step 4: Preserve Evidence (within 1 hour)
```text
1. Save all agent outputs from the failed version to:
   reports/incidents/[date]_[agent]_[version]/
2. Export monitoring metrics for the incident window
3. Capture any customer complaints related to the issue
4. Save the feature flag state history
```

### Step 5: Root Cause Analysis (within 24 hours)
```text
1. Run /eval:error-review on failed cases
2. Classify error type (7-type taxonomy)
3. Identify root cause (not just symptom)
4. Document in incident review template
5. Add failed cases as new Golden Set cases
```

### Step 6: Fix & Re-test (within 3 days)
```text
1. Apply fix to SKILL.md / prompt / knowledge base
2. Run full regression test
3. If regression passes: restart grayscale from Stage 0
4. If regression fails: repeat fix cycle
5. Do NOT skip grayscale stages even under time pressure
```

### Step 7: Re-release
```text
1. Re-run full Golden Set → must PASS (100%)
2. Start grayscale from Stage 0 (internal)
3. Monitor extra closely for first 48 hours
4. Document lessons learned in incident review
```

## Rollback Authority

| Role | Can Trigger Rollback |
|------|----------------------|
| On-call support lead | ✅ Yes — immediate |
| Engineering on-call | ✅ Yes — immediate |
| Support agent (human) | ⚠️ Request to on-call |
| Automated monitoring | ✅ Yes — automatic |

## Post-Incident Checklist

- [ ] Rollback executed and verified
- [ ] All affected customers identified and contacted
- [ ] Evidence preserved (outputs, metrics, logs)
- [ ] Root cause analysis completed
- [ ] New Golden Set cases added from incident
- [ ] Fix applied and regression tested
- [ ] Incident review document completed
- [ ] Team retrospective held
- [ ] Prevention measures implemented
