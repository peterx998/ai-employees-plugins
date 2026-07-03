"""Core permission gateway for the Runtime Permission Gateway system.

The :class:`PermissionGateway` is the single enforcement point for every
tool call made by a customer-support AI agent.  It consults the
:mod:`tool_registry` permission matrix, applies PII redaction via
:mod:`redaction`, logs every check via :mod:`audit_logger`, and submits
human-review-required calls to :mod:`human_review_gateway`.

Enforcement rules
-----------------
1. **send_email** — ALWAYS denied, no override, no priority exception.
2. **shopify.update_page** — ALWAYS denied for agents (human-only).
3. **human_review.approve** — ALWAYS denied for agents (human-only).
4. **P1 cases** — ALL write tools denied (includes create_draft).
5. **create_draft** on P2+ — requires human review.
6. **shopify.read_customer** — PII fields redacted before logging.
7. All other read tools — auto-allowed.
8. Unknown tools — denied (fail-closed).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .audit_logger import AuditLogger
from .human_review_gateway import HumanReviewGateway
from .redaction import Redactor
from .tool_registry import ToolEntry, ToolRegistry


# ---------------------------------------------------------------------- #
# Result dataclass
# ---------------------------------------------------------------------- #

@dataclass
class PermissionResult:
    """Outcome of a single permission check.

    Attributes
    ----------
    allowed : bool
        ``True`` if the tool call may proceed immediately.
    reason : str
        Human-readable explanation of the decision.
    redacted_arguments : dict[str, Any]
        Copy of *arguments* with PII fields redacted.  Always populated,
        even for denied calls (for safe logging).
    requires_human_review : bool
        ``True`` if the call was neither fully allowed nor fully denied,
        but instead deferred to the human-review queue.  When ``True``,
        ``allowed`` is ``False`` and a review request has been submitted.
    tool_name : str
        The tool that was checked.
    case_id : str | None
        The case ID from the context, if available.
    review_id : str | None
        If human review was submitted, the ID of the review request.
    """

    allowed: bool
    reason: str
    redacted_arguments: dict[str, Any] = field(default_factory=dict)
    requires_human_review: bool = False
    tool_name: str = ""
    case_id: str | None = None
    review_id: str | None = None

    @property
    def status(self) -> str:
        """Return the status string used in audit logs.

        - ``"allowed"`` — call may proceed.
        - ``"denied"`` — call blocked.
        - ``"human_required"`` — call deferred to human review.
        """
        if self.allowed:
            return "allowed"
        if self.requires_human_review:
            return "human_required"
        return "denied"

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a plain dict (for JSON logging)."""
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "redacted_arguments": self.redacted_arguments,
            "requires_human_review": self.requires_human_review,
            "tool_name": self.tool_name,
            "case_id": self.case_id,
            "review_id": self.review_id,
            "status": self.status,
        }


# ---------------------------------------------------------------------- #
# Case context
# ---------------------------------------------------------------------- #

@dataclass
class CaseContext:
    """Context about the current support case.

    Attributes
    ----------
    priority : str
        Case priority — ``P1``, ``P2``, ``P3``, or ``P4``.
    category : str
        Case category (e.g. ``medical``, ``retail``, ``billing``).
    case_id : str
        Unique case identifier.
    """

    priority: str = "P4"
    category: str = "general"
    case_id: str = "unknown"


# ---------------------------------------------------------------------- #
# Permission gateway
# ---------------------------------------------------------------------- #

class PermissionGateway:
    """Central permission enforcement point for tool calls.

    Parameters
    ----------
    case_context : CaseContext | dict | None
        Context about the current support case.  If a dict, it should
        contain ``priority``, ``category``, and ``case_id`` keys.
        If ``None``, a default context with priority ``P4`` is used.
    registry : ToolRegistry | None
        Custom tool registry.  If ``None``, a default registry is
        created.
    audit_logger : AuditLogger | None
        Custom audit logger.  If ``None``, a default logger writing to
        ``customer-support/evals/tool_calls`` is created.
    review_gateway : HumanReviewGateway | None
        Custom human-review gateway.  If ``None``, a default gateway
        writing to ``customer-support/evals/human_review_queue`` is
        created.
    """

    # Tools that are always denied for agents — no override possible.
    _ALWAYS_DENIED = frozenset({
        "gmail.send_email",
        "shopify.update_page",
        "human_review.approve",
    })

    def __init__(
        self,
        case_context: CaseContext | dict[str, Any] | None = None,
        registry: ToolRegistry | None = None,
        audit_logger: AuditLogger | None = None,
        review_gateway: HumanReviewGateway | None = None,
    ) -> None:
        # --- resolve case context --------------------------------------
        if case_context is None:
            self.case_context = CaseContext()
        elif isinstance(case_context, CaseContext):
            self.case_context = case_context
        elif isinstance(case_context, dict):
            self.case_context = CaseContext(
                priority=case_context.get("priority", "P4"),
                category=case_context.get("category", "general"),
                case_id=case_context.get("case_id", "unknown"),
            )
        else:
            raise TypeError(
                f"case_context must be CaseContext, dict, or None; "
                f"got {type(case_context).__name__}"
            )

        # --- resolve dependencies --------------------------------------
        self.registry = registry or ToolRegistry()
        self.redactor = Redactor()
        self.audit_logger = audit_logger or AuditLogger()
        self.review_gateway = review_gateway or HumanReviewGateway()

    # ------------------------------------------------------------------ #
    # Core check
    # ------------------------------------------------------------------ #

    def check(
        self,
        tool_name: str,
        arguments: dict[str, Any] | None,
        caller_agent: str,
        caller_skill: str,
    ) -> PermissionResult:
        """Check whether a tool call is permitted.

        This is the main entry point.  Every call is:

        1. Looked up in the registry.
        2. PII fields redacted.
        3. Evaluated against the permission matrix and case priority.
        4. Logged to the audit trail.
        5. If human-required, submitted to the review queue.

        Parameters
        ----------
        tool_name
            Fully-qualified tool name.
        arguments
            Tool-call arguments (may be ``None`` for no-arg tools).
        caller_agent
            Identifier of the calling agent.
        caller_skill
            Identifier of the calling skill.

        Returns
        -------
        PermissionResult
            The decision and (if applicable) the review ID.
        """
        start = datetime.now(timezone.utc)
        arguments = arguments or {}
        case_id = self.case_context.case_id
        priority = self.case_context.priority

        # --- 1. Look up tool in registry -------------------------------
        tool = self.registry.get(tool_name)
        if tool is None:
            redacted = self.redactor.redact_dict(arguments)
            reason = f"Unknown tool: {tool_name} — denied (fail-closed)"
            self._log_and_violate(
                tool_name, redacted, caller_agent, caller_skill,
                case_id, reason, start,
            )
            return PermissionResult(
                allowed=False,
                reason=reason,
                redacted_arguments=redacted,
                tool_name=tool_name,
                case_id=case_id,
            )

        # --- 2. Redact PII fields --------------------------------------
        redacted_args = self._redact_arguments(tool, arguments)

        # --- 3. Evaluate permission matrix -----------------------------
        # 3a. Always-denied tools
        if tool_name in self._ALWAYS_DENIED:
            reason = self._always_denied_reason(tool_name)
            self._log(
                tool_name, redacted_args, caller_agent, caller_skill,
                case_id, "denied", reason, start,
            )
            self._log_violation(tool_name, redacted_args, case_id, reason)
            return PermissionResult(
                allowed=False,
                reason=reason,
                redacted_arguments=redacted_args,
                tool_name=tool_name,
                case_id=case_id,
            )

        # 3b. Resolve priority-specific outcome
        try:
            outcome = ToolRegistry.parse_priority_restriction(
                tool.priority_restriction, priority,
            )
        except ValueError as exc:
            # Malformed restriction — fail-closed
            reason = f"Permission config error for {tool_name}: {exc}"
            self._log(
                tool_name, redacted_args, caller_agent, caller_skill,
                case_id, "error", reason, start,
            )
            return PermissionResult(
                allowed=False,
                reason=reason,
                redacted_arguments=redacted_args,
                tool_name=tool_name,
                case_id=case_id,
            )

        # 3c. Act on the outcome
        if outcome == "denied":
            reason = self._denied_reason(tool_name, priority)
            self._log(
                tool_name, redacted_args, caller_agent, caller_skill,
                case_id, "denied", reason, start,
            )
            self._log_violation(tool_name, redacted_args, case_id, reason)
            return PermissionResult(
                allowed=False,
                reason=reason,
                redacted_arguments=redacted_args,
                tool_name=tool_name,
                case_id=case_id,
            )

        if outcome == "human_required":
            # Submit to human review queue
            review_id = self.review_gateway.submit_for_review(
                tool_name=tool_name,
                arguments=arguments,  # gateway will redact internally
                case_id=case_id,
                reason=f"{tool_name} requires human review (priority {priority})",
            )
            reason = (
                f"{tool_name} requires human review for {priority} cases. "
                f"Review ID: {review_id}"
            )
            self._log(
                tool_name, redacted_args, caller_agent, caller_skill,
                case_id, "denied", reason, start,  # logged as denied since not auto-allowed
            )
            return PermissionResult(
                allowed=False,
                reason=reason,
                redacted_arguments=redacted_args,
                requires_human_review=True,
                tool_name=tool_name,
                case_id=case_id,
                review_id=review_id,
            )

        # outcome == "allowed"
        reason = f"{tool_name} allowed (auto_allow, priority {priority})"
        self._log(
            tool_name, redacted_args, caller_agent, caller_skill,
            case_id, "allowed", reason, start,
        )
        return PermissionResult(
            allowed=True,
            reason=reason,
            redacted_arguments=redacted_args,
            tool_name=tool_name,
            case_id=case_id,
        )

    # ------------------------------------------------------------------ #
    # Batch check
    # ------------------------------------------------------------------ #

    def check_batch(
        self,
        tool_calls: list[dict[str, Any]],
    ) -> list[PermissionResult]:
        """Check a list of tool calls.

        Each element of *tool_calls* should be a dict with keys:
        ``tool_name``, ``arguments``, ``caller_agent``, ``caller_skill``.

        Parameters
        ----------
        tool_calls
            List of tool-call specification dicts.

        Returns
        -------
        list[PermissionResult]
            One result per input call, in order.
        """
        results: list[PermissionResult] = []
        for call in tool_calls:
            try:
                result = self.check(
                    tool_name=call.get("tool_name", ""),
                    arguments=call.get("arguments", {}),
                    caller_agent=call.get("caller_agent", "unknown"),
                    caller_skill=call.get("caller_skill", "unknown"),
                )
            except Exception as exc:
                # Catch unexpected errors — fail-closed per call
                result = PermissionResult(
                    allowed=False,
                    reason=f"Error during check: {exc}",
                    redacted_arguments={},
                    tool_name=call.get("tool_name", ""),
                    case_id=self.case_context.case_id,
                )
            results.append(result)
        return results

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _redact_arguments(
        self,
        tool: ToolEntry,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        """Redact PII fields in *arguments* based on the tool's annotation."""
        if not tool.pii_fields:
            # Still do a general redact pass on all string values,
            # in case PII appears in unannotated fields.
            return self.redactor.redact_dict(arguments)

        # Redact specifically annotated fields, then do a general pass
        # on the rest for defence-in-depth.
        partially_redacted = self.redactor.redact_fields(arguments, tool.pii_fields)
        return self.redactor.redact_dict(partially_redacted)

    def _always_denied_reason(self, tool_name: str) -> str:
        """Return the human-readable reason for an always-denied tool."""
        reasons = {
            "gmail.send_email": (
                "gmail.send_email is ALWAYS denied — agents must use "
                "create_draft + human review. No override possible."
            ),
            "shopify.update_page": (
                "shopify.update_page is denied for agents — "
                "this is a human-only action."
            ),
            "human_review.approve": (
                "human_review.approve is denied for agents — "
                "this is a human-only action."
            ),
        }
        return reasons.get(
            tool_name,
            f"{tool_name} is always denied for agents.",
        )

    def _denied_reason(self, tool_name: str, priority: str) -> str:
        """Return the reason for a priority-based denial."""
        return (
            f"{tool_name} is denied for {priority} cases — "
            f"write tools are not permitted at this priority level."
        )

    # ------------------------------------------------------------------ #
    # Logging helpers
    # ------------------------------------------------------------------ #

    def _log(
        self,
        tool_name: str,
        redacted_args: dict[str, Any],
        caller_agent: str,
        caller_skill: str,
        case_id: str,
        result: str,
        reason: str | None,
        start: datetime,
    ) -> None:
        """Log a tool-call check to the audit trail."""
        end = datetime.now(timezone.utc)
        latency_ms = (end - start).total_seconds() * 1000.0
        self.audit_logger.log_tool_call(
            tool_name=tool_name,
            arguments=redacted_args,
            caller_agent=caller_agent,
            caller_skill=caller_skill,
            case_id=case_id,
            result=result,
            denial_reason=reason,
            latency_ms=round(latency_ms, 3),
        )

    def _log_violation(
        self,
        tool_name: str,
        redacted_args: dict[str, Any],
        case_id: str,
        reason: str,
    ) -> None:
        """Log a permission violation (denied call = policy breach attempt)."""
        self.audit_logger.log_permission_violation(
            tool_name=tool_name,
            arguments=redacted_args,
            case_id=case_id,
            reason=reason,
        )

    def _log_and_violate(
        self,
        tool_name: str,
        redacted_args: dict[str, Any],
        caller_agent: str,
        caller_skill: str,
        case_id: str,
        reason: str,
        start: datetime,
    ) -> None:
        """Convenience: log both a tool-call record and a violation."""
        self._log(
            tool_name, redacted_args, caller_agent, caller_skill,
            case_id, "denied", reason, start,
        )
        self._log_violation(tool_name, redacted_args, case_id, reason)


# ---------------------------------------------------------------------- #
# Self-test
# ---------------------------------------------------------------------- #
if __name__ == "__main__":
    import json
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmpdir:
        log_dir = str(Path(tmpdir) / "logs")
        queue_dir = str(Path(tmpdir) / "queue")

        audit = AuditLogger(log_dir=log_dir)
        review_gw = HumanReviewGateway(queue_dir=queue_dir)

        # --- P2 context (create_draft should require human review) ----
        gw_p2 = PermissionGateway(
            case_context={"priority": "P2", "category": "retail", "case_id": "CS-002"},
            audit_logger=audit,
            review_gateway=review_gw,
        )

        # Test 1: read tool — allowed
        r = gw_p2.check("gmail.search_threads", {"query": "DRP-1234"}, "agent", "kb-search")
        assert r.allowed, f"search_threads should be allowed, got: {r.reason}"
        assert not r.requires_human_review
        print(f"✓ P2 gmail.search_threads → allowed")

        # Test 2: send_email — always denied
        r = gw_p2.check(
            "gmail.send_email",
            {"to": "customer@example.com", "body": "Refund processed"},
            "agent", "draft-response",
        )
        assert not r.allowed
        assert not r.requires_human_review
        assert "always denied" in r.reason.lower()
        assert r.redacted_arguments["to"] == "[REDACTED_EMAIL]"
        print(f"✓ P2 gmail.send_email → denied (always)")

        # Test 3: create_draft on P2 — human_required
        r = gw_p2.check(
            "gmail.create_draft",
            {"to": "customer@example.com", "subject": "Re: Order", "body": "Draft"},
            "agent", "draft-response",
        )
        assert not r.allowed
        assert r.requires_human_review
        assert r.review_id is not None
        assert r.redacted_arguments["to"] == "[REDACTED_EMAIL]"
        print(f"✓ P2 gmail.create_draft → human_required (review_id={r.review_id})")

        # Test 4: shopify.read_customer — allowed with PII redaction
        r = gw_p2.check(
            "shopify.read_customer",
            {"email": "customer@example.com", "phone": "555-123-4567", "order_id": "DRP-1234"},
            "agent", "order-lookup",
        )
        assert r.allowed
        assert r.redacted_arguments["email"] == "[REDACTED_EMAIL]"
        assert r.redacted_arguments["phone"] == "[REDACTED_PHONE]"
        print(f"✓ P2 shopify.read_customer → allowed (PII redacted)")

        # Test 5: shopify.update_page — denied
        r = gw_p2.check("shopify.update_page", {"page_id": "123"}, "agent", "content-update")
        assert not r.allowed
        assert "human-only" in r.reason.lower()
        print(f"✓ P2 shopify.update_page → denied (human-only)")

        # Test 6: human_review.approve — denied
        r = gw_p2.check("human_review.approve", {"review_id": "HR-123"}, "agent", "review")
        assert not r.allowed
        assert "human-only" in r.reason.lower()
        print(f"✓ P2 human_review.approve → denied (human-only)")

        # Test 7: unknown tool — denied (fail-closed)
        r = gw_p2.check("unknown.tool", {}, "agent", "test")
        assert not r.allowed
        assert "unknown" in r.reason.lower()
        print(f"✓ P2 unknown.tool → denied (fail-closed)")

        # --- P1 context (all write tools denied) ---------------------
        gw_p1 = PermissionGateway(
            case_context={"priority": "P1", "category": "medical", "case_id": "CS-001"},
            audit_logger=audit,
            review_gateway=review_gw,
        )

        # Test 8: create_draft on P1 — denied
        r = gw_p1.check(
            "gmail.create_draft",
            {"to": "patient@example.com", "subject": "Re: Medical query"},
            "agent", "draft-response",
        )
        assert not r.allowed
        assert not r.requires_human_review  # P1 → straight denial, not review
        assert "p1" in r.reason.lower()
        print(f"✓ P1 gmail.create_draft → denied (P1 blocks all writes)")

        # Test 9: read tool on P1 — still allowed
        r = gw_p1.check("gmail.search_threads", {"query": "urgent"}, "agent", "kb-search")
        assert r.allowed
        print(f"✓ P1 gmail.search_threads → allowed (reads still OK on P1)")

        # --- Batch check ----------------------------------------------
        batch = [
            {"tool_name": "gmail.search_threads", "arguments": {"q": "test"}, "caller_agent": "a", "caller_skill": "s"},
            {"tool_name": "gmail.send_email", "arguments": {"to": "x@y.com"}, "caller_agent": "a", "caller_skill": "s"},
            {"tool_name": "gmail.create_draft", "arguments": {"to": "x@y.com"}, "caller_agent": "a", "caller_skill": "s"},
            {"tool_name": "kb.search_policies", "arguments": {"q": "refund"}, "caller_agent": "a", "caller_skill": "s"},
        ]
        results = gw_p2.check_batch(batch)
        assert len(results) == 4
        assert results[0].allowed         # search_threads
        assert not results[1].allowed     # send_email
        assert results[2].requires_human_review  # create_draft P2
        assert results[3].allowed         # search_policies
        print(f"✓ Batch check: 4 calls → {[r.status for r in results]}")

        # --- Verify audit log -----------------------------------------
        all_calls = audit.get_tool_calls()
        assert len(all_calls) >= 10  # at least 10 checks above
        violations = audit.get_violations()
        assert len(violations) >= 3  # send_email, update_page, approve, unknown, P1 create_draft
        print(f"✓ Audit log: {len(all_calls)} tool calls, {len(violations)} violations")

        # --- Verify review queue --------------------------------------
        pending = review_gw.get_pending_reviews()
        assert len(pending) >= 2  # at least 2 create_draft P2 submissions
        print(f"✓ Review queue: {len(pending)} pending reviews")

        # --- Approve a review and re-check is_approved ----------------
        if pending:
            rid = pending[0]["review_id"]
            review_gw.approve(rid)
            assert review_gw.is_approved(rid)
            print(f"✓ Approved review {rid}")

        # --- CaseContext dataclass ------------------------------------
        cc = CaseContext(priority="P3", category="billing", case_id="CS-003")
        gw_cc = PermissionGateway(case_context=cc, audit_logger=audit, review_gateway=review_gw)
        r = gw_cc.check("gmail.create_draft", {"to": "x@y.com"}, "agent", "s")
        assert r.requires_human_review  # P3 → human_required
        print(f"✓ P3 create_draft via CaseContext → human_required")

        print("\nAll PermissionGateway self-tests passed ✓")
