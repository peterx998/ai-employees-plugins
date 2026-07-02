#!/usr/bin/env python3
"""
human_review_server.py — Human review queue MCP server.

Manages the human review pipeline for P1/P2 cases that require
human intervention before auto-reply or action.

Features:
- Queue P1/P2 cases for human review
- Track review status (pending/in_review/resolved)
- Prevent auto-reply until human approves
- Track SLAs for time-sensitive cases

Configuration: None (mock server; replace with real queue in production)

Usage:
  python human_review_server.py
  # Runs as MCP stdio server
"""

import json
import sys
from datetime import datetime, timezone


REVIEW_QUEUE = {}


def submit_for_review(case_id, category, priority, risk_flags, internal_notes):
    """Submit a case to the human review queue."""
    review_id = f"HR-{case_id}"
    REVIEW_QUEUE[review_id] = {
        "review_id": review_id,
        "case_id": case_id,
        "category": category,
        "priority": priority,
        "risk_flags": risk_flags,
        "internal_notes": internal_notes,
        "status": "pending",
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "sla_minutes": 15 if priority == "P1" else 60,
    }
    return REVIEW_QUEUE[review_id]


def get_review_status(review_id):
    """Get the status of a review request."""
    return REVIEW_QUEUE.get(review_id)


def approve_review(review_id, reviewer, notes=""):
    """Approve a review (simulate human action)."""
    entry = REVIEW_QUEUE.get(review_id)
    if not entry:
        return None
    entry["status"] = "resolved"
    entry["resolution"] = "approved"
    entry["reviewer"] = reviewer
    entry["reviewer_notes"] = notes
    entry["resolved_at"] = datetime.now(timezone.utc).isoformat()
    return entry


def reject_review(review_id, reviewer, reason):
    """Reject a review with reason."""
    entry = REVIEW_QUEUE.get(review_id)
    if not entry:
        return None
    entry["status"] = "resolved"
    entry["resolution"] = "rejected"
    entry["reviewer"] = reviewer
    entry["rejection_reason"] = reason
    entry["resolved_at"] = datetime.now(timezone.utc).isoformat()
    return entry


def list_pending_reviews():
    """List all pending reviews sorted by priority."""
    pending = [
        r for r in REVIEW_QUEUE.values()
        if r["status"] == "pending"
    ]
    # P1 first, then by submit time
    pending.sort(key=lambda r: (0 if r["priority"] == "P1" else 1, r["submitted_at"]))
    return pending


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
                        "name": "submit_for_review",
                        "description": "Submit a P1/P2 case for human review (blocks auto-reply)",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "case_id": {"type": "string"},
                                "category": {"type": "string"},
                                "priority": {"type": "string"},
                                "risk_flags": {"type": "array"},
                                "internal_notes": {"type": "string"},
                            },
                            "required": ["case_id", "category", "priority"],
                        },
                    },
                    {
                        "name": "get_review_status",
                        "description": "Get the status of a submitted review",
                        "inputSchema": {
                            "type": "object",
                            "properties": {"review_id": {"type": "string"}},
                            "required": ["review_id"],
                        },
                    },
                    {
                        "name": "list_pending_reviews",
                        "description": "List all pending reviews (P1 first)",
                        "inputSchema": {"type": "object", "properties": {}},
                    },
                    {
                        "name": "approve_review",
                        "description": "Approve a review (human action — simulated in mock)",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "review_id": {"type": "string"},
                                "reviewer": {"type": "string"},
                                "notes": {"type": "string"},
                            },
                            "required": ["review_id", "reviewer"],
                        },
                    },
                    {
                        "name": "reject_review",
                        "description": "Reject a review with reason (human action — simulated in mock)",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "review_id": {"type": "string"},
                                "reviewer": {"type": "string"},
                                "reason": {"type": "string"},
                            },
                            "required": ["review_id", "reviewer", "reason"],
                        },
                    },
                ],
            },
        }

    elif method == "tools/call":
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})

        try:
            if tool_name == "submit_for_review":
                result = submit_for_review(
                    case_id=arguments.get("case_id", ""),
                    category=arguments.get("category", ""),
                    priority=arguments.get("priority", ""),
                    risk_flags=arguments.get("risk_flags", []),
                    internal_notes=arguments.get("internal_notes", ""),
                )
            elif tool_name == "get_review_status":
                result = get_review_status(arguments.get("review_id", ""))
                if result is None:
                    return {"jsonrpc": "2.0", "id": req_id,
                            "error": {"code": -32000, "message": "Review not found"}}
            elif tool_name == "list_pending_reviews":
                result = list_pending_reviews()
            elif tool_name == "approve_review":
                result = approve_review(
                    review_id=arguments.get("review_id", ""),
                    reviewer=arguments.get("reviewer", ""),
                    notes=arguments.get("notes", ""),
                )
                if result is None:
                    return {"jsonrpc": "2.0", "id": req_id,
                            "error": {"code": -32000, "message": "Review not found"}}
            elif tool_name == "reject_review":
                result = reject_review(
                    review_id=arguments.get("review_id", ""),
                    reviewer=arguments.get("reviewer", ""),
                    reason=arguments.get("reason", ""),
                )
                if result is None:
                    return {"jsonrpc": "2.0", "id": req_id,
                            "error": {"code": -32000, "message": "Review not found"}}
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
    print("Human Review MCP Server starting (MOCK mode)...", file=sys.stderr)
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
