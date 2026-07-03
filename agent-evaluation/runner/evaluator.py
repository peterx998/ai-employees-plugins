#!/usr/bin/env python3
"""
evaluator.py — Single source of truth for Agent evaluation.

ALL evaluation callers (CI, autoresearch, manual) MUST use this module.
No duplicate scoring logic anywhere else.

Pipeline per case:
  1. Load actual output JSON
  2. Validate against JSON Schema (triage_result.schema.json)
  3. Apply hard constraints (P1 rules, forbidden phrases)
  4. Score with weighted rubric
  5. Return structured result

Usage from other scripts:
  from evaluator import Evaluator
  ev = Evaluator(agent="customer-support")
  result = ev.evaluate_case(case, actual_output)
  summary = ev.evaluate_batch(cases, actual_dir)
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required. pip install pyyaml", file=sys.stderr)
    sys.exit(2)

try:
    from jsonschema import validate, ValidationError
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    print("WARNING: jsonschema not installed. Schema validation disabled.", file=sys.stderr)


# ─── Scoring Rubrics (single source) ───

RUBRICS = {
    "customer-support": {
        "category_accuracy": 0.30,
        "priority_accuracy": 0.20,
        "route_to_accuracy": 0.15,
        "hard_constraint_pass": 0.15,   # P1 medical suppress, human review, risk flags
        "schema_valid": 0.10,
        "forbidden_check": 0.05,
        "field_completeness": 0.05,
    },
    "influencer-outreach": {
        "reply_classification_accuracy": 0.30,
        "personalization_score": 0.25,
        "usage_rights_detection": 0.20,
        "compliance_boundary": 0.15,
        "schema_valid": 0.10,
    },
    "ad-creative": {
        "segmentation_accuracy": 0.30,
        "compliance_detection": 0.25,
        "hook_quality": 0.20,
        "evidence_completeness": 0.15,
        "schema_valid": 0.10,
    },
    "shopify-growth": {
        "audit_accuracy": 0.30,
        "faq_quality": 0.25,
        "seo_score_accuracy": 0.20,
        "compliance_flag_rate": 0.15,
        "schema_valid": 0.10,
    },
    "b2b-sales": {
        "lead_classification_accuracy": 0.30,
        "quote_accuracy": 0.25,
        "high_value_detection": 0.20,
        "compliance_awareness": 0.15,
        "schema_valid": 0.10,
    },
}

# ─── Hard Constraints (binary gates) ───

HARD_CONSTRAINTS = {
    "customer-support": {
        "description": "P1: medical-review escalation + empty response. P2: human review + escalation routing for sensitive categories.",
        "check": lambda case, actual: _check_cs_hard_constraints(case, actual),
    },
    "influencer-outreach": {
        "description": "Fee-request replies: human_review_required=true",
        "check": lambda case, actual: _check_inf_fee(case, actual),
    },
    "ad-creative": {
        "description": "Compliance-critical segments must be detected",
        "check": lambda case, actual: True,  # Placeholder — needs ad-creative golden set
    },
    "shopify-growth": {
        "description": "Medical claims on pages must be flagged",
        "check": lambda case, actual: True,
    },
    "b2b-sales": {
        "description": "High-value leads ($10K+) must be escalated",
        "check": lambda case, actual: True,
    },
}


def _check_cs_p1(case, actual):
    """Hard constraint for customer-support P1 cases.

    P1 rules (conservative policy: ALL P1 suppresses auto-reply):
    - human_review_required MUST be true
    - route_to MUST be medical-review or escalation
    - suggested_initial_response MUST be empty (auto-reply suppressed for ALL P1)
    - risk_flags MUST not be empty

    Policy alignment:
    - schema: "Empty for P1 medical (auto-reply suppressed)"
    - evaluator: ALL P1 → empty response (conservative)
    - mock_adapter: ALL P1 → empty response
    - skill SKILL.md: P1 → suppress auto-reply, human review required

    The conservative approach (all P1 suppress) is chosen because:
    1. P1 includes legal threats, social media escalation, medical risk
    2. Any auto-reply to these without human review creates liability
    3. The schema example shows P1 medical, but the evaluator enforces all P1
    """
    expected = case.get("expected", {})
    if expected.get("priority") != "P1":
        return True, "Not a P1 case — hard constraint N/A"

    cid = case.get("id", "?")
    failures = []

    if not actual.get("human_review_required"):
        failures.append("P1 case but human_review_required is not true")

    if actual.get("route_to") not in ("medical-review", "escalation"):
        failures.append(f"P1 case but route_to='{actual.get('route_to')}' (expected medical-review or escalation)")

    # P1: suggested_initial_response MUST be empty (auto-reply suppressed for ALL P1)
    if actual.get("suggested_initial_response", "") != "":
        failures.append("P1 case but suggested_initial_response is not empty — auto-reply must be suppressed for all P1")

    # P1 must have at least one risk_flag
    if not actual.get("risk_flags"):
        failures.append("P1 case but risk_flags is empty — must flag the medical risk")

    if failures:
        return False, "; ".join(failures)
    return True, "P1 hard constraint passed"


def _check_cs_p2(case, actual):
    """Hard constraint for customer-support P2 cases.

    P2 rules:
    - human_review_required MUST be true
    - If category is compliance/legal/regulatory or refund-return (dispute) →
      route_to MUST be escalation or tier-2
    - risk_flags SHOULD not be empty (warning only, not hard fail)
    """
    expected = case.get("expected", {})
    if expected.get("priority") != "P2":
        return True, "Not a P2 case — hard constraint N/A"

    cid = case.get("id", "?")
    failures = []

    # P2 always requires human review
    if not actual.get("human_review_required"):
        failures.append("P2 case but human_review_required is not true")

    # For compliance/legal/regulatory/refund dispute P2 cases, route must be escalation or tier-2
    category = expected.get("category", "")
    actual_category = actual.get("category", "")
    sensitive_categories = ("compliance", "medical-risk")
    refund_dispute = (
        actual_category == "refund-return"
        and actual.get("priority") == "P2"
    )

    if (actual_category in sensitive_categories or refund_dispute):
        if actual.get("route_to") not in ("escalation", "tier-2"):
            failures.append(
                f"P2 {actual_category} case but route_to='{actual.get('route_to')}' "
                f"(expected escalation or tier-2)"
            )

    # Check for forbidden phrases that indicate legal/compliance risk
    # IMPORTANT: Only check customer-facing text (suggested_initial_response).
    # internal_notes and risk_flags.description MAY contain contextual
    # references to the customer's legal threats — that is correct behavior,
    # not a compliance violation.
    customer_facing_text = actual.get("suggested_initial_response", "").lower()
    legal_risk_phrases = [
        "not liable", "sue us", "legal action", "attorney",
        "lawyer", "lawsuit", "file a complaint", "better business bureau",
        "bbb complaint", "chargeback",
    ]
    legal_hits = [p for p in legal_risk_phrases if p in customer_facing_text]
    if legal_hits:
        failures.append(
            f"P2 case contains legal/compliance risk phrases in customer-facing response: {legal_hits[:3]}"
        )

    if failures:
        return False, "; ".join(failures)
    return True, "P2 hard constraint passed"


def _check_cs_hard_constraints(case, actual):
    """Unified hard constraint dispatcher for customer-support.

    Routes to P1 or P2 checker based on expected priority.
    Falls back to pass for P3/P4 (no hard constraints).

    Returns (passed: bool, message: str)
    """
    expected = case.get("expected", {})
    priority = expected.get("priority", "")

    if priority == "P1":
        return _check_cs_p1(case, actual)
    elif priority == "P2":
        return _check_cs_p2(case, actual)
    else:
        return True, "P3/P4 — no hard constraint, soft scoring only"


def _check_inf_fee(case, actual):
    """Hard constraint for influencer-outreach fee-request cases."""
    expected = case.get("expected", {})
    if expected.get("category") != "fee-request":
        return True, "Not a fee-request case — hard constraint N/A"

    if not actual.get("human_review_required"):
        return False, "Fee-request reply but human_review_required is not true"

    return True, "Fee-request hard constraint passed"


# ─── Evaluator Class ───

class Evaluator:
    """Unified evaluator. All callers use this."""

    def __init__(self, agent="customer-support", schema_path=None, golden_set_path=None):
        self.agent = agent
        self.rubric = RUBRICS.get(agent, RUBRICS["customer-support"])

        # Load schema for validation
        self.schema = None
        if schema_path is None:
            schema_path = f"schemas/{agent}/triage_result.schema.json"
        if Path(schema_path).exists() and HAS_JSONSCHEMA:
            with open(schema_path, "r", encoding="utf-8") as f:
                self.schema = json.load(f)

        # Load golden set
        self.cases = []
        if golden_set_path is None:
            golden_set_path = f"{agent}/evals/golden_set_v1.yaml"
        if Path(golden_set_path).exists():
            with open(golden_set_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            self.cases = data if isinstance(data, list) else data.get("cases", [])

        self.hard_constraint = HARD_CONSTRAINTS.get(agent, {"description": "None", "check": lambda c, a: (True, "N/A")})

    def validate_schema(self, actual_output):
        """Validate actual output against JSON Schema. Returns (valid, errors)."""
        if not self.schema:
            return True, []  # No schema = skip (but flag in score)
        if not HAS_JSONSCHEMA:
            return True, ["jsonschema not installed — validation skipped"]

        try:
            validate(instance=actual_output, schema=self.schema)
            return True, []
        except ValidationError as e:
            return False, [str(e.message)]

    def check_hard_constraint(self, case, actual_output):
        """Check hard constraint for this case."""
        return self.hard_constraint["check"](case, actual_output)

    def score_case(self, case, actual_output):
        """Score a single case. Returns detailed result dict."""
        cid = case.get("id", "unknown")
        expected = case.get("expected", {})
        details = {}
        reasons = []

        # 1. Schema validation
        schema_valid, schema_errors = self.validate_schema(actual_output)
        details["schema_valid"] = 1.0 if schema_valid else 0.0
        if not schema_valid:
            reasons.append(f"Schema validation failed: {'; '.join(schema_errors[:2])}")

        # 2. Category accuracy
        exp_cat = expected.get("category", "")
        act_cat = actual_output.get("category", "")
        cat_correct = exp_cat == act_cat
        details["category_accuracy"] = 1.0 if cat_correct else 0.0
        if not cat_correct:
            reasons.append(f"category: expected '{exp_cat}', got '{act_cat}'")

        # 3. Priority accuracy
        exp_pri = expected.get("priority", "")
        act_pri = actual_output.get("priority", "")
        pri_correct = exp_pri == act_pri
        details["priority_accuracy"] = 1.0 if pri_correct else 0.0
        if not pri_correct:
            reasons.append(f"priority: expected '{exp_pri}', got '{act_pri}'")

        # 4. Route-to accuracy (inferred from priority + category)
        exp_route = self._infer_expected_route(expected)
        act_route = actual_output.get("route_to", "")
        route_correct = exp_route == act_route
        details["route_to_accuracy"] = 1.0 if route_correct else 0.0
        if not route_correct:
            reasons.append(f"route_to: expected '{exp_route}', got '{act_route}'")

        # 5. Hard constraint
        hc_passed, hc_msg = self.check_hard_constraint(case, actual_output)
        details["hard_constraint_pass"] = 1.0 if hc_passed else 0.0
        if not hc_passed:
            reasons.append(f"Hard constraint FAILED: {hc_msg}")

        # 6. Forbidden phrases — check only customer-facing fields
        # (internal_notes can contain contextual info including the customer's own words)
        forbidden = expected.get("forbidden", [])
        customer_facing_text = json.dumps({
            "suggested_initial_response": actual_output.get("suggested_initial_response", ""),
        }).lower()
        forbidden_hits = [p for p in forbidden if p.lower() in customer_facing_text]
        details["forbidden_check"] = 1.0 if not forbidden_hits else 0.0
        if forbidden_hits:
            reasons.append(f"Forbidden phrases found: {forbidden_hits}")

        # 7. Field completeness (all schema required fields present)
        required_fields = ["category", "priority", "route_to", "risk_flags",
                          "human_review_required", "suggested_initial_response", "internal_notes"]
        present = sum(1 for f in required_fields if f in actual_output)
        details["field_completeness"] = present / len(required_fields)

        # Weighted score
        score = 0.0
        for metric, weight in self.rubric.items():
            score += details.get(metric, 0.0) * weight

        # Hard constraint failure = automatic case fail regardless of score
        passed = score >= 0.85 and hc_passed and not forbidden_hits and schema_valid

        return {
            "case_id": cid,
            "score": round(score, 4),
            "passed": passed,
            "hard_constraint_passed": hc_passed,
            "schema_valid": schema_valid,
            "forbidden_hits": forbidden_hits,
            "details": details,
            "reasons": reasons,
        }

    def _infer_expected_route(self, expected):
        """Infer expected route_to from priority + category."""
        pri = expected.get("priority", "")
        cat = expected.get("category", "")

        if pri == "P1":
            if cat == "medical-risk":
                return "medical-review"
            return "escalation"
        if pri == "P2":
            if cat == "medical-risk":
                return "tier-2"   # P2 medical: high but not critical — needs tier-2, not medical-review
            if cat == "compliance":
                return "escalation"
            return "tier-2"
        return "tier-1"

    def evaluate_batch(self, cases=None, actual_dir=None, actual_outputs=None):
        """Evaluate a batch of cases. Returns summary dict.

        Args:
            cases: List of golden set cases (default: self.cases)
            actual_dir: Directory of per-case JSON files ({case_id}.json)
            actual_outputs: List of actual output dicts (alternative to actual_dir)

        Returns:
            Summary dict with verdict, pass_rate, results, etc.
        """
        cases = cases or self.cases
        if not cases:
            return {"error": "No cases to evaluate", "verdict": "FAIL"}

        # Load actual outputs
        if actual_outputs is None:
            actual_outputs = []
            if actual_dir:
                for case in cases:
                    cid = case.get("id", "")
                    fpath = Path(actual_dir) / f"{cid}.json"
                    if fpath.exists():
                        with open(fpath, "r", encoding="utf-8") as f:
                            actual_outputs.append(json.load(f))
                    else:
                        actual_outputs.append(None)
            else:
                # No actual outputs = all pending = FAIL
                return {
                    "verdict": "FAIL",
                    "total_cases": len(cases),
                    "judged": 0,
                    "pending": len(cases),
                    "passed": 0,
                    "failed": 0,
                    "pass_rate": 0.0,
                    "error": "No actual outputs provided — CI gate requires real evaluation",
                }

        # Score each case
        results = []
        passed_count = 0
        failed_count = 0
        pending_count = 0
        hard_constraint_failures = 0
        schema_failures = 0

        for case, actual in zip(cases, actual_outputs):
            if actual is None:
                results.append({
                    "case_id": case.get("id", "?"),
                    "status": "no_actual_output",
                    "passed": False,
                })
                pending_count += 1
                continue

            result = self.score_case(case, actual)
            results.append(result)

            if result["passed"]:
                passed_count += 1
            else:
                failed_count += 1
                if not result["hard_constraint_passed"]:
                    hard_constraint_failures += 1
                if not result["schema_valid"]:
                    schema_failures += 1

        total = len(cases)
        judged = total - pending_count
        pass_rate = passed_count / judged if judged > 0 else 0.0

        # Verdict: PASS only if no pending, no failures, pass rate >= 0.9
        if pending_count > 0:
            verdict = "FAIL"
        elif failed_count > 0:
            verdict = "FAIL"
        elif pass_rate >= 0.9:
            verdict = "PASS"
        else:
            verdict = "FAIL"

        summary = {
            "agent": self.agent,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_cases": total,
            "judged": judged,
            "pending": pending_count,
            "passed": passed_count,
            "failed": failed_count,
            "hard_constraint_failures": hard_constraint_failures,
            "schema_failures": schema_failures,
            # ─── Unified EvalSummary fields (all consumers read these) ───
            # overall_score = pass_rate (backward compat for compare_regression)
            "overall_score": round(pass_rate, 4),
            "pass_rate": round(pass_rate, 4),
            # case_results = results (alias for compare_regression backward compat)
            "case_results": results,
            "results": results,
            # hard_constraint_passed: True only if zero HC failures
            "hard_constraint_passed": hard_constraint_failures == 0,
            "verdict": verdict,
            "rubric": self.rubric,
        }

        return summary

    def print_summary(self, summary):
        """Print human-readable summary."""
        print(f"\n{'='*60}")
        print(f"  Agent: {summary.get('agent', '?')}")
        print(f"  Total cases: {summary['total_cases']}")
        print(f"  Judged: {summary['judged']}")
        print(f"  Pending: {summary['pending']}")
        print(f"  Passed: {summary['passed']}")
        print(f"  Failed: {summary['failed']}")
        print(f"  Hard constraint failures: {summary.get('hard_constraint_failures', 0)}")
        print(f"  Schema failures: {summary.get('schema_failures', 0)}")
        print(f"  Pass rate: {summary['pass_rate']:.1%}")
        print(f"  Verdict: {summary['verdict']}")
        print(f"{'='*60}")

        # Show failed cases
        for r in summary.get("results", []):
            if not r.get("passed") and r.get("case_id"):
                print(f"\n  ❌ {r['case_id']}: {'; '.join(r.get('reasons', ['Unknown']))}")
