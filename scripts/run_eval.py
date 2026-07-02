#!/usr/bin/env python3
"""
run_eval.py — Thin wrapper that delegates to the unified Evaluator.

DEPRECATED as standalone scorer. Use agent-evaluation/runner/run_eval.py instead.
This file exists only for backward compatibility with scripts/run_autoresearch.py.

All scoring logic: agent-evaluation/runner/evaluator.py
"""

import sys
from pathlib import Path

# Delegate to the real runner
sys.path.insert(0, str(Path(__file__).parent.parent / "agent-evaluation" / "runner"))

from evaluator import Evaluator


def run_evaluation(agent_name, golden_set_path=None, output_path=None,
                   agent_output_path=None, actual_dir=None, fail_on_no_output=True):
    """Backward-compatible wrapper. Delegates to Evaluator."""

    ev = Evaluator(
        agent=agent_name,
        golden_set_path=golden_set_path,
    )

    if not ev.cases:
        if fail_on_no_output:
            print(f"ERROR: No golden set found for agent: {agent_name}", file=sys.stderr)
            sys.exit(1)
        return {"overall_score": 0, "hard_constraint_passed": False, "verdict": "FAIL"}

    # Load actual outputs
    actual_outputs = None
    if actual_dir:
        import json
        actual_outputs = []
        for case in ev.cases:
            cid = case.get("id", "")
            fpath = Path(actual_dir) / f"{cid}.json"
            if fpath.exists():
                with open(fpath, "r", encoding="utf-8") as f:
                    actual_outputs.append(json.load(f))
            else:
                actual_outputs.append(None)

        if all(a is None for a in actual_outputs):
            if fail_on_no_output:
                print(f"ERROR: No actual outputs in {actual_dir}", file=sys.stderr)
                sys.exit(1)
            # Non-CI mode: use expected as baseline (for autoresearch only)
            actual_outputs = [c.get("expected", {}) for c in ev.cases]

    if actual_outputs is None:
        if fail_on_no_output:
            print("ERROR: No actual outputs provided.", file=sys.stderr)
            sys.exit(1)
        actual_outputs = [c.get("expected", {}) for c in ev.cases]

    summary = ev.evaluate_batch(cases=ev.cases, actual_outputs=actual_outputs)

    # Save scorecard
    if output_path is None:
        output_path = f"experiments/scorecards/{agent_name}/latest.json"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    import json
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    ev.print_summary(summary)

    # Return backward-compatible format
    return {
        "overall_score": summary["pass_rate"],
        "hard_constraint_passed": summary.get("hard_constraint_failures", 0) == 0,
        "verdict": summary["verdict"],
        "summary": summary,
    }


# Backward compat exports
SCORING_RUBRICS = {}  # Deprecated — use evaluator.RUBRICS
HARD_CONSTRAINTS = {}  # Deprecated — use evaluator.HARD_CONSTRAINTS


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Eval wrapper (delegates to evaluator.py)")
    parser.add_argument("--agent", required=True)
    parser.add_argument("--golden-set")
    parser.add_argument("--output")
    parser.add_argument("--actual-dir")
    parser.add_argument("--allow-no-output", action="store_true")
    args = parser.parse_args()

    run_evaluation(
        agent_name=args.agent,
        golden_set_path=args.golden_set,
        output_path=args.output,
        actual_dir=args.actual_dir,
        fail_on_no_output=not args.allow_no_output,
    )
