#!/usr/bin/env python3
"""
agent_gate.py — Local quality gate for AI Employee plugin changes.

Adapted from kunchenguid/no-mistakes pipeline architecture:
  intent → contract-check → schema-check → golden-set-eval
  → agent-batch-run → regression-check → findings → pr-body

Unlike no-mistakes, this does NOT act as a git proxy.
It's a local pre-push / pre-PR gate that runs the same checks as CI.

Usage:
  python scripts/agent_gate.py --agent customer-support
  python scripts/agent_gate.py --agent customer-support --intent "fix P1 hard rule"
  python scripts/agent_gate.py --agent customer-support --real-adapter codex
  python scripts/agent_gate.py --agent customer-support --dry-run

Stages:
  1. intent        — read or infer the change intent
  2. contract      — validate schema/taxonomy/golden_set alignment
  3. schema        — validate JSON Schema consistency
  4. eval-baseline — evaluate against baseline actual outputs
  5. mock-batch    — run mock adapter and evaluate outputs
  6. eval-current  — evaluate mock batch outputs
  7. findings      — generate structured findings from all results
  8. pr-body       — generate PR body for human review

Exit codes:
  0 — All gates passed (including P1 hard constraints)
  1 — Non-critical findings (warnings only)
  2 — Critical findings (errors, hard constraint failures)
"""

import argparse
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone


# ─── Pipeline definition ───

PIPELINE_STAGES = [
    "intent",
    "contract",
    "schema",
    "eval-baseline",
    "mock-batch",
    "eval-current",
    "findings",
    "pr-body",
]

# What can be auto-fixed vs. must ask user
AUTO_FIXABLE = [
    "schema_enum_mismatch",
    "missing_field_in_output",
    "yaml_format_error",
    "json_format_error",
    "badge_outdated",
    "docs_missing_section",
    "command_output_schema_path_wrong",
    "mock_output_missing_field",
]

ASK_USER_ALWAYS = [
    "medical_policy_changed",
    "refund_policy_changed",
    "human_review_rule_relaxed",
    "p1_judgment_changed",
    "p2_judgment_changed",
    "connector_permission_upgraded",
    "golden_set_expected_changed",
    "hard_constraint_modified",
]


# ─── Stage runners ───

def run_stage(command, capture=True, timeout=120):
    """Run a stage command and return (success, output, elapsed)."""
    start = datetime.now(timezone.utc)
    try:
        result = subprocess.run(
            shlex.split(command), shell=False,
            capture_output=capture, text=True, timeout=timeout,
            cwd=os.getcwd(),
        )
        elapsed = (datetime.now(timezone.utc) - start).total_seconds()
        success = result.returncode == 0
        output = result.stdout.strip() if capture else ""
        stderr = result.stderr.strip()
        return success, output + ("\n" + stderr if stderr else ""), elapsed
    except subprocess.TimeoutExpired:
        elapsed = (datetime.now(timezone.utc) - start).total_seconds()
        return False, f"Timeout after {timeout}s", elapsed
    except Exception as e:
        elapsed = (datetime.now(timezone.utc) - start).total_seconds()
        return False, str(e), elapsed


def run_pipeline(agent, intent=None, real_adapter=None, dry_run=False):
    """Run the full gate pipeline. Returns (passed, findings, report)."""
    findings = []
    report_lines = []
    start_all = datetime.now(timezone.utc)

    print(f"\n{'='*60}")
    print(f"  AI Employee Gate — {agent}")
    print(f"  Intent: {intent or '(inferred from changes)'}")
    print(f"{'='*60}")

    # ── Stage 1: Intent ──
    print(f"\n── Stage 1/8: Intent ──")
    intent_text = intent or _infer_intent(agent)
    print(f"  Intent: {intent_text}")
    report_lines.append(f"## Intent\n{intent_text}\n")

    # ── Stage 2: Contract validation ──
    print(f"\n── Stage 2/8: Contract ──")
    ok, out, elapsed = run_stage(f"python scripts/ci_validate_schema.py")
    status = "PASS" if ok else "FAIL"
    print(f"  {status} ({elapsed:.1f}s)")
    if not ok:
        findings.append({
            "stage": "contract",
            "severity": "error",
            "action": "auto-fix" if "enum" in (out or "") else "ask-user",
            "message": "Schema/taxonomy/golden_set misalignment",
            "detail": (out or "")[:500],
        })

    # ── Stage 3: Schema validation ──
    print(f"\n── Stage 3/8: Schema ──")
    schema_path = f"schemas/{agent}/triage_result.schema.json"
    ok = Path(schema_path).exists()
    print(f"  {'PASS' if ok else 'WARN'} — {schema_path} {'exists' if ok else 'missing'}")
    if not ok:
        findings.append({
            "stage": "schema",
            "severity": "warning",
            "action": "ask-user",
            "message": f"Schema not found: {schema_path}",
        })

    # ── Stage 4: Evaluate baseline ──
    print(f"\n── Stage 4/8: Eval Baseline ──")
    baseline_dir = f"{agent}/evals/actual_outputs/baseline"
    golden_set = f"{agent}/evals/golden_set_v1.yaml"
    ok, out, elapsed = run_stage(
        f"python agent-evaluation/runner/run_eval.py --golden-set {golden_set} --agent {agent} --actual-dir {baseline_dir}"
    )
    status = "PASS" if ok else "FAIL"
    print(f"  {status} ({elapsed:.1f}s)")
    if not ok:
        findings.append({
            "stage": "eval-baseline",
            "severity": "error",
            "action": "ask-user",
            "message": "Baseline evaluation failed — possible regression in existing outputs",
            "detail": (out or "")[:300],
        })
    report_lines.append(f"## Baseline Eval\n{_summarize(out)}\n")

    # ── Stage 5: Mock batch run ──
    print(f"\n── Stage 5/8: Mock Batch ──")
    output_dir = f"{agent}/evals/actual_outputs/current"
    ok, out, elapsed = run_stage(
        f"python agent-evaluation/runner/run_agent_batch.py --agent {agent} --adapter mock --output-dir {output_dir}"
    )
    status = "PASS" if ok else "FAIL"
    print(f"  {status} ({elapsed:.1f}s)")
    report_lines.append(f"## Mock Batch\n{_summarize(out)}\n")

    # ── Stage 6: Evaluate current ──
    print(f"\n── Stage 6/8: Eval Current ──")
    ok, out, elapsed = run_stage(
        f"python agent-evaluation/runner/run_eval.py --golden-set {golden_set} --agent {agent} --actual-dir {output_dir}"
    )
    status = "PASS" if ok else "FAIL"
    print(f"  {status} ({elapsed:.1f}s)")
    if not ok:
        findings.append({
            "stage": "eval-current",
            "severity": "error",
            "action": "ask-user",
            "message": "Mock batch evaluation failed",
            "detail": (out or "")[:300],
        })
    report_lines.append(f"## Current Eval\n{_summarize(out)}\n")

    # ── Optional: Real adapter ──
    if real_adapter:
        print(f"\n── Optional: Real Adapter ({real_adapter}) ──")
        ok, out, elapsed = run_stage(
            f"python agent-evaluation/runner/run_agent_batch.py --agent {agent} --adapter {real_adapter} --output-dir {output_dir}",
            timeout=600,
        )
        print(f"  {'PASS' if ok else 'FAIL'} ({elapsed:.1f}s)")
        report_lines.append(f"## Real Adapter ({real_adapter})\n{_summarize(out)}\n")

    # ── Stage 7: Findings ──
    print(f"\n── Stage 7/8: Findings ──")
    finding_data = generate_findings(agent, findings)
    auto_fix = [f for f in finding_data if f.get("action") == "auto-fix"]
    ask_user = [f for f in finding_data if f.get("action") == "ask-user"]
    critical = [f for f in finding_data if f.get("severity") == "error"]

    print(f"  Total findings: {len(finding_data)}")
    print(f"  Auto-fixable: {len(auto_fix)}")
    print(f"  Requires human: {len(ask_user)}")
    print(f"  Critical: {len(critical)}")

    for f in finding_data:
        if f.get("action") == "ask-user":
            print(f"  ⚠️  [{f['stage']}] {f['message']}")
        elif f.get("action") == "auto-fix":
            print(f"  🔧 [{f['stage']}] {f['message']}")

    # Save findings
    findings_path = f"experiments/runs/{agent}/findings.json"
    Path(findings_path).parent.mkdir(parents=True, exist_ok=True)
    with open(findings_path, "w", encoding="utf-8") as f:
        json.dump(finding_data, f, indent=2, ensure_ascii=False)
    print(f"  Saved: {findings_path}")

    report_lines.append(f"## Findings ({len(finding_data)} total)\n")
    for f in finding_data:
        report_lines.append(f"- [{f['severity'].upper()}] {f['stage']}: {f['message']}")

    # ── Stage 8: PR Body ──
    print(f"\n── Stage 8/8: PR Body ──")
    pr_body = generate_pr_body(agent, intent_text, report_lines, finding_data)
    pr_path = f"experiments/runs/{agent}/pr_body.md"
    Path(pr_path).parent.mkdir(parents=True, exist_ok=True)
    with open(pr_path, "w", encoding="utf-8") as f:
        f.write(pr_body)
    print(f"  Saved: {pr_path}")

    # ── Final verdict ──
    total_elapsed = (datetime.now(timezone.utc) - start_all).total_seconds()
    if critical:
        verdict = "BLOCKED"
        exit_code = 2
    elif ask_user:
        verdict = "NEEDS_REVIEW"
        exit_code = 1
    else:
        verdict = "PASS"
        exit_code = 0

    print(f"\n{'='*60}")
    print(f"  Verdict: {verdict}")
    print(f"  Total time: {total_elapsed:.1f}s")
    print(f"{'='*60}")

    return exit_code, finding_data, "\n\n".join(report_lines)


# ─── Helpers ───

def _infer_intent(agent):
    """Infer intent from recent git log."""
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "-1", "--", f"{agent}/", "agent-evaluation/", "schemas/"],
            capture_output=True, text=True, cwd=os.getcwd(),
        )
        return result.stdout.strip() or f"Update {agent} plugin"
    except:
        return f"Update {agent} plugin"


def _summarize(output):
    """Extract key lines from evaluation output."""
    if not output:
        return "_No output_"
    lines = output.split("\n")
    key_lines = [l for l in lines if any(k in l for k in ["Verdict", "Pass rate", "Passed", "Failed", "OVERALL"])]
    return "\n".join(key_lines[:10]) if key_lines else output[:200]


def generate_findings(agent, stage_findings):
    """Convert stage results into structured findings."""
    all_findings = list(stage_findings)

    # Check eval_results.json for schema/hard constraint failures
    eval_path = f"{agent}/reports/eval_results.json"
    if Path(eval_path).exists():
        with open(eval_path) as f:
            d = json.load(f)
        if d.get("hard_constraint_failures", 0) > 0:
            all_findings.append({
                "stage": "eval-current",
                "severity": "error",
                "action": "ask-user",
                "file": f"{agent}/skills/ticket-triage/SKILL.md",
                "message": f"Hard constraint failures: P1 medical escalate or auto-reply suppress violated",
                "risk_level": "high",
            })
        if d.get("schema_failures", 0) > 0:
            all_findings.append({
                "stage": "eval-current",
                "severity": "error",
                "action": "auto-fix",
                "file": f"schemas/{agent}/triage_result.schema.json",
                "message": "Output does not match required schema fields",
                "risk_level": "medium",
            })

    # Check for regressions
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD~1"],
        capture_output=True, text=True, cwd=os.getcwd(),
    )
    changed = set(result.stdout.strip().split("\n"))

    # Golden set changed → ask user
    if any("golden_set" in f for f in changed):
        all_findings.append({
            "stage": "contract",
            "severity": "warning",
            "action": "ask-user",
            "message": "Golden set modified — verify expected values are still correct",
            "risk_level": "high",
        })

    # Policy changed → ask user
    for f in changed:
        if "policy" in f.lower() and f.endswith(".md"):
            all_findings.append({
                "stage": "contract",
                "severity": "warning",
                "action": "ask-user",
                "file": f,
                "message": f"Policy file changed: {f} — requires human review",
                "risk_level": "high",
            })

    return all_findings


def generate_pr_body(agent, intent, report_lines, findings):
    """Generate PR body from pipeline results."""
    critical = [f for f in findings if f["severity"] == "error"]
    needs_review = [f for f in findings if f["action"] == "ask-user"]
    auto_fixed = [f for f in findings if f["action"] == "auto-fix"]

    body = f"""## Intent

{intent}

## What Changed

Agent: `{agent}`

Findings: {len(findings)} total ({len(critical)} critical, {len(needs_review)} needs review, {len(auto_fixed)} auto-fixable)

### Critical ({len(critical)})
"""
    for f in critical:
        body += f"- **[{f['stage']}]** {f['message']}\n"

    body += f"\n### Requires Human Review ({len(needs_review)})\n"
    for f in needs_review:
        body += f"- [{f['stage']}] {f['message']}\n"

    body += f"\n### Auto-Fixable ({len(auto_fixed)})\n"
    for f in auto_fixed:
        body += f"- [{f['stage']}] {f['message']}\n"

    body += f"""
## Risk Assessment

| Area | Impact |
|------|--------|
| P1 medical escalation | {'⚠️ CHECK' if any('p1' in str(f).lower() for f in findings) else '✅ No change'} |
| Human review boundary | {'⚠️ CHECK' if any('human_review' in str(f).lower() for f in findings) else '✅ No change'} |
| Connector permissions | {'⚠️ CHECK' if any('connector' in str(f).lower() for f in findings) else '✅ No change'} |
| Schema contract | {'⚠️ CHECK' if any('schema' in str(f).lower() for f in findings) else '✅ No change'} |

## Pipeline Results

"""
    for line in report_lines:
        body += line + "\n"

    body += """
## Next Steps

1. Review critical findings above
2. Run `python scripts/agent_gate.py --agent """ + agent + """` locally
3. Merge only after all critical findings resolved
"""

    return body


def main():
    parser = argparse.ArgumentParser(description="AI Employee Gate — local quality pipeline")
    parser.add_argument("--agent", required=True, help="Agent name")
    parser.add_argument("--intent", help="Change intent (auto-inferred if omitted)")
    parser.add_argument("--real-adapter", choices=["codex", "hermes"],
                       help="Also run real adapter (requires credentials)")
    parser.add_argument("--dry-run", action="store_true",
                       help="Print what would run without executing")
    args = parser.parse_args()

    if args.dry_run:
        print("Pipeline stages (dry run):")
        for i, stage in enumerate(PIPELINE_STAGES, 1):
            print(f"  {i}. {stage}")
        return

    exit_code, findings, report = run_pipeline(
        agent=args.agent,
        intent=args.intent,
        real_adapter=args.real_adapter,
        dry_run=False,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
