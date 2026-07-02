#!/usr/bin/env python3
"""
kb_mcp_server.py — Knowledge Base MCP server (Notion + local docs).

Provides KB search and retrieval for customer-support agent.
Searches Notion KB, local policy docs, and FAQ content.

Configuration:
  NOTION_API_KEY — Notion API key

Usage:
  python kb_mcp_server.py
  # Runs as MCP stdio server

This is a STUB implementation. Replace with real KB integration when deploying.
"""

import json
import sys
from pathlib import Path


KB_ENTRIES = {
    "return policy": {
        "title": "Return & Refund Policy",
        "content": (
            "Returns accepted within 30 days of delivery. "
            "Device must be in original packaging. "
            "Used cartridges cannot be returned for hygiene reasons. "
            "EU customers: 14-day cooling-off period applies. "
            "Defective items: full refund or replacement within warranty period."
        ),
    },
    "shipping": {
        "title": "Shipping Policy",
        "content": (
            "Standard shipping: 5-7 business days (US), 7-14 days (international). "
            "Express shipping: 2-3 business days (US only). "
            "Free shipping on orders over $75. "
            "Tracking number provided within 24 hours of shipment."
        ),
    },
    "warranty": {
        "title": "Warranty Information",
        "content": (
            "1-year limited warranty covering manufacturing defects. "
            "Does NOT cover: misuse, unauthorized modifications, consumable parts. "
            "Cartridges are consumable items — not covered. "
            "To claim: contact support with order number and description of issue."
        ),
    },
    "usage": {
        "title": "Device Usage Guide",
        "content": (
            "Use 1-2 times per week. Do not use daily. "
            "Needle depth: 0.25mm for beginners, up to 2.0mm for experienced users. "
            "Replace cartridge after each use. "
            "Apply serum after treatment. "
            "Do not use on broken, irritated, or infected skin. "
            "Consult a dermatologist before use if you have skin conditions."
        ),
    },
    "medical safety": {
        "title": "Medical Safety Guidelines",
        "content": (
            "⚠️ Device is a cosmetic tool, NOT a medical device. "
            "Do not use on active acne, open wounds, or infections. "
            "Discontinue use if irritation, bleeding, or adverse reaction occurs. "
            "Not suitable for: pregnant women, hemophiliacs, people on blood thinners. "
            "If you experience persistent bleeding or severe pain, seek medical attention immediately. "
            "Agent MUST NOT give medical advice — escalate P1 medical cases."
        ),
    },
}


def search_kb(query):
    """Search knowledge base. MOCK implementation."""
    query_lower = query.lower()
    results = []
    for key, entry in KB_ENTRIES.items():
        if any(term in key or term in entry["title"].lower() or term in entry["content"].lower()
               for term in query_lower.split()):
            results.append({"key": key, **entry})
    return results[:5]


def get_page(page_key):
    """Get a specific KB page. MOCK implementation."""
    return KB_ENTRIES.get(page_key)


def handle_request(request):
    method = request.get("method", "")
    params = request.get("params", {})
    req_id = request.get("id")

    if method == "tools/list":
        return {
            "jsonrpc": "2.0", "id": req_id,
            "result": {
                "tools": [
                    {
                        "name": "search_kb",
                        "description": "Search the knowledge base for policies, FAQs, and guides",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string"},
                                "max_results": {"type": "integer", "default": 5},
                            },
                            "required": ["query"],
                        },
                    },
                    {
                        "name": "get_page",
                        "description": "Retrieve a specific KB page by key",
                        "inputSchema": {
                            "type": "object",
                            "properties": {"key": {"type": "string"}},
                            "required": ["key"],
                        },
                    },
                ],
            },
        }

    elif method == "tools/call":
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})

        try:
            if tool_name == "search_kb":
                result = search_kb(arguments.get("query", ""))
            elif tool_name == "get_page":
                result = get_page(arguments.get("key", ""))
                if result is None:
                    return {"jsonrpc": "2.0", "id": req_id,
                            "error": {"code": -32000, "message": "Page not found"}}
            else:
                return {"jsonrpc": "2.0", "id": req_id,
                        "error": {"code": -32601, "message": f"Unknown: {tool_name}"}}

            return {
                "jsonrpc": "2.0", "id": req_id,
                "result": {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]},
            }
        except Exception as e:
            return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32000, "message": str(e)}}

    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Unknown: {method}"}}


def main():
    print("KB MCP Server starting (MOCK mode)...", file=sys.stderr)
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            print(json.dumps(handle_request(json.loads(line))))
            sys.stdout.flush()
        except json.JSONDecodeError:
            print(json.dumps({"jsonrpc": "2.0", "id": None,
                             "error": {"code": -32700, "message": "Parse error"}}), file=sys.stderr)


if __name__ == "__main__":
    main()
