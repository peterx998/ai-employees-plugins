#!/usr/bin/env python3
"""
mock_adapter.py — Mock agent adapter for testing the batch runner pipeline.

Produces realistic-looking triage outputs by applying template rules to
golden set inputs. Uses golden set `expected` as a strong prior but applies
minor variations to simulate real agent behavior (not just copy-paste).

Used when:
  - Running CI without a live AI agent
  - Testing batch runner pipeline end-to-end
  - Developing evaluator rules without API costs

NOT for production evaluation of real agent quality.
"""

import json
import random
import sys
from pathlib import Path
from datetime import datetime, timezone


class MockAdapter:
    """Mock agent that generates triage results from golden-set expected values.

    Strategy: For each case, produce a triage_result that is ~90% similar to the
    expected values but with small variations that exercise the evaluator.
    """

    def __init__(self, agent="customer-support", seed=42, variation_rate=0.15):
        self.agent = agent
        self.seed = seed
        self.variation_rate = variation_rate
        self.rng = random.Random(seed)

        # Load schema enums for valid random values
        self._load_enums(agent)

    def _load_enums(self, agent):
        """Load taxonomy enums for correct fallback values."""
        try:
            import yaml
            tax_path = Path(f"schemas/enums/{agent}_taxonomy.yaml" if agent != "customer-support"
                          else "schemas/enums/customer_support_taxonomy.yaml")
            if tax_path.exists():
                with open(tax_path) as f:
                    taxonomy = yaml.safe_load(f)
                self.categories = taxonomy.get("category", [])
                self.priorities = taxonomy.get("priority", [])
                self.routes = taxonomy.get("route_to", [])
            else:
                self._set_fallback_enums(agent)
        except Exception:
            self._set_fallback_enums(agent)

    def _set_fallback_enums(self, agent):
        """Fallback enums if taxonomy file not found."""
        if agent == "customer-support":
            self.categories = ["medical-risk", "order-status", "refund-return",
                              "product-usage", "warranty", "billing", "compliance"]
            self.priorities = ["P1", "P2", "P3", "P4"]
            self.routes = ["medical-review", "tier-1", "tier-2", "escalation"]
        else:
            self.categories = []
            self.priorities = ["P1", "P2", "P3", "P4"]
            self.routes = []

    def _category_to_risk_type(self, category):
        """Map golden set category to valid risk_flag type enum value.

        Valid risk_flag types: medical, legal, social, regulatory, compliance, repeat-contact
        """
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
        """Run a single golden set case through the mock adapter.

        Args:
            case: dict from golden_set_v1.yaml with keys:
                  id, agent, skill, input, expected, scoring

        Returns:
            dict: triage_result conforming to triage_result.schema.json
        """
        cid = case.get("id", "unknown")
        expected = case.get("expected", {})
        case_input = case.get("input", {})

        # Template-based generation from golden set expected values
        output = self._generate_triage(cid, expected, case_input)

        # Add _meta for evidence chain
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
        """Generate triage result applying template rules.

        Core rules:
        1. P1 medical → route_to=medical-review, response empty, risk_flags non-empty
        2. P2 → route_to=tier-2 or escalation depending on category
        3. P3/P4 → route_to=tier-1
        4. Apply small variations to test evaluator robustness
        """
        category = expected.get("category", "refund-return")
        priority = expected.get("priority", "P3")

        # Route inference matching evaluator._infer_expected_route
        if priority == "P1" or category == "medical-risk":
            route_to = "medical-review"
        elif priority == "P2":
            route_to = "escalation" if category == "compliance" else "tier-2"
        else:
            route_to = "tier-1"

        # Risk flags
        if priority == "P1":
            risk_flags = [
                {"type": "medical", "severity": "critical",
                 "description": f"P1 medical escalation — case {cid}"}
            ]
        elif priority == "P2":
            # Map category to valid risk_flag type enum
            risk_type = self._category_to_risk_type(category)
            risk_flags = [
                {"type": risk_type, "severity": "high",
                 "description": f"P2 priority case — {cid}"}
            ]
        else:
            risk_flags = []

        # Human review: P1/P2 always true, P3/P4 as expected
        if priority in ("P1", "P2"):
            human_review_required = True
        else:
            human_review_required = expected.get("human_review_required", False)

        # Suggested initial response: empty for P1 medical
        if priority == "P1" and category == "medical-risk":
            suggested_initial_response = ""
        else:
            suggested_initial_response = (
                "Thank you for contacting us. "
                "We have received your inquiry and will assist you shortly."
            )

        # Internal notes
        msg = case_input.get("message", "")[:60]
        internal_notes = (
            f"Mock agent triaged {cid}: category={category}, priority={priority}, "
            f"route={route_to}. Input preview: {msg}"
        )

        # Apply random variation (simulating agent variance) unless P1
        if self.rng.random() < self.variation_rate and priority != "P1":
            output = self._apply_variation(output={
                "category": category,
                "priority": priority,
                "route_to": route_to,
                "risk_flags": risk_flags,
                "human_review_required": human_review_required,
                "suggested_initial_response": suggested_initial_response,
                "internal_notes": internal_notes,
            }, cid=cid, priority=priority)
        else:
            output = {
                "category": category,
                "priority": priority,
                "route_to": route_to,
                "risk_flags": risk_flags,
                "human_review_required": human_review_required,
                "suggested_initial_response": suggested_initial_response,
                "internal_notes": internal_notes,
            }

        return output

    def _apply_variation(self, output, cid, priority):
        """Apply minor random variation to non-P1 cases.

        Kinds of variation (one randomly chosen per case):
        - Skip risk_flags for P3/P4 (test empty detection)
        - Slightly different route (test route accuracy)
        - Different internal_notes format (test field completeness)
        """
        variation_type = self.rng.choice(["no_flags", "alt_route", "minimal"])

        if variation_type == "no_flags" and priority not in ("P1", "P2"):
            output["risk_flags"] = []

        elif variation_type == "alt_route" and priority == "P2":
            output["route_to"] = self.rng.choice([r for r in self.routes
                                                    if r != output["route_to"]])

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
    parser.add_argument("--variation", type=float, default=0.15,
                       help="Probability of variation per case (0.0 = exact expected)")
    args = parser.parse_args()

    if args.case == "-" or not args.case:
        case = json.load(sys.stdin)
    else:
        with open(args.case, "r", encoding="utf-8") as f:
            case = json.load(f)

    adapter = MockAdapter(agent=args.agent, seed=args.seed,
                          variation_rate=args.variation)
    result = adapter.run_case(case)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
