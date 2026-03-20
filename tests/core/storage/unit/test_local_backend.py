"""Unit + integration tests for LocalBackend."""

import os

import pytest

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
        "## Non-Functional Requirements\n- **Latency / response time:** best-effort\n\n"
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
    assert entries[0]["priority"] == "Medium"
    assert entries[0]["text"] == "Build a notification system"
    assert entries[1]["status"] == "architect review"
    assert "created_at" in entries[0]
    assert "updated_at" in entries[0]


def test_append_inbox(backend):
    backend.append_inbox({"type": "tech-debt", "text": "Refactor sync module"})
    entries = backend.read_inbox()
    assert len(entries) == 3
    assert entries[2]["type"] == "tech-debt"
    assert entries[2]["priority"] == "Medium"
    assert entries[2]["text"] == "Refactor sync module"


def test_append_inbox_with_priority(backend):
    backend.append_inbox(
        {"type": "idea", "text": "Investigate flaky test", "priority": "High"}
    )
    entries = backend.read_inbox()
    assert entries[-1]["type"] == "idea"
    assert entries[-1]["priority"] == "High"


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
    assert "Latency / response time" in brief["non_functional_requirements"]


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
            "non_functional_requirements": "- **Other constraints:** Preserve body updates",
            "out_of_scope": "- Nothing else",
            "open_questions": "- TBD",
        },
    )
    brief = backend.read_brief("new-feature")
    assert brief["status"] == "draft"
    assert "Something is missing" in brief["problem"]
    assert "Preserve body updates" in brief["non_functional_requirements"]


def test_list_briefs(backend):
    briefs = backend.list_briefs()
    assert len(briefs) == 1
    assert briefs[0]["name"] == "notifications"
    assert briefs[0]["status"] == "draft"
    assert "date" in briefs[0]


def test_write_brief_creates_revision_history_for_existing_head(backend):
    backend.write_brief(
        "notifications",
        {
            "title": "Notifications",
            "status": "implementation-ready",
            "problem": "Users still miss updates.",
            "goal": "Send email alerts faster.",
            "acceptance_criteria": "- [ ] Email sent on event",
            "_actor": "tester",
            "_change_summary": "Clarified implementation scope.",
        },
    )

    revisions = backend.list_brief_revisions("notifications")
    assert len(revisions) == 1
    assert revisions[0]["actor"] == "tester"
    assert revisions[0]["change_summary"] == "Clarified implementation scope."

    revision = backend.read_brief_revision("notifications", revisions[0]["revision_id"])
    assert revision["snapshot"]["status"] == "draft"
    assert "Users miss updates." in revision["snapshot"]["problem"]


def test_restore_brief_revision_replaces_head_and_preserves_history(backend):
    backend.write_brief(
        "notifications",
        {
            "title": "Notifications",
            "status": "implementation-ready",
            "problem": "Updated problem.",
            "goal": "Updated goal.",
            "acceptance_criteria": "- [ ] Updated AC",
        },
    )
    first_revision = backend.list_brief_revisions("notifications")[0]["revision_id"]

    restored = backend.restore_brief_revision(
        "notifications",
        first_revision,
        actor="tester",
        change_summary="Undo scope drift.",
    )

    assert restored["status"] == "draft"
    assert restored["problem"] == "Users miss updates."

    revisions = backend.list_brief_revisions("notifications")
    assert len(revisions) == 2
    assert revisions[0]["change_summary"] == "Undo scope drift."


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
    assert "created_at" in rows[0]
    assert "updated_at" in rows[0]


def test_read_inbox_since_filters_by_updated_at(backend, project):
    inbox_path = project / "docs" / "plan" / "_inbox.md"
    old_ts = 1704067200  # 2024-01-01T00:00:00Z
    os.utime(inbox_path, (old_ts, old_ts))
    assert backend.read_inbox(since="2026-01-01") == []
    assert len(backend.read_inbox(since="2023-01-01")) == 2


def test_read_backlog_since_filters_by_updated_at(backend, project):
    backlog_path = project / "docs" / "plan" / "_shared" / "backlog.md"
    old_ts = 1704067200  # 2024-01-01T00:00:00Z
    os.utime(backlog_path, (old_ts, old_ts))
    assert backend.read_backlog(since="2026-01-01") == []
    assert len(backend.read_backlog(since="2023-01-01")) == 1


def test_list_children_filters_feature_rows_by_parent(backend, monkeypatch):
    monkeypatch.setattr(
        backend,
        "read_backlog",
        lambda since=None: [
            {
                "title": "Child Feature A",
                "type": "Feature",
                "status": "done",
                "parent_ids": ["idea-1"],
            },
            {
                "title": "Child Feature B",
                "type": "Feature",
                "status": "in-progress",
                "parent_ids": ["idea-1"],
            },
            {
                "title": "Unrelated Feature",
                "type": "Feature",
                "status": "done",
                "parent_ids": ["idea-2"],
            },
            {
                "title": "Task under idea",
                "type": "Task",
                "status": "done",
                "parent_ids": ["idea-1"],
            },
        ],
    )

    children = backend.list_children("idea-1")

    assert [row["title"] for row in children] == ["Child Feature A", "Child Feature B"]


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


def test_write_backlog_row_without_id_appends(backend):
    """When no id is provided, the row should still be appended."""
    backend.write_backlog_row(
        {
            "title": "New task without ID",
            "type": "Task",
            "status": "to-do",
            "priority": "High",
            "notes": "Created via CLI without --id",
        }
    )
    rows = backend.read_backlog()
    assert len(rows) == 2
    assert rows[1]["title"] == "New task without ID"


def test_write_backlog_row_without_id_updates_by_title_type(backend):
    """When no id is provided, lookup falls back to title + type."""
    # First write without id
    backend.write_backlog_row(
        {
            "title": "Some feature",
            "type": "Feature",
            "status": "draft",
            "priority": "Medium",
        }
    )
    rows = backend.read_backlog()
    assert len(rows) == 2

    # Update by title + type
    backend.write_backlog_row(
        {
            "title": "Some feature",
            "type": "Feature",
            "status": "implementation-ready",
            "priority": "High",
            "notes": "Updated",
        }
    )
    rows = backend.read_backlog()
    assert len(rows) == 2  # No duplication
    feature_row = [r for r in rows if r["title"] == "Some feature"][0]
    assert feature_row["status"] == "implementation-ready"
    assert feature_row["notes"] == "Updated"


def test_write_backlog_row_placeholder_id_updates_by_title_type(backend):
    backend.write_backlog_row(
        {
            "title": "Add email alerts",
            "type": "Feature",
            "status": "In Progress",
            "priority": "High",
            "notes": "Placeholder ID should still update by title.",
            "id": "—",
        }
    )

    rows = backend.read_backlog()
    assert len(rows) == 1
    assert rows[0]["title"] == "Add email alerts"
    assert rows[0]["status"] == "In Progress"


def test_write_backlog_row_without_feature_field(backend):
    """Missing feature field should not crash."""
    backend.write_backlog_row(
        {
            "id": "T-003",
            "title": "Standalone task",
            "type": "Task",
            "status": "to-do",
            "priority": "Low",
        }
    )
    rows = backend.read_backlog()
    assert len(rows) == 2
    assert rows[1]["feature"] == "\u2014"


def test_write_backlog_row_persists_workflow_fields(backend):
    backend.write_backlog_row(
        {
            "id": "T-001",
            "type": "Feature",
            "use_case": "User needs alerts",
            "feature": "notifications",
            "title": "Add email alerts",
            "priority": "High",
            "status": "review-accepted",
            "review_verdict": "accepted",
            "route_state": "routed",
            "release_note_link": "https://example.com/releases/v1.0.0",
            "notes": "Ready to ship",
            "automation_trace": "dispatch trace",
        }
    )

    rows = backend.read_backlog()
    assert rows[0]["review_verdict"] == "accepted"
    assert rows[0]["route_state"] == "routed"
    assert rows[0]["release_note_link"] == "https://example.com/releases/v1.0.0"
    assert rows[0]["automation_trace"] == "dispatch trace"


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


# --- Release Notes ---


def test_write_release_note(backend, project):
    backend.write_release_note("v0.5.0", "# v0.5.0\n\nNew feature added.\n")
    path = project / "docs" / "plan" / "_releases" / "v0.5.0" / "release-notes.md"
    assert path.exists()
    assert "New feature added" in path.read_text()


def test_read_release_note(backend, project):
    release_dir = project / "docs" / "plan" / "_releases" / "v0.1.0"
    release_dir.mkdir(parents=True)
    (release_dir / "release-notes.md").write_text("# v0.1.0\n\nInitial release.\n")
    note = backend.read_release_note("v0.1.0")
    assert note["version"] == "v0.1.0"
    assert note["title"] == "v0.1.0 Release Notes"
    assert "Initial release" in note["content"]


def test_read_release_note_not_found(backend):
    with pytest.raises(KeyError, match="Release note not found"):
        backend.read_release_note("v99.0.0")


def test_list_release_notes(backend, project):
    releases = project / "docs" / "plan" / "_releases"
    for v in ["v0.1.0", "v0.2.0"]:
        d = releases / v
        d.mkdir(parents=True)
        (d / "release-notes.md").write_text(f"# {v}\n")
    notes = backend.list_release_notes()
    assert len(notes) == 2
    assert notes[0]["version"] == "v0.1.0"
    assert notes[1]["version"] == "v0.2.0"


def test_list_release_notes_empty(tmp_path):
    (tmp_path / "docs" / "plan").mkdir(parents=True)
    b = LocalBackend(tmp_path)
    assert b.list_release_notes() == []


def test_write_release_note_overwrites(backend, project):
    backend.write_release_note("v0.5.0", "Original content.\n")
    backend.write_release_note("v0.5.0", "Updated content.\n")
    note = backend.read_release_note("v0.5.0")
    assert "Updated content" in note["content"]
    assert "Original content" not in note["content"]
