#!/usr/bin/env python3
"""
run_agent_case.py — Run a single golden set case through an AI Agent adapter.

Produces a real actual_outputs JSON file by calling the specified adapter
(mock, codex, or hermes). This proves that agents CAN produce triage outputs,
not just that hand-written JSON files match the golden set.

Usage:
  # Mock adapter (for CI testing)
  python run_agent_case.py --golden-set customer-support/evals/golden_set_v1.yaml \\
    --case-id CS-MED-001 --adapter mock --output-dir actual_outputs/current/

  # Codex adapter (real agent)
  python run_agent_case.py --golden-set customer-support/evals/golden_set_v1.yaml \\
    --case-id CS-MED-001 --adapter codex --output-dir actual_outputs/current/

  # Hermes adapter (real agent)
  python run_agent_case.py --golden-set customer-support/evals/golden_set_v1.yaml \\
    --case-id CS-MED-001 --adapter hermes --api-url http://localhost:8787/v1

  # All cases for an agent
  python run_agent_case.py --golden-set customer-support/evals/golden_set_v1.yaml \\
    --adapter mock --output-dir actual_outputs/current/ --all

Exit codes:
  0 — Success
  1 — Adapter error
  2 — Setup error
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

# Import adapters
sys.path.insert(0, str(Path(__file__).parent))
from adapters import MockAdapter, CodexAdapter, HermesAdapter


def load_golden_set(path):
    """Load golden set YAML file."""
    import yaml
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if isinstance(data, list):
        return data
    return data.get("cases", [])


def find_case(cases, case_id):
    """Find a specific case by ID."""
    for case in cases:
        if case.get("id") == case_id:
            return case
    return None


def create_adapter(adapter_name, agent, **kwargs):
    """Factory for creating the right adapter."""
    if adapter_name == "mock":
        return MockAdapter(agent=agent)
    elif adapter_name == "codex":
        return CodexAdapter(
            agent=agent,
            timeout=kwargs.get("timeout", 120),
            model=kwargs.get("model"),
        )
    elif adapter_name == "hermes":
        # Real Hermes adapter — fail-closed, no dry-run fallback
        return HermesAdapter(
            agent=agent,
            timeout=kwargs.get("timeout", 180),
            model=kwargs.get("model"),
            api_url=kwargs.get("api_url"),
        )
    elif adapter_name == "hermes-dry-run":
        # Explicit dry-run — uses golden set expected, NOT real agent evaluation
        # Must be explicitly requested, never used as silent fallback
        adapter = HermesAdapter(
            agent=agent,
            timeout=kwargs.get("timeout", 180),
            model=kwargs.get("model"),
            api_url=kwargs.get("api_url"),
        )
        adapter._dry_run_mode = True
        return adapter
    else:
        print(f"ERROR: Unknown adapter: {adapter_name}", file=sys.stderr)
        print(f"  Available: mock, codex, hermes, hermes-dry-run", file=sys.stderr)
        sys.exit(2)


def run_single_case(case, adapter, output_dir, verbose=False):
    """Run a single case and save the output.

    Returns:
        tuple: (success: bool, output_path: str, elapsed: float)
    """
    cid = case.get("id", "unknown")

    if verbose:
        print(f"  Running {cid} via {adapter.__class__.__name__}...")

    start = time.time()

    try:
        result = adapter.run_case(case)
        elapsed = time.time() - start

        # Ensure _meta is present
        if "_meta" not in result:
            result["_meta"] = {
                "generated_by": adapter.__class__.__name__.replace("Adapter", "").lower(),
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "case_id": cid,
            }

        # Write output
        output_path = Path(output_dir) / f"{cid}.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        if verbose:
            cat = result.get("category", "?")
            pri = result.get("priority", "?")
            print(f"    ✓ {cid}: {cat}/{pri} ({elapsed:.1f}s) → {output_path}")

        return True, str(output_path), elapsed

    except Exception as e:
        elapsed = time.time() - start
        if verbose:
            print(f"    ✗ {cid}: {e} ({elapsed:.1f}s)")

        # Write error output
        error_result = {
            "category": "compliance",
            "priority": "P1",
            "route_to": "escalation",
            "risk_flags": [{"type": "compliance", "severity": "critical",
                           "description": f"Agent crash: {str(e)[:100]}"}],
            "human_review_required": True,
            "suggested_initial_response": "",
            "internal_notes": f"CRASH: {str(e)[:200]}",
            "_meta": {
                "generated_by": adapter.__class__.__name__.replace("Adapter", "").lower(),
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "case_id": cid,
                "error": str(e)[:200],
                "elapsed_seconds": round(elapsed, 2),
            },
        }

        output_path = Path(output_dir) / f"{cid}.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(error_result, f, indent=2, ensure_ascii=False)

        return False, str(output_path), elapsed


def main():
    parser = argparse.ArgumentParser(
        description="Run golden set cases through an AI Agent adapter"
    )
    parser.add_argument("--golden-set", required=True,
                       help="Path to golden_set_v1.yaml")
    parser.add_argument("--case-id", help="Run specific case ID (omit with --all)")
    parser.add_argument("--all", action="store_true",
                       help="Run all cases in the golden set")
    parser.add_argument("--adapter", default="mock",
                       choices=["mock", "codex", "hermes", "hermes-dry-run"],
                       help="Agent adapter to use (default: mock)")
    parser.add_argument("--output-dir", default=None,
                       help="Output directory for JSON files (default: <agent>/evals/actual_outputs/current/)")
    parser.add_argument("--timeout", type=int, default=180,
                       help="Per-case timeout in seconds")
    parser.add_argument("--model", help="Model override for codex/hermes adapters")
    parser.add_argument("--api-url", help="Hermes API URL (for hermes adapter)")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Verbose output")
    parser.add_argument("--agent", default=None,
                       help="Agent name (auto-detected from golden set path)")
    args = parser.parse_args()

    # Validate
    if not args.case_id and not args.all:
        parser.error("Must specify --case-id or --all")

    if not os.path.exists(args.golden_set):
        print(f"ERROR: Golden set not found: {args.golden_set}", file=sys.stderr)
        sys.exit(2)

    # Auto-detect agent from golden set path
    agent = args.agent
    if not agent:
        gs_path = Path(args.golden_set)
        # Path pattern: <agent>/evals/golden_set_v1.yaml
        agent = gs_path.parent.parent.name if gs_path.parent.name == "evals" else "customer-support"

    # Set output dir
    output_dir = args.output_dir
    if not output_dir:
        output_dir = str(Path(agent) / "evals" / "actual_outputs" / "current")

    # Load golden set
    cases = load_golden_set(args.golden_set)
    if not cases:
        print(f"ERROR: No cases found in {args.golden_set}", file=sys.stderr)
        sys.exit(2)

    # Select cases
    if args.case_id:
        case = find_case(cases, args.case_id)
        if not case:
            print(f"ERROR: Case {args.case_id} not found in golden set", file=sys.stderr)
            sys.exit(2)
        cases = [case]

    # Create adapter
    adapter = create_adapter(args.adapter, agent,
                            timeout=args.timeout,
                            model=args.model,
                            api_url=args.api_url)

    # Run banner
    print(f"Agent Case Runner")
    print(f"  Agent: {agent}")
    print(f"  Adapter: {args.adapter}")
    print(f"  Cases: {len(cases)}")
    print(f"  Output: {output_dir}")
    print()

    # Run cases
    total = len(cases)
    success = 0
    failed = 0
    total_elapsed = 0.0

    for i, case in enumerate(cases):
        cid = case.get("id", "?")
        print(f"[{i+1}/{total}] {cid}", end=" ")

        ok, path, elapsed = run_single_case(case, adapter, output_dir,
                                            verbose=args.verbose)
        total_elapsed += elapsed

        if ok:
            success += 1
        else:
            failed += 1

        if not args.verbose:
            status = "✓" if ok else "✗"
            result = json.loads(Path(path).read_text()) if Path(path).exists() else {}
            cat = result.get("category", "?")
            pri = result.get("priority", "?")
            print(f"{status} {cat}/{pri} ({elapsed:.1f}s)")

    # Summary
    print(f"\n{'='*50}")
    print(f"  Total: {total}")
    print(f"  Success: {success}")
    print(f"  Failed: {failed}")
    print(f"  Time: {total_elapsed:.1f}s")
    print(f"  Output: {output_dir}")
    print(f"{'='*50}")

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
