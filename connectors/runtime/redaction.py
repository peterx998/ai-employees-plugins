"""PII redaction module for the Runtime Permission Gateway.

Provides pattern-based redaction of Personally Identifiable Information (PII)
in text and structured data (dicts).  Used by the permission gateway to
sanitize tool-call arguments before they are logged or passed to downstream
connectors.

Supported PII types
-------------------
- Email addresses       → [REDACTED_EMAIL]
- Phone numbers         → [REDACTED_PHONE]
- Order numbers (DRP-…)  → [REDACTED_ORDER]
- Credit card numbers    → [REDACTED_CC]
- IP addresses           → [REDACTED_IP]

All patterns are applied case-insensitively where appropriate.
"""

from __future__ import annotations

import re
from typing import Any


class Redactor:
    """Pattern-based PII redactor.

    Each PII type has an associated regex pattern and a replacement token.
    :meth:`redact` applies all patterns to a plain string.
    :meth:`redact_dict` walks a nested dict/list structure recursively.
    :meth:`redact_fields` redacts only the named keys in a flat dict.
    """

    # ------------------------------------------------------------------ #
    # Pattern definitions
    # ------------------------------------------------------------------ #
    # Email — standard RFC 5322 simplified pattern
    _EMAIL_RE = re.compile(
        r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"
    )

    # Phone — international and US formats
    #  +1-555-123-4567, (555) 123-4567, 555.123.4567, +44 20 7946 0958
    _PHONE_RE = re.compile(
        r"""
        (?<!\w)                     # no preceding word char
        (\+\d{1,3}[\s.-]?)?         # optional country code
        (\(?\d{2,4}\)?[\s.-]?)      # area / region
        \d{3,4}[\s.-]?              # exchange
        \d{3,4}                     # subscriber
        (?!\w)                      # no trailing word char
        """,
        re.VERBOSE,
    )

    # Order number — DRP- followed by 3-8 alphanumeric chars
    _ORDER_RE = re.compile(
        r"\bDRP-[A-Za-z0-9]{3,8}\b",
        re.IGNORECASE,
    )

    # Credit card — 13-19 digit groups, separated by spaces or dashes
    _CC_RE = re.compile(
        r"""
        \b(?:\d[ -]*?){13,19}\b
        """,
        re.VERBOSE,
    )

    # IP address — IPv4 only (most common in logs)
    _IP_RE = re.compile(
        r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}"
        r"(?:25[0-5]|2[0-4]\d|1?\d?\d)\b"
    )

    #: Mapping of compiled pattern → replacement token, applied in order.
    _PATTERNS: list[tuple[re.Pattern[str], str]] = [
        (_CC_RE,    "[REDACTED_CC]"),     # CC before phone — longer digit runs
        (_EMAIL_RE, "[REDACTED_EMAIL]"),
        (_PHONE_RE, "[REDACTED_PHONE]"),
        (_ORDER_RE, "[REDACTED_ORDER]"),
        (_IP_RE,    "[REDACTED_IP]"),
    ]

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def redact(self, text: str) -> str:
        """Redact all known PII patterns from *text*.

        Parameters
        ----------
        text
            The input string that may contain PII.

        Returns
        -------
        str
            A new string with every PII match replaced by its
            redaction token.
        """
        if not isinstance(text, str):
            return text
        result = text
        for pattern, replacement in self._PATTERNS:
            result = pattern.sub(replacement, result)
        return result

    def redact_dict(self, d: Any) -> Any:
        """Recursively redact all string values in a nested structure.

        Walks dicts and lists, applying :meth:`redact` to every string
        value encountered.  Non-string values are returned as-is.

        Parameters
        ----------
        d
            The dict, list, or scalar to redact.

        Returns
        -------
        Any
            A new structure of the same shape with all string values
            redacted.
        """
        if isinstance(d, dict):
            return {key: self.redact_dict(val) for key, val in d.items()}
        if isinstance(d, list):
            return [self.redact_dict(item) for item in d]
        if isinstance(d, str):
            return self.redact(d)
        return d

    def redact_fields(self, data: dict[str, Any], fields: list[str]) -> dict[str, Any]:
        """Redact specific top-level keys in *data*.

        Only the named *fields* are redacted (if present and string-typed).
        Nested dict values are processed with :meth:`redact_dict`.

        Parameters
        ----------
        data
            Flat or nested dict whose specified fields should be redacted.
        fields
            List of field names to redact.

        Returns
        -------
        dict[str, Any]
            A **new** dict with the specified fields redacted.
            The original dict is not mutated.
        """
        result = dict(data)  # shallow copy — don't mutate caller's dict
        for field in fields:
            if field in result:
                val = result[field]
                if isinstance(val, str):
                    result[field] = self.redact(val)
                elif isinstance(val, (dict, list)):
                    result[field] = self.redact_dict(val)
                # Non-string, non-container scalars (int, bool, …) are left as-is
        return result

    # ------------------------------------------------------------------ #
    # Introspection helpers (useful for tests / debugging)
    # ------------------------------------------------------------------ #

    def get_patterns(self) -> dict[str, str]:
        """Return a human-readable mapping of PII type → regex source."""
        return {
            "email":       self._EMAIL_RE.pattern,
            "phone":       self._PHONE_RE.pattern,
            "order":       self._ORDER_RE.pattern,
            "credit_card": self._CC_RE.pattern,
            "ip_address":  self._IP_RE.pattern,
        }


# ---------------------------------------------------------------------- #
# Module-level singleton for convenience
# ---------------------------------------------------------------------- #
_default_redactor: Redactor | None = None


def get_default_redactor() -> Redactor:
    """Return a process-wide :class:`Redactor` singleton."""
    global _default_redactor
    if _default_redactor is None:
        _default_redactor = Redactor()
    return _default_redactor


# ---------------------------------------------------------------------- #
# Self-test
# ---------------------------------------------------------------------- #
if __name__ == "__main__":
    r = Redactor()

    # --- redact() -------------------------------------------------------
    samples = [
        "Contact me at john.doe@example.com please",
        "Call +1-555-123-4567 or (555) 987-6543",
        "Order DRP-AB12C has shipped",
        "Card 4111 1111 1111 1111 was charged",
        "Server at 192.168.1.100 responded",
        "Mixed: john@x.com, DRP-9999, 10.0.0.1",
    ]
    print("=== redact() tests ===")
    for s in samples:
        print(f"  IN : {s}")
        print(f"  OUT: {r.redact(s)}")
        print()

    # --- redact_dict() --------------------------------------------------
    nested = {
        "to": "customer@example.com",
        "body": "Order DRP-1234, phone 555-123-4567",
        "meta": {"ip": "10.20.30.40", "cc": "4111111111111111"},
        "count": 5,
        "items": ["email@test.org", "DRP-XYZ"],
    }
    print("=== redact_dict() tests ===")
    redacted = r.redact_dict(nested)
    import json
    print(json.dumps(redacted, indent=2))
    print()

    # --- redact_fields() ------------------------------------------------
    print("=== redact_fields() tests ===")
    data = {
        "to": "customer@example.com",
        "subject": "Re: DRP-1234",
        "body": "Your order DRP-1234 is confirmed.",
        "order_id": "DRP-1234",
    }
    field_result = r.redact_fields(data, ["to", "body"])
    print(json.dumps(field_result, indent=2))

    # Verify no-arg fields are untouched
    assert "DRP-1234" in field_result["subject"], "subject should be untouched"
    assert "DRP-1234" not in field_result["body"], "body should be redacted"
    assert field_result["to"] == "[REDACTED_EMAIL]", "email should be redacted"
    print("\nAll self-tests passed ✓")
