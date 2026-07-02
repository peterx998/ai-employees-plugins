"""
Runtime MCP server implementations for ai-employees-plugins.

Each server provides mock implementations that can be replaced
with real API integrations in production. All servers implement
the MCP stdio protocol (JSON-RPC over stdin/stdout).

Servers:
  gmail_mcp_server     — Gmail API (read threads, create drafts)
  shopify_mcp_server   — Shopify Admin API (read orders, products, customers)
  kb_mcp_server        — Knowledge Base (search policies, FAQs)
  human_review_server  — Human review queue (submit, approve, reject)
"""
