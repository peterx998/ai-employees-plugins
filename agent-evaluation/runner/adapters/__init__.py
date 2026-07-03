"""
Agent adapters for running evaluation cases against real AI agents.

Each adapter implements `run_case(case: dict) -> dict` returning
a triage_result JSON object conforming to triage_result.schema.json.

Adapter types:
  mock            — Pipeline integrity testing (uses golden set expected)
  codex           — Real agent via Codex CLI
  hermes          — Real agent via Hermes CLI/API (fail-closed, no fallback)
  hermes-dry-run  — Explicit dry-run using golden set expected (NOT real eval)
"""

from .mock_adapter import MockAdapter
from .codex_adapter import CodexAdapter
from .hermes_adapter import HermesAdapter

ADAPTERS = {
    "mock": MockAdapter,
    "codex": CodexAdapter,
    "hermes": HermesAdapter,
    "hermes-dry-run": HermesAdapter,  # Same class, but factory sets dry_run=True
}

__all__ = ["MockAdapter", "CodexAdapter", "HermesAdapter", "ADAPTERS"]
