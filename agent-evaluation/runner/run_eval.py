#!/usr/bin/env python3
"""
run_eval.py — CLI wrapper for the unified Evaluator.

All scoring logic lives in evaluator.py. This file is just a CLI entry point.

Usage:
  # Evaluate with actual outputs directory
  python run_eval.py --golden-set customer-support/evals/golden_set_v1.yaml \
    --agent customer-support \
    --actual-dir customer-support/evals/actual_outputs/baseline

  # Evaluate with single actual output file
  python run_eval.py --golden-set ... --agent customer-support --case-id CS-MED-001 --actual output.json

  # Print cases without evaluating (interactive mode)
  python run_eval.py --golden-set ... --agent customer-support

Exit codes:
  0 — PASS (verdict == PASS)
  1 — FAIL (verdict == FAIL, including no actual outputs)
  2 — Error in setup
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Import the unified evaluator
sys.path.insert(0, str(Path(__file__).parent))
from evaluator import Evaluator


def main():
    parser = argparse.ArgumentParser(description="Golden Set Evaluation Runner (CLI wrapper for evaluator.py)")
    parser.add_argument("--golden-set", required=True, help="Path to golden_set_v1.yaml")
    parser.add_argument("--agent", help="Agent name (e.g., customer-support)")
    parser.add_argument("--case-id", help="Run specific case ID only")
    parser.add_argument("--actual", help="Path to actual output JSON file (single case mode)")
    parser.add_argument("--actual-dir", help="Directory containing per-case actual output JSON files")
    parser.add_argument("--schema", help="Path to JSON Schema for output validation")
    parser.add_argument("--output", help="Output path for eval_results.json (default: {agent}/reports/eval_results.json)")
    args = parser.parse_args()

    if not os.path.exists(args.golden_set):
        print(f"ERROR: Golden set file not found: {args.golden_set}", file=sys.stderr)
        sys.exit(2)

    # Create evaluator
    ev = Evaluator(
        agent=args.agent or "customer-support",
        schema_path=args.schema,
        golden_set_path=args.golden_set,
    )

    cases = ev.cases

    # Filter by case_id if specified
    if args.case_id:
        cases = [c for c in cases if c.get("id") == args.case_id]
        if not cases:
            print(f"ERROR: No case found with ID: {args.case_id}", file=sys.stderr)
            sys.exit(2)

    # Load actual outputs
    actual_outputs = None
    if args.actual and len(cases) == 1:
        with open(args.actual, "r", encoding="utf-8") as f:
            actual_outputs = [json.load(f)]
    elif args.actual_dir:
        actual_outputs = []
        for case in cases:
            cid = case.get("id", "")
            fpath = Path(args.actual_dir) / f"{cid}.json"
            if fpath.exists():
                with open(fpath, "r", encoding="utf-8") as f:
                    actual_outputs.append(json.load(f))
            else:
                actual_outputs.append(None)

    # Evaluate
    summary = ev.evaluate_batch(cases=cases, actual_outputs=actual_outputs)

    # Print summary
    ev.print_summary(summary)

    # Save results
    output_path = args.output
    if not output_path:
        golden_set_dir = Path(args.golden_set).parent
        agent_root = golden_set_dir.parent
        output_path = agent_root / "reports" / "eval_results.json"

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"\nFull results saved to: {output_path}")

    # Exit code
    if summary["verdict"] != "PASS":
        if summary.get("pending", 0) > 0:
            print("FAIL: No actual outputs provided. CI gate requires real evaluation.", file=sys.stderr)
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
