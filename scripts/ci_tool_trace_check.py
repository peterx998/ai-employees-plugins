#!/usr/bin/env python3
"""
ci_tool_trace_check.py — CI step: run tool trace evaluation and block on failures.

Generates actual tool_calls.jsonl from expected traces (simulating what a
compliant agent would do), runs ToolTraceEvaluator, and exits non-zero if
any case has forbidden tools, permission violations, or missing required tools.

In production, actual tool_calls.jsonl would come from the agent runtime.
For CI, we generate a "golden compliant" trace to verify the evaluator itself
works end-to-end. A second pass injects a deliberate violation to verify
the evaluator catches it (negative test).

Usage:
  python3 scripts/ci_tool_trace_check.py
  python3 scripts/ci_tool_trace_check.py --traces-dir customer-support/evals/tool_traces
"""

import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root / "agent-evaluation" / "runner"))
sys.path.insert(0, str(project_root))

from tool_trace_evaluator import ToolTraceEvaluator


def generate_compliant_traces(eval_dir: str) -> dict[str, list[dict]]:
    """Generate compliant tool calls from expected traces.

    For each expected trace, produce the exact tools in the expected order
    with minimal valid arguments. This simulates a perfectly compliant agent.
    """
    import yaml

    traces_path = Path("customer-support/evals/tool_traces/expected_tool_traces.yaml")
    with open(traces_path, "r", encoding="utf-8") as f:
        expected = yaml.safe_load(f)

    compliant: dict[str, list[dict]] = {}
    for entry in expected:
        cid = entry["case_id"]
        calls = []
        for tool_spec in entry.get("expected_tools", []):
            tool_name = tool_spec["tool"]
            args = {}
            for arg_name in tool_spec.get("args_required", []):
                if arg_name == "query":
                    args[arg_name] = f"search for {cid}"
                elif arg_name == "case_id":
                    args[arg_name] = cid
                elif arg_name == "reason":
                    args[arg_name] = f"escalation for {cid}"
                else:
                    args[arg_name] = "test_value"
            calls.append({"tool": tool_name, "args": args})
        compliant[cid] = calls

    return compliant


def generate_violation_trace(case_id: str) -> list[dict]:
    """Generate a trace with a deliberate permission violation.

    Injects gmail.send_email which must ALWAYS be denied.
    """
    return [
        {"tool": "kb.search_policies", "args": {"query": "test"}},
        {"tool": "gmail.send_email", "args": {"to": "customer@test.com", "subject": "Re: issue"}},
    ]


def main():
    import argparse
    parser = argparse.ArgumentParser(description="CI tool trace evaluation")
    parser.add_argument("--traces-dir", default="customer-support/evals/tool_traces")
    args = parser.parse_args()

    print("=" * 60)
    print("  Tool Trace Evaluation (CI)")
    print("=" * 60)

    evaluator = ToolTraceEvaluator()
    print(f"  Expected traces: {len(evaluator.traces)}")
    print(f"  PermissionGateway: {'available' if evaluator._gateway else 'NOT available'}")
    print()

    # ─── Phase 1: Compliant traces (should all pass) ───
    print("─" * 60)
    print("  Phase 1: Compliant traces (positive test)")
    print("─" * 60)

    compliant = generate_compliant_traces(args.traces_dir)
    passed = 0
    failed = 0

    for cid, calls in compliant.items():
        result = evaluator.evaluate_trace(cid, calls)
        icon = "✓" if result.passed else "✗"
        print(f"  {icon} {cid}: score={result.score:.2f} passed={result.passed}")
        if not result.passed:
            failed += 1
            for reason in result.reasons:
                print(f"      {reason}")
        else:
            passed += 1

    print(f"\n  Compliant: {passed}/{len(compliant)} passed, {failed} failed")

    if failed > 0:
        print("\n  ✗ FAIL: Compliant traces should all pass — evaluator has a bug")
        sys.exit(1)

    # ─── Phase 2: Violation trace (should fail) ───
    print()
    print("─" * 60)
    print("  Phase 2: Violation trace (negative test)")
    print("─" * 60)

    # Use CS-MED-001 (P1 medical — must not send email)
    violation_case = "CS-MED-001"
    violation_calls = generate_violation_trace(violation_case)
    result = evaluator.evaluate_trace(violation_case, violation_calls)

    print(f"  {violation_case} with send_email injection:")
    print(f"    Score: {result.score:.2f}  Passed: {result.passed}")
    print(f"    Forbidden tools: {result.unexpected_forbidden_tools}")
    print(f"    Permission violations: {result.permission_violations}")

    if result.passed:
        print("\n  ✗ FAIL: Violation trace should be caught — evaluator is fail-open!")
        sys.exit(1)

    has_permission_violation = len(result.permission_violations) > 0
    has_forbidden = len(result.unexpected_forbidden_tools) > 0

    if not has_permission_violation:
        print("\n  ✗ FAIL: Permission violation not detected — gateway check is broken!")
        sys.exit(1)

    print(f"  ✓ Violation correctly detected (forbidden={has_forbidden}, permission_violation={has_permission_violation})")

    # ─── Summary ───
    print()
    print("=" * 60)
    print(f"  Tool Trace CI: PASS")
    print(f"  Compliant traces: {passed}/{len(compliant)} passed")
    print(f"  Violation detection: working (send_email correctly denied)")
    print("=" * 60)


if __name__ == "__main__":
    main()
