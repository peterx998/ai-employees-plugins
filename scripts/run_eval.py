#!/usr/bin/env python3
"""
run_eval.py — Golden Set evaluation runner for AI Employees Plugins.

Adapted from karpathy/autoresearch's evaluate_bpb pattern:
  - Fixed test set (golden_set_v1.yaml) is the ground truth
  - Agent output is compared against expected results
  - Score is computed using weighted rubric
  - Hard constraints (P1/medical/fee/high-value) are binary gates

Usage:
  python scripts/run_eval.py --agent customer-support
  python scripts/run_eval.py --agent customer-support --golden-set custom.yaml
  python scripts/run_eval.py --agent customer-support --output experiments/scorecards/latest.json

This script does NOT call any LLM. It is a deterministic scoring harness.
The agent (or human) runs the golden set cases through the agent separately,
captures outputs, and feeds them to this script for scoring.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime

import yaml

# ─── Scoring Weights per Agent ───

SCORING_RUBRICS = {
    "customer-support": {
        "category_accuracy": 0.40,
        "escalation_accuracy": 0.25,
        "compliance_recall": 0.20,
        "structure_completeness": 0.10,
        "tone_match": 0.05,
    },
    "influencer-outreach": {
        "reply_classification_accuracy": 0.30,
        "personalization_score": 0.25,
        "usage_rights_detection": 0.20,
        "compliance_boundary": 0.15,
        "human_usability": 0.10,
    },
    "ad-creative": {
        "segmentation_accuracy": 0.30,
        "compliance_detection": 0.25,
        "hook_quality": 0.20,
        "evidence_completeness": 0.15,
        "brief_usability": 0.10,
    },
    "shopify-growth": {
        "audit_accuracy": 0.30,
        "faq_quality": 0.25,
        "seo_score_accuracy": 0.20,
        "compliance_flag_rate": 0.15,
        "brief_usability": 0.10,
    },
    "b2b-sales": {
        "lead_classification_accuracy": 0.30,
        "quote_accuracy": 0.25,
        "high_value_detection": 0.20,
        "compliance_awareness": 0.15,
        "summary_quality": 0.10,
    },
}

# ─── Hard Constraints per Agent ───
# If any hard constraint fails, the experiment is auto-discarded
# regardless of overall score.

HARD_CONSTRAINTS = {
    "customer-support": {
        "field": "priority",
        "values": ["P1"],
        "check": "must_escalate",
        "description": "P1 medical-risk cases must have human_review_required: true",
    },
    "influencer-outreach": {
        "field": "category",
        "values": ["fee-request"],
        "check": "must_require_human_review",
        "description": "Fee-request replies must have human_review_required: true",
    },
    "ad-creative": {
        "field": "risk_flags",
        "values": ["medical_claim", "before_after_no_disclosure"],
        "check": "must_detect",
        "description": "Compliance-critical segments must be detected at 100% recall",
    },
    "shopify-growth": {
        "field": "compliance_flags",
        "values": ["medical_claim_on_page"],
        "check": "must_detect",
        "description": "Medical claims on product pages must be flagged",
    },
    "b2b-sales": {
        "field": "lead_score",
        "values": ["high_value"],
        "check": "must_escalate",
        "description": "High-value leads ($10K+) must be escalated",
    },
}


def load_golden_set(agent_name, golden_set_path=None):
    """Load golden set YAML for the specified agent."""
    if golden_set_path is None:
        golden_set_path = Path(f"{agent_name}/evals/golden_set_v1.yaml")

    if not Path(golden_set_path).exists():
        print(f"ERROR: Golden set not found: {golden_set_path}", file=sys.stderr)
        sys.exit(1)

    with open(golden_set_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return data if isinstance(data, list) else data.get("cases", data.get("test_cases", []))


def load_agent_output(output_path):
    """Load agent output JSONL for scoring."""
    results = []
    if not Path(output_path).exists():
        return results

    with open(output_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                results.append(json.loads(line))
    return results


def score_case(case, agent_output, rubric):
    """Score a single case against agent output using the rubric."""
    score = 0.0
    details = {}

    # Category accuracy
    expected_cat = case.get("expected", {}).get("category", "")
    actual_cat = agent_output.get("category", "")
    cat_correct = expected_cat == actual_cat
    details["category_accuracy"] = 1.0 if cat_correct else 0.0

    # Priority / escalation accuracy
    expected_priority = case.get("expected", {}).get("priority", "")
    actual_priority = agent_output.get("priority", "")
    pri_correct = expected_priority == actual_priority
    details["escalation_accuracy"] = 1.0 if pri_correct else 0.0

    # Compliance recall (forbidden phrases check)
    forbidden = case.get("expected", {}).get("forbidden", [])
    actual_text = json.dumps(agent_output.get("suggested_initial_response", "")).lower()
    no_forbidden = all(phrase.lower() not in actual_text for phrase in forbidden)
    details["compliance_recall"] = 1.0 if no_forbidden else 0.0

    # Structure completeness
    required_fields = ["category", "priority", "human_review_required"]
    present_fields = sum(1 for f in required_fields if f in agent_output)
    details["structure_completeness"] = present_fields / len(required_fields)

    # Tone match (simplified: check if response is not empty and not too short)
    response_text = agent_output.get("suggested_initial_response", "") or agent_output.get("draft_text", "")
    details["tone_match"] = 1.0 if len(response_text) > 20 else 0.0

    # Weighted score
    weight_map = {
        "category_accuracy": rubric.get("category_accuracy", 0.4),
        "escalation_accuracy": rubric.get("escalation_accuracy", 0.25),
        "compliance_recall": rubric.get("compliance_recall", 0.20),
        "structure_completeness": rubric.get("structure_completeness", 0.10),
        "tone_match": rubric.get("tone_match", 0.05),
    }

    for metric, value in details.items():
        score += value * weight_map.get(metric, 0.0)

    return score, details


def check_hard_constraint(cases, outputs, agent_name):
    """Check if hard constraints are met. Returns (passed, details)."""
    constraint = HARD_CONSTRAINTS.get(agent_name)
    if not constraint:
        return True, {"description": "No hard constraint defined"}

    field = constraint["field"]
    check_type = constraint["check"]
    critical_values = constraint["values"]

    total_critical = 0
    passed_critical = 0

    for case, output in zip(cases, outputs):
        expected = case.get("expected", {})

        # Identify critical cases (P1, fee-request, etc.)
        is_critical = any(
            expected.get(field) == val or val in str(expected.get(field, ""))
            for val in critical_values
        )

        if is_critical:
            total_critical += 1

            if check_type == "must_escalate":
                if output.get("human_review_required") == True or output.get("route_to") == "immediate-escalation":
                    passed_critical += 1
            elif check_type == "must_require_human_review":
                if output.get("human_review_required") == True:
                    passed_critical += 1
            elif check_type == "must_detect":
                actual_flags = output.get("risk_flags", []) or output.get("compliance_flags", [])
                if any(cv in str(actual_flags) for cv in critical_values):
                    passed_critical += 1

    pass_rate = passed_critical / total_critical if total_critical > 0 else 1.0
    passed = pass_rate == 1.0

    return passed, {
        "constraint": constraint["description"],
        "total_critical_cases": total_critical,
        "passed_critical_cases": passed_critical,
        "pass_rate": pass_rate,
    }


def run_evaluation(agent_name, golden_set_path=None, output_path=None, agent_output_path=None, actual_dir=None, fail_on_no_output=True):
    """Run full evaluation for an agent.

    Args:
        fail_on_no_output: If True (default), FAIL when no actual outputs are provided.
                          This is required for CI gate integrity.
    """
    rubric = SCORING_RUBRICS.get(agent_name)
    if not rubric:
        print(f"ERROR: No rubric found for agent: {agent_name}", file=sys.stderr)
        sys.exit(1)

    # Load golden set
    cases = load_golden_set(agent_name, golden_set_path)
    print(f"Loaded {len(cases)} cases from golden set")

    # Load agent output
    agent_outputs = []

    # Try actual_dir first (directory of per-case JSON files)
    if actual_dir:
        actual_path = Path(actual_dir)
        if actual_path.exists():
            for case in cases:
                case_id = case.get("id", "")
                case_file = actual_path / f"{case_id}.json"
                if case_file.exists():
                    with open(case_file, "r", encoding="utf-8") as f:
                        agent_outputs.append(json.load(f))
                else:
                    agent_outputs.append({})
            missing = sum(1 for o in agent_outputs if not o)
            if missing > 0:
                print(f"WARNING: {missing}/{len(cases)} cases have no actual output in {actual_dir}")
        else:
            if fail_on_no_output:
                print(f"ERROR: actual-dir not found: {actual_dir}", file=sys.stderr)
                print(f"CI GATE: Cannot evaluate without actual outputs. Create baseline outputs first.", file=sys.stderr)
                sys.exit(1)
            print(f"WARNING: actual-dir not found: {actual_dir}")

    # Fall back to agent_output_path (JSONL)
    if not agent_outputs and agent_output_path:
        agent_outputs = load_agent_output(agent_output_path)

    # If still no agent output, FAIL (do NOT use expected as baseline)
    if not agent_outputs:
        if fail_on_no_output:
            print("ERROR: No actual agent outputs provided.", file=sys.stderr)
            print("CI GATE: Evaluation requires actual agent outputs.", file=sys.stderr)
            print("Provide --actual-dir or --agent-output argument.", file=sys.stderr)
            sys.exit(1)
        else:
            print("WARNING: No agent output provided. Using expected as baseline (non-CI mode).")
            agent_outputs = [case.get("expected", {}) for case in cases]

    # Score each case
    total_score = 0.0
    case_results = []
    for i, (case, output) in enumerate(zip(cases, agent_outputs)):
        score, details = score_case(case, output, rubric)
        total_score += score
        case_results.append({
            "case_id": case.get("id", f"case-{i}"),
            "score": round(score, 4),
            "details": details,
            "passed": score >= 0.6,
        })

    overall_score = total_score / len(cases) if cases else 0.0

    # Check hard constraints
    hard_passed, hard_details = check_hard_constraint(cases, agent_outputs, agent_name)

    # Generate scorecard
    scorecard = {
        "agent": agent_name,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "golden_set": str(golden_set_path or f"{agent_name}/evals/golden_set_v1.yaml"),
        "total_cases": len(cases),
        "passed": sum(1 for r in case_results if r["passed"]),
        "failed": sum(1 for r in case_results if not r["passed"]),
        "overall_score": round(overall_score, 4),
        "hard_constraint_passed": hard_passed,
        "hard_constraint_details": hard_details,
        "rubric": rubric,
        "case_results": case_results,
        "verdict": "PASS" if overall_score >= 0.90 and hard_passed else
                   "WARN" if overall_score >= 0.75 and hard_passed else
                   "FAIL",
    }

    # Output
    if output_path is None:
        output_path = f"experiments/scorecards/{agent_name}/latest.json"

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(scorecard, f, indent=2, ensure_ascii=False)

    # Print summary
    print(f"\n{'='*50}")
    print(f"  Agent: {agent_name}")
    print(f"  Total cases: {len(cases)}")
    print(f"  Passed: {scorecard['passed']}")
    print(f"  Failed: {scorecard['failed']}")
    print(f"  Overall score: {overall_score:.1%}")
    print(f"  Hard constraint: {'PASS' if hard_passed else 'FAIL'}")
    print(f"  Verdict: {scorecard['verdict']}")
    print(f"  Scorecard: {output_path}")
    print(f"{'='*50}")

    return scorecard


def main():
    parser = argparse.ArgumentParser(description="Run Golden Set evaluation for an agent")
    parser.add_argument("--agent", required=True, help="Agent name (e.g., customer-support)")
    parser.add_argument("--golden-set", help="Path to golden set YAML (default: agent's standard)")
    parser.add_argument("--output", help="Output scorecard path (default: experiments/scorecards/<agent>/latest.json)")
    parser.add_argument("--agent-output", help="Path to agent output JSONL for scoring")
    parser.add_argument("--actual-dir", help="Directory of per-case actual output JSON files")
    parser.add_argument("--allow-no-output", action="store_true", help="Allow using expected as baseline (non-CI mode)")
    args = parser.parse_args()

    run_evaluation(
        agent_name=args.agent,
        golden_set_path=args.golden_set,
        output_path=args.output,
        agent_output_path=args.agent_output,
        actual_dir=args.actual_dir,
        fail_on_no_output=not args.allow_no_output,
    )


if __name__ == "__main__":
    main()
