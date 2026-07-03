"""
Runtime MCP server implementations and permission gateway for ai-employees-plugins.

Each server provides mock implementations that can be replaced
with real API integrations in production. All servers implement
the MCP stdio protocol (JSON-RPC over stdin/stdout).

Servers:
  gmail_mcp_server     — Gmail API (read threads, create drafts)
  shopify_mcp_server   — Shopify Admin API (read orders, products, customers)
  kb_mcp_server        — Knowledge Base (search policies, FAQs)
  human_review_server  — Human review queue (submit, approve, reject)

Permission Gateway (P0-A):
  tool_registry         — Tool registry with permission matrix
  permission_gateway    — Core enforcement point for tool calls
  audit_logger          — Append-only JSONL audit trail
  redaction             — PII redaction for email, phone, orders, CC, IP
  human_review_gateway  — File-based human-review queue
"""

from .tool_registry import ToolRegistry, get_tool, get_all_tools
from .permission_gateway import PermissionGateway, PermissionResult, CaseContext
from .audit_logger import AuditLogger
from .redaction import Redactor
from .human_review_gateway import HumanReviewGateway

__all__ = [
    "ToolRegistry",
    "get_tool",
    "get_all_tools",
    "PermissionGateway",
    "PermissionResult",
    "CaseContext",
    "AuditLogger",
    "Redactor",
    "HumanReviewGateway",
]
