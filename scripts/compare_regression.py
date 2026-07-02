#!/usr/bin/env python3
"""
compare_regression.py — Compare evaluation results between two versions.

Adapted from karpathy/autoresearch's results.tsv comparison pattern:
  - Load two scorecards (baseline and candidate)
  - Compare case-by-case
  - Identify degraded cases (passed before, fail now)
  - Identify improved cases (failed before, pass now)
  - Generate regression report

Usage:
  python scripts/compare_regression.py --agent customer-support
  python scripts/compare_regression.py --agent customer-support --baseline path/to/baseline.json --candidate path/to/candidate.json
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime


def load_scorecard(path):
    """Load a scorecard JSON file."""
    if not Path(path).exists():
        print(f"ERROR: Scorecard not found: {path}", file=sys.stderr)
        sys.exit(1)

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def find_scorecards(agent_name):
    """Find the most recent baseline and candidate scorecards."""
    scorecard_dir = Path(f"experiments/scorecards/{agent_name}")

    if not scorecard_dir.exists():
        print(f"ERROR: No scorecards found for agent: {agent_name}", file=sys.stderr)
        sys.exit(1)

    # Find baseline
    baseline_path = scorecard_dir / "baseline.json"
    if not baseline_path.exists():
        # Use the first scorecard as baseline
        all_cards = sorted(scorecard_dir.glob("*.json"))
        if not all_cards:
            print(f"ERROR: No scorecards in {scorecard_dir}", file=sys.stderr)
            sys.exit(1)
        baseline_path = all_cards[0]

    # Find latest (most recent non-baseline)
    all_cards = sorted(scorecard_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    candidate_path = None
    for card in all_cards:
        if card.name != "baseline.json" and card.name != "latest.json":
            candidate_path = card
            break

    if candidate_path is None:
        candidate_path = scorecard_dir / "latest.json"

    return baseline_path, candidate_path


def compare_scorecards(baseline, candidate):
    """Compare two scorecards case by case."""
    baseline_cases = {c["case_id"]: c for c in baseline.get("case_results", [])}
    candidate_cases = {c["case_id"]: c for c in candidate.get("case_results", [])}

    degraded = []
    improved = []
    persistent_fail = []
    persistent_pass = []
    new_failures = []

    all_case_ids = set(baseline_cases.keys()) | set(candidate_cases.keys())

    for case_id in all_case_ids:
        b = baseline_cases.get(case_id, {})
        c = candidate_cases.get(case_id, {})

        b_passed = b.get("passed", False)
        c_passed = c.get("passed", False)

        if b_passed and not c_passed:
            degraded.append({
                "case_id": case_id,
                "baseline_score": b.get("score", 0),
                "candidate_score": c.get("score", 0),
                "details": c.get("details", {}),
            })
        elif not b_passed and c_passed:
            improved.append({
                "case_id": case_id,
                "baseline_score": b.get("score", 0),
                "candidate_score": c.get("score", 0),
            })
        elif not b_passed and not c_passed:
            persistent_fail.append({
                "case_id": case_id,
                "score": c.get("score", 0),
            })
        else:
            persistent_pass.append(case_id)

    # New failures = cases in candidate that failed but weren't in baseline
    new_failures = [d for d in degraded if d["case_id"] not in baseline_cases]

    # Determine verdict
    has_degradation = len(degraded) > 0
    has_improvement = len(improved) > 0

    if has_degradation:
        verdict = "BLOCK_MERGE"
    elif has_improvement:
        verdict = "IMPROVED"
    else:
        verdict = "NO_CHANGE"

    return {
        "agent": baseline.get("agent", "unknown"),
        "baseline_version": baseline.get("timestamp", "unknown"),
        "candidate_version": candidate.get("timestamp", "unknown"),
        "total_cases": len(all_case_ids),
        "baseline_score": baseline.get("overall_score", 0),
        "candidate_score": candidate.get("overall_score", 0),
        "baseline_hard_constraint": baseline.get("hard_constraint_passed", False),
        "candidate_hard_constraint": candidate.get("hard_constraint_passed", False),
        "degraded_count": len(degraded),
        "improved_count": len(improved),
        "persistent_fail_count": len(persistent_fail),
        "persistent_pass_count": len(persistent_pass),
        "new_failures_count": len(new_failures),
        "degraded_cases": degraded,
        "improved_cases": improved,
        "verdict": verdict,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


def generate_report(comparison):
    """Generate a human-readable regression report."""
    report = f"""# Regression Report

| Field | Value |
|-------|-------|
| Agent | {comparison['agent']} |
| Baseline version | {comparison['baseline_version']} |
| Candidate version | {comparison['candidate_version']} |
| Total cases | {comparison['total_cases']} |
| Baseline score | {comparison['baseline_score']:.1%} |
| Candidate score | {comparison['candidate_score']:.1%} |
| Baseline hard constraint | {'PASS' if comparison['baseline_hard_constraint'] else 'FAIL'} |
| Candidate hard constraint | {'PASS' if comparison['candidate_hard_constraint'] else 'FAIL'} |
| Degraded cases | {comparison['degraded_count']} |
| Improved cases | {comparison['improved_count']} |
| Persistent failures | {comparison['persistent_fail_count']} |
| New failures | {comparison['new_failures_count']} |
| **Verdict** | **{comparison['verdict']}** |

"""

    if comparison['degraded_count'] > 0:
        report += "## Degraded Cases (BLOCK MERGE)\n\n"
        for case in comparison['degraded_cases']:
            report += f"- `{case['case_id']}`: {case['baseline_score']:.4f} → {case['candidate_score']:.4f}\n"
        report += "\n"

    if comparison['improved_count'] > 0:
        report += "## Improved Cases\n\n"
        for case in comparison['improved_cases']:
            report += f"- `{case['case_id']}`: {case['baseline_score']:.4f} → {case['candidate_score']:.4f}\n"
        report += "\n"

    if comparison['persistent_fail_count'] > 0:
        report += "## Persistent Failures (need attention)\n\n"
        for case in comparison.get('degraded_cases', []):
            pass  # Already listed above
        report += f"{comparison['persistent_fail_count']} cases still failing from baseline.\n\n"

    if comparison['verdict'] == 'BLOCK_MERGE':
        report += "## Action Required\n\n"
        report += "⚠️  **Merge blocked** due to degraded cases.\n"
        report += "Fix the degraded cases before merging.\n"
        report += "Run `python scripts/run_eval.py --agent " + comparison['agent'] + "` to re-evaluate.\n"

    return report


def main():
    parser = argparse.ArgumentParser(description="Compare regression between two scorecards")
    parser.add_argument("--agent", required=True, help="Agent name")
    parser.add_argument("--baseline", help="Path to baseline scorecard JSON")
    parser.add_argument("--candidate", help="Path to candidate scorecard JSON")
    parser.add_argument("--output", help="Output report path (default: experiments/reports/regression-report.md)")
    args = parser.parse_args()

    # Find scorecards
    if args.baseline and args.candidate:
        baseline_path = args.baseline
        candidate_path = args.candidate
    else:
        baseline_path, candidate_path = find_scorecards(args.agent)

    print(f"Baseline: {baseline_path}")
    print(f"Candidate: {candidate_path}")

    baseline = load_scorecard(baseline_path)
    candidate = load_scorecard(candidate_path)

    comparison = compare_scorecards(baseline, candidate)

    # Print summary
    print(f"\n{'='*50}")
    print(f"  Agent: {comparison['agent']}")
    print(f"  Baseline score: {comparison['baseline_score']:.1%}")
    print(f"  Candidate score: {comparison['candidate_score']:.1%}")
    print(f"  Degraded: {comparison['degraded_count']}")
    print(f"  Improved: {comparison['improved_count']}")
    print(f"  Verdict: {comparison['verdict']}")
    print(f"{'='*50}")

    # Generate report
    report = generate_report(comparison)
    output_path = args.output or "experiments/reports/regression-report.md"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\nReport: {output_path}")

    # Exit with error if degraded
    if comparison['verdict'] == 'BLOCK_MERGE':
        sys.exit(1)


if __name__ == "__main__":
    main()
