"""Tests for Notion schemas and provisioner (v2 unified Backlog)."""

import pytest
from unittest.mock import MagicMock, patch, call
from pathlib import Path

from src.integrations.notion.schemas import (
    DATABASE_REGISTRY,
    BACKLOG_SCHEMA,
    DECISIONS_SCHEMA,
)
from src.integrations.notion.provisioner import NotionProvisioner


# --- Schema tests ---


def test_registry_has_two_databases():
    assert len(DATABASE_REGISTRY) == 2
    assert set(DATABASE_REGISTRY.keys()) == {"backlog", "decisions"}


def test_backlog_schema_has_required_properties():
    assert "Title" in BACKLOG_SCHEMA
    assert "Type" in BACKLOG_SCHEMA
    assert "Idea Status" in BACKLOG_SCHEMA
    assert "Feature Status" in BACKLOG_SCHEMA
    assert "Task Status" in BACKLOG_SCHEMA
    assert "Priority" in BACKLOG_SCHEMA
    assert "Brief Link" in BACKLOG_SCHEMA
    assert "Notes" in BACKLOG_SCHEMA


def test_backlog_type_options():
    opts = BACKLOG_SCHEMA["Type"]["select"]["options"]
    names = [o["name"] for o in opts]
    assert names == ["Idea", "Feature", "Task"]


def test_backlog_idea_status_options():
    opts = BACKLOG_SCHEMA["Idea Status"]["select"]["options"]
    names = [o["name"] for o in opts]
    assert names == ["new", "exploring", "promoted", "rejected", "shipped"]


def test_backlog_feature_status_options():
    opts = BACKLOG_SCHEMA["Feature Status"]["select"]["options"]
    names = [o["name"] for o in opts]
    assert names == ["draft", "architect-review", "implementation-ready", "done"]


def test_backlog_task_status_options():
    opts = BACKLOG_SCHEMA["Task Status"]["select"]["options"]
    names = [o["name"] for o in opts]
    assert names == ["to-do", "in-progress", "blocked", "done"]


def test_decisions_schema_has_required_properties():
    assert "Title" in DECISIONS_SCHEMA
    assert "ID" in DECISIONS_SCHEMA
    assert "Date" in DECISIONS_SCHEMA
    assert "Status" in DECISIONS_SCHEMA
    assert "Why" in DECISIONS_SCHEMA
    assert "Feature Link" in DECISIONS_SCHEMA
    assert "ADR Link" in DECISIONS_SCHEMA


# --- Provisioner tests ---


@pytest.fixture
def mock_client():
    client = MagicMock()
    client.get_block_children.return_value = []
    db_counter = iter(range(1, 100))
    client.create_database.side_effect = (
        lambda *a, **kw: {"id": f"db-{next(db_counter)}"}
    )
    client.update_database.return_value = {}
    client.create_page.side_effect = (
        lambda pid, title, **kw: {"id": f"page-{title.lower().replace(' ', '-')}"}
    )
    return client


@pytest.fixture
def provisioner(mock_client):
    return NotionProvisioner(mock_client)


def test_provision_creates_databases_and_pages(provisioner, mock_client):
    resource_ids, result = provisioner.provision("parent-page-id")

    assert "backlog" in resource_ids
    assert "decisions" in resource_ids
    assert "readme" in resource_ids
    assert "templates" in resource_ids
    assert mock_client.create_database.call_count == 2
    assert mock_client.create_page.call_count == 2  # README + Templates
    assert result.success
    assert len(result.databases_created) == 2
    assert len(result.pages_created) == 2


def test_provision_adds_self_relation(provisioner, mock_client):
    resource_ids, result = provisioner.provision("parent-page-id")

    mock_client.update_database.assert_called_once()
    call_args = mock_client.update_database.call_args
    backlog_id = resource_ids["backlog"]
    assert call_args[0][0] == backlog_id
    props = call_args[1].get("properties") or call_args[0][1]
    assert "Parent" in props
    assert props["Parent"]["relation"]["database_id"] == backlog_id


def test_provision_is_idempotent(provisioner, mock_client):
    mock_client.get_block_children.return_value = [
        {"type": "child_database", "id": "ex-db-1", "child_database": {"title": "Backlog"}},
        {"type": "child_database", "id": "ex-db-2", "child_database": {"title": "Decisions"}},
        {"type": "child_page", "id": "ex-p-1", "child_page": {"title": "README"}},
        {"type": "child_page", "id": "ex-p-2", "child_page": {"title": "Templates"}},
    ]

    resource_ids, result = provisioner.provision("parent-page-id")

    assert resource_ids["backlog"] == "ex-db-1"
    assert resource_ids["decisions"] == "ex-db-2"
    assert resource_ids["readme"] == "ex-p-1"
    assert resource_ids["templates"] == "ex-p-2"
    assert mock_client.create_database.call_count == 0
    assert mock_client.create_page.call_count == 0
    # update_database may be called for schema upgrades on found DBs
    assert len(result.databases_found) == 2


def test_provision_creates_only_missing(provisioner, mock_client):
    mock_client.get_block_children.return_value = [
        {"type": "child_database", "id": "ex-1", "child_database": {"title": "Backlog"}},
    ]

    resource_ids, result = provisioner.provision("parent-page-id")

    assert resource_ids["backlog"] == "ex-1"
    assert mock_client.create_database.call_count == 1  # decisions only
    assert len(result.databases_found) == 1
    assert len(result.databases_created) == 1


def test_provision_seeds_templates(provisioner, mock_client, tmp_path):
    template_dir = tmp_path / "template"
    template_dir.mkdir()
    (template_dir / "brief.md").write_text("# Brief (v3)\nTemplate content")
    (template_dir / "tasks.md").write_text("# Tasks (v2)\nTask template")

    resource_ids, result = provisioner.provision(
        "parent-page-id", template_dir=template_dir
    )

    assert len(result.templates_seeded) == 2
    assert "brief" in result.templates_seeded
    assert "tasks" in result.templates_seeded


def test_provision_reports_errors(provisioner, mock_client):
    mock_client.create_database.side_effect = Exception("API error")

    resource_ids, result = provisioner.provision("parent-page-id")

    assert not result.success
    assert len(result.errors) >= 2  # Both DB creations fail


def test_markdown_to_blocks():
    content = "# Heading\n\n## Subheading\n\n- Bullet\n- [ ] Todo\n- [x] Done\n\nParagraph"
    blocks = NotionProvisioner._markdown_to_blocks(content)

    assert blocks[0]["type"] == "heading_1"
    assert blocks[1]["type"] == "heading_2"
    assert blocks[2]["type"] == "bulleted_list_item"
    assert blocks[3]["type"] == "to_do"
    assert blocks[3]["to_do"]["checked"] is False
    assert blocks[4]["type"] == "to_do"
    assert blocks[4]["to_do"]["checked"] is True
    assert blocks[3]["to_do"]["checked"] is False
    assert blocks[4]["type"] == "to_do"
    assert blocks[4]["to_do"]["checked"] is True
    assert blocks[5]["type"] == "paragraph"
