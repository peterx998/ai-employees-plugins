#!/usr/bin/env python3
"""
run_agent_batch.py — Full pipeline: Golden Set → Agent → Eval → Regression.

This runner proves the end-to-end evaluation path:

  1. Load golden_set_v1.yaml
  2. Select the intended case set (all / --case-id / --max-cases)
  3. Run each selected case through an adapter (mock/codex/hermes)
  4. Save actual_outputs/current/*.json
  5. Evaluate exactly the selected cases against the fresh outputs
  6. Optionally compare against a baseline scorecard

Important: when --max-cases or --case-id is used, evaluation must use the same
selected cases. Otherwise the evaluator sees missing outputs for ungenerated
cases and reports false pending failures.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime

# Add runner to path
sys.path.insert(0, str(Path(__file__).parent))

from evaluator import Evaluator
from run_agent_case import load_golden_set, create_adapter, run_single_case


def select_cases(cases, case_id=None, max_cases=0):
    """Return the exact subset of cases that this run should generate/evaluate."""
    selected = list(cases)

    if case_id:
        selected = [c for c in selected if c.get("id") == case_id]
        if not selected:
            print(f"ERROR: Case {case_id} not found", file=sys.stderr)
            sys.exit(2)

    if max_cases and max_cases > 0 and len(selected) > max_cases:
        print(f"  Capping at {max_cases} of {len(selected)} cases")
        selected = selected[:max_cases]

    return selected


def run_evaluation(agent, golden_set_path, actual_dir, output_path, cases):
    """Run evaluation on actual outputs for the same selected case set."""
    ev = Evaluator(agent=agent, golden_set_path=golden_set_path)
    summary = ev.evaluate_batch(cases=cases, actual_dir=actual_dir)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    return summary


def run_regression_comparison(agent, baseline_path, candidate_path):
    """Run regression comparison between baseline and candidate scorecards."""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
    from compare_regression import compare_scorecards

    if not Path(baseline_path).exists():
        print(f"  ⚠ Baseline not found: {baseline_path} — skipping regression")
        return None

    if not Path(candidate_path).exists():
        print(f"  ⚠ Candidate not found: {candidate_path} — skipping regression")
        return None

    baseline = json.loads(Path(baseline_path).read_text(encoding="utf-8"))
    candidate = json.loads(Path(candidate_path).read_text(encoding="utf-8"))

    return compare_scorecards(baseline, candidate)


def main():
    parser = argparse.ArgumentParser(
        description="Full agent evaluation pipeline: Golden Set → Agent → Eval → Regression"
    )
    parser.add_argument("--agent", default="customer-support", help="Agent name")
    parser.add_argument("--golden-set", default=None, help="Path to golden_set_v1.yaml")
    parser.add_argument("--adapter", default="mock", choices=["mock", "codex", "hermes", "hermes-dry-run"], help="Agent adapter")
    parser.add_argument("--timeout", type=int, default=180, help="Per-case timeout in seconds")
    parser.add_argument("--model", help="Model override")
    parser.add_argument("--api-url", help="Hermes API URL")
    parser.add_argument("--output-dir", default=None, help="Output dir for actual outputs")
    parser.add_argument("--eval-output", default=None, help="Path for eval results JSON")
    parser.add_argument("--baseline-scorecard", default=None, help="Baseline scorecard for regression comparison")
    parser.add_argument("--generate-only", action="store_true", help="Only generate outputs, skip evaluation")
    parser.add_argument("--eval-only", action="store_true", help="Only evaluate, skip generation")
    parser.add_argument("--actual-dir", default=None, help="Directory of existing actual outputs for --eval-only")
    parser.add_argument("--skip-regression", action="store_true", help="Skip regression comparison")
    parser.add_argument("--case-id", help="Run only a specific case")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--max-cases", type=int, default=0, help="Cap number of cases (0 = all)")
    args = parser.parse_args()

    agent = args.agent
    golden_set_path = args.golden_set or f"{agent}/evals/golden_set_v1.yaml"
    output_dir = args.output_dir or f"{agent}/evals/actual_outputs/current"
    eval_output = args.eval_output or f"{agent}/reports/eval_results.json"
    baseline_scorecard = args.baseline_scorecard or f"experiments/scorecards/{agent}/baseline.json"

    if not os.path.exists(golden_set_path):
        print(f"ERROR: Golden set not found: {golden_set_path}", file=sys.stderr)
        sys.exit(2)

    all_cases = load_golden_set(golden_set_path)
    cases = select_cases(all_cases, case_id=args.case_id, max_cases=args.max_cases)

    print("=" * 60)
    print("  Agent Evaluation Pipeline")
    print("=" * 60)
    print(f"  Agent:   {agent}")
    print(f"  Adapter: {args.adapter}")
    print(f"  Golden:  {golden_set_path}")
    print(f"  Cases:   {len(cases)} / {len(all_cases)}")
    print()

    pipeline_start = time.time()
    verdicts = []

    # Phase 1: Generate outputs
    if not args.eval_only:
        print("─" * 60)
        print("  Phase 1/3: Generate actual outputs")
        print("─" * 60)

        adapter = create_adapter(
            args.adapter,
            agent,
            timeout=args.timeout,
            model=args.model,
            api_url=args.api_url,
        )

        total = len(cases)
        success = 0
        failed = 0

        for i, case in enumerate(cases):
            cid = case.get("id", "?")
            print(f"  [{i + 1}/{total}] {cid}", end=" ")

            ok, path, elapsed = run_single_case(case, adapter, output_dir, verbose=args.verbose)
            if ok:
                success += 1
            else:
                failed += 1

            result = json.loads(Path(path).read_text(encoding="utf-8")) if Path(path).exists() else {}
            cat = result.get("category", "?")
            pri = result.get("priority", "?")
            print(f"{'✓' if ok else '✗'} {cat}/{pri} ({elapsed:.1f}s)")

        print(f"\n  Generated: {success}/{total} success, {failed} failed")
        print(f"  Output: {output_dir}")

        if args.generate_only:
            print("\n  ✓ Generation complete (--generate-only)")
            sys.exit(0 if failed == 0 else 1)

    # Phase 2: Evaluate outputs
    print()
    print("─" * 60)
    print("  Phase 2/3: Evaluate outputs")
    print("─" * 60)

    actual_dir = args.actual_dir or output_dir
    summary = run_evaluation(agent, golden_set_path, actual_dir, eval_output, cases)

    ev = Evaluator(agent=agent, golden_set_path=golden_set_path)
    ev.print_summary(summary)

    verdicts.append(("evaluation", summary["verdict"]))

    if args.eval_only:
        print("\n  ✓ Evaluation complete (--eval-only)")
        sys.exit(0 if summary["verdict"] == "PASS" else 1)

    # Phase 3: Regression comparison
    if not args.skip_regression:
        print()
        print("─" * 60)
        print("  Phase 3/3: Regression comparison")
        print("─" * 60)

        # For first run, create a baseline from the candidate so regression is a no-op.
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
                print("  ⚠ Hard constraint regression detected")
            if comparison.get("schema_regression", False):
                print("  ⚠ Schema validation regression detected")

            verdicts.append(("regression", comparison["verdict"]))

            report_dir = Path("experiments/reports")
            report_dir.mkdir(parents=True, exist_ok=True)
            report_path = report_dir / f"regression-{agent}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md"
            with open(report_path, "w", encoding="utf-8") as f:
                from compare_regression import generate_report
                f.write(generate_report(comparison))
            print(f"  Report: {report_path}")

    # Final verdict
    pipeline_elapsed = time.time() - pipeline_start

    print()
    print("=" * 60)
    print("  Pipeline Complete")
    print("=" * 60)
    for phase, verdict in verdicts:
        status = "✓" if verdict in ("PASS", "NO_CHANGE", "IMPROVED") else "✗"
        print(f"  {status} {phase}: {verdict}")
    print(f"  Time: {pipeline_elapsed:.1f}s")

    overall_pass = all(v in ("PASS", "NO_CHANGE", "IMPROVED") for _, v in verdicts)

    if overall_pass:
        print("\n  ✓ OVERALL: PASS")
        sys.exit(0)

    print("\n  ✗ OVERALL: FAIL")
    sys.exit(1)


if __name__ == "__main__":
    main()
