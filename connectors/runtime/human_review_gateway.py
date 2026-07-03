"""Human review queue gateway for the Runtime Permission Gateway.

When the permission gateway decides a tool call requires human review
(e.g. ``gmail.create_draft`` on a P2+ case), the call is submitted to
this gateway.  It stores review requests as individual JSON files in a
queue directory and provides methods to approve, reject, and query the
status of pending reviews.

In a production system, :meth:`approve` would trigger the actual tool
execution.  Here it simply updates the review item's status.
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .redaction import Redactor


class HumanReviewGateway:
    """File-based human-review queue.

    Each review request is stored as a single JSON file named
    ``<review_id>.json`` in *queue_dir*.

    Parameters
    ----------
    queue_dir
        Directory where review-request JSON files are stored.
        Created automatically if it does not exist.
    """

    def __init__(
        self,
        queue_dir: str = "customer-support/evals/human_review_queue",
    ) -> None:
        self.queue_dir = Path(queue_dir)
        self.queue_dir.mkdir(parents=True, exist_ok=True)
        self._redactor = Redactor()

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _now() -> str:
        """Return current UTC time as an ISO-8601 string."""
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _generate_review_id() -> str:
        """Generate a unique review ID.

        Format: ``HR-<8-char-uuid>`` (e.g. ``HR-a1b2c3d4``).
        """
        return f"HR-{uuid.uuid4().hex[:8]}"

    def _review_path(self, review_id: str) -> Path:
        """Return the file path for a given review_id."""
        return self.queue_dir / f"{review_id}.json"

    def _load(self, review_id: str) -> dict[str, Any] | None:
        """Load a review item by ID.  Returns ``None`` if not found."""
        path = self._review_path(review_id)
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)

    def _save(self, review: dict[str, Any]) -> None:
        """Persist a review item to its JSON file."""
        path = self._review_path(review["review_id"])
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(review, fh, indent=2, default=str, ensure_ascii=False)

    def _all_reviews(self) -> list[dict[str, Any]]:
        """Load all review items from the queue directory."""
        reviews: list[dict[str, Any]] = []
        for path in sorted(self.queue_dir.glob("HR-*.json")):
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    reviews.append(json.load(fh))
            except (json.JSONDecodeError, OSError):
                continue
        return reviews

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def submit_for_review(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        case_id: str,
        reason: str,
    ) -> str:
        """Create a new human-review request.

        Parameters
        ----------
        tool_name
            The tool that was intercepted and needs review.
        arguments
            The tool-call arguments.  Will be redacted before storage.
        case_id
            The support case associated with the request.
        reason
            Why human review is required (e.g. ``"create_draft on P2 case"``).

        Returns
        -------
        str
            The generated ``review_id``.
        """
        review_id = self._generate_review_id()
        redacted_args = self._redactor.redact_dict(arguments)

        review: dict[str, Any] = {
            "review_id": review_id,
            "tool_name": tool_name,
            "arguments": redacted_args,
            "case_id": case_id,
            "reason": reason,
            "status": "pending",
            "submitted_at": self._now(),
            "reviewed_at": None,
        }
        self._save(review)
        return review_id

    def get_pending_reviews(self) -> list[dict[str, Any]]:
        """Return all review items with status ``pending``."""
        return [r for r in self._all_reviews() if r.get("status") == "pending"]

    def get_review(self, review_id: str) -> dict[str, Any] | None:
        """Return a single review item by ID, or ``None`` if not found."""
        return self._load(review_id)

    def approve(self, review_id: str) -> dict[str, Any] | None:
        """Mark a review item as approved.

        In a production system this would also trigger execution of the
        deferred tool call.  Here it only updates the status.

        Parameters
        ----------
        review_id
            The review item to approve.

        Returns
        -------
        dict[str, Any] | None
            The updated review item, or ``None`` if not found or already
            reviewed.
        """
        review = self._load(review_id)
        if review is None:
            return None
        if review["status"] != "pending":
            return None  # Already reviewed — cannot re-approve

        review["status"] = "approved"
        review["reviewed_at"] = self._now()
        self._save(review)
        return review

    def reject(self, review_id: str, reason: str) -> dict[str, Any] | None:
        """Mark a review item as rejected.

        Parameters
        ----------
        review_id
            The review item to reject.
        reason
            Human-readable rejection reason.

        Returns
        -------
        dict[str, Any] | None
            The updated review item (with a ``rejection_reason`` field
            added), or ``None`` if not found or already reviewed.
        """
        review = self._load(review_id)
        if review is None:
            return None
        if review["status"] != "pending":
            return None

        review["status"] = "rejected"
        review["rejection_reason"] = reason
        review["reviewed_at"] = self._now()
        self._save(review)
        return review

    def is_approved(self, review_id: str) -> bool:
        """Check whether a review item has been approved.

        Returns ``False`` if the item doesn't exist, is pending, or was
        rejected.
        """
        review = self._load(review_id)
        if review is None:
            return False
        return review.get("status") == "approved"

    def is_pending(self, review_id: str) -> bool:
        """Check whether a review item is still pending."""
        review = self._load(review_id)
        if review is None:
            return False
        return review.get("status") == "pending"

    def is_rejected(self, review_id: str) -> bool:
        """Check whether a review item has been rejected."""
        review = self._load(review_id)
        if review is None:
            return False
        return review.get("status") == "rejected"

    # ------------------------------------------------------------------ #
    # Maintenance / introspection
    # ------------------------------------------------------------------ #

    def clear(self) -> None:
        """Remove all review files (for fresh test runs)."""
        for path in self.queue_dir.glob("HR-*.json"):
            path.unlink()

    def stats(self) -> dict[str, int]:
        """Return counts by status."""
        all_reviews = self._all_reviews()
        return {
            "total": len(all_reviews),
            "pending": sum(1 for r in all_reviews if r.get("status") == "pending"),
            "approved": sum(1 for r in all_reviews if r.get("status") == "approved"),
            "rejected": sum(1 for r in all_reviews if r.get("status") == "rejected"),
        }


# ---------------------------------------------------------------------- #
# Self-test
# ---------------------------------------------------------------------- #
if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        gw = HumanReviewGateway(queue_dir=tmpdir)

        # --- submit ----------------------------------------------------
        rid1 = gw.submit_for_review(
            tool_name="gmail.create_draft",
            arguments={
                "to": "customer@example.com",
                "subject": "Re: DRP-1234",
                "body": "Your refund has been processed.",
            },
            case_id="CS-001",
            reason="create_draft requires human review on P2+ cases",
        )
        rid2 = gw.submit_for_review(
            tool_name="gmail.create_draft",
            arguments={"to": "another@test.org", "subject": "Hello"},
            case_id="CS-002",
            reason="create_draft requires human review on P2+ cases",
        )
        print(f"✓ Submitted: {rid1}, {rid2}")

        # --- verify PII redaction in stored arguments ------------------
        review1 = gw.get_review(rid1)
        assert review1 is not None
        assert review1["arguments"]["to"] == "[REDACTED_EMAIL]", (
            f"Expected redacted email, got: {review1['arguments']['to']}"
        )
        assert "DRP-1234" not in review1["arguments"]["subject"]
        print(f"✓ PII redacted in stored review: {review1['arguments']}")

        # --- verify pending -------------------------------------------
        pending = gw.get_pending_reviews()
        assert len(pending) == 2
        assert gw.is_pending(rid1)
        assert not gw.is_approved(rid1)
        print(f"✓ {len(pending)} pending reviews")

        # --- approve one ----------------------------------------------
        approved = gw.approve(rid1)
        assert approved is not None
        assert approved["status"] == "approved"
        assert approved["reviewed_at"] is not None
        assert gw.is_approved(rid1)
        assert not gw.is_pending(rid1)
        print(f"✓ Approved {rid1}")

        # --- cannot re-approve ----------------------------------------
        re_approve = gw.approve(rid1)
        assert re_approve is None
        print("✓ Cannot re-approve already-reviewed item")

        # --- reject the other -----------------------------------------
        rejected = gw.reject(rid2, "Draft content not appropriate")
        assert rejected is not None
        assert rejected["status"] == "rejected"
        assert rejected["rejection_reason"] == "Draft content not appropriate"
        assert gw.is_rejected(rid2)
        assert not gw.is_approved(rid2)
        print(f"✓ Rejected {rid2}")

        # --- verify pending now empty ---------------------------------
        pending_after = gw.get_pending_reviews()
        assert len(pending_after) == 0
        print("✓ No pending reviews after approve/reject")

        # --- stats ----------------------------------------------------
        stats = gw.stats()
        assert stats["total"] == 2
        assert stats["approved"] == 1
        assert stats["rejected"] == 1
        assert stats["pending"] == 0
        print(f"✓ Stats: {stats}")

        # --- clear ----------------------------------------------------
        gw.clear()
        assert len(gw.get_pending_reviews()) == 0
        assert gw.get_review(rid1) is None
        print("✓ Clear works")

        # --- verify timestamps are timezone-aware ---------------------
        # Re-submit to check
        rid3 = gw.submit_for_review(
            tool_name="gmail.create_draft",
            arguments={"to": "x@y.com"},
            case_id="CS-003",
            reason="test",
        )
        r3 = gw.get_review(rid3)
        assert r3 is not None
        ts = datetime.fromisoformat(r3["submitted_at"])
        assert ts.tzinfo is not None, "submitted_at should be timezone-aware"

        print("\nAll HumanReviewGateway self-tests passed ✓")
