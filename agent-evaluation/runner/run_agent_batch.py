#!/usr/bin/env python3
"""
run_agent_batch.py — Run Golden Set cases through a real Agent and capture outputs.

This is the missing execution layer: it takes Golden Set inputs, feeds them to
an Agent (via adapter), and writes actual_outputs/{run_id}/ for the evaluator.

Adapters:
  --adapter mock    — Uses expected outputs as actual (for CI smoke test)
  --adapter codex   — Calls Codex CLI to process each case
  --adapter hermes  — Calls Hermes Agent to process each case
  --adapter openai  — Calls OpenAI API directly

Usage:
  # Generate baseline outputs (mock adapter for CI)
  python run_agent_batch.py --agent customer-support --adapter mock \
    --output-dir customer-support/evals/actual_outputs/current

  # Run with real Codex
  python run_agent_batch.py --agent customer-support --adapter codex \
    --output-dir customer-support/evals/actual_outputs/current

  # Then evaluate
  python run_eval.py --golden-set customer-support/evals/golden_set_v1.yaml \
    --agent customer-support --actual-dir customer-support/evals/actual_outputs/current
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required", file=sys.stderr)
    sys.exit(2)


# ─── Metadata for output provenance ───

def create_metadata(agent, adapter, run_id=None):
    """Create metadata dict for output provenance."""
    # Get git commit if available
    commit = "unknown"
    try:
        result = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True)
        commit = result.stdout.strip()
    except:
        pass

    return {
        "generated_by": adapter,
        "agent": agent,
        "model": os.environ.get("AGENT_MODEL", "unknown"),
        "runtime": adapter,
        "skill_version": "1.1.0",
        "commit_sha": commit,
        "timestamp": datetime.now(datetime.UTC).isoformat(),
        "run_id": run_id or f"{agent}-{datetime.now().strftime('%Y%m%d_%H%M%S')}",
    }


# ─── Adapters ───

def mock_adapter(case, agent):
    """Mock adapter: returns expected output (for CI smoke test only).

    WARNING: This produces 'correct' outputs by design. It validates the
    evaluation pipeline but does NOT test real Agent capability.
    """
    return case.get("expected", {})


def codex_adapter(case, agent):
    """Codex adapter: calls Codex CLI to process the case.

    Constructs a prompt from the golden set input and asks Codex to produce
    a triage result matching the output schema.
    """
    cid = case.get("id", "unknown")
    inp = case.get("input", {})
    message = inp.get("message", "")
    region = inp.get("region", "US")

    # Construct prompt
    prompt = f"""You are a customer support triage agent. Analyze this customer message and produce a triage result.

Customer message: "{message}"
Region: {region}

Output a JSON object with these exact fields:
- category: one of medical-risk, order-status, refund-return, product-usage, warranty, billing, compliance
- priority: one of P1, P2, P3, P4
- route_to: one of medical-review, tier-1, tier-2, escalation
- risk_flags: array of {{type, severity, description}} (empty array if none)
- human_review_required: boolean (true for P1/P2)
- suggested_initial_response: string (empty string for P1 medical — auto-reply suppressed)
- internal_notes: string

Output ONLY the JSON, no other text."""

    try:
        result = subprocess.run(
            ["codex", "--quiet", "--json", prompt],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return {"error": f"Codex returned {result.returncode}", "stderr": result.stderr[:200]}

        # Try to parse Codex output as JSON
        output_text = result.stdout.strip()
        # Find JSON in output
        start = output_text.find("{")
        end = output_text.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(output_text[start:end])
        return {"error": "Could not parse Codex output as JSON", "raw": output_text[:200]}

    except subprocess.TimeoutExpired:
        return {"error": "Codex timed out after 30s"}
    except json.JSONDecodeError as e:
        return {"error": f"JSON parse error: {e}"}
    except FileNotFoundError:
        return {"error": "Codex CLI not found. Install codex or use --adapter mock."}


def hermes_adapter(case, agent):
    """Hermes adapter: calls Hermes Agent to process the case.

    Uses hermes CLI to send the case as a prompt.
    """
    cid = case.get("id", "unknown")
    inp = case.get("input", {})
    message = inp.get("message", "")
    region = inp.get("region", "US")

    prompt = f"""Triage this customer support message and output JSON only.

Message: "{message}"
Region: {region}

Output JSON with: category, priority, route_to, risk_flags, human_review_required, suggested_initial_response, internal_notes"""

    try:
        result = subprocess.run(
            ["hermes", "run", "--prompt", prompt, "--no-tools"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return {"error": f"Hermes returned {result.returncode}"}

        output_text = result.stdout.strip()
        start = output_text.find("{")
        end = output_text.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(output_text[start:end])
        return {"error": "Could not parse Hermes output as JSON", "raw": output_text[:200]}

    except subprocess.TimeoutExpired:
        return {"error": "Hermes timed out after 30s"}
    except FileNotFoundError:
        return {"error": "Hermes CLI not found. Install hermes or use --adapter mock."}


ADAPTERS = {
    "mock": mock_adapter,
    "codex": codex_adapter,
    "hermes": hermes_adapter,
}


def main():
    parser = argparse.ArgumentParser(description="Run Golden Set through a real Agent")
    parser.add_argument("--agent", required=True, help="Agent name (e.g., customer-support)")
    parser.add_argument("--adapter", required=True, choices=["mock", "codex", "hermes"],
                       help="Which adapter to use")
    parser.add_argument("--golden-set", help="Path to golden set YAML")
    parser.add_argument("--output-dir", required=True, help="Directory to write actual outputs")
    parser.add_argument("--case-id", help="Run only one case")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout per case in seconds")
    args = parser.parse_args()

    # Load golden set
    golden_set_path = args.golden_set or f"{args.agent}/evals/golden_set_v1.yaml"
    with open(golden_set_path, "r", encoding="utf-8") as f:
        cases = yaml.safe_load(f)

    if args.case_id:
        cases = [c for c in cases if c.get("id") == args.case_id]

    if not cases:
        print(f"ERROR: No cases found", file=sys.stderr)
        sys.exit(2)

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create metadata
    metadata = create_metadata(args.agent, args.adapter)
    metadata["golden_set_path"] = golden_set_path
    metadata["total_cases"] = len(cases)

    # Write metadata
    with open(output_dir / "_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"=== Agent Batch Run ===")
    print(f"Agent: {args.agent}")
    print(f"Adapter: {args.adapter}")
    print(f"Cases: {len(cases)}")
    print(f"Output: {output_dir}")
    print(f"Run ID: {metadata['run_id']}")
    print()

    adapter_fn = ADAPTERS[args.adapter]
    results = []
    success = 0
    errors = 0

    for i, case in enumerate(cases):
        cid = case.get("id", f"case-{i}")
        print(f"  [{i+1}/{len(cases)}] {cid}...", end=" ")

        try:
            actual = adapter_fn(case, args.agent)
            if "error" in actual:
                print(f"❌ ERROR: {actual['error']}")
                errors += 1
            else:
                print(f"✅")
                success += 1
        except Exception as e:
            print(f"❌ EXCEPTION: {e}")
            actual = {"error": str(e)}
            errors += 1

        # Write output
        out_file = output_dir / f"{cid}.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(actual, f, indent=2, ensure_ascii=False)

        results.append({"case_id": cid, "has_error": "error" in actual})

    # Summary
    print(f"\n=== Batch Complete ===")
    print(f"Success: {success}/{len(cases)}")
    print(f"Errors: {errors}/{len(cases)}")
    print(f"Outputs: {output_dir}")
    print(f"Metadata: {output_dir / '_metadata.json'}")

    if errors > 0 and args.adapter != "mock":
        print(f"\n⚠️  {errors} cases had errors. Check output files for details.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
