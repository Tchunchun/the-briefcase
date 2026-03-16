"""Unit + integration tests for LocalBackend."""

import pytest
from pathlib import Path

from src.core.storage.local_backend import LocalBackend
from src.core.storage.protocol import ArtifactStore


@pytest.fixture
def project(tmp_path):
    """Set up a minimal project directory structure."""
    plan = tmp_path / "docs" / "plan"
    shared = plan / "_shared"
    shared.mkdir(parents=True)
    (tmp_path / "_project").mkdir()
    (tmp_path / "template").mkdir()

    # Seed inbox
    inbox = plan / "_inbox.md"
    inbox.write_text(
        "# Inbox\n\n## Entries\n\n"
        "- [idea] Build a notification system\n"
        "- [bug] Search fails on empty query [-> architect review]\n"
    )

    # Seed backlog
    backlog = shared / "backlog.md"
    backlog.write_text(
        "# Backlog\n\n"
        "| ID | Type | Use Case | Feature | Title | Priority | Status | Notes |\n"
        "|---|---|---|---|---|---|---|---|\n"
        "| T-001 | Feature | User needs alerts | notifications | Add email alerts | High | To Do | — |\n"
    )

    # Seed decisions
    decisions = tmp_path / "_project" / "decisions.md"
    decisions.write_text(
        "# Decisions Log\n\n"
        "| ID | Date | Decision | Why | Alternatives Rejected | ADR |\n"
        "|---|---|---|---|---|---|\n"
        "| D-001 | 2026-03-16 | Use Python | Ecosystem fit | Node.js | — |\n"
    )

    # Seed a brief
    brief_dir = plan / "notifications"
    brief_dir.mkdir()
    (brief_dir / "brief.md").write_text(
        "# Notifications (v1)\n\n"
        "**Status: draft**\n\n---\n\n"
        "## Problem\nUsers miss updates.\n\n"
        "## Goal\nSend email alerts.\n\n"
        "## Acceptance Criteria\n- [ ] Email sent on event\n\n"
        "## Out of Scope\n- SMS\n\n"
        "## Open Questions\n- Which email provider?\n\n"
        "## Technical Approach\n*Owned by architect agent.*\n"
    )

    # Seed a template
    (tmp_path / "template" / "brief.md").write_text(
        "# {Feature Name} (v3)\n\n**Status: draft**\n"
    )

    return tmp_path


@pytest.fixture
def backend(project):
    return LocalBackend(project)


# --- Protocol compliance ---


def test_local_backend_satisfies_artifact_store(backend):
    assert isinstance(backend, ArtifactStore)


# --- Inbox ---


def test_read_inbox(backend):
    entries = backend.read_inbox()
    assert len(entries) == 2
    assert entries[0]["type"] == "idea"
    assert entries[0]["text"] == "Build a notification system"
    assert entries[1]["status"] == "architect review"


def test_append_inbox(backend):
    backend.append_inbox({"type": "tech-debt", "text": "Refactor sync module"})
    entries = backend.read_inbox()
    assert len(entries) == 3
    assert entries[2]["type"] == "tech-debt"
    assert entries[2]["text"] == "Refactor sync module"


def test_read_inbox_empty(tmp_path):
    (tmp_path / "docs" / "plan").mkdir(parents=True)
    b = LocalBackend(tmp_path)
    assert b.read_inbox() == []


# --- Briefs ---


def test_read_brief(backend):
    brief = backend.read_brief("notifications")
    assert brief["name"] == "notifications"
    assert brief["status"] == "draft"
    assert "Users miss updates" in brief["problem"]
    assert "Email sent on event" in brief["acceptance_criteria"]


def test_read_brief_not_found(backend):
    with pytest.raises(KeyError, match="Brief not found"):
        backend.read_brief("nonexistent")


def test_write_brief(backend, project):
    backend.write_brief(
        "new-feature",
        {
            "title": "New Feature",
            "status": "draft",
            "problem": "Something is missing.",
            "goal": "Fix it.",
            "acceptance_criteria": "- [ ] It works",
            "out_of_scope": "- Nothing else",
            "open_questions": "- TBD",
        },
    )
    brief = backend.read_brief("new-feature")
    assert brief["status"] == "draft"
    assert "Something is missing" in brief["problem"]


def test_list_briefs(backend):
    briefs = backend.list_briefs()
    assert len(briefs) == 1
    assert briefs[0]["name"] == "notifications"
    assert briefs[0]["status"] == "draft"


# --- Decisions ---


def test_read_decisions(backend):
    decisions = backend.read_decisions()
    assert len(decisions) == 1
    assert decisions[0]["id"] == "D-001"
    assert decisions[0]["title"] == "Use Python"


def test_append_decision(backend):
    backend.append_decision(
        {
            "id": "D-002",
            "date": "2026-03-16",
            "title": "Use Click",
            "why": "Simple CLI",
            "alternatives_rejected": "argparse",
            "adr_link": "—",
        }
    )
    decisions = backend.read_decisions()
    assert len(decisions) == 2
    assert decisions[1]["id"] == "D-002"


# --- Backlog ---


def test_read_backlog(backend):
    rows = backend.read_backlog()
    assert len(rows) == 1
    assert rows[0]["id"] == "T-001"
    assert rows[0]["status"] == "To Do"


def test_write_backlog_row_update(backend):
    backend.write_backlog_row(
        {
            "id": "T-001",
            "type": "Feature",
            "use_case": "User needs alerts",
            "feature": "notifications",
            "title": "Add email alerts",
            "priority": "High",
            "status": "In Progress",
            "notes": "Started work",
        }
    )
    rows = backend.read_backlog()
    assert rows[0]["status"] == "In Progress"
    assert rows[0]["notes"] == "Started work"


def test_write_backlog_row_append(backend):
    backend.write_backlog_row(
        {
            "id": "T-002",
            "type": "Bug",
            "feature": "notifications",
            "title": "Fix email format",
            "priority": "Medium",
            "status": "To Do",
        }
    )
    rows = backend.read_backlog()
    assert len(rows) == 2
    assert rows[1]["id"] == "T-002"


# --- Templates ---


def test_read_templates(backend):
    templates = backend.read_templates()
    assert len(templates) >= 1
    brief_tpl = next(t for t in templates if t["name"] == "brief")
    assert brief_tpl["version"] == "v3"
    assert "Status: draft" in brief_tpl["content"]


def test_write_template(backend, project):
    backend.write_template("custom", "# Custom Template (v1)\n", "v1")
    path = project / "template" / "custom.md"
    assert path.exists()
    assert "Custom Template" in path.read_text()
