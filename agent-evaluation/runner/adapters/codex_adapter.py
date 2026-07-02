#!/usr/bin/env python3
"""
codex_adapter.py — Run evaluation cases through Codex CLI (OpenAI Codex).

Requires Codex CLI to be installed and authenticated:
  npm install -g @openai/codex
  codex login

Usage:
  python codex_adapter.py --case case.json --skill ticket-triage
  python codex_adapter.py --batch cases.jsonl --output-dir actual_outputs/current/

The adapter:
  1. Constructs a prompt from the golden set case input
  2. Calls `codex exec` with the SKILL.md as system context
  3. Parses the JSON output
  4. Returns a triage_result dict
"""

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from datetime import datetime, timezone


class CodexAdapter:
    """Run cases through Codex CLI and return triage results."""

    def __init__(self, agent="customer-support", timeout=120, model=None, skill_path=None):
        self.agent = agent
        self.timeout = timeout
        self.model = model or os.environ.get("CODEX_MODEL", "gpt-4o")
        self.skill_path = skill_path

        # Verify codex is available
        self._check_codex_installed()

    def _check_codex_installed(self):
        """Verify codex CLI is available."""
        try:
            result = subprocess.run(
                ["codex", "--version"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode != 0:
                print(f"WARNING: codex --version returned {result.returncode}",
                      file=sys.stderr)
        except FileNotFoundError:
            print("WARNING: codex CLI not found. Install: npm install -g @openai/codex",
                  file=sys.stderr)
        except Exception as e:
            print(f"WARNING: Could not check codex: {e}", file=sys.stderr)

    def run_case(self, case):
        """Run a single case through Codex CLI.

        Args:
            case: dict from golden set with id, agent, skill, input, expected

        Returns:
            dict: triage_result with _meta
        """
        cid = case.get("id", "unknown")
        skill_name = case.get("skill", "ticket-triage")
        case_input = case.get("input", {})

        # Build the prompt
        prompt = self._build_prompt(case)

        # Build the system context from SKILL.md
        skill_context = self._load_skill_context(skill_name)

        start_time = time.time()

        try:
            # Write prompt to temp file for codex to read
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", delete=False, encoding="utf-8"
            ) as f:
                f.write(skill_context + "\n\n---\n\n" + prompt)
                prompt_file = f.name

            # Run codex
            cmd = [
                "codex", "exec",
                "--model", self.model,
                "--prompt-file", prompt_file,
                "--output-format", "json",
                "--max-turns", "1",
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=os.getcwd(),
            )

            elapsed = time.time() - start_time

            # Clean up temp file
            try:
                os.unlink(prompt_file)
            except OSError:
                pass

            if result.returncode != 0:
                return self._error_result(cid, f"Codex exit {result.returncode}: {result.stderr[:200]}",
                                         elapsed)

            # Parse output
            output = self._parse_codex_output(result.stdout, cid)
            output["_meta"] = {
                "generated_by": "codex",
                "model": self.model,
                "skill_version": f"{skill_name}@1.1.0",
                "commit_sha": self._get_commit_sha(),
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "elapsed_seconds": round(elapsed, 2),
                "case_id": cid,
            }

            return output

        except subprocess.TimeoutExpired:
            return self._error_result(cid, f"Timeout after {self.timeout}s", self.timeout)
        except Exception as e:
            return self._error_result(cid, f"Exception: {str(e)[:200]}",
                                     time.time() - start_time)

    def _build_prompt(self, case):
        """Build the evaluation prompt from a golden set case."""
        cid = case.get("id", "unknown")
        case_input = case.get("input", {})
        message = case_input.get("message", "")
        region = case_input.get("region", "US")

        return f"""You are a customer support triage agent. Triage the following ticket.

Case ID: {cid}
Customer message: "{message}"
Region: {region}

Output a JSON object with these fields:
- category: one of [medical-risk, order-status, refund-return, product-usage, warranty, billing, compliance]
- priority: one of [P1, P2, P3, P4]
- route_to: one of [medical-review, tier-1, tier-2, escalation]
- risk_flags: array of {{"type": "...", "severity": "...", "description": "..."}}
- human_review_required: boolean
- suggested_initial_response: string (empty for P1 medical)
- internal_notes: string

Rules:
- P1 (critical): medical risk, safety threat, legal threat → medical-review, response empty
- P2 (high): out-of-window returns, defects, regulatory concerns → tier-2 or escalation
- P3 (standard): normal returns within window, product questions → tier-1
- P4 (low): general inquiries → tier-1

Output ONLY the JSON object, no other text."""

    def _load_skill_context(self, skill_name):
        """Load SKILL.md content for Codex system context."""
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

    def _parse_codex_output(self, stdout, cid):
        """Parse Codex JSON output, with robust error handling."""
        # Try parsing directly
        try:
            return json.loads(stdout.strip())
        except json.JSONDecodeError:
            pass

        # Try extracting JSON from markdown code blocks
        import re
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', stdout, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try finding any JSON object in output
        brace_start = stdout.find("{")
        if brace_start >= 0:
            brace_end = stdout.rfind("}")
            if brace_end > brace_start:
                try:
                    return json.loads(stdout[brace_start:brace_end + 1])
                except json.JSONDecodeError:
                    pass

        # Fallback: return error structure
        return {
            "category": "compliance",
            "priority": "P1",
            "route_to": "escalation",
            "risk_flags": [{"type": "compliance", "severity": "critical",
                           "description": f"Codex output parse failure for {cid}"}],
            "human_review_required": True,
            "suggested_initial_response": "",
            "internal_notes": f"COULD NOT PARSE CODEX OUTPUT: {stdout[:200]}",
        }

    def _get_commit_sha(self):
        """Get current git commit SHA."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                capture_output=True, text=True, timeout=5
            )
            return result.stdout.strip() if result.returncode == 0 else "unknown"
        except Exception:
            return "unknown"

    def _error_result(self, cid, error_msg, elapsed):
        """Return a safe error triage result."""
        return {
            "category": "compliance",
            "priority": "P1",
            "route_to": "escalation",
            "risk_flags": [{"type": "compliance", "severity": "critical",
                           "description": f"Agent error for {cid}: {error_msg[:100]}"}],
            "human_review_required": True,
            "suggested_initial_response": "",
            "internal_notes": f"AGENT ERROR: {error_msg}",
            "_meta": {
                "generated_by": "codex",
                "model": self.model,
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
    parser = argparse.ArgumentParser(description="Codex agent adapter")
    parser.add_argument("--case", help="Path to case JSON, or '-' for stdin")
    parser.add_argument("--agent", default="customer-support")
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--model", help="Codex model (default: $CODEX_MODEL or gpt-4o)")
    args = parser.parse_args()

    if args.case == "-" or not args.case:
        case = json.load(sys.stdin)
    else:
        with open(args.case, "r", encoding="utf-8") as f:
            case = json.load(f)

    adapter = CodexAdapter(agent=args.agent, timeout=args.timeout, model=args.model)
    result = adapter.run_case(case)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
