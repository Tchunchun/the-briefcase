"""Tests for Notion schemas and provisioner."""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from src.integrations.notion.schemas import (
    DATABASE_REGISTRY,
    INTAKE_SCHEMA,
    BRIEFS_SCHEMA,
    DECISIONS_SCHEMA,
    BACKLOG_SCHEMA,
    TEMPLATES_SCHEMA,
)
from src.integrations.notion.provisioner import NotionProvisioner


# --- Schema tests ---


def test_registry_has_five_databases():
    assert len(DATABASE_REGISTRY) == 5
    assert set(DATABASE_REGISTRY.keys()) == {
        "intake", "briefs", "decisions", "backlog", "templates"
    }


def test_intake_schema_has_required_properties():
    assert "Title" in INTAKE_SCHEMA
    assert "Type" in INTAKE_SCHEMA
    assert "Status" in INTAKE_SCHEMA


def test_briefs_schema_has_required_properties():
    assert "Title" in BRIEFS_SCHEMA
    assert "Brief Name" in BRIEFS_SCHEMA
    assert "Status" in BRIEFS_SCHEMA


def test_decisions_schema_has_required_properties():
    assert "Title" in DECISIONS_SCHEMA
    assert "ID" in DECISIONS_SCHEMA
    assert "Date" in DECISIONS_SCHEMA
    assert "Status" in DECISIONS_SCHEMA
    assert "Why" in DECISIONS_SCHEMA


def test_backlog_schema_has_required_properties():
    assert "Title" in BACKLOG_SCHEMA
    assert "ID" in BACKLOG_SCHEMA
    assert "Type" in BACKLOG_SCHEMA
    assert "Priority" in BACKLOG_SCHEMA
    assert "Status" in BACKLOG_SCHEMA


def test_templates_schema_has_required_properties():
    assert "Name" in TEMPLATES_SCHEMA
    assert "Version" in TEMPLATES_SCHEMA
    assert "Last Seeded" in TEMPLATES_SCHEMA


def test_intake_type_options():
    opts = INTAKE_SCHEMA["Type"]["select"]["options"]
    names = [o["name"] for o in opts]
    assert "idea" in names
    assert "bug" in names
    assert "tech-debt" in names


# --- Provisioner tests ---


@pytest.fixture
def mock_client():
    client = MagicMock()
    # Default: no existing databases
    client.get_block_children.return_value = []
    # Each create_database returns a unique ID
    db_counter = iter(range(1, 100))
    client.create_database.side_effect = lambda *a, **kw: {"id": f"db-{next(db_counter)}"}
    return client


@pytest.fixture
def provisioner(mock_client):
    return NotionProvisioner(mock_client)


def test_provision_creates_all_databases(provisioner, mock_client):
    db_ids, result = provisioner.provision("parent-page-id")

    assert len(db_ids) == 5
    assert mock_client.create_database.call_count == 5
    assert result.success
    assert len(result.databases_created) == 5
    assert len(result.databases_found) == 0


def test_provision_is_idempotent(provisioner, mock_client):
    # Simulate existing databases
    mock_client.get_block_children.return_value = [
        {"type": "child_database", "id": "existing-db-1", "child_database": {"title": "Intake"}},
        {"type": "child_database", "id": "existing-db-2", "child_database": {"title": "Feature Briefs"}},
        {"type": "child_database", "id": "existing-db-3", "child_database": {"title": "Decisions"}},
        {"type": "child_database", "id": "existing-db-4", "child_database": {"title": "Backlog"}},
        {"type": "child_database", "id": "existing-db-5", "child_database": {"title": "Templates"}},
    ]

    db_ids, result = provisioner.provision("parent-page-id")

    assert db_ids["intake"] == "existing-db-1"
    assert db_ids["templates"] == "existing-db-5"
    assert mock_client.create_database.call_count == 0
    assert len(result.databases_found) == 5
    assert len(result.databases_created) == 0


def test_provision_creates_only_missing_databases(provisioner, mock_client):
    mock_client.get_block_children.return_value = [
        {"type": "child_database", "id": "existing-1", "child_database": {"title": "Intake"}},
        {"type": "child_database", "id": "existing-2", "child_database": {"title": "Backlog"}},
    ]

    db_ids, result = provisioner.provision("parent-page-id")

    assert db_ids["intake"] == "existing-1"
    assert db_ids["backlog"] == "existing-2"
    assert mock_client.create_database.call_count == 3  # briefs, decisions, templates
    assert len(result.databases_found) == 2
    assert len(result.databases_created) == 3


def test_provision_seeds_templates(provisioner, mock_client, tmp_path):
    # Create a minimal template directory
    template_dir = tmp_path / "template"
    template_dir.mkdir()
    (template_dir / "brief.md").write_text("# Brief (v3)\nTemplate content")
    (template_dir / "tasks.md").write_text("# Tasks (v2)\nTask template")

    # Mock query_database (no existing templates)
    mock_client.query_database.return_value = []
    mock_client.pages.create = MagicMock(return_value={"id": "tpl-page-1"})
    mock_client.create_database_page.return_value = {"id": "tpl-1"}

    db_ids, result = provisioner.provision(
        "parent-page-id", template_dir=template_dir
    )

    assert len(result.templates_seeded) == 2
    assert "brief" in result.templates_seeded
    assert "tasks" in result.templates_seeded


def test_provision_skips_already_seeded_templates(provisioner, mock_client, tmp_path):
    template_dir = tmp_path / "template"
    template_dir.mkdir()
    (template_dir / "brief.md").write_text("# Brief (v3)\ncontent")

    # Mock: "brief" already exists in Notion templates DB
    mock_client.query_database.return_value = [
        {
            "properties": {
                "Name": {"title": [{"plain_text": "brief"}]}
            }
        }
    ]

    db_ids, result = provisioner.provision(
        "parent-page-id", template_dir=template_dir
    )

    assert "brief" not in result.templates_seeded


def test_provision_reports_errors(provisioner, mock_client):
    mock_client.create_database.side_effect = Exception("API error")

    db_ids, result = provisioner.provision("parent-page-id")

    assert not result.success
    assert len(result.errors) == 5


def test_provision_result_summary(provisioner, mock_client):
    db_ids, result = provisioner.provision("parent-page-id")
    summary = result.summary()

    assert summary["databases_created"] == 5
    assert summary["databases_found_existing"] == 0
    assert summary["errors"] == []


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
    assert blocks[5]["type"] == "paragraph"
