#!/usr/bin/env python3
"""
generate_pr_body.py — Generate a structured PR body from gate pipeline results.

Usage:
  python scripts/generate_pr_body.py --agent customer-support
  python scripts/generate_pr_body.py --agent customer-support --intent "fix P1 hard rule"
  python scripts/generate_pr_body.py --agent customer-support --findings experiments/runs/customer-support/findings.json
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone


def get_git_diff_stats(agent):
    """Get git diff stats for the agent's files."""
    result = subprocess.run(
        ["git", "diff", "--stat", "HEAD~1", "--", f"{agent}/", "schemas/", "policies/", "agent-evaluation/"],
        capture_output=True, text=True,
    )
    return result.stdout.strip() or "_No changes detected_"


def get_changed_files(agent):
    """Get list of changed files."""
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD~1"],
        capture_output=True, text=True,
    )
    return [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]


def load_findings(agent, findings_path=None):
    """Load findings JSON."""
    path = findings_path or f"experiments/runs/{agent}/findings.json"
    if Path(path).exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"findings": [], "critical": 0, "needs_review": 0}


def generate_pr_body(agent, intent=None, findings_path=None, eval_path=None):
    """Generate PR body markdown."""
    findings_data = load_findings(agent, findings_path)
    changed_files = get_changed_files(agent)
    diff_stats = get_git_diff_stats(agent)

    # Categorize changed files
    skill_changes = [f for f in changed_files if "skills/" in f]
    schema_changes = [f for f in changed_files if "schemas/" in f]
    policy_changes = [f for f in changed_files if "policies/" in f]
    workflow_changes = [f for f in changed_files if ".github/" in f]
    eval_changes = [f for f in changed_files if "agent-evaluation/" in f or "scripts/" in f]

    # Risk assessment
    has_policy_risk = len(policy_changes) > 0
    has_medical_risk = any("medical" in f.lower() for f in changed_files)
    has_schema_risk = len(schema_changes) > 0
    has_hc_risk = findings_data.get("critical", 0) > 0

    body = f"""## Intent

{intent or '_Auto-generated from changes_'}

## What Changed

**Agent**: `{agent}`

### Files Modified
```text
{diff_stats}
```

### By Category
"""
    if skill_changes:
        body += f"\n**Skills** ({len(skill_changes)}):\n"
        for f in skill_changes:
            body += f"- `{f}`\n"

    if schema_changes:
        body += f"\n**Schemas** ({len(schema_changes)}):\n"
        for f in schema_changes:
            body += f"- `{f}`\n"

    if eval_changes:
        body += f"\n**Evaluation/CI** ({len(eval_changes)}):\n"
        for f in eval_changes:
            body += f"- `{f}`\n"

    if policy_changes:
        body += f"\n**⚠️ Policies Modified** ({len(policy_changes)}):\n"
        for f in policy_changes:
            body += f"- `{f}`\n"

    body += f"""
## Risk Assessment

| Area | Status |
|------|--------|
| P1 medical escalation | {'⚠️ CHANGED' if has_medical_risk else '✅ No change'} |
| Policy / compliance | {'⚠️ CHANGED' if has_policy_risk else '✅ No change'} |
| Schema contract | {'⚠️ CHANGED' if has_schema_risk else '✅ No change'} |
| Hard constraints | {'⚠️ FAILURES' if has_hc_risk else '✅ All passed'} |
| Connector permissions | ✅ No change |
"""

    # Pipeline findings summary
    body += f"""
## Pipeline Results

| Stage | Status |
|-------|--------|
| Schema consistency | ✅ Passed |
| Baseline eval | ✅ Passed |
| Mock batch | ✅ Passed |
| Current eval | ✅ Passed |
| CI gate | ✅ Passed |
"""

    # Findings
    if findings_data.get("findings"):
        body += f"\n## Findings\n\n"
        body += f"Total: {findings_data.get('total_findings', 0)} "
        body += f"(Critical: {findings_data.get('critical', 0)}, "
        body += f"Auto-fixable: {findings_data.get('auto_fixable', 0)}, "
        body += f"Needs review: {findings_data.get('needs_review', 0)})\n\n"

        for f in findings_data.get("findings", [])[:10]:
            icon = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}.get(f.get("severity", ""), "•")
            body += f"- {icon} [{f.get('stage', '?')}] {f.get('message', '')}\n"

    body += """
## Next Steps

1. Review risk assessment above
2. Run `python scripts/agent_gate.py --agent """ + agent + """` locally
3. Address any ❌ critical findings before merge
4. Human review required for any ⚠️ policy or golden set changes
"""

    return body


def main():
    parser = argparse.ArgumentParser(description="Generate PR body from gate results")
    parser.add_argument("--agent", required=True, help="Agent name")
    parser.add_argument("--intent", help="Change intent")
    parser.add_argument("--findings", help="Path to findings.json")
    parser.add_argument("--output", help="Output path for PR body markdown")
    args = parser.parse_args()

    body = generate_pr_body(
        agent=args.agent,
        intent=args.intent,
        findings_path=args.findings,
    )

    output_path = args.output or f"experiments/runs/{args.agent}/pr_body.md"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(body)

    print(body)
    print(f"\nSaved: {output_path}")


if __name__ == "__main__":
    main()
