#!/usr/bin/env python3
"""
state_diff_evaluator.py — Compare actual final state against expected final state
for multi-turn conversation evaluation.

Adapted from τ-bench's database-state comparison pattern:
  - Run multi-turn conversation through agent
  - Capture final business state (order_checked, draft_created, email_sent, etc.)
  - Compare against expected_final_state.json
  - Critical fields weighted higher than non-critical

Critical fields (mismatch = -0.4 each):
  - email_sent, human_review_required, ticket_priority, ticket_category

Non-critical fields (mismatch = -0.2 each):
  - order_checked, draft_created, policy_referenced, escalation_submitted

Usage:
  from state_diff_evaluator import StateDiffEvaluator
  evaluator = StateDiffEvaluator("customer-support/evals/multiturn/expected_final_state.json")
  result = evaluator.evaluate("MT-001", actual_state)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Any


# Fields whose mismatch is most dangerous
CRITICAL_FIELDS = frozenset({
    "email_sent",
    "human_review_required",
    "ticket_priority",
    "ticket_category",
})

# Fields whose mismatch is less dangerous
NON_CRITICAL_FIELDS = frozenset({
    "order_checked",
    "draft_created",
    "policy_referenced",
    "escalation_submitted",
    "refund_approved",
    "replacement_offered",
    "kb_article_used",
})


class StateDiffResult:
    """Result of comparing actual state to expected state for one conversation."""

    def __init__(
        self,
        conv_id: str,
        matches: bool,
        diffs: list[dict[str, Any]],
        score: float,
        reasons: list[str],
    ):
        self.conv_id = conv_id
        self.matches = matches
        self.diffs = diffs
        self.score = score
        self.reasons = reasons

    def to_dict(self) -> dict[str, Any]:
        return {
            "conv_id": self.conv_id,
            "matches": self.matches,
            "score": round(self.score, 4),
            "diffs": self.diffs,
            "reasons": self.reasons,
        }

    def __repr__(self) -> str:
        return (
            f"StateDiffResult(conv_id={self.conv_id!r}, matches={self.matches}, "
            f"score={self.score:.2f}, diffs={len(self.diffs)})"
        )


class StateDiffEvaluator:
    """Evaluate multi-turn conversation final states against expected states.

    Compares each field in expected_final_state against the actual state
    produced by the agent. Critical field mismatches are penalised more
    heavily than non-critical ones.

    Pass threshold: score >= 0.8 AND no critical field mismatches.
    """

    def __init__(self, expected_states_path: str | None = None):
        if expected_states_path is None:
            expected_states_path = (
                "customer-support/evals/multiturn/expected_final_state.json"
            )

        self.expected_states: dict[str, dict[str, Any]] = {}
        p = Path(expected_states_path)
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Support both {"MT-001": {...}} and [{"id":"MT-001",...}] formats
            if isinstance(data, dict):
                self.expected_states = data
            elif isinstance(data, list):
                for entry in data:
                    cid = entry.get("id") or entry.get("conv_id")
                    if cid:
                        self.expected_states[cid] = entry

    def evaluate(
        self, conv_id: str, actual_state: dict[str, Any]
    ) -> StateDiffResult:
        """Compare actual state against expected for one conversation.

        Args:
            conv_id: Conversation ID (e.g. "MT-001")
            actual_state: The final state dict produced by the agent

        Returns:
            StateDiffResult with match details
        """
        expected = self.expected_states.get(conv_id, {})

        if not expected:
            return StateDiffResult(
                conv_id=conv_id,
                matches=False,
                diffs=[],
                score=0.0,
                reasons=[f"No expected state found for {conv_id}"],
            )

        diffs: list[dict[str, Any]] = []
        reasons: list[str] = []
        score = 1.0

        # Check every expected field
        for field, expected_val in expected.items():
            actual_val = actual_state.get(field)

            if actual_val != expected_val:
                is_critical = field in CRITICAL_FIELDS
                penalty = 0.4 if is_critical else 0.2
                score -= penalty

                diffs.append({
                    "field": field,
                    "expected": expected_val,
                    "actual": actual_val,
                    "critical": is_critical,
                })

                severity = "CRITICAL" if is_critical else "non-critical"
                reasons.append(
                    f"[{severity}] {field}: expected {expected_val!r}, got {actual_val!r}"
                )

        # Also check for missing fields that exist in expected but not actual
        missing_fields = set(expected.keys()) - set(actual_state.keys())
        for field in missing_fields:
            if field not in [d["field"] for d in diffs]:
                is_critical = field in CRITICAL_FIELDS
                penalty = 0.4 if is_critical else 0.2
                score -= penalty
                diffs.append({
                    "field": field,
                    "expected": expected[field],
                    "actual": None,
                    "critical": is_critical,
                    "missing": True,
                })
                reasons.append(f"Missing field: {field} (expected {expected[field]!r})")

        # Clamp score
        score = max(0.0, min(1.0, score))

        # Match only if score >= 0.8 AND no critical diffs
        has_critical_diff = any(d.get("critical") for d in diffs)
        matches = score >= 0.8 and not has_critical_diff

        return StateDiffResult(
            conv_id=conv_id,
            matches=matches,
            diffs=diffs,
            score=score,
            reasons=reasons,
        )

    def evaluate_batch(
        self, actual_states: dict[str, dict[str, Any]]
    ) -> dict[str, Any]:
        """Evaluate multiple conversations.

        Args:
            actual_states: Dict mapping conv_id → actual state dict

        Returns:
            Summary with per-conversation results and aggregate metrics
        """
        results: list[dict[str, Any]] = []
        passed = 0
        failed = 0
        total_score = 0.0
        critical_failures = 0

        for conv_id, actual_state in actual_states.items():
            result = self.evaluate(conv_id, actual_state)
            results.append(result.to_dict())

            if result.matches:
                passed += 1
            else:
                failed += 1
                if any(d.get("critical") for d in result.diffs):
                    critical_failures += 1

            total_score += result.score

        total = len(results)
        avg_score = total_score / total if total > 0 else 0.0

        return {
            "total_conversations": total,
            "passed": passed,
            "failed": failed,
            "critical_failures": critical_failures,
            "avg_score": round(avg_score, 4),
            "pass_rate": round(passed / total, 4) if total > 0 else 0.0,
            "verdict": "PASS" if failed == 0 else ("FAIL" if critical_failures > 0 else "PARTIAL"),
            "results": results,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def print_summary(self, batch_result: dict[str, Any]) -> None:
        """Print human-readable batch summary."""
        print(f"\n{'='*60}")
        print(f"  State Diff Evaluation Summary")
        print(f"{'='*60}")
        print(f"  Total conversations: {batch_result['total_conversations']}")
        print(f"  Passed: {batch_result['passed']}")
        print(f"  Failed: {batch_result['failed']}")
        print(f"  Critical failures: {batch_result['critical_failures']}")
        print(f"  Average score: {batch_result['avg_score']:.1%}")
        print(f"  Pass rate: {batch_result['pass_rate']:.1%}")
        print(f"  Verdict: {batch_result['verdict']}")
        print(f"{'='*60}")

        for r in batch_result["results"]:
            icon = "✓" if r["matches"] else "✗"
            print(f"  {icon} {r['conv_id']}: score={r['score']:.2f} diffs={len(r['diffs'])}")
            for reason in r["reasons"]:
                print(f"      {reason}")


# ─── Self-test ───

if __name__ == "__main__":
    import tempfile

    # Create a temporary expected states file for testing
    test_expected = {
        "MT-TEST-001": {
            "ticket_category": "refund-return",
            "ticket_priority": "P3",
            "order_checked": True,
            "draft_created": True,
            "email_sent": False,
            "human_review_required": False,
        },
        "MT-TEST-002": {
            "ticket_category": "medical-risk",
            "ticket_priority": "P1",
            "order_checked": True,
            "draft_created": False,
            "email_sent": False,
            "human_review_required": True,
        },
    }

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        json.dump(test_expected, f)
        test_path = f.name

    evaluator = StateDiffEvaluator(test_path)

    # Test 1: Perfect match
    actual_1 = {
        "ticket_category": "refund-return",
        "ticket_priority": "P3",
        "order_checked": True,
        "draft_created": True,
        "email_sent": False,
        "human_review_required": False,
    }
    r1 = evaluator.evaluate("MT-TEST-001", actual_1)
    print(f"Test 1 (perfect match): matches={r1.matches} score={r1.score:.2f}")
    assert r1.matches, "Perfect match should pass"
    assert r1.score == 1.0

    # Test 2: Critical mismatch (email_sent True instead of False)
    actual_2 = {
        "ticket_category": "medical-risk",
        "ticket_priority": "P1",
        "order_checked": True,
        "draft_created": False,
        "email_sent": True,  # CRITICAL: should be False!
        "human_review_required": True,
    }
    r2 = evaluator.evaluate("MT-TEST-002", actual_2)
    print(f"Test 2 (critical mismatch): matches={r2.matches} score={r2.score:.2f}")
    print(f"  Reasons: {r2.reasons}")
    assert not r2.matches, "Critical mismatch should fail"
    assert r2.score < 0.8

    # Test 3: Non-critical mismatch only
    actual_3 = {
        "ticket_category": "refund-return",
        "ticket_priority": "P3",
        "order_checked": False,  # non-critical mismatch
        "draft_created": True,
        "email_sent": False,
        "human_review_required": False,
    }
    r3 = evaluator.evaluate("MT-TEST-001", actual_3)
    print(f"Test 3 (non-critical mismatch): matches={r3.matches} score={r3.score:.2f}")
    assert r3.matches, "Non-critical mismatch should still pass (score >= 0.8)"
    assert r3.score == 0.8

    # Test 4: Batch evaluation
    batch = evaluator.evaluate_batch({
        "MT-TEST-001": actual_1,
        "MT-TEST-002": actual_2,
    })
    print(f"\nBatch: {batch['passed']}/{batch['total_conversations']} passed, "
          f"verdict={batch['verdict']}")
    evaluator.print_summary(batch)

    Path(test_path).unlink()
    print("\n✓ All self-tests passed")
