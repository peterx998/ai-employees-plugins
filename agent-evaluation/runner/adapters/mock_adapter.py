#!/usr/bin/env python3
"""
mock_adapter.py — Mock agent adapter for testing the batch runner pipeline.

Produces schema-valid triage outputs from golden-set expected values.

Used when:
  - Running CI without a live AI agent
  - Testing batch runner pipeline end-to-end
  - Developing evaluator rules without API costs

Default behavior is deterministic and should pass CI. Optional variation can be
enabled manually by constructing MockAdapter(..., variation_rate>0), but CI
should keep variation_rate=0.0 so the pipeline itself is stable.

NOT for production evaluation of real agent quality.
"""

import json
import random
import sys
from pathlib import Path
from datetime import datetime, timezone


class MockAdapter:
    """Mock agent that generates triage results from golden-set expected values."""

    def __init__(self, agent="customer-support", seed=42, variation_rate=0.0):
        self.agent = agent
        self.seed = seed
        self.variation_rate = variation_rate
        self.rng = random.Random(seed)
        self._load_enums(agent)

    def _load_enums(self, agent):
        """Load taxonomy enums for correct fallback values."""
        try:
            import yaml
            tax_path = Path(
                f"schemas/enums/{agent}_taxonomy.yaml"
                if agent != "customer-support"
                else "schemas/enums/customer_support_taxonomy.yaml"
            )
            if tax_path.exists():
                with open(tax_path, encoding="utf-8") as f:
                    taxonomy = yaml.safe_load(f)
                self.categories = taxonomy.get("category", [])
                self.priorities = taxonomy.get("priority", [])
                self.routes = taxonomy.get("route_to", [])
            else:
                self._set_fallback_enums(agent)
        except Exception:
            self._set_fallback_enums(agent)

    def _set_fallback_enums(self, agent):
        """Fallback enums if taxonomy file is not found."""
        if agent == "customer-support":
            self.categories = [
                "medical-risk", "order-status", "refund-return",
                "product-usage", "warranty", "billing", "compliance"
            ]
            self.priorities = ["P1", "P2", "P3", "P4"]
            self.routes = ["medical-review", "tier-1", "tier-2", "escalation"]
        else:
            self.categories = []
            self.priorities = ["P1", "P2", "P3", "P4"]
            self.routes = []

    def _category_to_risk_type(self, category):
        """Map golden set category to valid risk_flag type enum value."""
        mapping = {
            "medical-risk": "medical",
            "compliance": "compliance",
            "refund-return": "regulatory",
            "warranty": "regulatory",
            "billing": "compliance",
            "order-status": "social",
            "product-usage": "social",
        }
        return mapping.get(category, "compliance")

    def run_case(self, case):
        """Run a single golden set case through the mock adapter."""
        cid = case.get("id", "unknown")
        expected = case.get("expected", {})
        case_input = case.get("input", {})

        output = self._generate_triage(cid, expected, case_input)
        output["_meta"] = {
            "generated_by": "mock",
            "model": "mock-adapter-v1",
            "skill_version": case.get("skill", "ticket-triage") + "@1.1.0",
            "commit_sha": "mock",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "case_id": cid,
            "variation_rate": self.variation_rate,
        }
        return output

    def _generate_triage(self, cid, expected, case_input):
        """Generate a schema-valid triage result."""
        category = expected.get("category", "refund-return")
        priority = expected.get("priority", "P3")

        # Route inference aligned with evaluator._infer_expected_route.
        if priority == "P1":
            # Legal/social P1 can use escalation; medical-risk uses medical-review.
            route_to = "medical-review" if category == "medical-risk" else "escalation"
        elif priority == "P2":
            route_to = "escalation" if category == "compliance" else "tier-2"
        else:
            route_to = "tier-1"

        # Risk flags.
        if priority == "P1":
            risk_type = "medical" if category == "medical-risk" else "legal"
            risk_flags = [
                {
                    "type": risk_type,
                    "severity": "critical",
                    "description": f"P1 escalation — case {cid}",
                }
            ]
        elif priority == "P2":
            risk_type = self._category_to_risk_type(category)
            risk_flags = [
                {
                    "type": risk_type,
                    "severity": "high",
                    "description": f"P2 priority case — {cid}",
                }
            ]
        else:
            risk_flags = []

        human_review_required = True if priority in ("P1", "P2") else expected.get("human_review_required", False)

        # Hard rule: any P1 auto-reply is suppressed.
        if priority == "P1":
            suggested_initial_response = ""
        else:
            suggested_initial_response = (
                "Thank you for contacting us. "
                "We have received your inquiry and will assist you shortly."
            )

        msg = case_input.get("message", "")[:60]
        internal_notes = (
            f"Mock agent triaged {cid}: category={category}, priority={priority}, "
            f"route={route_to}. Input preview: {msg}"
        )

        output = {
            "category": category,
            "priority": priority,
            "route_to": route_to,
            "risk_flags": risk_flags,
            "human_review_required": human_review_required,
            "suggested_initial_response": suggested_initial_response,
            "internal_notes": internal_notes,
        }

        if self.variation_rate > 0 and self.rng.random() < self.variation_rate and priority not in ("P1", "P2"):
            output = self._apply_variation(output=output, cid=cid, priority=priority)

        return output

    def _apply_variation(self, output, cid, priority):
        """Apply minor safe variation to non-critical cases only."""
        variation_type = self.rng.choice(["no_flags", "minimal"])

        if variation_type == "no_flags" and priority not in ("P1", "P2"):
            output["risk_flags"] = []
        elif variation_type == "minimal":
            output["internal_notes"] = f"mock-{cid}"

        return output


def main():
    """CLI entry: run a single case from JSON stdin or file arg."""
    import argparse
    parser = argparse.ArgumentParser(description="Mock agent adapter")
    parser.add_argument("--case", help="Path to case JSON, or '-' for stdin")
    parser.add_argument("--agent", default="customer-support")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--variation", type=float, default=0.0, help="Probability of safe variation per case")
    args = parser.parse_args()

    if args.case == "-" or not args.case:
        case = json.load(sys.stdin)
    else:
        with open(args.case, "r", encoding="utf-8") as f:
            case = json.load(f)

    adapter = MockAdapter(agent=args.agent, seed=args.seed, variation_rate=args.variation)
    result = adapter.run_case(case)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
