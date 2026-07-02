# Customer Support Autoresearch Program

## Goal

Improve customer-support skills (ticket-triage, draft-response) on the Golden Set without violating policy boundaries. Agent proposes small edits to SKILL.md / command files, runs evaluation, keeps improvements, discards regressions.

## Architecture (adapted from karpathy/autoresearch)

```text
prepare.py  →  policies/ + schemas/ + connectors/     (READ-ONLY, never modified)
train.py    →  skills/*/SKILL.md + commands/*.md       (AGENT EDITS THIS)
program.md  →  this file                                (HUMAN EDITS THIS)
results.tsv →  experiments/customer-support-results.tsv (AGENT LOGS HERE)
```

## Editable Files (Agent's "train.py")

Agent MAY modify these files:

- `customer-support/skills/ticket-triage/SKILL.md`
- `customer-support/skills/draft-response/SKILL.md`
- `customer-support/skills/refund-policy/SKILL.md`
- `customer-support/skills/shipping-policy/SKILL.md`
- `customer-support/skills/compliance-boundary/SKILL.md`
- `customer-support/skills/escalation-rules/SKILL.md`
- `customer-support/skills/tone-guide/SKILL.md`
- `customer-support/commands/triage.md`
- `customer-support/commands/draft-response.md`
- `customer-support/commands/escalate-risk.md`
- `customer-support/commands/summarize-thread.md`
- `customer-support/commands/kb-gap.md`

## Read-Only Files (Agent's "prepare.py")

Agent MUST NOT modify:

- `policies/medical-compliance.md`
- `policies/privacy-and-pii.md`
- `policies/human-review.md`
- `policies/tool-permissions.md`
- `policies/advertising-claims.md`
- `schemas/customer-support/*.schema.json`
- `schemas/common/*.schema.json`
- `connectors/gmail.connector.md`
- `connectors/shopify.connector.md`
- `connectors/notion.connector.md`
- `connectors/mock/mock-gmail.json`
- `connectors/mock/mock-shopify-orders.json`
- `connectors/mock/mock-kb.json`
- `customer-support/.claude-plugin/plugin.json`
- `customer-support/.mcp.json`
- `customer-support/evals/golden_set_v1.yaml`
- `customer-support/examples/*.md`
- `agent-evaluation/runner/run_eval.py`
- `agent-evaluation/runner/judge_output.py`

## Evaluation Metric

```
support_score = 
  40% × category_accuracy        (correct triage category)
+ 25% × escalation_accuracy      (P1/P2 correctly escalated)
+ 20% × compliance_recall        (medical/risk flags caught)
+ 10% × structure_completeness   (output matches schema)
+ 5%  × tone_match               (empathetic/professional tone)
```

Metric is computed by `scripts/run_eval.py` against `customer-support/evals/golden_set_v1.yaml`.

**Hard constraint**: P1 medical-risk cases must score 100% escalation_accuracy. Any regression on P1 cases → auto-discard, no matter the overall score.

## Budget Control

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Max cases per experiment | 50 | Full golden set |
| Max skill files modified per experiment | 1 | Isolate variables |
| Max experiments per session | 30 | Overnight run (~5 min each) |
| Max API cost per session | $5.00 | Cost-controllable iteration |
| Max tokens per experiment | 50,000 | Prevent runaway prompts |
| Timeout per experiment | 5 minutes | Wall clock including eval |

If budget exceeded, STOP and generate session report.

## Experiment Loop

```
SETUP:
1. Agree on run tag (e.g., cs-jul02). Create branch: autoresearch/cs-jul02
2. Read all editable files for context
3. Run baseline evaluation on golden set → record in results.tsv
4. Confirm setup with human

LOOP (max 30 iterations per session):
1. Identify one improvement hypothesis from:
   - Failed cases in last run (priority)
   - Error review recommendations
   - Edge case gaps
2. Modify ONE skill or command file
3. Git commit with descriptive message
4. Run evaluation: python scripts/run_eval.py --agent customer-support
5. Read score from experiments/scorecards/latest.json
6. Compare to baseline:
   - If score improved AND P1 cases still 100% → KEEP
   - If score same but simpler code → KEEP (simplicity win)
   - If score worse OR P1 regressed → DISCARD (git reset)
7. Log to results.tsv
8. Continue to next hypothesis
```

## results.tsv Format

```tsv
commit	agent	skill_modified	score	p1_pass_rate	cost	status	description
a1b2c3d	customer-support	baseline	0.820	1.00	0.12	keep	baseline run
b2c3d4e	customer-support	ticket-triage	0.860	1.00	0.11	keep	added 3 P1 escalation examples
c3d4e5f	customer-support	draft-response	0.810	1.00	0.13	discard	tone became too rigid after stricter wording
d4e5f6g	customer-support	ticket-triage	0.840	0.80	0.10	discard	P1 medical case missed — auto-revert
```

## Safety Boundaries

### Agent CAN autonomously:
- Edit SKILL.md draft content
- Edit command .md instructions
- Run golden set evaluation
- Generate scorecards and reports
- Create git commits on experiment branch
- Create PR for human review

### Agent CANNOT autonomously:
- Send any email (create_draft only, human approval to send)
- Issue refunds or modify orders
- Modify Shopify store pages
- Change compliance policies
- Modify evaluation harness or golden set
- Merge PR without human approval
- Exceed budget without human approval
- Run more than 30 experiments per session

## Human Checkpoints

After each session (max 30 experiments), agent MUST:
1. Generate session report (experiments/sessions/session-<tag>.md)
2. Create PR with summary of kept changes
3. Wait for human review before merging

## Stopping Conditions

- Budget exhausted (cost or count)
- 3 consecutive crashes
- P1 regression detected (auto-discard + alert)
- Human interrupt
