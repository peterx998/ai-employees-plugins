#!/usr/bin/env python3
"""
agent_run_logger.py — Structured logging for agent evaluation runs.

Writes agent_run.jsonl with per-case metrics:
  run_id, case_id, adapter, model, commit_sha, latency_ms, cost,
  verdict, tool_trace_path, state_diff_path, timestamp

This provides observability for the evaluation harness — each case
evaluation is logged as a structured JSON line that can be queried
for latency analysis, cost tracking, and regression detection.

Usage:
  from agent_run_logger import AgentRunLogger
  logger = AgentRunLogger()
  logger.log_case(run_id="run-20260703", case_id="CS-MED-001",
                  adapter="mock", model="mock-v1", latency_ms=42,
                  verdict="PASS", cost=0.0)
  summary = logger.get_runs(adapter="mock")
"""

from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class AgentRunLogger:
    """Structured logger for agent evaluation runs.

    Each evaluation case is logged as a JSON line in agent_run.jsonl.
    This is the observability layer — reports are results, logs are process.
    """

    def __init__(self, log_path: str = "reports/agent_run.jsonl"):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def _get_commit_sha(self) -> str:
        """Get current git short hash."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                capture_output=True, text=True, timeout=5,
            )
            return result.stdout.strip() if result.returncode == 0 else "unknown"
        except Exception:
            return "unknown"

    def log_case(
        self,
        run_id: str,
        case_id: str,
        adapter: str,
        model: str = "",
        latency_ms: float = 0.0,
        cost: float = 0.0,
        verdict: str = "",
        score: float = 0.0,
        hard_constraint_passed: bool = True,
        tool_trace_path: str = "",
        state_diff_path: str = "",
        error: str = "",
    ) -> None:
        """Log a single case evaluation run.

        Parameters
        ----------
        run_id : str
            Unique identifier for this evaluation run (e.g. "run-20260703-001")
        case_id : str
            Golden set case ID (e.g. "CS-MED-001")
        adapter : str
            Adapter used ("mock", "codex", "hermes", "hermes-dry-run")
        model : str
            Model name (e.g. "gpt-4o", "claude-sonnet-4", "mock-v1")
        latency_ms : float
            Time to process this case in milliseconds
        cost : float
            Estimated cost in USD for this case
        verdict : str
            "PASS" or "FAIL"
        score : float
            Evaluation score (0.0 to 1.0)
        hard_constraint_passed : bool
            Whether hard constraints passed
        tool_trace_path : str
            Path to tool_calls.jsonl for this case (if tool trace was evaluated)
        state_diff_path : str
            Path to state_diff.json for this case (if state diff was evaluated)
        error : str
            Error message if the case errored
        """
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "run_id": run_id,
            "case_id": case_id,
            "adapter": adapter,
            "model": model,
            "commit_sha": self._get_commit_sha(),
            "latency_ms": round(latency_ms, 2),
            "cost": round(cost, 4),
            "verdict": verdict,
            "score": round(score, 4),
            "hard_constraint_passed": hard_constraint_passed,
            "tool_trace_path": tool_trace_path,
            "state_diff_path": state_diff_path,
        }
        if error:
            entry["error"] = error

        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def get_runs(
        self,
        run_id: str | None = None,
        adapter: str | None = None,
        case_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Read logged runs, optionally filtered.

        Parameters
        ----------
        run_id : str, optional
            Filter by run ID
        adapter : str, optional
            Filter by adapter name
        case_id : str, optional
            Filter by case ID

        Returns
        -------
        list[dict]
            List of run entries matching the filters
        """
        if not self.log_path.exists():
            return []

        results = []
        with open(self.log_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if run_id and entry.get("run_id") != run_id:
                    continue
                if adapter and entry.get("adapter") != adapter:
                    continue
                if case_id and entry.get("case_id") != case_id:
                    continue
                results.append(entry)

        return results

    def get_summary(self, run_id: str | None = None) -> dict[str, Any]:
        """Get aggregate summary of runs.

        Parameters
        ----------
        run_id : str, optional
            If provided, summarize only this run

        Returns
        -------
        dict
            Summary with total_cases, passed, failed, avg_latency, total_cost, etc.
        """
        runs = self.get_runs(run_id=run_id)

        if not runs:
            return {"total": 0, "message": "No runs found"}

        total = len(runs)
        passed = sum(1 for r in runs if r.get("verdict") == "PASS")
        failed = total - passed
        total_latency = sum(r.get("latency_ms", 0) for r in runs)
        total_cost = sum(r.get("cost", 0) for r in runs)
        avg_score = sum(r.get("score", 0) for r in runs) / total

        adapters = {}
        for r in runs:
            adp = r.get("adapter", "unknown")
            if adp not in adapters:
                adapters[adp] = {"count": 0, "passed": 0, "cost": 0.0}
            adapters[adp]["count"] += 1
            if r.get("verdict") == "PASS":
                adapters[adp]["passed"] += 1
            adapters[adp]["cost"] += r.get("cost", 0)

        return {
            "run_id": run_id or "all",
            "total_cases": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": round(passed / total, 4) if total > 0 else 0,
            "avg_latency_ms": round(total_latency / total, 2) if total > 0 else 0,
            "avg_score": round(avg_score, 4),
            "total_cost": round(total_cost, 4),
            "by_adapter": adapters,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def clear(self) -> None:
        """Clear the log file."""
        self.log_path.write_text("", encoding="utf-8")


# ─── Self-test ───

if __name__ == "__main__":
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
        test_path = f.name

    logger = AgentRunLogger(test_path)

    # Log some test cases
    logger.log_case("test-run-001", "CS-MED-001", "mock", "mock-v1",
                    latency_ms=42.5, cost=0.0, verdict="PASS", score=1.0)
    logger.log_case("test-run-001", "CS-REF-003", "mock", "mock-v1",
                    latency_ms=38.2, cost=0.0, verdict="PASS", score=0.95)
    logger.log_case("test-run-001", "CS-ESC-001", "hermes", "claude-sonnet-4",
                    latency_ms=1500.0, cost=0.05, verdict="FAIL", score=0.6,
                    hard_constraint_passed=False)
    logger.log_case("test-run-002", "CS-MED-001", "codex", "gpt-4o",
                    latency_ms=2200.0, cost=0.08, verdict="PASS", score=1.0)

    # Query
    all_runs = logger.get_runs()
    assert len(all_runs) == 4, f"Expected 4 runs, got {len(all_runs)}"

    run1 = logger.get_runs(run_id="test-run-001")
    assert len(run1) == 3, f"Expected 3 runs for test-run-001, got {len(run1)}"

    mock_runs = logger.get_runs(adapter="mock")
    assert len(mock_runs) == 2, f"Expected 2 mock runs, got {len(mock_runs)}"

    # Summary
    summary = logger.get_summary("test-run-001")
    print(f"Summary for test-run-001:")
    print(f"  Total: {summary['total_cases']}")
    print(f"  Passed: {summary['passed']}")
    print(f"  Failed: {summary['failed']}")
    print(f"  Avg latency: {summary['avg_latency_ms']}ms")
    print(f"  Avg score: {summary['avg_score']}")
    print(f"  Total cost: ${summary['total_cost']}")
    print(f"  By adapter: {summary['by_adapter']}")

    Path(test_path).unlink()
    print("\n✓ All self-tests passed")
