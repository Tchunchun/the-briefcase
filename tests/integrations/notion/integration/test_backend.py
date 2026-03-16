"""Tests for NotionBackend (ArtifactStore + SyncableStore)."""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from src.core.storage.config import NotionConfig
from src.core.storage.protocol import ArtifactStore, SyncableStore
from src.integrations.notion.backend import NotionBackend


@pytest.fixture
def notion_config():
    return NotionConfig(
        parent_page_id="parent-1",
        parent_page_url="https://notion.so/parent-1",
        databases={
            "intake": "db-intake",
            "briefs": "db-briefs",
            "decisions": "db-decisions",
            "backlog": "db-backlog",
            "templates": "db-templates",
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


# --- Inbox ---


def test_read_inbox(backend):
    backend._mock_client.query_database.return_value = [
        {
            "id": "row-1",
            "properties": {
                "Title": {"title": [{"plain_text": "Add notification system"}]},
                "Type": {"select": {"name": "idea"}},
                "Status": {"select": {"name": "new"}},
            },
        }
    ]
    entries = backend.read_inbox()
    assert len(entries) == 1
    assert entries[0]["text"] == "Add notification system"
    assert entries[0]["type"] == "idea"


def test_append_inbox(backend):
    backend._mock_client.create_database_page.return_value = {"id": "new-1"}
    backend.append_inbox({"text": "New idea", "type": "idea"})
    backend._mock_client.create_database_page.assert_called_once()


# --- Briefs ---


def test_read_brief(backend):
    backend._mock_client.query_database.return_value = [
        {
            "id": "brief-page-1",
            "properties": {
                "Title": {"title": [{"plain_text": "Notifications"}]},
                "Brief Name": {"rich_text": [{"plain_text": "notifications"}]},
                "Status": {"select": {"name": "draft"}},
            },
        }
    ]
    backend._mock_client.get_block_children.return_value = [
        {"type": "heading_2", "heading_2": {"rich_text": [{"plain_text": "Problem"}]}},
        {"type": "paragraph", "paragraph": {"rich_text": [{"plain_text": "Users miss updates."}]}},
        {"type": "heading_2", "heading_2": {"rich_text": [{"plain_text": "Goal"}]}},
        {"type": "paragraph", "paragraph": {"rich_text": [{"plain_text": "Send email alerts."}]}},
    ]

    brief = backend.read_brief("notifications")
    assert brief["status"] == "draft"
    assert "Users miss updates" in brief["problem"]


def test_read_brief_not_found(backend):
    backend._mock_client.query_database.return_value = []
    with pytest.raises(KeyError, match="Brief not found"):
        backend.read_brief("nonexistent")


def test_list_briefs(backend):
    backend._mock_client.query_database.return_value = [
        {
            "id": "b1",
            "properties": {
                "Title": {"title": [{"plain_text": "Notifications"}]},
                "Brief Name": {"rich_text": [{"plain_text": "notifications"}]},
                "Status": {"select": {"name": "draft"}},
            },
        }
    ]
    briefs = backend.list_briefs()
    assert len(briefs) == 1
    assert briefs[0]["name"] == "notifications"


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
                "ADR Link": {"url": None},
            },
        }
    ]
    decisions = backend.read_decisions()
    assert len(decisions) == 1
    assert decisions[0]["id"] == "D-001"
    assert decisions[0]["why"] == "Ecosystem fit"


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


# --- Backlog ---


def test_read_backlog(backend):
    backend._mock_client.query_database.return_value = [
        {
            "id": "bl-1",
            "properties": {
                "Title": {"title": [{"plain_text": "Add email alerts"}]},
                "ID": {"rich_text": [{"plain_text": "T-001"}]},
                "Type": {"select": {"name": "Feature"}},
                "Use Case": {"rich_text": [{"plain_text": "User needs alerts"}]},
                "Feature": {"rich_text": [{"plain_text": "notifications"}]},
                "Priority": {"select": {"name": "High"}},
                "Status": {"select": {"name": "To Do"}},
                "Notes": {"rich_text": [{"plain_text": ""}]},
            },
        }
    ]
    rows = backend.read_backlog()
    assert len(rows) == 1
    assert rows[0]["id"] == "T-001"
    assert rows[0]["status"] == "To Do"


def test_write_backlog_row_creates_new(backend):
    backend._mock_client.query_database.return_value = []
    backend._mock_client.create_database_page.return_value = {"id": "new-bl"}
    backend.write_backlog_row({
        "id": "T-002",
        "type": "Bug",
        "feature": "notifications",
        "title": "Fix format",
        "priority": "Medium",
        "status": "To Do",
    })
    backend._mock_client.create_database_page.assert_called_once()


def test_write_backlog_row_updates_existing(backend):
    backend._mock_client.query_database.return_value = [{"id": "existing-bl"}]
    backend._mock_client.update_database_page.return_value = {"id": "existing-bl"}
    backend.write_backlog_row({
        "id": "T-001",
        "type": "Feature",
        "feature": "notifications",
        "title": "Add email alerts",
        "priority": "High",
        "status": "In Progress",
    })
    backend._mock_client.update_database_page.assert_called_once()


# --- Sync to local ---


def test_sync_to_local(backend, tmp_path):
    # Set up local project structure
    plan_dir = tmp_path / "docs" / "plan"
    plan_dir.mkdir(parents=True)
    inbox_path = plan_dir / "_inbox.md"
    inbox_path.write_text("# Inbox\n\n## Entries\n\n")

    project_dir = tmp_path / "_project"
    project_dir.mkdir()
    (project_dir / "decisions.md").write_text("# Decisions\n\n| ID | Date |\n|---|---|\n")

    # Mock Notion data
    backend._mock_client.query_database.side_effect = [
        # read_inbox call
        [
            {
                "id": "r1",
                "properties": {
                    "Title": {"title": [{"plain_text": "New idea"}]},
                    "Type": {"select": {"name": "idea"}},
                    "Status": {"select": {"name": "new"}},
                },
            }
        ],
        # list_briefs call
        [],
        # read_decisions call
        [
            {
                "id": "d1",
                "properties": {
                    "Title": {"title": [{"plain_text": "Use Python"}]},
                    "ID": {"rich_text": [{"plain_text": "D-001"}]},
                    "Date": {"date": {"start": "2026-03-16"}},
                    "Status": {"select": {"name": "accepted"}},
                    "Why": {"rich_text": [{"plain_text": "Ecosystem fit"}]},
                    "Alternatives Rejected": {"rich_text": [{"plain_text": "Node.js"}]},
                    "ADR Link": {"url": None},
                },
            }
        ],
    ]

    result = backend.sync_to_local(str(tmp_path))
    assert result["fetched"] >= 2
    assert result["created"] >= 1

    # Verify inbox was written
    inbox_content = inbox_path.read_text()
    assert "New idea" in inbox_content


def test_sync_to_local_dry_run(backend, tmp_path):
    plan_dir = tmp_path / "docs" / "plan"
    plan_dir.mkdir(parents=True)
    inbox = plan_dir / "_inbox.md"
    inbox.write_text("# Inbox\n")

    project_dir = tmp_path / "_project"
    project_dir.mkdir()
    (project_dir / "decisions.md").write_text("")

    backend._mock_client.query_database.side_effect = [
        [{"id": "r1", "properties": {
            "Title": {"title": [{"plain_text": "Dry run idea"}]},
            "Type": {"select": {"name": "idea"}},
            "Status": {"select": {"name": "new"}},
        }}],
        [],
        [],
    ]

    result = backend.sync_to_local(str(tmp_path), dry_run=True)
    assert "Dry run idea" not in inbox.read_text()


# --- Blocks conversion ---


def test_blocks_to_markdown():
    blocks = [
        {"type": "heading_1", "heading_1": {"rich_text": [{"plain_text": "Title"}]}},
        {"type": "paragraph", "paragraph": {"rich_text": [{"plain_text": "Body text."}]}},
        {"type": "bulleted_list_item", "bulleted_list_item": {"rich_text": [{"plain_text": "Item"}]}},
        {"type": "to_do", "to_do": {"rich_text": [{"plain_text": "Task"}], "checked": True}},
    ]
    md = NotionBackend._blocks_to_markdown(blocks)
    assert "# Title" in md
    assert "Body text." in md
    assert "- Item" in md
    assert "- [x] Task" in md
