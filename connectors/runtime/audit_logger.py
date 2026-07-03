"""Audit logger for the Runtime Permission Gateway.

Records every permission check (allowed, denied, error) and every explicit
permission violation to append-only JSONL files.  Provides query helpers
for filtering by case_id and a :meth:`clear` method for fresh test runs.

Log files
---------
- ``tool_calls.jsonl``           — one line per permission check
- ``permission_violations.jsonl``— one line per denied/violation entry

Each JSONL line conforms to ``schemas/common/tool_call.schema.json``.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class AuditLogger:
    """Append-only audit logger writing timezone-aware JSONL records.

    Parameters
    ----------
    log_dir
        Directory where ``tool_calls.jsonl`` and
        ``permission_violations.jsonl`` are stored.
        Created automatically if it does not exist.
    """

    TOOL_CALLS_FILE = "tool_calls.jsonl"
    VIOLATIONS_FILE = "permission_violations.jsonl"

    def __init__(self, log_dir: str = "customer-support/evals/tool_calls") -> None:
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.tool_calls_path = self.log_dir / self.TOOL_CALLS_FILE
        self.violations_path = self.log_dir / self.VIOLATIONS_FILE

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _now() -> str:
        """Return current UTC time as an ISO-8601 string."""
        return datetime.now(timezone.utc).isoformat()

    def _append(self, path: Path, record: dict[str, Any]) -> None:
        """Append a single JSON record to *path* as one line."""
        line = json.dumps(record, default=str, ensure_ascii=False)
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")

    @staticmethod
    def _read_jsonl(path: Path) -> list[dict[str, Any]]:
        """Read all JSONL lines from *path*.  Returns ``[]`` if missing."""
        if not path.exists():
            return []
        records: list[dict[str, Any]] = []
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    # Skip malformed lines but don't crash the read
                    continue
        return records

    # ------------------------------------------------------------------ #
    # Public API — writing
    # ------------------------------------------------------------------ #

    def log_tool_call(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        caller_agent: str,
        caller_skill: str,
        case_id: str,
        result: str,
        denial_reason: str | None = None,
        latency_ms: float | None = None,
    ) -> None:
        """Append a tool-call permission check record.

        Parameters
        ----------
        tool_name
            Fully-qualified tool name (e.g. ``gmail.search_threads``).
        arguments
            Tool-call arguments.  Should already be redacted if PII was
            present — the logger does **not** re-redact.
        caller_agent
            Identifier of the calling agent.
        caller_skill
            Identifier of the calling skill.
        case_id
            Support case identifier.
        result
            ``"allowed"``, ``"denied"``, or ``"error"``.
        denial_reason
            Human-readable reason (required when *result* is ``denied``
            or ``error``).
        latency_ms
            Permission-check latency in milliseconds, if measured.
        """
        record: dict[str, Any] = {
            "timestamp": self._now(),
            "tool_name": tool_name,
            "arguments": arguments,
            "caller_agent": caller_agent,
            "caller_skill": caller_skill,
            "case_id": case_id,
            "result": result,
            "denial_reason": denial_reason,
            "latency_ms": latency_ms,
        }
        self._append(self.tool_calls_path, record)

    def log_permission_violation(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        case_id: str,
        reason: str,
    ) -> None:
        """Append a permission-violation record.

        Violations are *denied* calls that represent a policy breach
        attempt (e.g. an agent trying to call ``gmail.send_email``).

        Parameters
        ----------
        tool_name
            The tool that was denied.
        arguments
            Arguments of the denied call (should be redacted).
        case_id
            Support case identifier.
        reason
            Why the call was denied.
        """
        record: dict[str, Any] = {
            "timestamp": self._now(),
            "tool_name": tool_name,
            "arguments": arguments,
            "case_id": case_id,
            "reason": reason,
            "latency_ms": None,
        }
        self._append(self.violations_path, record)

    # ------------------------------------------------------------------ #
    # Public API — reading
    # ------------------------------------------------------------------ #

    def get_tool_calls(self, case_id: str | None = None) -> list[dict[str, Any]]:
        """Return tool-call records, optionally filtered by *case_id*.

        Parameters
        ----------
        case_id
            If provided, only records with this ``case_id`` are returned.

        Returns
        -------
        list[dict[str, Any]]
            Chronologically-ordered list of records.
        """
        records = self._read_jsonl(self.tool_calls_path)
        if case_id is not None:
            records = [r for r in records if r.get("case_id") == case_id]
        return records

    def get_violations(self, case_id: str | None = None) -> list[dict[str, Any]]:
        """Return permission-violation records, optionally filtered by *case_id*.

        Parameters
        ----------
        case_id
            If provided, only records with this ``case_id`` are returned.

        Returns
        -------
        list[dict[str, Any]]
            Chronologically-ordered list of records.
        """
        records = self._read_jsonl(self.violations_path)
        if case_id is not None:
            records = [r for r in records if r.get("case_id") == case_id]
        return records

    # ------------------------------------------------------------------ #
    # Public API — maintenance
    # ------------------------------------------------------------------ #

    def clear(self) -> None:
        """Truncate both log files (for fresh test runs).

        Removes the files entirely rather than zeroing them, so the
        next write recreates them cleanly.
        """
        for path in (self.tool_calls_path, self.violations_path):
            if path.exists():
                path.unlink()

    # ------------------------------------------------------------------ #
    # Introspection
    # ------------------------------------------------------------------ #

    def stats(self) -> dict[str, int]:
        """Return a summary of how many records exist in each log file."""
        return {
            "tool_calls": len(self._read_jsonl(self.tool_calls_path)),
            "violations": len(self._read_jsonl(self.violations_path)),
        }


# ---------------------------------------------------------------------- #
# Self-test
# ---------------------------------------------------------------------- #
if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        logger = AuditLogger(log_dir=tmpdir)

        # --- log some tool calls ---------------------------------------
        logger.log_tool_call(
            tool_name="gmail.search_threads",
            arguments={"query": "DRP-1234"},
            caller_agent="cs-agent",
            caller_skill="kb-search",
            case_id="CS-001",
            result="allowed",
            latency_ms=0.5,
        )
        logger.log_tool_call(
            tool_name="gmail.send_email",
            arguments={"to": "[REDACTED_EMAIL]"},
            caller_agent="cs-agent",
            caller_skill="draft-response",
            case_id="CS-001",
            result="denied",
            denial_reason="send_email is always denied",
            latency_ms=0.3,
        )
        logger.log_tool_call(
            tool_name="gmail.search_threads",
            arguments={"query": "refund"},
            caller_agent="cs-agent",
            caller_skill="kb-search",
            case_id="CS-002",
            result="allowed",
            latency_ms=0.4,
        )

        # --- log a violation -------------------------------------------
        logger.log_permission_violation(
            tool_name="gmail.send_email",
            arguments={"to": "[REDACTED_EMAIL]"},
            case_id="CS-001",
            reason="send_email is always denied — no override allowed",
        )

        # --- verify reads ----------------------------------------------
        all_calls = logger.get_tool_calls()
        assert len(all_calls) == 3, f"Expected 3 tool calls, got {len(all_calls)}"

        cs001_calls = logger.get_tool_calls(case_id="CS-001")
        assert len(cs001_calls) == 2, f"Expected 2 CS-001 calls, got {len(cs001_calls)}"

        all_violations = logger.get_violations()
        assert len(all_violations) == 1, f"Expected 1 violation, got {len(all_violations)}"

        cs001_violations = logger.get_violations(case_id="CS-001")
        assert len(cs001_violations) == 1

        cs002_violations = logger.get_violations(case_id="CS-002")
        assert len(cs002_violations) == 0, "CS-002 should have no violations"

        stats = logger.stats()
        assert stats["tool_calls"] == 3
        assert stats["violations"] == 1

        # --- verify timestamps are timezone-aware ----------------------
        for call in all_calls:
            ts = call["timestamp"]
            parsed = datetime.fromisoformat(ts)
            assert parsed.tzinfo is not None, f"Timestamp {ts} is not timezone-aware"

        # --- clear and verify ------------------------------------------
        logger.clear()
        assert len(logger.get_tool_calls()) == 0
        assert len(logger.get_violations()) == 0

        print("All AuditLogger self-tests passed ✓")
        print(f"  Log dir used: {tmpdir}")
