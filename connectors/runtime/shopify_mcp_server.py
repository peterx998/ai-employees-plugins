#!/usr/bin/env python3
"""
shopify_mcp_server.py — Runtime Shopify MCP server for customer-support agent.

Provides Shopify Admin API integration as an MCP server.
Read-only by default; mutation operations require human approval.

Configuration:
  SHOPIFY_ACCESS_TOKEN   — Admin API access token
  SHOPIFY_STORE_DOMAIN   — Store domain (e.g., 'your-store')

Usage:
  python shopify_mcp_server.py
  # Runs as MCP stdio server

This is a STUB implementation. Replace with real Shopify API calls when deploying.
"""

import json
import os
import sys
from datetime import datetime, timezone


MOCK_ORDERS = {
    "DRP-1001": {
        "order_id": "DRP-1001",
        "status": "delivered",
        "created_at": "2026-06-20T10:00:00Z",
        "total": "$129.99",
        "items": [{"sku": "DRP-A6S", "name": "Dr. Pen A6S Device"}],
        "customer_email": "customer@example.com",
        "shipping_region": "US",
        "fulfillment_status": "delivered",
    },
    "DRP-1002": {
        "order_id": "DRP-1002",
        "status": "delivered",
        "created_at": "2026-06-22T14:00:00Z",
        "total": "$89.99",
        "items": [{"sku": "DRP-CART-12", "name": "Needle Cartridges 12-pack"}],
        "customer_email": "customer2@example.com",
        "shipping_region": "EU",
        "fulfillment_status": "delivered",
    },
}


def get_order(order_id):
    """Fetch order by ID. MOCK implementation."""
    return MOCK_ORDERS.get(order_id.upper())


def get_product(product_id=None, sku=None):
    """Fetch product details. MOCK implementation."""
    return {
        "product_id": product_id or "DRP-A6S",
        "sku": sku or "DRP-A6S",
        "name": "Dr. Pen A6S Microneedling Device",
        "warranty": "1 year",
        "return_window_days": 30,
        "region_restrictions": ["US", "EU", "CA", "UK"],
    }


def get_customer(email):
    """Fetch customer by email. MOCK implementation."""
    if "example.com" in email:
        return {
            "email": email,
            "total_orders": 2,
            "first_order": "2026-01-15T00:00:00Z",
            "last_order": "2026-06-20T10:00:00Z",
            "region": "US",
        }
    return None


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
                        "name": "read_order",
                        "description": "Fetch a Shopify order by ID (e.g., DRP-1001)",
                        "inputSchema": {
                            "type": "object",
                            "properties": {"order_id": {"type": "string"}},
                            "required": ["order_id"],
                        },
                    },
                    {
                        "name": "get_product",
                        "description": "Fetch product details by ID or SKU",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "product_id": {"type": "string"},
                                "sku": {"type": "string"},
                            },
                        },
                    },
                    {
                        "name": "get_customer",
                        "description": "Fetch customer profile by email",
                        "inputSchema": {
                            "type": "object",
                            "properties": {"email": {"type": "string"}},
                            "required": ["email"],
                        },
                    },
                ],
            },
        }

    elif method == "tools/call":
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})

        try:
            if tool_name == "read_order":
                result = get_order(arguments.get("order_id", ""))
                if result is None:
                    return {"jsonrpc": "2.0", "id": req_id,
                            "error": {"code": -32000, "message": "Order not found"}}
            elif tool_name == "get_product":
                result = get_product(
                    product_id=arguments.get("product_id"),
                    sku=arguments.get("sku"),
                )
            elif tool_name == "get_customer":
                result = get_customer(arguments.get("email", ""))
                if result is None:
                    return {"jsonrpc": "2.0", "id": req_id,
                            "error": {"code": -32000, "message": "Customer not found"}}
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
    print("Shopify MCP Server starting (MOCK mode)...", file=sys.stderr)
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
            print(json.dumps(handle_request(request)))
            sys.stdout.flush()
        except json.JSONDecodeError:
            print(json.dumps({"jsonrpc": "2.0", "id": None,
                             "error": {"code": -32700, "message": "Parse error"}}), file=sys.stderr)


if __name__ == "__main__":
    main()
