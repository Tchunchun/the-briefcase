"""Notion database property schemas for each artifact type.

Defines the property schemas used when provisioning databases and
validates that existing databases match the expected schema.

v3: Unified Backlog (Idea/Feature/Task) + Decisions + Briefs database.
Templates and release notes are standalone pages, not databases.
"""

from __future__ import annotations


def _select_options(values: list[str]) -> dict:
    """Build a select property schema with named options."""
    return {
        "select": {"options": [{"name": v} for v in values]}
    }


# -- Database schemas --

BACKLOG_SCHEMA: dict[str, dict] = {
    "Title": {"title": {}},
    "Type": _select_options(["Idea", "Feature", "Task"]),
    "Idea Status": _select_options(["new", "exploring", "promoted", "rejected", "shipped"]),
    "Feature Status": _select_options(
        ["draft", "architect-review", "implementation-ready", "in-progress",
         "review-ready", "review-accepted", "done", "shipped"]
    ),
    "Task Status": _select_options(["to-do", "in-progress", "blocked", "done"]),
    "Priority": _select_options(["High", "Medium", "Low"]),
    "Project": {"select": {"options": []}},
    "Review Verdict": _select_options(["pending", "accepted", "changes-requested"]),
    "Route State": _select_options(["routed", "returned", "blocked"]),
    "Lane": _select_options(["quick-fix", "small", "feature"]),
    "Brief Link": {"url": {}},
    "Release Note Link": {"url": {}},
    "Notes": {"rich_text": {}},
    "Automation Trace": {"rich_text": {}},
}
# Note: The "Parent" self-relation property is added via PATCH after
# the database is created (the DB ID is needed as the relation target).

DECISIONS_SCHEMA: dict[str, dict] = {
    "Title": {"title": {}},
    "ID": {"rich_text": {}},
    "Date": {"date": {}},
    "Status": _select_options(["proposed", "accepted", "superseded"]),
    "Why": {"rich_text": {}},
    "Alternatives Rejected": {"rich_text": {}},
    "Feature Link": {"url": {}},
    "ADR Link": {"url": {}},
}


BRIEFS_SCHEMA: dict[str, dict] = {
    "Name": {"title": {}},
    "Slug": {"rich_text": {}},
    "Status": _select_options(["draft", "implementation-ready"]),
    "Date": {"date": {}},
    "Linked Feature": {"url": {}},
    "Author": {"rich_text": {}},
}


# -- Registry: name → (schema, icon, display title) --

DATABASE_REGISTRY: dict[str, tuple[dict[str, dict], str, str]] = {
    "backlog": (BACKLOG_SCHEMA, "📊", "Backlog"),
    "decisions": (DECISIONS_SCHEMA, "⚖️", "Decisions"),
    "briefs_db": (BRIEFS_SCHEMA, "📋", "Briefs"),
}
