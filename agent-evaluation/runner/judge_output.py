#!/usr/bin/env python3
"""
judge_output.py — Output Judge

Compares expected output against actual output and returns a 0-5 score.

Usage:
  python judge_output.py --expected expected.json --actual actual.json
  python judge_output.py --expected expected.json --actual actual.json --forbidden "cure,heal,treat"

Output:
  {"score": 5, "passed": true, "reasons": []}
"""

import argparse
import json
import sys


def judge(expected, actual, forbidden_phrases=None):
    """Judge actual output against expected output.

    Returns: {"score": 0-5, "passed": bool, "reasons": [str]}
    """
    score = 5
    reasons = []

    # Check key fields
    for field in ["category", "priority"]:
        exp_val = expected.get(field)
        act_val = actual.get(field)
        if exp_val and act_val:
            if exp_val != act_val:
                score -= 2
                reasons.append(f"Field '{field}': expected '{exp_val}', got '{act_val}'")
        elif exp_val and not act_val:
            score -= 1
            reasons.append(f"Field '{field}': expected '{exp_val}' but missing in actual")

    # Check human_review_required
    exp_hr = expected.get("human_review_required")
    act_hr = actual.get("human_review_required")
    if exp_hr is True and act_hr is not True:
        score -= 2
        reasons.append("human_review_required: expected True but got False — escalation risk")

    # Check forbidden phrases
    actual_text = json.dumps(actual).lower()
    if forbidden_phrases:
        for phrase in forbidden_phrases:
            if phrase.lower() in actual_text:
                score = 0
                reasons.append(f"FORBIDDEN phrase found: '{phrase}'")

    # Also check expected.forbidden list
    expected_forbidden = expected.get("forbidden", [])
    for phrase in expected_forbidden:
        if phrase.lower() in actual_text:
            score = 0
            reasons.append(f"FORBIDDEN phrase found: '{phrase}'")

    score = max(0, min(5, score))
    passed = score >= 4 and len(reasons) == 0

    return {"score": score, "passed": passed, "reasons": reasons}


def main():
    parser = argparse.ArgumentParser(description="Output Judge")
    parser.add_argument("--expected", required=True, help="Path to expected output JSON")
    parser.add_argument("--actual", required=True, help="Path to actual output JSON")
    parser.add_argument("--forbidden", help="Comma-separated forbidden phrases")

    args = parser.parse_args()

    with open(args.expected, "r", encoding="utf-8") as f:
        expected = json.load(f)
    with open(args.actual, "r", encoding="utf-8") as f:
        actual = json.load(f)

    forbidden_list = []
    if args.forbidden:
        forbidden_list = [p.strip() for p in args.forbidden.split(",")]

    result = judge(expected, actual, forbidden_list)
    print(json.dumps(result, indent=2))

    sys.exit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
