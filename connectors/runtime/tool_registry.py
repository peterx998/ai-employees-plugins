"""Tool registry and permission matrix for the Runtime Permission Gateway.

Defines every tool available to the ``customer-support`` AI employee along
with its connector, category, permission level, priority-based
restrictions, description, and PII field annotations.

The registry is consumed by :mod:`permission_gateway` to make allow / deny /
human-review decisions at runtime.

Permission levels
-----------------
- ``auto_allow``       — gateway permits the call immediately
- ``human_required``   — gateway submits the call for human review
- ``denied``           — gateway blocks the call unconditionally

Priority restrictions
---------------------
A comma-separated string that maps case priority (P1–P4) to a
permission outcome for that specific tool:

    ``"P1:denied,P2:human_required,P3:human_required,P4:human_required"``
    ``"always_denied"``
    ``"all_allowed"``
"""

from __future__ import annotations

from typing import Any


# ---------------------------------------------------------------------- #
# Data class for individual tool entries
# ---------------------------------------------------------------------- #

class ToolEntry:
    """Immutable description of a single tool and its permission rules.

    Attributes
    ----------
    name : str
        Fully-qualified tool name (e.g. ``gmail.search_threads``).
    connector : str
        MCP server / connector that provides this tool.
    category : str
        ``read``, ``write``, or ``admin``.
    permission_level : str
        Default permission: ``auto_allow``, ``human_required``, or ``denied``.
    priority_restriction : str
        Comma-separated priority → outcome mapping, or ``always_denied``
        / ``all_allowed``.
    description : str
        Human-readable summary of what the tool does.
    pii_fields : list[str]
        Names of argument fields that may contain PII and require
        redaction before logging.
    """

    __slots__ = (
        "name",
        "connector",
        "category",
        "permission_level",
        "priority_restriction",
        "description",
        "pii_fields",
    )

    def __init__(
        self,
        name: str,
        connector: str,
        category: str,
        permission_level: str,
        priority_restriction: str,
        description: str,
        pii_fields: list[str] | None = None,
    ) -> None:
        self.name = name
        self.connector = connector
        self.category = category
        self.permission_level = permission_level
        self.priority_restriction = priority_restriction
        self.description = description
        self.pii_fields: list[str] = pii_fields if pii_fields is not None else []

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a plain dict (for logging / JSON output)."""
        return {
            "name": self.name,
            "connector": self.connector,
            "category": self.category,
            "permission_level": self.permission_level,
            "priority_restriction": self.priority_restriction,
            "description": self.description,
            "pii_fields": list(self.pii_fields),
        }

    def __repr__(self) -> str:
        return (
            f"ToolEntry(name={self.name!r}, category={self.category!r}, "
            f"permission_level={self.permission_level!r})"
        )


# ---------------------------------------------------------------------- #
# Tool registry — the permission matrix
# ---------------------------------------------------------------------- #

class ToolRegistry:
    """Central registry of all tools and their permission rules.

    The registry is populated at construction time with the canonical
    tool set for the ``customer-support`` AI employee.  Tools can be
    looked up by name via :meth:`get` or iterated via :meth:`all`.
    """

    def __init__(self) -> None:
        self._tools: dict[str, ToolEntry] = {}
        self._register_default_tools()

    # ------------------------------------------------------------------ #
    # Registration
    # ------------------------------------------------------------------ #

    def _register_default_tools(self) -> None:
        """Register the canonical customer-support tool set."""
        tools = [
            # --- Gmail ---------------------------------------------------
            ToolEntry(
                name="gmail.search_threads",
                connector="gmail",
                category="read",
                permission_level="auto_allow",
                priority_restriction="all_allowed",
                description="Search Gmail threads by query string.",
                pii_fields=[],
            ),
            ToolEntry(
                name="gmail.read_thread",
                connector="gmail",
                category="read",
                permission_level="auto_allow",
                priority_restriction="all_allowed",
                description="Read a specific Gmail thread by thread ID.",
                pii_fields=[],
            ),
            ToolEntry(
                name="gmail.create_draft",
                connector="gmail",
                category="write",
                permission_level="human_required",
                priority_restriction="P1:denied,P2:human_required,P3:human_required,P4:human_required",
                description="Create a draft email. Denied for P1 cases; requires human review for P2+.",
                pii_fields=["to", "cc", "bcc", "body", "subject"],
            ),
            ToolEntry(
                name="gmail.send_email",
                connector="gmail",
                category="write",
                permission_level="denied",
                priority_restriction="always_denied",
                description="Send an email directly. ALWAYS DENIED — no override. Agents must use create_draft + human review.",
                pii_fields=["to", "cc", "bcc", "body", "subject"],
            ),

            # --- Shopify -------------------------------------------------
            ToolEntry(
                name="shopify.read_orders",
                connector="shopify",
                category="read",
                permission_level="auto_allow",
                priority_restriction="all_allowed",
                description="Read Shopify orders by query or order ID.",
                pii_fields=[],
            ),
            ToolEntry(
                name="shopify.read_customer",
                connector="shopify",
                category="read",
                permission_level="auto_allow",
                priority_restriction="all_allowed",
                description="Read a Shopify customer record. PII fields are redacted before logging.",
                pii_fields=["email", "phone", "first_name", "last_name", "address"],
            ),
            ToolEntry(
                name="shopify.update_page",
                connector="shopify",
                category="write",
                permission_level="denied",
                priority_restriction="always_denied",
                description="Update a Shopify page. DENIED for agents — human-only action.",
                pii_fields=[],
            ),

            # --- Knowledge Base ------------------------------------------
            ToolEntry(
                name="kb.search_policies",
                connector="kb",
                category="read",
                permission_level="auto_allow",
                priority_restriction="all_allowed",
                description="Search the knowledge base for policies and FAQs.",
                pii_fields=[],
            ),

            # --- Human Review --------------------------------------------
            ToolEntry(
                name="human_review.submit",
                connector="human_review",
                category="write",
                permission_level="auto_allow",
                priority_restriction="all_allowed",
                description="Submit a tool call or artifact for human review.",
                pii_fields=[],
            ),
            ToolEntry(
                name="human_review.approve",
                connector="human_review",
                category="admin",
                permission_level="denied",
                priority_restriction="always_denied",
                description="Approve a pending human review item. DENIED for agents — human-only action.",
                pii_fields=[],
            ),
        ]
        for tool in tools:
            self._register(tool)

    def _register(self, entry: ToolEntry) -> None:
        """Add a :class:`ToolEntry` to the registry."""
        if entry.name in self._tools:
            raise ValueError(f"Tool already registered: {entry.name}")
        self._tools[entry.name] = entry

    # ------------------------------------------------------------------ #
    # Public lookup API
    # ------------------------------------------------------------------ #

    def get(self, name: str) -> ToolEntry | None:
        """Look up a tool by fully-qualified name.

        Returns ``None`` if the tool is not registered.
        """
        return self._tools.get(name)

    def all(self) -> list[ToolEntry]:
        """Return all registered tools as a list."""
        return list(self._tools.values())

    def names(self) -> list[str]:
        """Return all registered tool names."""
        return list(self._tools.keys())

    def by_connector(self, connector: str) -> list[ToolEntry]:
        """Return all tools for a given connector (e.g. ``gmail``)."""
        return [t for t in self._tools.values() if t.connector == connector]

    def by_category(self, category: str) -> list[ToolEntry]:
        """Return all tools of a given category (read / write / admin)."""
        return [t for t in self._tools.values() if t.category == category]

    def to_dict(self) -> dict[str, dict[str, Any]]:
        """Serialise the entire registry to a name→dict mapping."""
        return {name: entry.to_dict() for name, entry in self._tools.items()}

    # ------------------------------------------------------------------ #
    # Priority restriction parsing
    # ------------------------------------------------------------------ #

    @staticmethod
    def parse_priority_restriction(restriction: str, priority: str) -> str:
        """Resolve a priority restriction string for a given priority.

        Parameters
        ----------
        restriction
            The ``priority_restriction`` value from a :class:`ToolEntry`.
        priority
            The case priority (``P1``, ``P2``, ``P3``, or ``P4``).

        Returns
        -------
        str
            One of ``"allowed"``, ``"denied"``, ``"human_required"``.

        Raises
        ------
        ValueError
            If the restriction string is malformed or the priority is
            not found.
        """
        if restriction == "all_allowed":
            return "allowed"
        if restriction == "always_denied":
            return "denied"

        # Parse comma-separated "P1:denied,P2:human_required,…" entries
        mapping: dict[str, str] = {}
        for part in restriction.split(","):
            part = part.strip()
            if ":" not in part:
                raise ValueError(
                    f"Malformed priority_restriction segment: {part!r}"
                )
            prio, outcome = part.split(":", 1)
            mapping[prio.strip()] = outcome.strip()

        if priority not in mapping:
            raise ValueError(
                f"Priority {priority!r} not found in restriction {restriction!r}"
            )

        outcome = mapping[priority]
        if outcome not in ("allowed", "denied", "human_required"):
            raise ValueError(
                f"Unknown outcome {outcome!r} for priority {priority!r}"
            )
        return outcome


# ---------------------------------------------------------------------- #
# Module-level convenience — process-wide singleton
# ---------------------------------------------------------------------- #

_registry: ToolRegistry | None = None


def _get_registry() -> ToolRegistry:
    """Return (or create) the process-wide :class:`ToolRegistry`."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry


def get_tool(name: str) -> ToolEntry | None:
    """Look up a tool by name using the default registry."""
    return _get_registry().get(name)


def get_all_tools() -> list[ToolEntry]:
    """Return all registered tools using the default registry."""
    return _get_registry().all()


# ---------------------------------------------------------------------- #
# Self-test
# ---------------------------------------------------------------------- #
if __name__ == "__main__":
    reg = ToolRegistry()

    # --- verify all 10 tools registered --------------------------------
    expected_names = [
        "gmail.search_threads",
        "gmail.read_thread",
        "gmail.create_draft",
        "gmail.send_email",
        "shopify.read_orders",
        "shopify.read_customer",
        "shopify.update_page",
        "kb.search_policies",
        "human_review.submit",
        "human_review.approve",
    ]
    assert reg.names() == expected_names, (
        f"Tool names mismatch.\n  Expected: {expected_names}\n  Got: {reg.names()}"
    )
    print(f"✓ {len(expected_names)} tools registered")

    # --- verify get() ---------------------------------------------------
    tool = reg.get("gmail.send_email")
    assert tool is not None
    assert tool.permission_level == "denied"
    assert tool.priority_restriction == "always_denied"
    assert tool.category == "write"
    print(f"✓ gmail.send_email: {tool}")

    assert reg.get("nonexistent.tool") is None
    print("✓ Lookup of nonexistent tool returns None")

    # --- verify by_connector / by_category -----------------------------
    gmail_tools = reg.by_connector("gmail")
    assert len(gmail_tools) == 4
    print(f"✓ gmail connector: {len(gmail_tools)} tools")

    write_tools = reg.by_category("write")
    assert len(write_tools) == 4  # create_draft, send_email, human_review.submit, update_page... let me count
    # create_draft (write), send_email (write), shopify.update_page (write), human_review.submit (write)
    print(f"✓ write category: {len(write_tools)} tools")

    read_tools = reg.by_category("read")
    assert len(read_tools) == 5  # search_threads, read_thread, read_orders, read_customer, search_policies
    print(f"✓ read category: {len(read_tools)} tools")

    # --- verify priority restriction parsing ---------------------------
    create_draft = reg.get("gmail.create_draft")
    assert create_draft is not None

    assert ToolRegistry.parse_priority_restriction(
        create_draft.priority_restriction, "P1"
    ) == "denied"
    assert ToolRegistry.parse_priority_restriction(
        create_draft.priority_restriction, "P2"
    ) == "human_required"
    assert ToolRegistry.parse_priority_restriction(
        create_draft.priority_restriction, "P4"
    ) == "human_required"

    send_email = reg.get("gmail.send_email")
    assert ToolRegistry.parse_priority_restriction(
        send_email.priority_restriction, "P1"
    ) == "denied"
    assert ToolRegistry.parse_priority_restriction(
        send_email.priority_restriction, "P4"
    ) == "denied"

    search = reg.get("gmail.search_threads")
    assert ToolRegistry.parse_priority_restriction(
        search.priority_restriction, "P3"
    ) == "allowed"
    print("✓ Priority restriction parsing correct")

    # --- verify PII fields ----------------------------------------------
    read_customer = reg.get("shopify.read_customer")
    assert read_customer is not None
    assert "email" in read_customer.pii_fields
    assert "phone" in read_customer.pii_fields
    print(f"✓ shopify.read_customer PII fields: {read_customer.pii_fields}")

    # --- verify module-level functions ----------------------------------
    assert get_tool("kb.search_policies") is not None
    assert len(get_all_tools()) == 10
    print("✓ Module-level get_tool / get_all_tools work")

    print("\nAll ToolRegistry self-tests passed ✓")
