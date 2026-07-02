"""
Agent adapters for running evaluation cases against real AI agents.

Each adapter implements `run_case(case: dict) -> dict` returning
a triage_result JSON object conforming to triage_result.schema.json.
"""

from .mock_adapter import MockAdapter
from .codex_adapter import CodexAdapter
from .hermes_adapter import HermesAdapter

ADAPTERS = {
    "mock": MockAdapter,
    "codex": CodexAdapter,
    "hermes": HermesAdapter,
}

__all__ = ["MockAdapter", "CodexAdapter", "HermesAdapter", "ADAPTERS"]
