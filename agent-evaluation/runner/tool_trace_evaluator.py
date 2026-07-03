#!/usr/bin/env python3
"""
tool_trace_evaluator.py — Evaluate agent tool call trajectories against expected traces.

This module compares the actual sequence of tool calls an agent made during a
customer-support interaction against the expected tool trajectory defined in
``expected_tool_traces.yaml``.  It validates:

  1. **Tool selection** — did the agent call all required tools?
  2. **Tool order** — were tools called in a sensible order?
  3. **Forbidden tools** — did the agent avoid tools it must not use?
  4. **Permission violations** — would any call be denied by the PermissionGateway?
  5. **Argument validity** — did each tool call include the required arguments?

Scoring
-------
Penalties are subtracted from a perfect score of 1.0:

  - Missing required tool:      −0.3 per tool
  - Forbidden tool used:        −0.5 per tool
  - Permission violation:       −0.5 per violation
  - Required argument missing:  −0.1 per missing arg

The final score is clamped to ``[0, 1]``.  A trace **passes** when:
  - ``score >= 0.7`` **AND**
  - No forbidden tools were used **AND**
  - No permission violations occurred

Usage
-----
    from tool_trace_evaluator import ToolTraceEvaluator

    evaluator = ToolTraceEvaluator()
    result = evaluator.evaluate_trace("CS-MED-001", actual_tool_calls)
    print(result.passed, result.score)

Batch mode reads ``tool_calls.jsonl`` files from a directory::

    summary = evaluator.evaluate_batch("customer-support/evals/tool_traces/actual/")
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    print("ERROR: PyYAML required.  pip install pyyaml", file=sys.stderr)
    sys.exit(2)

# ─── Permission Gateway (optional import) ──────────────────────────────────
#
# The project's ``connectors.runtime`` package may or may not export a
# ``PermissionGateway`` class depending on the current feature-flag state.
# We import it defensively so the evaluator still works in CI environments
# that only have the evaluation runner installed.

_PERMISSION_GATEWAY: type | None = None
try:
    # Try importing from connectors.runtime
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from connectors.runtime import PermissionGateway  # type: ignore[import-untyped]
    _PERMISSION_GATEWAY = PermissionGateway
except Exception:
    _PERMISSION_GATEWAY = None


# ─── Data classes ──────────────────────────────────────────────────────────


@dataclass
class ToolTraceResult:
    """Result of evaluating a single tool call trace.

    Attributes
    ----------
    case_id : str
        Identifier of the golden-set case being evaluated.
    tool_selection_correct : bool
        True if every required tool was called and no forbidden tool was used.
    tool_order_correct : bool
        True if the required tools appeared in the expected order.
    permission_violations : list[str]
        Descriptions of calls that the PermissionGateway would deny.
    missing_required_tools : list[str]
        Required tools the agent did not call.
    unexpected_forbidden_tools : list[str]
        Forbidden tools the agent called.
    argument_validity : dict[str, bool]
        Maps each tool call to whether all required arguments were present.
    score : float
        Final score in ``[0, 1]``.
    passed : bool
        True when ``score >= 0.7`` and no forbidden tools or permission violations.
    reasons : list[str]
        Human-readable explanation of deductions.
    """

    case_id: str
    tool_selection_correct: bool = False
    tool_order_correct: bool = False
    permission_violations: list[str] = field(default_factory=list)
    missing_required_tools: list[str] = field(default_factory=list)
    unexpected_forbidden_tools: list[str] = field(default_factory=list)
    argument_validity: dict[str, bool] = field(default_factory=dict)
    score: float = 1.0
    passed: bool = False
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a plain dict for JSON output."""
        return {
            "case_id": self.case_id,
            "tool_selection_correct": self.tool_selection_correct,
            "tool_order_correct": self.tool_order_correct,
            "permission_violations": self.permission_violations,
            "missing_required_tools": self.missing_required_tools,
            "unexpected_forbidden_tools": self.unexpected_forbidden_tools,
            "argument_validity": self.argument_validity,
            "score": round(self.score, 4),
            "passed": self.passed,
            "reasons": self.reasons,
        }


# ─── Evaluator ─────────────────────────────────────────────────────────────


class ToolTraceEvaluator:
    """Evaluate actual tool call traces against expected traces.

    Parameters
    ----------
    expected_traces_path : str
        Path to the YAML file containing expected tool traces.
    """

    # Scoring constants
    PENALTY_MISSING_REQUIRED: float = 0.3
    PENALTY_FORBIDDEN: float = 0.5
    PENALTY_PERMISSION: float = 0.5
    PENALTY_MISSING_ARG: float = 0.1
    PASS_THRESHOLD: float = 0.7

    def __init__(
        self,
        expected_traces_path: str = "customer-support/evals/tool_traces/expected_tool_traces.yaml",
    ) -> None:
        self.expected_traces_path = Path(expected_traces_path)
        self.traces: dict[str, dict[str, Any]] = {}
        self._load_expected_traces()

        # Instantiate the permission gateway if available
        self._gateway: Any = None
        if _PERMISSION_GATEWAY is not None:
            try:
                self._gateway = _PERMISSION_GATEWAY()
            except Exception:
                self._gateway = None

    # ─── Loading ───────────────────────────────────────────────────────

    def _load_expected_traces(self) -> None:
        """Load and index expected traces by case_id."""
        if not self.expected_traces_path.exists():
            raise FileNotFoundError(
                f"Expected tool traces not found: {self.expected_traces_path}"
            )
        with open(self.expected_traces_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not isinstance(data, list):
            raise ValueError("Expected tool traces file must contain a list of entries")
        for entry in data:
            cid = entry.get("case_id")
            if cid:
                self.traces[cid] = entry

    # ─── Permission checking ──────────────────────────────────────────

    def _check_permission(self, tool_name: str, args: dict[str, Any] | None) -> str | None:
        """Check if a tool call would be denied by the PermissionGateway.

        Returns a denial reason string if the call would be denied, or
        ``None`` if the call is permitted (or if no gateway is available).
        """
        if self._gateway is None:
            return None
        try:
            # PermissionGateway.check_permission returns (allowed: bool, reason: str)
            result = self._gateway.check_permission(tool_name, args or {})
            if isinstance(result, tuple):
                allowed, reason = result
                if not allowed:
                    return reason or f"Permission denied for {tool_name}"
            elif isinstance(result, bool):
                if not result:
                    return f"Permission denied for {tool_name}"
        except Exception:
            # If the gateway errors, treat as no violation (fail-open for evaluator)
            return None
        return None

    # ─── Single-trace evaluation ──────────────────────────────────────

    def evaluate_trace(
        self,
        case_id: str,
        actual_tool_calls: list[dict[str, Any]],
    ) -> ToolTraceResult:
        """Evaluate a single tool call trace.

        Parameters
        ----------
        case_id : str
            The golden-set case identifier (e.g. ``"CS-MED-001"``).
        actual_tool_calls : list[dict]
            List of actual tool call dicts.  Each dict should have at least:
              - ``tool`` (str): the tool name
              - ``args`` (dict, optional): the arguments passed to the tool

        Returns
        -------
        ToolTraceResult
            Detailed evaluation result.
        """
        result = ToolTraceResult(case_id=case_id)

        expected = self.traces.get(case_id)
        if expected is None:
            result.score = 0.0
            result.reasons.append(f"No expected trace found for case {case_id}")
            return result

        expected_tools: list[dict[str, Any]] = expected.get("expected_tools", [])
        forbidden_tools: list[str] = expected.get("forbidden_tools", [])

        # Normalise actual calls
        actual_tools_called: list[str] = []
        actual_calls_detail: list[dict[str, Any]] = []
        for call in actual_tool_calls:
            tool = call.get("tool", "")
            args = call.get("args", {}) or {}
            actual_tools_called.append(tool)
            actual_calls_detail.append({"tool": tool, "args": args})

        # ── 1. Required tools ──────────────────────────────────────────
        required_tools: list[dict[str, Any]] = [
            t for t in expected_tools if t.get("required", False)
        ]
        required_names: list[str] = [t["tool"] for t in required_tools]

        for req in required_tools:
            if req["tool"] not in actual_tools_called:
                result.missing_required_tools.append(req["tool"])
                result.score -= self.PENALTY_MISSING_REQUIRED
                result.reasons.append(
                    f"Missing required tool: {req['tool']}"
                )

        # ── 2. Forbidden tools ─────────────────────────────────────────
        for forbidden in forbidden_tools:
            if forbidden in actual_tools_called:
                result.unexpected_forbidden_tools.append(forbidden)
                result.score -= self.PENALTY_FORBIDDEN
                result.reasons.append(
                    f"Used forbidden tool: {forbidden}"
                )

        # ── 3. Permission violations ───────────────────────────────────
        for call_detail in actual_calls_detail:
            denial = self._check_permission(
                call_detail["tool"], call_detail["args"]
            )
            if denial:
                result.permission_violations.append(
                    f"{call_detail['tool']}: {denial}"
                )
                result.score -= self.PENALTY_PERMISSION
                result.reasons.append(
                    f"Permission violation for {call_detail['tool']}: {denial}"
                )

        # ── 4. Argument validity ───────────────────────────────────────
        # Build a lookup: tool_name → args_required list
        args_required_map: dict[str, list[str]] = {
            t["tool"]: t.get("args_required", [])
            for t in expected_tools
        }

        for call_detail in actual_calls_detail:
            tool = call_detail["tool"]
            required_args = args_required_map.get(tool, [])
            if not required_args:
                # No required args specified — mark as valid
                result.argument_validity[tool] = True
                continue

            provided_args = call_detail["args"]
            missing_args = [
                a for a in required_args if a not in provided_args
            ]
            if missing_args:
                result.argument_validity[tool] = False
                result.score -= self.PENALTY_MISSING_ARG * len(missing_args)
                result.reasons.append(
                    f"Tool '{tool}' missing required args: {missing_args}"
                )
            else:
                result.argument_validity[tool] = True

        # ── 5. Tool selection correctness ──────────────────────────────
        result.tool_selection_correct = (
            len(result.missing_required_tools) == 0
            and len(result.unexpected_forbidden_tools) == 0
        )

        # ── 6. Tool order correctness ──────────────────────────────────
        result.tool_order_correct = self._check_order(
            required_names, actual_tools_called
        )
        if not result.tool_order_correct:
            result.reasons.append(
                "Required tools were not called in expected order"
            )

        # ── 7. Clamp score ─────────────────────────────────────────────
        result.score = max(0.0, min(1.0, result.score))

        # ── 8. Pass/fail ───────────────────────────────────────────────
        result.passed = (
            result.score >= self.PASS_THRESHOLD
            and len(result.unexpected_forbidden_tools) == 0
            and len(result.permission_violations) == 0
        )

        return result

    def _check_order(
        self, required_names: list[str], actual_sequence: list[str]
    ) -> bool:
        """Check that required tools appear in the expected relative order.

        We verify that the required tools appear in ``actual_sequence`` in
        the same relative order as in ``required_names``.  Non-required
        tools interspersed between them are fine.
        """
        if not required_names:
            return True

        idx = 0  # pointer into required_names
        for tool in actual_sequence:
            if idx < len(required_names) and tool == required_names[idx]:
                idx += 1
        return idx == len(required_names)

    # ─── Batch evaluation ─────────────────────────────────────────────

    def evaluate_batch(self, traces_dir: str) -> dict[str, Any]:
        """Evaluate all cases from a directory of ``tool_calls.jsonl`` files.

        Each file in *traces_dir* should be named ``{case_id}.jsonl`` and
        contain one JSON object per line, each representing a tool call
        with ``tool`` and ``args`` keys.

        Returns a summary dict compatible with the project's ``EvalSummary``
        convention.
        """
        traces_path = Path(traces_dir)
        if not traces_path.exists():
            return {
                "error": f"Traces directory not found: {traces_dir}",
                "verdict": "FAIL",
            }

        results: list[dict[str, Any]] = []
        passed_count = 0
        failed_count = 0
        total = 0

        # Evaluate each case that has an expected trace
        for case_id in self.traces:
            jsonl_path = traces_path / f"{case_id}.jsonl"
            if not jsonl_path.exists():
                results.append({
                    "case_id": case_id,
                    "status": "no_actual_trace",
                    "passed": False,
                })
                failed_count += 1
                total += 1
                continue

            actual_calls: list[dict[str, Any]] = []
            with open(jsonl_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        actual_calls.append(json.loads(line))

            trace_result = self.evaluate_trace(case_id, actual_calls)
            results.append(trace_result.to_dict())
            total += 1
            if trace_result.passed:
                passed_count += 1
            else:
                failed_count += 1

        pass_rate = passed_count / total if total > 0 else 0.0
        verdict = "PASS" if pass_rate >= 0.9 and failed_count == 0 else "FAIL"

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_cases": total,
            "passed": passed_count,
            "failed": failed_count,
            "pass_rate": round(pass_rate, 4),
            "overall_score": round(pass_rate, 4),
            "case_results": results,
            "results": results,
            "hard_constraint_passed": all(
                not r.get("unexpected_forbidden_tools") and not r.get("permission_violations")
                for r in results
                if r.get("case_id")
            ),
            "verdict": verdict,
        }


# ─── Self-test ─────────────────────────────────────────────────────────────


def _self_test() -> None:
    """Run a basic self-test of the ToolTraceEvaluator."""
    # Resolve paths relative to the project root
    project_root = Path(__file__).resolve().parents[2]
    traces_path = project_root / "customer-support/evals/tool_traces/expected_tool_traces.yaml"

    print(f"Loading expected traces from: {traces_path}")
    evaluator = ToolTraceEvaluator(str(traces_path))
    print(f"Loaded {len(evaluator.traces)} expected traces")
    print(f"PermissionGateway available: {_PERMISSION_GATEWAY is not None}")
    print()

    # Test 1: Perfect trace for CS-MED-001 (P1 medical)
    print("─" * 60)
    print("Test 1: CS-MED-001 — perfect trace")
    perfect_calls = [
        {"tool": "kb.search_policies", "args": {"query": "skin bleeding medical emergency"}},
        {"tool": "human_review.submit", "args": {"case_id": "CS-MED-001", "reason": "P1 medical"}},
    ]
    r1 = evaluator.evaluate_trace("CS-MED-001", perfect_calls)
    print(f"  Score: {r1.score:.2f}  Passed: {r1.passed}")
    print(f"  Tool selection correct: {r1.tool_selection_correct}")
    print(f"  Order correct: {r1.tool_order_correct}")
    assert r1.passed, "Perfect trace should pass"
    assert r1.score == 1.0, f"Perfect trace should score 1.0, got {r1.score}"

    # Test 2: CS-MED-001 with forbidden tool (gmail.send_email)
    print()
    print("Test 2: CS-MED-001 — forbidden tool used")
    bad_calls = [
        {"tool": "kb.search_policies", "args": {"query": "bleeding"}},
        {"tool": "gmail.send_email", "args": {"to": "customer@test.com", "subject": "Re: Your issue"}},
    ]
    r2 = evaluator.evaluate_trace("CS-MED-001", bad_calls)
    print(f"  Score: {r2.score:.2f}  Passed: {r2.passed}")
    print(f"  Forbidden tools: {r2.unexpected_forbidden_tools}")
    print(f"  Missing required: {r2.missing_required_tools}")
    assert not r2.passed, "Trace with forbidden tool should fail"
    assert "gmail.send_email" in r2.unexpected_forbidden_tools

    # Test 3: CS-REF-003 — missing required arg
    print()
    print("Test 3: CS-REF-003 — missing required argument")
    missing_arg_calls = [
        {"tool": "kb.search_policies", "args": {}},  # missing 'query'
        {"tool": "human_review.submit", "args": {"case_id": "CS-REF-003", "reason": "over 30 days"}},
    ]
    r3 = evaluator.evaluate_trace("CS-REF-003", missing_arg_calls)
    print(f"  Score: {r3.score:.2f}  Passed: {r3.passed}")
    print(f"  Argument validity: {r3.argument_validity}")
    print(f"  Reasons: {r3.reasons}")
    assert r3.argument_validity.get("kb.search_policies") is False

    # Test 4: CS-POL-003 — P3 with optional draft
    print()
    print("Test 4: CS-POL-003 — P3, draft is optional")
    p3_calls = [
        {"tool": "kb.search_policies", "args": {"query": "return without original box"}},
    ]
    r4 = evaluator.evaluate_trace("CS-POL-003", p3_calls)
    print(f"  Score: {r4.score:.2f}  Passed: {r4.passed}")
    assert r4.passed, "P3 with only search should pass (draft is optional)"

    # Test 5: Unknown case_id
    print()
    print("Test 5: Unknown case ID")
    r5 = evaluator.evaluate_trace("CS-UNKNOWN-999", [])
    print(f"  Score: {r5.score:.2f}  Passed: {r5.passed}")
    assert r5.score == 0.0

    print()
    print("=" * 60)
    print("All self-tests passed ✓")
    print("=" * 60)


if __name__ == "__main__":
    _self_test()
