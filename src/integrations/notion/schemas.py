"""Notion database property schemas for each artifact type.

Defines the property schemas used when provisioning databases and
validates that existing databases match the expected schema.
"""

from __future__ import annotations


def _select_options(values: list[str]) -> dict:
    """Build a select property schema with named options."""
    return {
        "select": {"options": [{"name": v} for v in values]}
    }


# -- Database schemas --

INTAKE_SCHEMA: dict[str, dict] = {
    "Title": {"title": {}},
    "Type": _select_options(
        ["idea", "bug", "feature-request", "tech-debt", "question", "other"]
    ),
    "Status": _select_options(["new", "planned", "architect-review", "rejected"]),
    "Brief Link": {"url": {}},
}

BRIEFS_SCHEMA: dict[str, dict] = {
    "Title": {"title": {}},
    "Brief Name": {"rich_text": {}},
    "Status": _select_options(["draft", "implementation-ready"]),
    "Phase": _select_options(["Phase 1", "Phase 2", "Phase 3"]),
}

DECISIONS_SCHEMA: dict[str, dict] = {
    "Title": {"title": {}},
    "ID": {"rich_text": {}},
    "Date": {"date": {}},
    "Status": _select_options(["proposed", "accepted", "superseded"]),
    "Why": {"rich_text": {}},
    "Alternatives Rejected": {"rich_text": {}},
    "ADR Link": {"url": {}},
}

BACKLOG_SCHEMA: dict[str, dict] = {
    "Title": {"title": {}},
    "ID": {"rich_text": {}},
    "Type": _select_options(["Feature", "Tech Debt", "Bug"]),
    "Use Case": {"rich_text": {}},
    "Feature": {"rich_text": {}},
    "Priority": _select_options(["High", "Medium", "Low"]),
    "Status": _select_options(["To Do", "In Progress", "Done", "Blocked"]),
    "Notes": {"rich_text": {}},
}

TEMPLATES_SCHEMA: dict[str, dict] = {
    "Name": {"title": {}},
    "Version": {"rich_text": {}},
    "Last Seeded": {"date": {}},
}


# -- Registry: name → (schema, icon, display title) --

DATABASE_REGISTRY: dict[str, tuple[dict[str, dict], str, str]] = {
    "intake": (INTAKE_SCHEMA, "📥", "Intake"),
    "briefs": (BRIEFS_SCHEMA, "📋", "Feature Briefs"),
    "decisions": (DECISIONS_SCHEMA, "⚖️", "Decisions"),
    "backlog": (BACKLOG_SCHEMA, "📊", "Backlog"),
    "templates": (TEMPLATES_SCHEMA, "📄", "Templates"),
}
