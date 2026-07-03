#!/usr/bin/env python3
"""
findings_report.py — Generate structured findings from all pipeline stages.

Reads evaluator output, CI artifacts, and stage results to produce
findings in the format defined by schemas/common/finding.schema.json.

Usage:
  python scripts/findings_report.py --agent customer-support
  python scripts/findings_report.py --agent customer-support --output experiments/runs/customer-support/findings.json
"""

import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False


# ─── Action classification rules ───

AUTO_FIX_CATEGORIES = {
    "schema_enum_mismatch": "auto-fix",
    "missing_field_in_output": "auto-fix",
    "yaml_format_error": "auto-fix",
    "json_format_error": "auto-fix",
    "output_schema_path_wrong": "auto-fix",
    "mock_output_missing_field": "auto-fix",
    "badge_outdated": "auto-fix",
}

ASK_USER_CATEGORIES = {
    "medical_policy_changed": "ask-user",
    "refund_policy_changed": "ask-user",
    "human_review_rule_relaxed": "ask-user",
    "p1_judgment_changed": "ask-user",
    "p2_judgment_changed": "ask-user",
    "connector_permission_upgraded": "ask-user",
    "golden_set_expected_changed": "ask-user",
    "hard_constraint_modified": "ask-user",
    "policy_file_modified": "ask-user",
}


def load_eval_results(agent):
    """Load eval_results.json for an agent."""
    path = Path(f"{agent}/reports/eval_results.json")
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_schema(findings):
    """Validate findings against the finding schema."""
    schema_path = Path("schemas/common/finding.schema.json")
    if not schema_path.exists() or not HAS_JSONSCHEMA:
        return True, "Schema validation skipped"

    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    errors = []
    for i, finding in enumerate(findings):
        try:
            jsonschema.validate(instance=finding, schema=schema)
        except jsonschema.ValidationError as e:
            errors.append(f"Finding #{i}: {e.message}")

    return len(errors) == 0, errors


def classify_action(message, file_path=""):
    """Classify the recommended action for a finding."""
    # Check ask-user categories first (safety-critical)
    for keyword, action in ASK_USER_CATEGORIES.items():
        k = keyword.replace("_", " ")
        if k in message.lower() or keyword in message.lower():
            return action

    # Check auto-fix categories
    for keyword, action in AUTO_FIX_CATEGORIES.items():
        k = keyword.replace("_", " ")
        if k in message.lower() or keyword in message.lower():
            return action

    # Check file-based rules
    if file_path:
        if "policy" in file_path.lower():
            return "ask-user"
        if "golden_set" in file_path:
            return "ask-user"
        if "schema" in file_path.lower() and file_path.endswith(".json"):
            return "auto-fix"

    # Default: ask user for safety
    return "ask-user"


def generate_findings(agent, output_path=None):
    """Generate all findings for an agent from pipeline results."""
    findings = []

    # 1. Check schema consistency
    validate_script = Path("scripts/ci_validate_schema.py")
    if validate_script.exists():
        import subprocess
        result = subprocess.run(
            ["python", str(validate_script)],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0:
            findings.append({
                "stage": "contract",
                "severity": "error",
                "action": "auto-fix",
                "file": "schemas/customer-support/triage_result.schema.json",
                "message": "Schema/taxonomy/golden_set misalignment",
                "detail": result.stdout[:500] + result.stderr[:200],
                "risk_level": "high",
            })

    # 2. Check eval results
    eval_data = load_eval_results(agent)
    if eval_data:
        # Hard constraint failures
        if eval_data.get("hard_constraint_failures", 0) > 0:
            for r in eval_data.get("results", []):
                if not r.get("passed") and any("Hard constraint" in reason for reason in r.get("reasons", [])):
                    findings.append({
                        "stage": "eval-current",
                        "severity": "error",
                        "action": "ask-user",
                        "related_case": r.get("case_id"),
                        "message": f"Hard constraint failure in {r.get('case_id', '?')}: {'; '.join(r.get('reasons', []))}",
                        "risk_level": "critical",
                    })

        # Schema failures
        if eval_data.get("schema_failures", 0) > 0:
            for r in eval_data.get("results", []):
                if not r.get("passed") and any("Schema validation" in reason for reason in r.get("reasons", [])):
                    findings.append({
                        "stage": "eval-current",
                        "severity": "error",
                        "action": "auto-fix",
                        "related_case": r.get("case_id"),
                        "message": f"Schema validation failure in {r.get('case_id', '?')}: {'; '.join(r.get('reasons', []))}",
                        "risk_level": "medium",
                    })

        # Pending outputs
        if eval_data.get("pending", 0) > 0:
            findings.append({
                "stage": "eval-current",
                "severity": "error",
                "action": "ask-user",
                "message": f"{eval_data['pending']} cases have no actual output — evaluation incomplete",
                "risk_level": "high",
            })

    # 3. Check for policy modifications
    import subprocess
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD~1"],
        capture_output=True, text=True,
    )
    for f in result.stdout.strip().split("\n"):
        f = f.strip()
        if not f:
            continue
        if "policies/" in f and f.endswith(".md"):
            findings.append({
                "stage": "contract",
                "severity": "warning",
                "action": "ask-user",
                "file": f,
                "message": f"Policy file modified: {f}",
                "risk_level": "high",
            })
        if "golden_set" in f:
            findings.append({
                "stage": "contract",
                "severity": "warning",
                "action": "ask-user",
                "file": f,
                "message": f"Golden set modified: {f}",
                "risk_level": "high",
            })

    # Classify actions
    for f in findings:
        if "action" not in f or not f["action"]:
            f["action"] = classify_action(f.get("message", ""), f.get("file", ""))

    # Validate findings
    valid, errors = validate_schema(findings)
    if not valid:
        print(f"WARNING: {len(errors)} findings failed schema validation")

    # Sort by severity
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    findings.sort(key=lambda x: severity_order.get(x.get("risk_level", "low"), 99))

    # Add metadata
    result = {
        "agent": agent,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_findings": len(findings),
        "critical": len([f for f in findings if f.get("risk_level") == "critical"]),
        "high": len([f for f in findings if f.get("risk_level") == "high"]),
        "medium": len([f for f in findings if f.get("risk_level") == "medium"]),
        "low": len([f for f in findings if f.get("risk_level") == "low"]),
        "auto_fixable": len([f for f in findings if f.get("action") == "auto-fix"]),
        "needs_review": len([f for f in findings if f.get("action") == "ask-user"]),
        "findings": findings,
    }

    # Save
    if output_path is None:
        output_path = f"reports/findings.json"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"Findings saved: {output_path}")

    return result


def main():
    parser = argparse.ArgumentParser(description="Generate findings from pipeline results")
    parser.add_argument("--agent", required=True, help="Agent name")
    parser.add_argument("--output", help="Output path for findings.json")
    args = parser.parse_args()

    result = generate_findings(args.agent, args.output)

    print(f"\nFindings Summary for {args.agent}:")
    print(f"  Total: {result['total_findings']}")
    print(f"  Critical: {result['critical']}")
    print(f"  Auto-fixable: {result['auto_fixable']}")
    print(f"  Needs review: {result['needs_review']}")

    if result["critical"] > 0:
        sys.exit(2)
    if result["needs_review"] > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
