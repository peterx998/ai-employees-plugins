#!/usr/bin/env python3
"""
run_agent_batch.py — Full pipeline: Golden Set → Agent → Eval → Regression.

This is the COMPLETE evaluation loop that proves agents can produce real outputs:

  1. Load golden_set_v1.yaml
  2. Run each case through an AI agent adapter (mock/codex/hermes)
  3. Save actual_outputs/current/*.json
  4. Run evaluator on the fresh outputs
  5. Compare against baseline scorecard (regression check)
  6. Report PASS/FAIL verdict

This replaces the old pattern of:
  "CI evaluates hand-written JSON → can only prove JSON writing, not agent capability"

With:
  "CI runs agent → evaluates real outputs → proves agent stability"

Usage:
  # Full pipeline with mock adapter (CI safe, no API costs)
  python run_agent_batch.py --agent customer-support --adapter mock

  # Full pipeline with real agent
  python run_agent_batch.py --agent customer-support --adapter hermes --api-url http://localhost:8787/v1

  # Just generate outputs (skip eval)
  python run_agent_batch.py --agent customer-support --adapter mock --generate-only

  # Just evaluate existing outputs
  python run_agent_batch.py --agent customer-support --eval-only --actual-dir path/to/outputs/
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

# Add runner to path
sys.path.insert(0, str(Path(__file__).parent))

from evaluator import Evaluator
from run_agent_case import load_golden_set, create_adapter, run_single_case


def run_evaluation(agent, golden_set_path, actual_dir, output_path):
    """Run evaluation on actual outputs and return summary."""
    ev = Evaluator(
        agent=agent,
        golden_set_path=golden_set_path,
    )

    summary = ev.evaluate_batch(cases=ev.cases, actual_dir=actual_dir)

    # Save results
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    return summary


def run_regression_comparison(agent, baseline_path, candidate_path):
    """Run regression comparison between baseline and candidate scorecards."""
    # Import compare_regression functionality
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
    from compare_regression import compare_scorecards, generate_report

    if not Path(baseline_path).exists():
        print(f"  ⚠ Baseline not found: {baseline_path} — skipping regression")
        return None

    if not Path(candidate_path).exists():
        print(f"  ⚠ Candidate not found: {candidate_path} — skipping regression")
        return None

    baseline = json.loads(Path(baseline_path).read_text())
    candidate = json.loads(Path(candidate_path).read_text())

    comparison = compare_scorecards(baseline, candidate)
    return comparison


def main():
    parser = argparse.ArgumentParser(
        description="Full agent evaluation pipeline: Golden Set → Agent → Eval → Regression"
    )
    parser.add_argument("--agent", default="customer-support",
                       help="Agent name (default: customer-support)")
    parser.add_argument("--golden-set", default=None,
                       help="Path to golden_set_v1.yaml (auto-detected from agent)")
    parser.add_argument("--adapter", default="mock",
                       choices=["mock", "codex", "hermes"],
                       help="Agent adapter (default: mock)")
    parser.add_argument("--timeout", type=int, default=180,
                       help="Per-case timeout in seconds")
    parser.add_argument("--model", help="Model override")
    parser.add_argument("--api-url", help="Hermes API URL")
    parser.add_argument("--output-dir", default=None,
                       help="Output dir for actual outputs (default: <agent>/evals/actual_outputs/current/)")
    parser.add_argument("--eval-output", default=None,
                       help="Path for eval results JSON")
    parser.add_argument("--baseline-scorecard", default=None,
                       help="Path to baseline scorecard for regression comparison")
    parser.add_argument("--generate-only", action="store_true",
                       help="Only generate outputs, skip evaluation")
    parser.add_argument("--eval-only", action="store_true",
                       help="Only evaluate, skip agent generation")
    parser.add_argument("--actual-dir", default=None,
                       help="Directory of existing actual outputs (for --eval-only)")
    parser.add_argument("--skip-regression", action="store_true",
                       help="Skip regression comparison")
    parser.add_argument("--case-id", help="Run only a specific case")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--max-cases", type=int, default=0,
                       help="Cap number of cases (0 = all, for quick tests)")
    args = parser.parse_args()

    agent = args.agent

    # Auto-detect paths
    golden_set_path = args.golden_set or f"{agent}/evals/golden_set_v1.yaml"
    output_dir = args.output_dir or f"{agent}/evals/actual_outputs/current"
    eval_output = args.eval_output or f"{agent}/reports/eval_results.json"
    baseline_scorecard = args.baseline_scorecard or f"experiments/scorecards/{agent}/baseline.json"

    # Validate
    if not args.eval_only and not os.path.exists(golden_set_path):
        print(f"ERROR: Golden set not found: {golden_set_path}", file=sys.stderr)
        sys.exit(2)

    print("=" * 60)
    print("  Agent Evaluation Pipeline")
    print("=" * 60)
    print(f"  Agent:   {agent}")
    print(f"  Adapter: {args.adapter}")
    print(f"  Golden:  {golden_set_path}")
    print()

    pipeline_start = time.time()
    verdicts = []

    # ─── Phase 1: Generate actual outputs ───
    if not args.eval_only:
        print("─" * 60)
        print("  Phase 1/3: Generate actual outputs")
        print("─" * 60)

        cases = load_golden_set(golden_set_path)

        if args.case_id:
            cases = [c for c in cases if c.get("id") == args.case_id]
            if not cases:
                print(f"ERROR: Case {args.case_id} not found", file=sys.stderr)
                sys.exit(2)

        if args.max_cases > 0 and len(cases) > args.max_cases:
            print(f"  Capping at {args.max_cases} of {len(cases)} cases")
            cases = cases[:args.max_cases]

        adapter = create_adapter(args.adapter, agent,
                                timeout=args.timeout,
                                model=args.model,
                                api_url=args.api_url)

        total = len(cases)
        success = 0
        failed = 0

        for i, case in enumerate(cases):
            cid = case.get("id", "?")
            print(f"  [{i+1}/{total}] {cid}", end=" ")

            ok, path, elapsed = run_single_case(case, adapter, output_dir,
                                                verbose=args.verbose)
            if ok:
                success += 1
            else:
                failed += 1

            result = json.loads(Path(path).read_text()) if Path(path).exists() else {}
            cat = result.get("category", "?")
            pri = result.get("priority", "?")
            print(f"{'✓' if ok else '✗'} {cat}/{pri} ({elapsed:.1f}s)")

        print(f"\n  Generated: {success}/{total} success, {failed} failed")
        print(f"  Output: {output_dir}")

        if args.generate_only:
            print(f"\n  ✓ Generation complete (--generate-only)")
            sys.exit(0 if failed == 0 else 1)

    # ─── Phase 2: Evaluate ───
    print()
    print("─" * 60)
    print("  Phase 2/3: Evaluate outputs")
    print("─" * 60)

    actual_dir = args.actual_dir or output_dir
    summary = run_evaluation(agent, golden_set_path, actual_dir, eval_output)

    ev = Evaluator(agent=agent, golden_set_path=golden_set_path)
    ev.print_summary(summary)

    verdicts.append(("evaluation", summary["verdict"]))

    if args.eval_only:
        print(f"\n  ✓ Evaluation complete (--eval-only)")
        sys.exit(0 if summary["verdict"] == "PASS" else 1)

    # ─── Phase 3: Regression comparison ───
    if not args.skip_regression:
        print()
        print("─" * 60)
        print("  Phase 3/3: Regression comparison")
        print("─" * 60)

        # Ensure baseline exists — create from first run baseline if needed
        if not Path(baseline_scorecard).exists():
            print(f"  Creating initial baseline scorecard: {baseline_scorecard}")
            import shutil
            Path(baseline_scorecard).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(eval_output, baseline_scorecard)

        comparison = run_regression_comparison(agent, baseline_scorecard, eval_output)

        if comparison:
            print(f"  Baseline score:  {comparison['baseline_score']:.1%}")
            print(f"  Candidate score: {comparison['candidate_score']:.1%}")
            print(f"  Degraded: {comparison['degraded_count']}")
            print(f"  Improved: {comparison['improved_count']}")
            print(f"  Verdict:  {comparison['verdict']}")

            if comparison.get("hard_constraint_regression", False):
                print(f"  ⚠ P1 hard constraint regression detected!")
            if comparison.get("schema_regression", False):
                print(f"  ⚠ Schema validation regression detected!")

            verdicts.append(("regression", comparison["verdict"]))

            # Save regression report
            report_dir = Path(f"experiments/reports")
            report_dir.mkdir(parents=True, exist_ok=True)
            report_path = report_dir / f"regression-{agent}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md"
            with open(report_path, "w") as f:
                from compare_regression import generate_report
                f.write(generate_report(comparison))
            print(f"  Report: {report_path}")

    # ─── Final verdict ───
    pipeline_elapsed = time.time() - pipeline_start

    print()
    print("=" * 60)
    print("  Pipeline Complete")
    print("=" * 60)
    for phase, verdict in verdicts:
        status = "✓" if verdict in ("PASS", "NO_CHANGE", "IMPROVED") else "✗"
        print(f"  {status} {phase}: {verdict}")
    print(f"  Time: {pipeline_elapsed:.1f}s")

    # Overall verdict
    overall_pass = all(
        v in ("PASS", "NO_CHANGE", "IMPROVED")
        for _, v in verdicts
    )

    if overall_pass:
        print(f"\n  ✓ OVERALL: PASS")
        sys.exit(0)
    else:
        print(f"\n  ✗ OVERALL: FAIL")
        sys.exit(1)


if __name__ == "__main__":
    main()
