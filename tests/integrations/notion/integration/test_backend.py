"""Tests for NotionBackend v2 (unified Backlog, standalone briefs)."""

import pytest
from unittest.mock import MagicMock, patch

from src.core.storage.briefs import parse_brief_sections, render_brief_markdown
from src.core.storage.config import NotionConfig
from src.core.storage.protocol import ArtifactStore, SyncableStore
from src.integrations.notion.backend import NotionBackend
from src.integrations.notion.provisioner import NotionProvisioner


@pytest.fixture
def notion_config():
    return NotionConfig(
        parent_page_id="parent-1",
        parent_page_url="https://notion.so/parent-1",
        databases={
            "backlog": "db-backlog",
            "decisions": "db-decisions",
            "readme": "page-readme",
            "release_notes": "page-release-notes",
            "templates": "page-templates",
        },
    )


@pytest.fixture
def backend(notion_config, tmp_path):
    with patch("src.integrations.notion.backend.NotionClient") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        b = NotionBackend(notion_config, tmp_path)
        b._mock_client = mock_client
        yield b


# --- Protocol compliance ---


def test_notion_backend_satisfies_artifact_store(backend):
    assert isinstance(backend, ArtifactStore)


def test_notion_backend_satisfies_syncable_store(backend):
    assert isinstance(backend, SyncableStore)


# --- Inbox (Backlog Type=Idea) ---


def test_read_inbox(backend):
    backend._mock_client.query_database.return_value = [
        {
            "id": "row-1",
            "created_time": "2026-03-20T01:02:03.000Z",
            "last_edited_time": "2026-03-20T04:05:06.000Z",
            "properties": {
                "Title": {"title": [{"plain_text": "Add notification system"}]},
                "Type": {"select": {"name": "Idea"}},
                "Idea Status": {"select": {"name": "new"}},
                "Priority": {"select": {"name": "High"}},
            },
        }
    ]
    entries = backend.read_inbox()
    assert len(entries) == 1
    assert entries[0]["text"] == "Add notification system"
    assert entries[0]["type"] == "idea"
    assert entries[0]["status"] == "new"
    assert entries[0]["priority"] == "High"
    assert entries[0]["created_at"] == "2026-03-20T01:02:03.000Z"
    assert entries[0]["updated_at"] == "2026-03-20T04:05:06.000Z"

    # Verify query used Type=Idea filter
    call_args = backend._mock_client.query_database.call_args
    assert call_args[0][0] == "db-backlog"
    assert call_args[1]["filter"]["property"] == "Type"
    assert call_args[1]["filter"]["select"]["equals"] == "Idea"


def test_read_inbox_applies_since_filter(backend):
    backend._mock_client.query_database.return_value = []
    backend.read_inbox(since="2026-03-20")
    call_args = backend._mock_client.query_database.call_args
    assert call_args[1]["filter"]["and"][0]["property"] == "Type"
    assert call_args[1]["filter"]["and"][1]["timestamp"] == "last_edited_time"
    assert call_args[1]["filter"]["and"][1]["last_edited_time"]["on_or_after"] == "2026-03-20"


def test_append_inbox(backend):
    backend._mock_client.create_database_page.return_value = {"id": "new-1"}
    backend.append_inbox({"text": "New idea", "type": "idea"})
    call_args = backend._mock_client.create_database_page.call_args
    props = call_args[0][1]
    assert props["Type"]["select"]["name"] == "Idea"
    assert props["Idea Status"]["select"]["name"] == "new"
    assert props["Priority"]["select"]["name"] == "Medium"


def test_append_inbox_with_priority(backend):
    backend._mock_client.create_database_page.return_value = {"id": "new-1"}
    backend.append_inbox({"text": "New idea", "type": "idea", "priority": "Low"})
    props = backend._mock_client.create_database_page.call_args[0][1]
    assert props["Priority"]["select"]["name"] == "Low"


# --- Briefs (standalone pages under project root) ---


def test_list_briefs(backend):
    parent_children = [
        {
            "type": "child_page",
            "id": "p1",
            "last_edited_time": "2026-03-19T10:00:00.000Z",
            "child_page": {"title": "Notifications"},
        },
        {
            "type": "child_page",
            "id": "p4",
            "last_edited_time": "2026-03-20T12:00:00.000Z",
            "child_page": {"title": "Agent Entry Point"},
        },
        {"type": "child_page", "id": "p2", "child_page": {"title": "README"}},
        {"type": "child_page", "id": "p3", "child_page": {"title": "Templates"}},
        {"type": "child_page", "id": "rn1", "child_page": {"title": "v0.1.0 Release Notes"}},
        {"type": "child_database", "id": "db1", "child_database": {"title": "Backlog"}},
    ]
    brief_blocks_draft = [
        {"type": "paragraph", "paragraph": {"rich_text": [{"plain_text": "**Status: draft**"}]}},
    ]
    brief_blocks_impl = [
        {
            "type": "paragraph",
            "paragraph": {"rich_text": [{"plain_text": "**Status: implementation-ready**"}]},
        },
    ]

    # first call = parent children, then one call per brief page
    backend._client.get_block_children = MagicMock(
        side_effect=[parent_children, brief_blocks_draft, brief_blocks_impl]
    )

    briefs = backend.list_briefs()
    assert len(briefs) == 2
    assert briefs[0]["name"] == "agent-entry-point"
    assert briefs[0]["status"] == "implementation-ready"
    assert briefs[0]["date"] == "2026-03-20"
    assert briefs[1]["name"] == "notifications"
    assert briefs[1]["date"] == "2026-03-19"


def test_read_brief_not_found(backend):
    backend._mock_client.get_block_children.return_value = []
    with pytest.raises(KeyError, match="Brief not found"):
        backend.read_brief("nonexistent")


def test_write_brief_creates_new_page_with_body(backend):
    backend._mock_client.get_block_children.return_value = []
    backend._mock_client.create_page.return_value = {"id": "brief-1"}

    backend.write_brief(
        "agent-entry-point",
        {
            "title": "Agent Entry Point",
            "status": "draft",
            "problem": "Old invocation is clunky.",
            "goal": "Use ./agent.",
            "acceptance_criteria": "- [ ] Works",
            "non_functional_requirements": "- **Other constraints:** No regressions",
            "out_of_scope": "New commands",
            "open_questions": "None",
            "technical_approach": "Use a generated wrapper.",
        },
    )

    backend._mock_client.create_page.assert_called_once()
    call_args = backend._mock_client.create_page.call_args
    assert call_args[0][0] == "parent-1"
    assert call_args[0][1] == "Agent Entry Point"
    assert call_args[1]["children"]
    first_block = call_args[1]["children"][0]
    assert first_block["type"] == "paragraph"
    assert first_block["paragraph"]["rich_text"][0]["text"]["content"] == "**Status: draft**"


def test_render_brief_body_includes_status_line(backend):
    body = backend._render_brief_body(
        "agent-entry-point",
        {"status": "implementation-ready", "problem": "P", "goal": "G"},
    )

    assert body.startswith("**Status: implementation-ready**")


def test_write_brief_updates_existing_body(backend):
    old_blocks = [
        {"type": "paragraph", "id": "blk-1", "paragraph": {"rich_text": [{"plain_text": "Old."}]}},
        {"type": "paragraph", "id": "blk-2", "paragraph": {"rich_text": [{"plain_text": "Body."}]}},
    ]
    briefs_children = [{"type": "child_page", "id": "brief-1", "child_page": {"title": "Agent Entry Point"}}]

    def _get_block_children(page_id):
        if page_id == "brief-1":
            return list(old_blocks)
        return list(briefs_children)

    backend._mock_client.get_block_children.side_effect = _get_block_children
    backend._mock_client.get_page.return_value = {
        "properties": {"title": {"title": [{"plain_text": "Agent Entry Point"}]}},
        "url": "https://notion.so/brief-1",
    }
    backend._mock_client.update_page.return_value = {"id": "brief-1"}
    backend._mock_client.delete_block.return_value = {}
    backend._mock_client.append_block_children.return_value = {}
    backend._mock_client.create_page.side_effect = [
        {"id": "history-1"},
        {"id": "revision-1"},
    ]

    backend.write_brief(
        "agent-entry-point",
        {
            "title": "Agent Entry Point",
            "status": "implementation-ready",
            "problem": "Old invocation is clunky.",
            "goal": "Use ./agent.",
            "acceptance_criteria": "- [ ] Works",
            "non_functional_requirements": "- **Other constraints:** No regressions",
            "out_of_scope": "New commands",
            "open_questions": "None",
            "technical_approach": "Use a generated wrapper.",
        },
    )

    backend._mock_client.update_page.assert_called_once()
    backend._mock_client.delete_block.assert_any_call("blk-1")
    backend._mock_client.delete_block.assert_any_call("blk-2")
    # Called twice: once to replace brief body, once to refresh briefs index
    assert backend._mock_client.append_block_children.call_count == 2
    assert backend._mock_client.create_page.call_count == 2


def test_write_brief_skips_archived_existing_blocks(backend):
    old_blocks = [
        {
            "type": "paragraph",
            "id": "blk-archived",
            "archived": True,
            "paragraph": {"rich_text": [{"plain_text": "Old archived."}]},
        },
        {
            "type": "paragraph",
            "id": "blk-active",
            "paragraph": {"rich_text": [{"plain_text": "Old active."}]},
        },
    ]
    briefs_children = [{"type": "child_page", "id": "brief-1", "child_page": {"title": "Agent Entry Point"}}]

    def _get_block_children_archived(page_id):
        if page_id == "brief-1":
            return list(old_blocks)
        return list(briefs_children)

    backend._mock_client.get_block_children.side_effect = _get_block_children_archived
    backend._mock_client.get_page.return_value = {
        "properties": {"title": {"title": [{"plain_text": "Agent Entry Point"}]}},
        "url": "https://notion.so/brief-1",
    }
    backend._mock_client.update_page.return_value = {"id": "brief-1"}
    backend._mock_client.delete_block.return_value = {}
    backend._mock_client.append_block_children.return_value = {}
    backend._mock_client.create_page.side_effect = [
        {"id": "history-1"},
        {"id": "revision-1"},
    ]

    backend.write_brief(
        "agent-entry-point",
        {
            "title": "Agent Entry Point",
            "status": "implementation-ready",
            "problem": "Old invocation is clunky.",
            "goal": "Use ./agent.",
            "acceptance_criteria": "- [ ] Works",
            "non_functional_requirements": "- **Other constraints:** No regressions",
            "out_of_scope": "New commands",
            "open_questions": "None",
            "technical_approach": "Use a generated wrapper.",
        },
    )

    backend._mock_client.delete_block.assert_called_once_with("blk-active")
    # Called twice: once to replace brief body, once to refresh briefs index
    assert backend._mock_client.append_block_children.call_count == 2


def test_read_brief_returns_updated_sections(backend):
    backend._mock_client.get_block_children.side_effect = [
        [{"type": "child_page", "id": "brief-1", "child_page": {"title": "Agent Entry Point"}}],
        [
            {"type": "paragraph", "paragraph": {"rich_text": [{"plain_text": "**Status: implementation-ready**"}]}},
            {"type": "heading_2", "heading_2": {"rich_text": [{"plain_text": "Problem"}]}},
            {"type": "paragraph", "paragraph": {"rich_text": [{"plain_text": "Old invocation is clunky."}]}},
            {"type": "heading_2", "heading_2": {"rich_text": [{"plain_text": "Goal"}]}},
            {"type": "paragraph", "paragraph": {"rich_text": [{"plain_text": "Use ./agent."}]}},
            {"type": "heading_2", "heading_2": {"rich_text": [{"plain_text": "Acceptance Criteria"}]}},
            {"type": "bulleted_list_item", "bulleted_list_item": {"rich_text": [{"plain_text": "[ ] Works"}]}},
            {
                "type": "heading_2",
                "heading_2": {"rich_text": [{"plain_text": "Non-Functional Requirements"}]},
            },
            {
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"plain_text": "**Other constraints:** No regressions"}]},
            },
            {"type": "heading_2", "heading_2": {"rich_text": [{"plain_text": "Out of Scope"}]}},
            {"type": "paragraph", "paragraph": {"rich_text": [{"plain_text": "New commands"}]}},
            {"type": "heading_2", "heading_2": {"rich_text": [{"plain_text": "Open Questions"}]}},
            {"type": "paragraph", "paragraph": {"rich_text": [{"plain_text": "None"}]}},
            {"type": "heading_2", "heading_2": {"rich_text": [{"plain_text": "Technical Approach"}]}},
            {"type": "paragraph", "paragraph": {"rich_text": [{"plain_text": "Use a generated wrapper."}]}},
        ],
    ]
    backend._mock_client.get_page.return_value = {
        "properties": {"title": {"title": [{"plain_text": "Agent Entry Point"}]}}
    }

    brief = backend.read_brief("agent-entry-point")

    assert brief["status"] == "implementation-ready"
    assert "No regressions" in brief["non_functional_requirements"]
    assert brief["technical_approach"] == "Use a generated wrapper."
    assert "Use ./agent." in brief["goal"]


def test_read_brief_parses_plain_status_after_body_replacement(backend):
    backend._mock_client.get_block_children.side_effect = [
        [{"type": "child_page", "id": "brief-1", "child_page": {"title": "Agent Entry Point"}}],
        [
            {"type": "paragraph", "paragraph": {"rich_text": [{"plain_text": "Status: implementation-ready"}]}},
            {"type": "heading_2", "heading_2": {"rich_text": [{"plain_text": "Problem"}]}},
            {"type": "paragraph", "paragraph": {"rich_text": [{"plain_text": "Old invocation is clunky."}]}},
        ],
    ]
    backend._mock_client.get_page.return_value = {
        "properties": {"title": {"title": [{"plain_text": "Agent Entry Point"}]}}
    }

    brief = backend.read_brief("agent-entry-point")

    assert brief["status"] == "implementation-ready"


def test_brief_write_read_roundtrip_preserves_all_fields(backend):
    """Regression: write a brief, re-read it, verify all fields survive."""
    write_data = {
        "title": "Test Feature Brief",
        "status": "implementation-ready",
        "problem": "Something is broken.",
        "goal": "Fix it properly.",
        "acceptance_criteria": "- [ ] AC1\n- [ ] AC2",
        "non_functional_requirements": "- **Other constraints:** Preserve body updates",
        "out_of_scope": "OOS items",
        "open_questions": "All resolved.",
        "technical_approach": "### Step 1\nDo this.\n### Step 2\nDo that.",
    }

    # Write: create new page
    backend._mock_client.get_block_children.return_value = []
    backend._mock_client.create_page.return_value = {"id": "brief-roundtrip"}
    backend.write_brief("test-feature-brief", write_data)
    backend._mock_client.create_page.assert_called_once()

    # Simulate Notion API returning the content (blocks with plain_text)
    read_blocks = [
        {"type": "paragraph", "paragraph": {"rich_text": [{"plain_text": "**Status: implementation-ready**"}]}},
        {"type": "heading_2", "heading_2": {"rich_text": [{"plain_text": "Problem"}]}},
        {"type": "paragraph", "paragraph": {"rich_text": [{"plain_text": "Something is broken."}]}},
        {"type": "heading_2", "heading_2": {"rich_text": [{"plain_text": "Goal"}]}},
        {"type": "paragraph", "paragraph": {"rich_text": [{"plain_text": "Fix it properly."}]}},
        {"type": "heading_2", "heading_2": {"rich_text": [{"plain_text": "Acceptance Criteria"}]}},
        {"type": "to_do", "to_do": {"rich_text": [{"plain_text": "AC1"}], "checked": False}},
        {"type": "to_do", "to_do": {"rich_text": [{"plain_text": "AC2"}], "checked": False}},
        {"type": "heading_2", "heading_2": {"rich_text": [{"plain_text": "Non-Functional Requirements"}]}},
        {
            "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": [{"plain_text": "**Other constraints:** Preserve body updates"}]},
        },
        {"type": "heading_2", "heading_2": {"rich_text": [{"plain_text": "Out of Scope"}]}},
        {"type": "paragraph", "paragraph": {"rich_text": [{"plain_text": "OOS items"}]}},
        {"type": "heading_2", "heading_2": {"rich_text": [{"plain_text": "Open Questions"}]}},
        {"type": "paragraph", "paragraph": {"rich_text": [{"plain_text": "All resolved."}]}},
        {"type": "heading_2", "heading_2": {"rich_text": [{"plain_text": "Technical Approach"}]}},
        {"type": "heading_3", "heading_3": {"rich_text": [{"plain_text": "Step 1"}]}},
        {"type": "paragraph", "paragraph": {"rich_text": [{"plain_text": "Do this."}]}},
        {"type": "heading_3", "heading_3": {"rich_text": [{"plain_text": "Step 2"}]}},
        {"type": "paragraph", "paragraph": {"rich_text": [{"plain_text": "Do that."}]}},
    ]

    backend._mock_client.get_block_children.side_effect = [
        [{"type": "child_page", "id": "brief-roundtrip", "child_page": {"title": "Test Feature Brief"}}],
        read_blocks,
    ]
    backend._mock_client.get_page.return_value = {
        "properties": {"title": {"title": [{"plain_text": "Test Feature Brief"}]}},
        "url": "https://notion.so/brief-roundtrip",
    }

    read_data = backend.read_brief("test-feature-brief")

    assert read_data["status"] == "implementation-ready"
    assert "Something is broken" in read_data["problem"]
    assert "Fix it properly" in read_data["goal"]
    assert "AC1" in read_data["acceptance_criteria"]
    assert "Preserve body updates" in read_data["non_functional_requirements"]
    assert "OOS items" in read_data["out_of_scope"]
    assert "All resolved" in read_data["open_questions"]
    assert "Step 1" in read_data["technical_approach"]
    assert read_data["notion_id"] == "brief-roundtrip"
    assert read_data["notion_url"] == "https://notion.so/brief-roundtrip"


def test_write_brief_snapshots_existing_head_to_history_page(backend):
    old_blocks = [
        {"type": "paragraph", "id": "blk-1", "paragraph": {"rich_text": [{"plain_text": "Old."}]}}
    ]
    briefs_children = [{"type": "child_page", "id": "brief-1", "child_page": {"title": "Agent Entry Point"}}]

    def _get_block_children_history(page_id):
        if page_id == "brief-1":
            return list(old_blocks)
        return list(briefs_children)

    backend._mock_client.get_block_children.side_effect = _get_block_children_history
    backend._mock_client.get_page.return_value = {
        "properties": {"title": {"title": [{"plain_text": "Agent Entry Point"}]}},
        "url": "https://notion.so/brief-1",
    }
    backend._mock_client.create_page.side_effect = [
        {"id": "history-1"},
        {"id": "revision-1"},
    ]

    backend.write_brief(
        "agent-entry-point",
        {
            "title": "Agent Entry Point",
            "status": "implementation-ready",
            "problem": "Old invocation is clunky.",
            "goal": "Use ./agent.",
            "acceptance_criteria": "- [ ] Works",
            "_actor": "tester",
            "_change_summary": "Clarified rollout path.",
        },
    )

    first_call = backend._mock_client.create_page.call_args_list[0]
    assert first_call[0][1] == "Agent Entry Point History"
    second_call = backend._mock_client.create_page.call_args_list[1]
    assert second_call[0][1].startswith("Revision ")


def test_list_and_read_brief_revisions(backend):
    briefs_children = [{"type": "child_page", "id": "history-1", "child_page": {"title": "Agent Entry Point History"}}]
    revision_children = [{"type": "child_page", "id": "rev-1", "child_page": {"title": "Revision 20260317T120000000000Z"}}]
    revision_body = [
        {"type": "paragraph", "paragraph": {"rich_text": [{"plain_text": "**Revision ID: 20260317T120000000000Z**"}]}},
        {"type": "paragraph", "paragraph": {"rich_text": [{"plain_text": "**Captured At: 20260317T120000000000Z**"}]}},
        {"type": "paragraph", "paragraph": {"rich_text": [{"plain_text": "**Actor: tester**"}]}},
        {"type": "paragraph", "paragraph": {"rich_text": [{"plain_text": "**Change Summary: Clarified rollout path.**"}]}},
        {"type": "heading_1", "heading_1": {"rich_text": [{"plain_text": "Agent Entry Point"}]}},
        {"type": "paragraph", "paragraph": {"rich_text": [{"plain_text": "**Status: draft**"}]}},
        {"type": "heading_2", "heading_2": {"rich_text": [{"plain_text": "Problem"}]}},
        {"type": "paragraph", "paragraph": {"rich_text": [{"plain_text": "Old invocation is clunky."}]}},
    ]

    def _get_block_children(page_id):
        briefs_page = backend._briefs_page_id()
        if page_id == briefs_page:
            return list(briefs_children)
        if page_id == "history-1":
            return list(revision_children)
        if page_id == "rev-1":
            return list(revision_body)
        return []

    backend._mock_client.get_block_children.side_effect = _get_block_children
    backend._mock_client.get_page.return_value = {"url": "https://notion.so/rev-1"}

    revisions = backend.list_brief_revisions("agent-entry-point")
    assert len(revisions) == 1
    assert revisions[0]["revision_id"] == "20260317T120000000000Z"
    assert revisions[0]["actor"] == "tester"

    revision = backend.read_brief_revision(
        "agent-entry-point", "20260317T120000000000Z"
    )
    assert revision["snapshot"]["status"] == "draft"
    assert revision["notion_url"] == "https://notion.so/rev-1"


def test_find_brief_history_page_matches_existing_title_variant(backend):
    backend._mock_client.get_block_children.return_value = [
        {
            "type": "child_page",
            "id": "history-1",
            "child_page": {"title": "Architect-review Automation History"},
        }
    ]

    page_id = backend._find_brief_history_page(
        "architect-review-automation",
        "Architect-review Automation",
    )

    assert page_id == "history-1"


def test_backlog_row_with_review_verdict_and_route_state(backend):
    """Verify new workflow fields are written and read correctly."""
    backend._mock_client.query_database.side_effect = [
        [],  # No existing row (for write)
        [  # Read after write
            {
                "id": "row-1",
                "url": "https://notion.so/row-1",
                "properties": {
                    "Title": {"title": [{"plain_text": "Test Feature"}]},
                    "Type": {"select": {"name": "Feature"}},
                    "Feature Status": {"select": {"name": "review-ready"}},
                    "Priority": {"select": {"name": "High"}},
                    "Review Verdict": {"select": {"name": "accepted"}},
                    "Route State": {"select": {"name": "routed"}},
                    "Brief Link": {"url": None},
                    "Release Note Link": {"url": "https://notion.so/release-v1"},
                    "Notes": {"rich_text": [{"plain_text": "Test notes"}]},
                    "Parent": {"relation": []},
                },
            }
        ],
    ]
    backend._mock_client.create_database_page.return_value = {"id": "row-1"}

    # Write row with new fields
    backend.write_backlog_row({
        "title": "Test Feature",
        "type": "Feature",
        "status": "review-ready",
        "priority": "High",
        "review_verdict": "accepted",
        "route_state": "routed",
        "release_note_link": "https://notion.so/release-v1",
        "notes": "Test notes",
    })

    write_call = backend._mock_client.create_database_page.call_args
    props = write_call[0][1]
    assert "Review Verdict" in props
    assert "Route State" in props
    assert "Release Note Link" in props

    # Read and verify
    rows = backend.read_backlog()
    assert rows[0]["review_verdict"] == "accepted"
    assert rows[0]["route_state"] == "routed"
    assert rows[0]["release_note_link"] == "https://notion.so/release-v1"
    assert rows[0]["notion_url"] == "https://notion.so/row-1"


# --- Decisions ---


def test_read_decisions(backend):
    backend._mock_client.query_database.return_value = [
        {
            "id": "dec-1",
            "properties": {
                "Title": {"title": [{"plain_text": "Use Python"}]},
                "ID": {"rich_text": [{"plain_text": "D-001"}]},
                "Date": {"date": {"start": "2026-03-16"}},
                "Status": {"select": {"name": "accepted"}},
                "Why": {"rich_text": [{"plain_text": "Ecosystem fit"}]},
                "Alternatives Rejected": {"rich_text": [{"plain_text": "Node.js"}]},
                "Feature Link": {"url": None},
                "ADR Link": {"url": None},
            },
        }
    ]
    decisions = backend.read_decisions()
    assert len(decisions) == 1
    assert decisions[0]["id"] == "D-001"
    assert decisions[0]["why"] == "Ecosystem fit"
    assert "feature_link" in decisions[0]


def test_append_decision(backend):
    backend._mock_client.create_database_page.return_value = {"id": "new-dec"}
    backend.append_decision({
        "id": "D-002",
        "title": "Use Click",
        "date": "2026-03-16",
        "status": "accepted",
        "why": "Simple CLI",
    })
    backend._mock_client.create_database_page.assert_called_once()


# --- Backlog (unified) ---


def test_read_backlog(backend):
    backend._mock_client.query_database.return_value = [
        {
            "id": "bl-1",
            "created_time": "2026-03-19T01:02:03.000Z",
            "last_edited_time": "2026-03-20T04:05:06.000Z",
            "properties": {
                "Title": {"title": [{"plain_text": "Add email alerts"}]},
                "Type": {"select": {"name": "Task"}},
                "Task Status": {"select": {"name": "to-do"}},
                "Priority": {"select": {"name": "High"}},
                "Brief Link": {"url": None},
                "Notes": {"rich_text": [{"plain_text": ""}]},
                "Parent": {"relation": [{"id": "feature-1"}]},
                "Idea Status": {"select": None},
                "Feature Status": {"select": None},
            },
        }
    ]
    rows = backend.read_backlog()
    assert len(rows) == 1
    assert rows[0]["type"] == "Task"
    assert rows[0]["status"] == "to-do"
    assert rows[0]["parent_ids"] == ["feature-1"]
    assert rows[0]["created_at"] == "2026-03-19T01:02:03.000Z"
    assert rows[0]["updated_at"] == "2026-03-20T04:05:06.000Z"


def test_read_backlog_applies_since_filter(backend):
    backend._mock_client.query_database.return_value = []
    backend.read_backlog(since="2026-03-20")
    call_args = backend._mock_client.query_database.call_args
    assert call_args[1]["filter"]["timestamp"] == "last_edited_time"
    assert call_args[1]["filter"]["last_edited_time"]["on_or_after"] == "2026-03-20"


def test_list_children_filters_by_parent_relation(backend):
    backend._mock_client.query_database.return_value = [
        {
            "id": "feat-1",
            "url": "https://notion.so/feat-1",
            "created_time": "2026-03-19T01:02:03.000Z",
            "last_edited_time": "2026-03-20T04:05:06.000Z",
            "properties": {
                "Title": {"title": [{"plain_text": "Feature A"}]},
                "Type": {"select": {"name": "Feature"}},
                "Feature Status": {"select": {"name": "done"}},
                "Priority": {"select": {"name": "High"}},
                "Parent": {"relation": [{"id": "idea-1"}]},
                "Notes": {"rich_text": []},
                "Automation Trace": {"rich_text": []},
                "Brief Link": {"url": ""},
                "Release Note Link": {"url": ""},
                "Review Verdict": {"select": {"name": ""}},
                "Route State": {"select": {"name": ""}},
            },
        }
    ]

    children = backend.list_children("idea-1")
    call_args = backend._mock_client.query_database.call_args
    assert call_args[1]["filter"]["and"][0]["property"] == "Type"
    assert call_args[1]["filter"]["and"][0]["select"]["equals"] == "Feature"
    assert call_args[1]["filter"]["and"][1]["property"] == "Parent"
    assert call_args[1]["filter"]["and"][1]["relation"]["contains"] == "idea-1"
    assert len(children) == 1
    assert children[0]["title"] == "Feature A"
    assert children[0]["status"] == "done"


def test_write_backlog_row_creates_new(backend):
    backend._mock_client.query_database.return_value = []
    backend._mock_client.create_database_page.return_value = {"id": "new-bl"}
    backend.write_backlog_row({
        "title": "Fix format",
        "type": "Task",
        "status": "to-do",
        "priority": "Medium",
    })
    call_args = backend._mock_client.create_database_page.call_args
    props = call_args[0][1]
    assert props["Type"]["select"]["name"] == "Task"
    assert "Task Status" in props


def test_write_backlog_row_updates_existing(backend):
    backend._mock_client.query_database.return_value = [{"id": "existing-bl"}]
    backend._mock_client.update_database_page.return_value = {"id": "existing-bl"}
    backend.write_backlog_row({
        "title": "Add email alerts",
        "type": "Task",
        "status": "in-progress",
        "priority": "High",
    })
    backend._mock_client.update_database_page.assert_called_once()


def test_write_backlog_row_updates_existing_by_notion_id_without_query(backend):
    backend._mock_client.update_database_page.return_value = {"id": "existing-bl"}
    backend.write_backlog_row({
        "title": "Add email alerts",
        "type": "Task",
        "status": "in-progress",
        "priority": "High",
        "notion_id": "existing-bl",
    })
    backend._mock_client.query_database.assert_not_called()
    backend._mock_client.update_database_page.assert_called_once()


def test_write_backlog_row_with_parent(backend):
    backend._mock_client.query_database.return_value = []
    backend._mock_client.create_database_page.return_value = {"id": "new-bl"}
    backend.write_backlog_row({
        "title": "Build feature",
        "type": "Feature",
        "status": "draft",
        "priority": "High",
        "parent_ids": ["idea-1"],
    })
    call_args = backend._mock_client.create_database_page.call_args
    props = call_args[0][1]
    assert props["Parent"]["relation"] == [{"id": "idea-1"}]


# --- Status helpers ---


def test_status_key_for_type():
    assert NotionBackend._status_key_for_type("Idea") == "Idea Status"
    assert NotionBackend._status_key_for_type("Feature") == "Feature Status"
    assert NotionBackend._status_key_for_type("Task") == "Task Status"


# --- Blocks conversion ---


def test_blocks_to_markdown():
    blocks = [
        {"type": "heading_1", "heading_1": {"rich_text": [{"plain_text": "Title"}]}},
        {"type": "paragraph", "paragraph": {"rich_text": [{"plain_text": "Body text."}]}},
        {"type": "bulleted_list_item", "bulleted_list_item": {"rich_text": [{"plain_text": "Item"}]}},
        {"type": "to_do", "to_do": {"rich_text": [{"plain_text": "Task"}], "checked": True}},
        {"type": "numbered_list_item", "numbered_list_item": {"rich_text": [{"plain_text": "Step"}]}},
    ]
    md = NotionBackend._blocks_to_markdown(blocks)
    assert "# Title" in md
    assert "Body text." in md
    assert "- Item" in md
    assert "- [x] Task" in md
    assert "1. Step" in md


def test_blocks_to_markdown_preserves_annotations_and_dividers():
    blocks = [
        {
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {"plain_text": "Status: draft", "annotations": {"bold": True}},
                    {"plain_text": " ", "annotations": {}},
                    {"plain_text": "needs review", "annotations": {"italic": True}},
                ]
            },
        },
        {"type": "divider", "divider": {}},
        {"type": "paragraph", "paragraph": {"rich_text": []}},
    ]

    md = NotionBackend._blocks_to_markdown(blocks)

    assert "**Status: draft**" in md
    assert "*needs review*" in md
    assert "---" in md
    assert "\n\n" in md


def test_brief_block_roundtrip_preserves_all_sections():
    write_data = {
        "title": "Brief Write Corruption",
        "status": "implementation-ready",
        "problem": "Problem line one.\n\nProblem line two.",
        "goal": "Keep content stable.",
        "acceptance_criteria": "- [ ] First\n- [x] Second",
        "non_functional_requirements": "- **Constraint:** No corruption",
        "out_of_scope": "No extra markdown features.",
        "open_questions": "None",
        "technical_approach": "### Step 1\nDo this.\n\n---\n\n### Step 2\nDo that.",
    }

    source = render_brief_markdown(
        "brief-write-corruption",
        write_data,
        include_title=False,
    ).rstrip()
    blocks = NotionProvisioner._markdown_to_blocks(source)
    markdown = NotionBackend._blocks_to_markdown(blocks)
    parsed = parse_brief_sections(markdown)

    expected = {
        "problem": write_data["problem"],
        "goal": write_data["goal"],
        "acceptance_criteria": write_data["acceptance_criteria"],
        "non_functional_requirements": write_data["non_functional_requirements"],
        "out_of_scope": write_data["out_of_scope"],
        "open_questions": write_data["open_questions"],
        "technical_approach": write_data["technical_approach"],
    }
    assert parsed == expected


def test_write_brief_merges_existing_fields_on_partial_update(backend):
    backend._find_brief_page = MagicMock(return_value="brief-1")
    backend._store_brief_revision = MagicMock()
    backend._replace_page_body = MagicMock()
    backend._mock_client.update_page.return_value = {"id": "brief-1"}
    backend.read_brief = MagicMock(
        return_value={
            "name": "brief-write-corruption",
            "title": "Brief Write Corruption",
            "status": "implementation-ready",
            "problem": "Existing problem",
            "goal": "Existing goal",
            "acceptance_criteria": "- [ ] Existing AC",
            "non_functional_requirements": "Existing NFR",
            "out_of_scope": "Existing OOS",
            "open_questions": "Existing OQ",
            "technical_approach": "Existing TA",
        }
    )

    with patch(
        "src.integrations.notion.provisioner.NotionProvisioner._markdown_to_blocks",
        return_value=[{"type": "paragraph", "paragraph": {"rich_text": []}}],
    ) as mocked_to_blocks:
        backend.write_brief(
            "brief-write-corruption",
            {
                "title": "Brief Write Corruption",
                "status": "implementation-ready",
                "goal": "Updated goal",
                "_actor": "tester",
            },
        )

    body = mocked_to_blocks.call_args[0][0]
    assert "## Problem\nExisting problem" in body
    assert "## Goal\nUpdated goal" in body
    assert "## Technical Approach\nExisting TA" in body

# --- Release Notes ---


def test_list_release_notes(backend):
    backend._mock_client.get_block_children.return_value = [
        {"type": "child_page", "id": "rn-1", "child_page": {"title": "v0.1.0 Release Notes"}},
        {"type": "child_page", "id": "rn-2", "child_page": {"title": "v0.2.0 Release Notes"}},
        {"type": "child_page", "id": "p1", "child_page": {"title": "Notifications"}},
    ]
    notes = backend.list_release_notes()
    assert len(notes) == 2
    assert notes[0]["version"] == "v0.1.0"
    assert notes[1]["version"] == "v0.2.0"
    assert notes[0]["notion_id"] == "rn-1"
    backend._mock_client.get_block_children.assert_called_once_with("page-release-notes")


def test_read_release_note(backend):
    # First call: find page via get_block_children on parent
    # Second call: get blocks of the release note page
    backend._mock_client.get_block_children.side_effect = [
        [{"type": "child_page", "id": "rn-1", "child_page": {"title": "v0.1.0 Release Notes"}}],
        [{"type": "paragraph", "paragraph": {"rich_text": [{"plain_text": "Initial release."}]}}],
    ]
    note = backend.read_release_note("v0.1.0")
    assert note["version"] == "v0.1.0"
    assert "Initial release" in note["content"]
    assert note["notion_id"] == "rn-1"
    assert backend._mock_client.get_block_children.call_args_list[0][0][0] == "page-release-notes"


def test_read_release_note_not_found(backend):
    backend._mock_client.get_block_children.return_value = []
    with pytest.raises(KeyError, match="Release note not found"):
        backend.read_release_note("v99.0.0")


def test_write_release_note_creates_new(backend):
    # _find_release_note_page returns None (no existing page)
    backend._mock_client.get_block_children.return_value = []
    backend._mock_client.create_page.return_value = {"id": "new-rn"}
    # _ensure_readme_release_link: readme blocks (heading not found, then re-fetch)
    backend._mock_client.get_block_children.side_effect = [
        [],  # _find_release_note_page
        [],  # _ensure_readme_release_link: initial fetch
        [{"type": "heading_2", "id": "h2-1", "heading_2": {"rich_text": [{"plain_text": "Release Notes"}]}}],  # re-fetch after heading append
    ]
    backend._mock_client.append_block_children.return_value = {}

    backend.write_release_note("v0.5.0", "# v0.5.0\n\nNew stuff.\n")

    backend._mock_client.create_page.assert_called_once()
    call_args = backend._mock_client.create_page.call_args
    assert call_args[0][0] == "page-release-notes"
    assert "v0.5.0 Release Notes" in call_args[0][1]


def test_write_release_note_updates_existing(backend):
    old_blocks = [
        {"type": "paragraph", "id": "blk-1", "paragraph": {"rich_text": [{"plain_text": "Old."}]}},
    ]
    backend._mock_client.get_block_children.side_effect = [
        [{"type": "child_page", "id": "rn-1", "child_page": {"title": "v0.5.0 Release Notes"}}],  # _find
        old_blocks,  # get old blocks for deletion
        [],  # _ensure_readme_release_link: readme blocks
        [{"type": "heading_2", "id": "h2-1", "heading_2": {"rich_text": [{"plain_text": "Release Notes"}]}}],  # re-fetch
    ]
    backend._mock_client.delete_block.return_value = {}
    backend._mock_client.append_block_children.return_value = {}

    backend.write_release_note("v0.5.0", "Updated content.\n")

    backend._mock_client.delete_block.assert_called_once_with("blk-1")
    # create_page should NOT be called for updates
    backend._mock_client.create_page.assert_not_called()


def test_write_release_note_skips_archived_existing_blocks(backend):
    old_blocks = [
        {
            "type": "paragraph",
            "id": "blk-archived",
            "archived": True,
            "paragraph": {"rich_text": [{"plain_text": "Old archived."}]},
        },
        {
            "type": "paragraph",
            "id": "blk-active",
            "paragraph": {"rich_text": [{"plain_text": "Old active."}]},
        },
    ]
    backend._mock_client.get_block_children.side_effect = [
        [{"type": "child_page", "id": "rn-1", "child_page": {"title": "v0.5.0 Release Notes"}}],
        old_blocks,
        [],
        [{"type": "heading_2", "id": "h2-1", "heading_2": {"rich_text": [{"plain_text": "Release Notes"}]}}],
    ]
    backend._mock_client.delete_block.return_value = {}
    backend._mock_client.append_block_children.return_value = {}

    backend.write_release_note("v0.5.0", "Updated content.\n")

    backend._mock_client.delete_block.assert_called_once_with("blk-active")
    backend._mock_client.create_page.assert_not_called()


def test_ensure_readme_release_link_deduplicates(backend):
    """If a bullet for the version already exists, don't add another."""
    backend._mock_client.get_block_children.side_effect = [
        [],  # _find_release_note_page (no existing page)
        # _ensure_readme_release_link: readme has heading + existing bullet
        [
            {"type": "heading_2", "id": "h2-1", "heading_2": {"rich_text": [{"plain_text": "Release Notes"}]}},
            {"type": "bulleted_list_item", "id": "b1", "bulleted_list_item": {"rich_text": [{"plain_text": "v0.5.0 Release Notes"}]}},
        ],
    ]
    backend._mock_client.create_page.return_value = {"id": "new-rn"}
    backend._mock_client.append_block_children.return_value = {}

    backend.write_release_note("v0.5.0", "Content.\n")

    # append_block_children should NOT be called for the bullet (only for page content if any)
    # The create_page call creates the page with children inline, so no extra append for bullet
    for call in backend._mock_client.append_block_children.call_args_list:
        args = call[0]
        if args[0] == "page-readme":
            # Should not be called to add a bullet since v0.5.0 already exists
            children = args[1]
            for child in children:
                assert child.get("type") != "bulleted_list_item"
