#!/usr/bin/env python3
"""
ci_multiturn_check.py — CI step: run multi-turn conversations and state-diff evaluation.

Runs the MultiTurnRunner with a mock adapter that follows expected actions,
captures the final state, and compares against expected_final_state.json using
StateDiffEvaluator. Exits non-zero if any critical field mismatches.

Usage:
  python3 scripts/ci_multiturn_check.py
"""

import json
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root / "agent-evaluation" / "runner"))

from multiturn_runner import MultiTurnRunner
from state_diff_evaluator import StateDiffEvaluator


def main():
    print("=" * 60)
    print("  Multi-turn Conversation + State Diff (CI)")
    print("=" * 60)

    conv_path = "customer-support/evals/multiturn/conversations_v1.yaml"
    state_path = "customer-support/evals/multiturn/initial_state.json"
    expected_path = "customer-support/evals/multiturn/expected_final_state.json"

    # Load runner
    runner = MultiTurnRunner(conv_path, state_path)
    print(f"  Conversations loaded: {len(runner.conversations)}")

    # Load state diff evaluator
    diff_ev = StateDiffEvaluator(expected_path)
    print(f"  Expected states loaded: {len(diff_ev.expected_states)}")
    print()

    # ─── Phase 1: Run all conversations with mock adapter ───
    print("─" * 60)
    print("  Phase 1: Run conversations (mock adapter)")
    print("─" * 60)

    actual_states: dict[str, dict] = {}
    conv_passed = 0
    conv_failed = 0

    # conversations is a dict: {conv_id: conv_dict}
    for cid, conv in runner.conversations.items():
        try:
            result = runner.run_conversation(cid)
            # ConversationResult is a dataclass — use attribute access
            actual_state = result.final_state if hasattr(result, 'final_state') else {}
            actual_states[cid] = actual_state
            turns = result.turns_completed if hasattr(result, 'turns_completed') else 0
            icon = "✓" if turns > 0 else "✗"
            print(f"  {icon} {cid}: {turns} turns completed")
            if hasattr(result, 'errors') and result.errors:
                for err in result.errors[:2]:
                    print(f"      ⚠ {err}")
            conv_passed += 1
        except Exception as e:
            print(f"  ✗ {cid}: ERROR — {e}")
            actual_states[cid] = {}
            conv_failed += 1

    print(f"\n  Conversations run: {conv_passed} ok, {conv_failed} failed")

    # ─── Phase 2: State diff evaluation ───
    print()
    print("─" * 60)
    print("  Phase 2: State diff evaluation")
    print("─" * 60)

    batch_result = diff_ev.evaluate_batch(actual_states)
    diff_ev.print_summary(batch_result)

    # ─── Phase 3: Negative test — inject a critical violation ───
    print()
    print("─" * 60)
    print("  Phase 3: Negative test (critical field violation)")
    print("─" * 60)

    # Take MT-002 (medical escalation) and flip email_sent to True
    if "MT-002" in diff_ev.expected_states:
        bad_state = dict(actual_states.get("MT-002", {}))
        bad_state["email_sent"] = True  # CRITICAL: should be False for P1 medical
        neg_result = diff_ev.evaluate("MT-002", bad_state)
        print(f"  MT-002 with email_sent=True: matches={neg_result.matches} score={neg_result.score:.2f}")
        print(f"  Critical diffs: {[d for d in neg_result.diffs if d.get('critical')]}")
        if neg_result.matches:
            print("  ✗ FAIL: Critical violation not detected!")
            sys.exit(1)
        print(f"  ✓ Critical violation correctly detected")
    else:
        print("  (skipped — MT-002 not found)")

    # ─── Verdict ───
    print()
    print("=" * 60)
    if batch_result["critical_failures"] > 0:
        print(f"  Multi-turn CI: FAIL ({batch_result['critical_failures']} critical failures)")
        sys.exit(1)
    elif batch_result["failed"] > 0:
        print(f"  Multi-turn CI: PARTIAL ({batch_result['failed']} non-critical failures)")
        # Non-critical failures don't block CI
    else:
        print(f"  Multi-turn CI: PASS ({batch_result['passed']}/{batch_result['total_conversations']} passed)")
    print("=" * 60)


if __name__ == "__main__":
    main()
