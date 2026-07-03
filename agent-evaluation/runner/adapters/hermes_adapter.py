#!/usr/bin/env python3
"""
hermes_adapter.py — Run evaluation cases through Hermes Agent.

Uses the Hermes Agent API to process cases. Requires Hermes Agent to be
running with a valid provider configured.

The adapter:
  1. Constructs a prompt from the golden set case input
  2. Calls Hermes Agent API (or local runner) with the SKILL.md as context
  3. Parses the JSON output
  4. Returns a triage_result dict

Usage:
  # Via Hermes CLI
  python hermes_adapter.py --case case.json --skill ticket-triage

  # Via Hermes Agent API (if running as server)
  python hermes_adapter.py --case case.json --api-url http://localhost:8787/v1
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class HermesAdapter:
    """Run cases through Hermes Agent and return triage results.

    Supports two modes:
    1. Hermes CLI: `hermes run --prompt "..."` (default)
    2. Hermes API: HTTP POST to Hermes gateway (if --api-url provided)
    """

    def __init__(self, agent="customer-support", timeout=180, model=None,
                 api_url=None, skill_path=None):
        self.agent = agent
        self.timeout = timeout
        self.model = model
        self.api_url = api_url
        self.skill_path = skill_path
        self._dry_run_mode = False  # Only set True by factory for hermes-dry-run

        # Check what mode we're in
        self.use_api = bool(api_url)
        if self.use_api and not HAS_REQUESTS:
            print("WARNING: requests library not installed. Falling back to CLI mode.",
                  file=sys.stderr)
            self.use_api = False

        if not self.use_api and not self._dry_run_mode:
            self._check_hermes_installed()

    def _check_hermes_installed(self):
        """Verify hermes CLI is available. Fail-closed — no silent fallback."""
        try:
            result = subprocess.run(
                ["hermes", "--version"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode != 0:
                print(f"WARNING: hermes --version returned {result.returncode}. "
                      f"Real agent evaluation will fail — use --adapter hermes-dry-run for pipeline testing.",
                      file=sys.stderr)
        except FileNotFoundError:
            print("WARNING: hermes CLI not found. Real agent evaluation will fail-closed. "
                  "Use --adapter mock or --adapter hermes-dry-run for pipeline testing.",
                  file=sys.stderr)

    def run_case(self, case):
        """Run a single case through Hermes Agent.

        Args:
            case: dict from golden set with id, agent, skill, input, expected

        Returns:
            dict: triage_result with _meta
        """
        cid = case.get("id", "unknown")
        skill_name = case.get("skill", "ticket-triage")

        # Explicit dry-run mode (only via --adapter hermes-dry-run)
        if self._dry_run_mode:
            output = self._dry_run(case, cid, skill_name)
            output["_meta"] = {
                "generated_by": "hermes-dry-run",
                "model": "dry-run (NOT real agent)",
                "skill_version": f"{skill_name}@1.1.0",
                "commit_sha": self._get_commit_sha(),
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "elapsed_seconds": 0.0,
                "case_id": cid,
                "mode": "dry-run",
                "warning": "NOT real agent evaluation — uses golden set expected values",
            }
            return output

        if self.use_api:
            return self._run_via_api(case, cid, skill_name)
        else:
            return self._run_via_cli(case, cid, skill_name)

    def _run_via_api(self, case, cid, skill_name):
        """Run via HTTP API to Hermes Agent gateway."""
        prompt = self._build_prompt(case)
        skill_context = self._load_skill_context(skill_name)

        payload = {
            "messages": [
                {"role": "system", "content": skill_context},
                {"role": "user", "content": prompt},
            ],
            "model": self.model or os.environ.get("HERMES_MODEL", ""),
            "temperature": 0.0,
        }

        start_time = time.time()

        try:
            resp = requests.post(
                f"{self.api_url.rstrip('/')}/chat/completions",
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"},
            )
            elapsed = time.time() - start_time

            if resp.status_code != 200:
                return self._error_result(cid, f"API {resp.status_code}: {resp.text[:200]}",
                                         elapsed)

            data = resp.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

            output = self._parse_output(content, cid)
            output["_meta"] = {
                "generated_by": "hermes",
                "model": data.get("model", self.model or "unknown"),
                "skill_version": f"{skill_name}@1.1.0",
                "commit_sha": self._get_commit_sha(),
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "elapsed_seconds": round(elapsed, 2),
                "case_id": cid,
                "api_url": self.api_url,
            }
            return output

        except requests.Timeout:
            return self._error_result(cid, f"API timeout after {self.timeout}s", self.timeout)
        except Exception as e:
            return self._error_result(cid, f"Exception: {str(e)[:200]}",
                                     time.time() - start_time)

    def _run_via_cli(self, case, cid, skill_name):
        """Run via `hermes run` CLI command.

        FAIL-CLOSED: If hermes CLI is not available or fails, returns an error
        result. This prevents false positives where expected-based dry-run
        output passes evaluation without real agent capability.

        For dry-run testing, use --adapter hermes-dry-run explicitly.
        """
        prompt = self._build_prompt(case)
        skill_context = self._load_skill_context(skill_name)
        full_prompt = skill_context + "\n\n---\n\n" + prompt

        start_time = time.time()

        try:
            # Try hermes CLI
            cmd = [
                "hermes", "run",
                "--prompt", full_prompt,
                "--json",
            ]
            if self.model:
                cmd.extend(["--model", self.model])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=os.getcwd(),
            )
            elapsed = time.time() - start_time

            if result.returncode == 0:
                output = self._parse_output(result.stdout, cid)
            else:
                # FAIL-CLOSED: Hermes CLI failed — return error, NOT dry-run
                return self._error_result(
                    cid,
                    f"Hermes CLI failed (exit {result.returncode}): {result.stderr[:200]}",
                    elapsed,
                )

        except FileNotFoundError:
            # FAIL-CLOSED: Hermes CLI not installed — return error, NOT dry-run
            elapsed = time.time() - start_time
            return self._error_result(
                cid,
                "Hermes CLI not found — install hermes or use --adapter hermes-dry-run for testing",
                elapsed,
            )
        except subprocess.TimeoutExpired:
            elapsed = self.timeout
            return self._error_result(cid, f"CLI timeout after {self.timeout}s", elapsed)
        except Exception as e:
            elapsed = time.time() - start_time
            return self._error_result(cid, f"Exception: {str(e)[:200]}", elapsed)

        output["_meta"] = {
            "generated_by": "hermes",
            "model": self.model or "hermes-cli",
            "skill_version": f"{skill_name}@1.1.0",
            "commit_sha": self._get_commit_sha(),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "elapsed_seconds": round(elapsed, 2),
            "case_id": cid,
            "mode": "cli",
        }

        return output

    def _dry_run(self, case, cid, skill_name):
        """Generate output from golden set expected values (dry-run mode).

        WARNING: This produces output from golden set expected values.
        It is NOT real agent evaluation. It must NEVER be called as a
        silent fallback — only via explicit --adapter hermes-dry-run.

        The output is marked with generated_by="hermes-dry-run" so that
        any downstream consumer can detect it is not a real agent result.
        """
        expected = case.get("expected", {})
        cat = expected.get("category", "refund-return")
        pri = expected.get("priority", "P3")
        hcr = expected.get("human_review_required", False)

        # Route inference (matching evaluator logic)
        if pri == "P1":
            route = "medical-review" if cat == "medical-risk" else "escalation"
        elif pri == "P2":
            route = "escalation" if cat == "compliance" else "tier-2"
        else:
            route = "tier-1"

        # Risk flags based on priority
        if pri == "P1":
            risk_flags = [{"type": "medical", "severity": "critical",
                          "description": f"P1 escalation — dry-run for {cid}"}]
        elif pri == "P2":
            risk_flags = [{"type": cat.replace("-", " "),
                          "severity": "high",
                          "description": f"P2 priority case — dry-run for {cid}"}]
        else:
            risk_flags = []

        # Response: empty for ALL P1 (unified policy — conservative)
        response = "" if pri == "P1" else (
            "Thank you for contacting us. We have received your inquiry."
        )

        return {
            "category": cat,
            "priority": pri,
            "route_to": route,
            "risk_flags": risk_flags,
            "human_review_required": hcr,
            "suggested_initial_response": response,
            "internal_notes": f"DRY-RUN (hermes CLI not available): case {cid}",
        }

    def _build_prompt(self, case):
        """Build the evaluation prompt."""
        cid = case.get("id", "unknown")
        case_input = case.get("input", {})
        message = case_input.get("message", "")
        region = case_input.get("region", "US")

        return f"""Triage this customer support ticket.

Case: {cid}
Message: "{message}"
Region: {region}

You must output ONLY a JSON object (no other text) with these fields:
category, priority, route_to, risk_flags (array), human_review_required (bool),
suggested_initial_response (string, empty for P1 medical), internal_notes (string).

Rules:
- P1 (critical): medical risk → medical-review, response must be empty
- P2 (high): out-of-window returns, defects → tier-2 or escalation
- P3 (standard), P4 (low) → tier-1

Output:"""

    def _load_skill_context(self, skill_name):
        """Load SKILL.md content."""
        skill_path = self.skill_path
        if not skill_path:
            skill_path = Path(self.agent) / "skills" / skill_name / "SKILL.md"

        if Path(skill_path).exists():
            try:
                with open(skill_path, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception:
                pass

        return f"Skill: {skill_name} for {self.agent} agent."

    def _parse_output(self, text, cid):
        """Parse agent output to JSON."""
        import re

        # Try direct parse
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass

        # Try markdown code block
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # Try any JSON object
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                pass

        # Fallback
        return {
            "category": "compliance",
            "priority": "P1",
            "route_to": "escalation",
            "risk_flags": [{"type": "compliance", "severity": "critical",
                           "description": f"Hermes output parse failure for {cid}"}],
            "human_review_required": True,
            "suggested_initial_response": "",
            "internal_notes": f"PARSE FAILURE: {text[:200]}",
        }

    def _get_commit_sha(self):
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                capture_output=True, text=True, timeout=5
            )
            return result.stdout.strip() if result.returncode == 0 else "unknown"
        except Exception:
            return "unknown"

    def _error_result(self, cid, error_msg, elapsed):
        return {
            "category": "compliance",
            "priority": "P1",
            "route_to": "escalation",
            "risk_flags": [{"type": "compliance", "severity": "critical",
                           "description": f"Agent error: {error_msg[:100]}"}],
            "human_review_required": True,
            "suggested_initial_response": "",
            "internal_notes": f"AGENT ERROR: {error_msg}",
            "_meta": {
                "generated_by": "hermes",
                "model": self.model or "hermes-cli",
                "skill_version": "error",
                "commit_sha": self._get_commit_sha(),
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "elapsed_seconds": round(elapsed, 2),
                "case_id": cid,
                "error": error_msg,
            },
        }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Hermes agent adapter")
    parser.add_argument("--case", help="Path to case JSON, or '-' for stdin")
    parser.add_argument("--agent", default="customer-support")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--model", help="Model override")
    parser.add_argument("--api-url", help="Hermes API URL (e.g. http://localhost:8787/v1)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Use dry-run mode (NOT real agent evaluation — uses golden set expected)")
    args = parser.parse_args()

    if args.case == "-" or not args.case:
        case = json.load(sys.stdin)
    else:
        with open(args.case, "r", encoding="utf-8") as f:
            case = json.load(f)

    adapter = HermesAdapter(
        agent=args.agent, timeout=args.timeout,
        model=args.model, api_url=args.api_url,
    )
    if args.dry_run:
        adapter._dry_run_mode = True
    result = adapter.run_case(case)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
