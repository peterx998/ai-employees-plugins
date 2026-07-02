#!/usr/bin/env python3
"""CI helper: validate schema consistency between taxonomy, schema, and golden set."""
import json, yaml, sys

with open("schemas/enums/customer_support_taxonomy.yaml") as f:
    taxonomy = yaml.safe_load(f)

with open("schemas/customer-support/triage_result.schema.json") as f:
    schema = json.load(f)

errors = []

sp = set(schema["properties"]["priority"]["enum"])
tp = set(taxonomy["priority"])
if sp != tp:
    errors.append(f"priority mismatch: {sp} vs {tp}")

sc = set(schema["properties"]["category"]["enum"])
tc = set(taxonomy["category"])
if sc != tc:
    errors.append(f"category mismatch: {sc} vs {tc}")

sr = set(schema["properties"]["route_to"]["enum"])
tr = set(taxonomy["route_to"])
if sr != tr:
    errors.append(f"route_to mismatch: {sr} vs {tr}")

with open("customer-support/evals/golden_set_v1.yaml") as f:
    cases = yaml.safe_load(f)

for case in cases:
    cid = case.get("id", "?")
    exp = case.get("expected", {})
    if exp.get("category", "") and exp["category"] not in tc:
        errors.append(f"{cid}: category {exp['category']} not in taxonomy")
    if exp.get("priority", "") and exp["priority"] not in tp:
        errors.append(f"{cid}: priority {exp['priority']} not in taxonomy")

if errors:
    for e in errors:
        print(f"::error::{e}")
    sys.exit(1)

print(f"Schema consistency: {len(cases)} cases aligned, {len(tc)} categories, {len(tp)} priorities")
