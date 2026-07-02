#!/usr/bin/env python3
"""
run_eval.py — Golden Set Evaluation Runner

Runs golden set test cases against an agent and scores the results.

Usage:
  python run_eval.py --golden-set evals/golden_set_v1.yaml
  python run_eval.py --golden-set evals/golden_set_v1.yaml --agent customer-support
  python run_eval.py --golden-set evals/golden_set_v1.yaml --case-id CS-MED-001 --actual actual_output.json
  python run_eval.py --golden-set evals/golden_set_v1.yaml --actual-dir actual_outputs/

Exit codes:
  0 — All cases passed
  1 — One or more cases failed
  2 — Error in evaluation setup
"""

import argparse
import json
import os
import sys
from pathlib import Path

# --- YAML Loading ---
try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(2)


def load_golden_set(path):
    """Load golden set YAML file."""
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, list):
        print("ERROR: Golden set must be a YAML list of test cases", file=sys.stderr)
        sys.exit(2)
    return data


def filter_cases(cases, agent=None, case_id=None):
    """Filter cases by agent or case ID."""
    filtered = cases
    if agent:
        filtered = [c for c in filtered if c.get("agent") == agent]
    if case_id:
        filtered = [c for c in filtered if c.get("id") == case_id]
    return filtered


def load_actual_output(path):
    """Load actual output from a JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def find_actual_file(actual_dir, case_id):
    """Find actual output file for a case ID in a directory."""
    possible_names = [f"{case_id}.json", f"{case_id}.yaml", f"{case_id}.yml"]
    for name in possible_names:
        path = os.path.join(actual_dir, name)
        if os.path.exists(path):
            return load_actual_output(path)
    return None


def judge_case(case, actual_output):
    """Judge a single case against expected output."""
    expected = case.get("expected", {})
    case_id = case.get("id", "unknown")
    score = 0
    max_score = 0
    reasons = []
    forbidden_hits = []

    # Check forbidden phrases
    forbidden = expected.get("forbidden", [])
    actual_text = json.dumps(actual_output).lower() if actual_output else ""
    for phrase in forbidden:
        max_score += 1
        if phrase.lower() in actual_text:
            forbidden_hits.append(phrase)
            reasons.append(f"FORBIDDEN phrase found: '{phrase}'")
        else:
            score += 1

    # Check expected fields
    for field in ["category", "priority", "human_review_required"]:
        if field in expected:
            max_score += 2
            actual_val = actual_output.get(field) if actual_output else None
            expected_val = expected[field]
            if actual_val == expected_val:
                score += 2
            else:
                reasons.append(f"Field '{field}': expected '{expected_val}', got '{actual_val}'")

    # Check forbidden phrases in actual text fields
    if forbidden_hits:
        score = 0  # Any forbidden phrase = automatic fail

    passed = score == max_score and len(forbidden_hits) == 0 and score > 0

    return {
        "case_id": case_id,
        "score": score,
        "max_score": max_score,
        "passed": passed,
        "forbidden_hits": forbidden_hits,
        "reasons": reasons,
    }


def run_evaluation(golden_set_path, agent=None, case_id=None, actual=None, actual_dir=None):
    """Run the full evaluation."""
    cases = load_golden_set(golden_set_path)
    cases = filter_cases(cases, agent, case_id)

    if not cases:
        print(json.dumps({"error": "No cases matched filters", "total": 0}, indent=2))
        sys.exit(2)

    results = []
    passed_count = 0
    failed_count = 0

    for case in cases:
        cid = case.get("id", "unknown")
        expected = case.get("expected", {})

        # Get actual output
        actual_output = None
        if actual and len(cases) == 1:
            actual_output = load_actual_output(actual)
        elif actual_dir:
            actual_output = find_actual_file(actual_dir, cid)
        else:
            # Interactive mode — just print the case for manual testing
            print(f"\n--- Case: {cid} ---")
            print(f"Input: {json.dumps(case.get('input', {}), indent=2)}")
            print(f"Expected: {json.dumps(expected, indent=2)}")
            results.append({
                "case_id": cid,
                "status": "pending_actual_output",
                "input": case.get("input", {}),
                "expected": expected,
            })
            continue

        if actual_output:
            result = judge_case(case, actual_output)
            results.append(result)
            if result["passed"]:
                passed_count += 1
                print(f"  ✅ {cid} — score {result['score']}/{result['max_score']}")
            else:
                failed_count += 1
                print(f"  ❌ {cid} — score {result['score']}/{result['max_score']}")
                for reason in result["reasons"]:
                    print(f"      → {reason}")
        else:
            # No actual output available
            print(f"\n--- Case: {cid} ---")
            print(f"Input: {json.dumps(case.get('input', {}), indent=2)}")
            print(f"Expected: {json.dumps(expected, indent=2)}")
            results.append({
                "case_id": cid,
                "status": "no_actual_output",
                "input": case.get("input", {}),
                "expected": expected,
            })

    # Generate summary
    total = len(results)
    judged = [r for r in results if "passed" in r]
    pass_rate = (passed_count / len(judged)) if judged else 0

    summary = {
        "golden_set_path": golden_set_path,
        "agent_filter": agent,
        "total_cases": total,
        "judged": len(judged),
        "passed": passed_count,
        "failed": failed_count,
        "pass_rate": round(pass_rate, 4),
        "verdict": "PASS" if failed_count == 0 and pass_rate >= 0.9 else ("FAIL" if failed_count > 0 else "PENDING"),
        "results": results,
    }

    print(f"\n{'='*60}")
    print(f"Golden Set Evaluation Summary")
    print(f"{'='*60}")
    print(f"Total cases: {total}")
    print(f"Judged: {len(judged)}")
    print(f"Passed: {passed_count}")
    print(f"Failed: {failed_count}")
    print(f"Pass rate: {pass_rate:.1%}")
    print(f"Verdict: {summary['verdict']}")
    print(f"{'='*60}")

    # Output full results as JSON
    output_path = os.path.join(os.path.dirname(golden_set_path), "..", "reports", "eval_results.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"\nFull results saved to: {output_path}")

    if failed_count > 0:
        sys.exit(1)
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description="Golden Set Evaluation Runner")
    parser.add_argument("--golden-set", required=True, help="Path to golden_set_v1.yaml")
    parser.add_argument("--agent", help="Filter by agent name")
    parser.add_argument("--case-id", help="Run specific case ID only")
    parser.add_argument("--actual", help="Path to actual output JSON file (single case mode)")
    parser.add_argument("--actual-dir", help="Directory containing actual output JSON files")

    args = parser.parse_args()

    if not os.path.exists(args.golden_set):
        print(f"ERROR: Golden set file not found: {args.golden_set}", file=sys.stderr)
        sys.exit(2)

    run_evaluation(
        golden_set_path=args.golden_set,
        agent=args.agent,
        case_id=args.case_id,
        actual=args.actual,
        actual_dir=args.actual_dir,
    )


if __name__ == "__main__":
    main()
