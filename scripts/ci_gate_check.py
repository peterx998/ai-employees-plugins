#!/usr/bin/env python3
"""CI helper: read eval_results.json and check verdict, printing summary."""
import json, sys

result_file = sys.argv[1] if len(sys.argv) > 1 else "customer-support/reports/eval_results.json"

try:
    with open(result_file) as f:
        d = json.load(f)
except FileNotFoundError:
    print(f"::error::Eval results not found at {result_file}")
    sys.exit(1)

verdict = d.get("verdict", "UNKNOWN")
pending = d.get("pending", 0)
hc_fail = d.get("hard_constraint_failures", 0)
schema_fail = d.get("schema_failures", 0)

print(f"Verdict: {verdict} | Pending: {pending} | HC failures: {hc_fail} | Schema failures: {schema_fail}")
print(f"Total: {d.get('total_cases','?')} | Passed: {d.get('passed','?')} | Failed: {d.get('failed','?')}")

if verdict != "PASS":
    print(f"::error::CI gate blocked — verdict is {verdict}")
    sys.exit(1)

print("CI Gate: PASS")
