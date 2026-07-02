#!/usr/bin/env python3
"""
gmail_mcp_server.py — Runtime Gmail MCP server for customer-support agent.

Provides Gmail API integration as an MCP server. Connects to Gmail API
using OAuth2 credentials from environment variables.

Configuration:
  GMAIL_CLIENT_ID      — OAuth2 client ID
  GMAIL_CLIENT_SECRET  — OAuth2 client secret
  GMAIL_REFRESH_TOKEN  — OAuth2 refresh token

Usage:
  python gmail_mcp_server.py
  # Runs as MCP stdio server

This is a STUB implementation for the production boundary.
Replace with real Gmail API integration when deploying.
"""

import json
import os
import sys
from datetime import datetime, timezone


# ─── Mock Data (replace with real Gmail API calls) ───

MOCK_THREADS = {
    "thread_001": {
        "id": "thread_001",
        "subject": "Order #DRP-1001 — Device not working",
        "from": "customer@example.com",
        "snippet": "I opened the device but it won't turn on...",
        "date": "2026-07-01T10:00:00Z",
        "labels": ["INBOX", "UNREAD"],
    },
}


def search_messages(query, max_results=10):
    """Search Gmail messages matching query. MOCK implementation."""
    results = []
    query_lower = query.lower()
    for tid, thread in MOCK_THREADS.items():
        if any(term in thread.get("subject", "").lower() or
               term in thread.get("snippet", "").lower()
               for term in query_lower.split()):
            results.append(thread)
    return results[:max_results]


def get_thread(thread_id):
    """Get a Gmail thread by ID. MOCK implementation."""
    return MOCK_THREADS.get(thread_id)


def create_draft(to, subject, body):
    """Create a Gmail draft. MOCK implementation."""
    draft_id = f"draft_{datetime.now(timezone.utc).timestamp()}"
    return {
        "id": draft_id,
        "to": to,
        "subject": subject,
        "body": body,
        "status": "draft_created",
        "note": "Draft created — NOT sent. Requires human approval to send.",
    }


# ─── MCP Server ───

def handle_request(request):
    """Handle a single MCP JSON-RPC request."""
    method = request.get("method", "")
    params = request.get("params", {})
    req_id = request.get("id")

    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": [
                    {
                        "name": "search_threads",
                        "description": "Search Gmail threads by query",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string"},
                                "max_results": {"type": "integer", "default": 10},
                            },
                            "required": ["query"],
                        },
                    },
                    {
                        "name": "read_thread",
                        "description": "Read a Gmail thread by ID",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "thread_id": {"type": "string"},
                            },
                            "required": ["thread_id"],
                        },
                    },
                    {
                        "name": "create_draft",
                        "description": "Create a draft reply (NOT send — requires human approval)",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "to": {"type": "string"},
                                "subject": {"type": "string"},
                                "body": {"type": "string"},
                            },
                            "required": ["to", "subject", "body"],
                        },
                    },
                ]
            },
        }

    elif method == "tools/call":
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})

        try:
            if tool_name == "search_threads":
                result = search_messages(
                    query=arguments.get("query", ""),
                    max_results=arguments.get("max_results", 10),
                )
            elif tool_name == "read_thread":
                result = get_thread(arguments.get("thread_id", ""))
                if result is None:
                    return {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "error": {"code": -32000, "message": "Thread not found"},
                    }
            elif tool_name == "create_draft":
                result = create_draft(
                    to=arguments.get("to", ""),
                    subject=arguments.get("subject", ""),
                    body=arguments.get("body", ""),
                )
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"},
                }

            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(result, indent=2)}],
                },
            }

        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32000, "message": str(e)},
            }

    else:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Unknown method: {method}"},
        }


def main():
    """Run as MCP stdio server."""
    print("Gmail MCP Server starting (MOCK mode)...", file=sys.stderr)

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            request = json.loads(line)
            response = handle_request(request)
            print(json.dumps(response))
            sys.stdout.flush()
        except json.JSONDecodeError:
            print(json.dumps({
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": "Parse error"},
            }), file=sys.stderr)


if __name__ == "__main__":
    main()
