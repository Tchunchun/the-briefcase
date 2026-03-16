"""Tests for NotionBackend v2 (unified Backlog, standalone briefs)."""

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
            "backlog": "db-backlog",
            "decisions": "db-decisions",
            "readme": "page-readme",
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
            "properties": {
                "Title": {"title": [{"plain_text": "Add notification system"}]},
                "Type": {"select": {"name": "Idea"}},
                "Idea Status": {"select": {"name": "new"}},
            },
        }
    ]
    entries = backend.read_inbox()
    assert len(entries) == 1
    assert entries[0]["text"] == "Add notification system"
    assert entries[0]["type"] == "idea"
    assert entries[0]["status"] == "new"

    # Verify query used Type=Idea filter
    call_args = backend._mock_client.query_database.call_args
    assert call_args[0][0] == "db-backlog"
    filt = call_args[1].get("filter") or call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get("filter")
    assert filt["property"] == "Type"


def test_append_inbox(backend):
    backend._mock_client.create_database_page.return_value = {"id": "new-1"}
    backend.append_inbox({"text": "New idea", "type": "idea"})
    call_args = backend._mock_client.create_database_page.call_args
    props = call_args[0][1]
    assert props["Type"]["select"]["name"] == "Idea"
    assert props["Idea Status"]["select"]["name"] == "new"


# --- Briefs (standalone pages under project root) ---


def test_list_briefs(backend):
    parent_children = [
        {"type": "child_page", "id": "p1", "child_page": {"title": "Notifications"}},
        {"type": "child_page", "id": "p2", "child_page": {"title": "README"}},
        {"type": "child_page", "id": "p3", "child_page": {"title": "Templates"}},
        {"type": "child_database", "id": "db1", "child_database": {"title": "Backlog"}},
    ]
    brief_blocks = [
        {"type": "paragraph", "paragraph": {"rich_text": [{"plain_text": "**Status: draft**"}]}},
    ]

    # Use side_effect list: first call = parent children, subsequent calls = brief blocks
    backend._client.get_block_children = MagicMock(
        side_effect=[parent_children, brief_blocks]
    )

    briefs = backend.list_briefs()
    assert len(briefs) == 1
    assert briefs[0]["name"] == "notifications"
    assert briefs[0]["status"] == "draft"


def test_read_brief_not_found(backend):
    backend._mock_client.get_block_children.return_value = []
    with pytest.raises(KeyError, match="Brief not found"):
        backend.read_brief("nonexistent")


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


