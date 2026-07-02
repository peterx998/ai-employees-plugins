#!/usr/bin/env python3
"""
validate-evals.py — Deep evaluation data validator.

Validates:
  - Golden set YAML structure and taxonomy consistency
  - Golden set expected values against taxonomy enums
  - actual_outputs JSON against schema
  - actual_outputs _meta completeness
  - Baseline vs current output comparison readiness

Usage:
  python install/validate-evals.py --agent customer-support
  python install/validate-evals.py --agent customer-support --check-actuals

Exit codes:
  0 — All valid
  1 — Warnings
  2 — Errors
"""

import json
import os
import sys
from pathlib import Path

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
    print("WARNING: jsonschema not installed. Schema validation skipped.", file=sys.stderr)


REPO = Path(__file__).parent.parent


def load_taxonomy(agent):
    """Load the agent's taxonomy enum file."""
    tax_path = REPO / "schemas" / "enums" / f"{agent}_taxonomy.yaml"
    if not tax_path.exists():
        # Try customer-support taxonomy as default
        tax_path = REPO / "schemas" / "enums" / "customer_support_taxonomy.yaml"

    if not tax_path.exists():
        return None

    with open(tax_path) as f:
        return yaml.safe_load(f)


def load_schema(agent):
    """Load the agent's output schema."""
    schema_path = REPO / "schemas" / agent / "triage_result.schema.json"
    if not schema_path.exists():
        return None

    with open(schema_path) as f:
        return json.load(f)


def validate_golden_set(golden_path, taxonomy, schema):
    """Validate golden set structure and taxonomy consistency."""
    errors = []
    warnings = []

    if not golden_path.exists():
        errors.append(f"Golden set not found: {golden_path}")
        return errors, warnings

    try:
        with open(golden_path) as f:
            cases = yaml.safe_load(f)
    except yaml.YAMLError as e:
        errors.append(f"Golden set YAML parse error: {e}")
        return errors, warnings

    if not isinstance(cases, list):
        errors.append(f"Golden set must be a list of cases, got {type(cases).__name__}")
        return errors, warnings

    print(f"  Loaded {len(cases)} cases")

    seen_ids = set()
    tax_categories = set(taxonomy.get("category", [])) if taxonomy else set()
    tax_priorities = set(taxonomy.get("priority", [])) if taxonomy else set()

    for case in cases:
        cid = case.get("id", "MISSING")

        # Required fields
        for field in ["id", "agent", "skill", "input", "expected"]:
            if field not in case:
                errors.append(f"{cid}: Missing required field '{field}'")

        # Duplicate ID check
        if cid in seen_ids:
            errors.append(f"{cid}: Duplicate case ID")
        seen_ids.add(cid)

        expected = case.get("expected", {})

        # Category check
        cat = expected.get("category", "")
        if cat and tax_categories and cat not in tax_categories:
            errors.append(f"{cid}: Category '{cat}' not in taxonomy: {sorted(tax_categories)}")

        # Priority check
        pri = expected.get("priority", "")
        if pri and tax_priorities and pri not in tax_priorities:
            errors.append(f"{cid}: Priority '{pri}' not in taxonomy: {sorted(tax_priorities)}")

        # P1 consistency checks
        if pri == "P1":
            if not expected.get("human_review_required", False):
                errors.append(f"{cid}: P1 case but human_review_required is not true in expected")

        # P2 consistency checks
        if pri == "P2":
            if not expected.get("human_review_required", False):
                errors.append(f"{cid}: P2 case but human_review_required is not true in expected")

        # Forbidden phrases must be lowercase
        forbidden = expected.get("forbidden", [])
        for phrase in forbidden:
            if phrase != phrase.lower():
                warnings.append(f"{cid}: Forbidden phrase '{phrase}' is not lowercase")

    # Check all golden set IDs have corresponding baseline outputs
    baseline_dir = golden_path.parent / "actual_outputs" / "baseline"
    if baseline_dir.exists():
        baseline_ids = {f.stem for f in baseline_dir.glob("*.json") if not f.name.startswith("_")}
        gold_ids = {c["id"] for c in cases}

        missing_baselines = gold_ids - baseline_ids
        for mid in missing_baselines:
            warnings.append(f"{mid}: No baseline output found in {baseline_dir}")

        extra_baselines = baseline_ids - gold_ids
        for eid in extra_baselines:
            warnings.append(f"{eid}: Baseline output exists but no golden set case with this ID")

    return errors, warnings


def validate_actual_outputs(actual_dir, schema, check_meta=True):
    """Validate actual output JSON files against schema."""
    errors = []
    warnings = []

    if not actual_dir.exists():
        errors.append(f"Actual outputs directory not found: {actual_dir}")
        return errors, warnings

    json_files = sorted(actual_dir.glob("*.json"))
    if not json_files:
        warnings.append(f"No JSON files in {actual_dir}")
        return errors, warnings

    total = 0
    schema_pass = 0
    schema_fail = 0

    for jf in json_files:
        if jf.name.startswith("_"):
            continue  # Skip metadata files

        total += 1
        try:
            with open(jf) as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            errors.append(f"{jf.name}: Invalid JSON: {e}")
            continue

        # Schema validation
        if schema and HAS_JSONSCHEMA:
            try:
                validate(instance=data, schema=schema)
                schema_pass += 1
            except ValidationError as e:
                errors.append(f"{jf.name}: Schema validation failed: {e.message}")
                schema_fail += 1
        elif schema and not HAS_JSONSCHEMA:
            warnings.append(f"{jf.name}: Schema validation skipped (jsonschema not installed)")

        # Required fields check
        if schema:
            required = schema.get("required", [])
            for field in required:
                if field not in data:
                    errors.append(f"{jf.name}: Missing required field '{field}'")

        # _meta check
        if check_meta:
            meta = data.get("_meta")
            if not meta:
                warnings.append(f"{jf.name}: Missing _meta block — cannot trace generation source")
            else:
                generated_by = meta.get("generated_by", "unknown")
                if generated_by == "unknown":
                    warnings.append(f"{jf.name}: _meta.generated_by is 'unknown'")
                elif generated_by not in ("mock", "codex", "hermes", "manual", "manual_baseline"):
                    warnings.append(f"{jf.name}: Unrecognized _meta.generated_by: {generated_by}")

        # Content checks
        pri = data.get("priority", "")
        cat = data.get("category", "")

        # P1 consistency: response must be empty
        if pri == "P1":
            resp = data.get("suggested_initial_response", "")
            if resp:
                errors.append(
                    f"{jf.name}: P1 case but suggested_initial_response is not empty: "
                    f"'{resp[:50]}...'"
                )

            route = data.get("route_to", "")
            if route not in ("medical-review", "escalation"):
                errors.append(
                    f"{jf.name}: P1 case but route_to='{route}' (expected medical-review or escalation)"
                )

            if not data.get("human_review_required"):
                errors.append(f"{jf.name}: P1 case but human_review_required is false")

    if total > 0:
        print(f"  Validated {total} actual outputs: {schema_pass} schema-pass, {schema_fail} schema-fail")

    return errors, warnings


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Deep evaluation data validator")
    parser.add_argument("--agent", default="customer-support", help="Agent name")
    parser.add_argument("--golden-set", help="Path to golden set YAML")
    parser.add_argument("--check-actuals", action="store_true",
                       help="Also validate actual output JSON files against schema")
    parser.add_argument("--actual-dir", help="Override actual outputs directory")
    args = parser.parse_args()

    agent = args.agent
    total_errors = 0
    total_warnings = 0

    print(f"Evaluation Data Validator — {agent}")
    print()

    # Load taxonomy and schema
    taxonomy = load_taxonomy(agent)
    schema = load_schema(agent)

    if not taxonomy:
        print(f"⚠ Taxonomy not found for {agent}")
    else:
        print(f"✅ Taxonomy loaded: {len(taxonomy.get('category', []))} categories, "
              f"{len(taxonomy.get('priority', []))} priorities, "
              f"{len(taxonomy.get('route_to', []))} routes")

    if not schema:
        print(f"⚠ Schema not found for {agent}")
    else:
        required = schema.get("required", [])
        print(f"✅ Schema loaded: {len(required)} required fields: {', '.join(required)}")

    # Validate golden set
    print(f"\n── Golden Set Validation ──")
    golden_path = Path(args.golden_set) if args.golden_set else REPO / agent / "evals" / "golden_set_v1.yaml"
    errors, warnings = validate_golden_set(golden_path, taxonomy, schema)

    for e in errors:
        print(f"  ❌ {e}")
    for w in warnings:
        print(f"  ⚠  {w}")
    if not errors and not warnings:
        print(f"  ✅ Golden set valid")

    total_errors += len(errors)
    total_warnings += len(warnings)

    # Validate actual outputs
    if args.check_actuals:
        print(f"\n── Actual Outputs Validation ──")
        actual_dir = Path(args.actual_dir) if args.actual_dir else REPO / agent / "evals" / "actual_outputs" / "baseline"
        errors, warnings = validate_actual_outputs(actual_dir, schema)

        for e in errors:
            print(f"  ❌ {e}")
        for w in warnings:
            print(f"  ⚠  {w}")
        if not errors and not warnings:
            print(f"  ✅ All actual outputs valid")

        total_errors += len(errors)
        total_warnings += len(warnings)

    # Summary
    print(f"\n{'='*60}")
    print(f"  Total: {total_errors} errors, {total_warnings} warnings")
    if total_errors == 0:
        print(f"  ✅ All evaluation data valid")
    else:
        print(f"  ❌ {total_errors} data violation(s) found")
    print(f"{'='*60}")

    sys.exit(2 if total_errors > 0 else (1 if total_warnings > 0 else 0))


if __name__ == "__main__":
    main()
