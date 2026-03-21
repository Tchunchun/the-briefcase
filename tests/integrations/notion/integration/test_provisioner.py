"""Tests for Notion schemas and provisioner (v2 unified Backlog)."""

import pytest
from unittest.mock import MagicMock

from src.integrations.notion.schemas import (
    DATABASE_REGISTRY,
    BACKLOG_SCHEMA,
    DECISIONS_SCHEMA,
)
from src.integrations.notion.provisioner import NotionProvisioner


# --- Schema tests ---


def test_registry_has_three_databases():
    assert len(DATABASE_REGISTRY) == 3
    assert set(DATABASE_REGISTRY.keys()) == {"backlog", "decisions", "briefs_db"}


def test_backlog_schema_has_required_properties():
    assert "Title" in BACKLOG_SCHEMA
    assert "Type" in BACKLOG_SCHEMA
    assert "Idea Status" in BACKLOG_SCHEMA
    assert "Feature Status" in BACKLOG_SCHEMA
    assert "Task Status" in BACKLOG_SCHEMA
    assert "Priority" in BACKLOG_SCHEMA
    assert "Brief Link" in BACKLOG_SCHEMA
    assert "Notes" in BACKLOG_SCHEMA
    assert "Automation Trace" in BACKLOG_SCHEMA


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
    assert names == ["draft", "architect-review", "implementation-ready", "in-progress",
                     "review-ready", "review-accepted", "done", "shipped"]


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
    client.get_page.return_value = {"id": "parent-page-id", "object": "page"}
    client.get_block_children.return_value = []
    db_counter = iter(range(1, 100))
    client.create_database.side_effect = (
        lambda *a, **kw: {"id": f"db-{next(db_counter)}"}
    )
    client.update_database.return_value = {}
    client.create_page.side_effect = (
        lambda pid, title, **kw: {"id": f"page-{title.lower().replace(' ', '-')}"}
    )
    client.append_block_children.return_value = {}
    return client


@pytest.fixture
def provisioner(mock_client):
    return NotionProvisioner(mock_client)


def test_provision_creates_databases_and_pages(provisioner, mock_client):
    resource_ids, result = provisioner.provision("parent-page-id")

    assert "backlog" in resource_ids
    assert "decisions" in resource_ids
    assert "briefs_db" in resource_ids
    assert "readme" in resource_ids
    assert "templates" in resource_ids
    assert "release_notes" in resource_ids
    assert mock_client.create_database.call_count == 3  # Backlog + Decisions + Briefs
    assert mock_client.create_page.call_count == 3  # README + Templates + Release Notes
    assert result.success
    assert len(result.databases_created) == 3
    assert len(result.pages_created) == 3
    # Section labels added on fresh provision
    assert mock_client.append_block_children.call_count == 3  # "Backlog", spacer, "Documentations"


def test_provision_adds_self_relation(provisioner, mock_client):
    resource_ids, result = provisioner.provision("parent-page-id")

    mock_client.update_database.assert_called_once()
    call_args = mock_client.update_database.call_args
    backlog_id = resource_ids["backlog"]
    assert call_args[0][0] == backlog_id
    props = call_args[1].get("properties") or call_args[0][1]
    assert "Parent" in props
    assert props["Parent"]["relation"]["database_id"] == backlog_id


def test_provision_repairs_missing_automation_trace_on_existing_backlog(provisioner, mock_client):
    mock_client.get_block_children.return_value = [
        {"type": "child_database", "id": "ex-db-1", "child_database": {"title": "Backlog"}},
        {"type": "child_database", "id": "ex-db-2", "child_database": {"title": "Decisions"}},
    ]
    mock_client.get_database.side_effect = [
        {
            "id": "ex-db-1",
            "properties": {
                "Title": {"type": "title", "title": {}},
                "Type": {"type": "select", "select": {"options": [{"name": "Idea"}]}},
            },
        },
        {
            "id": "ex-db-2",
            "properties": {
                "Title": {"type": "title", "title": {}},
                "ID": {"type": "rich_text", "rich_text": {}},
                "Date": {"type": "date", "date": {}},
                "Status": {"type": "select", "select": {"options": []}},
                "Why": {"type": "rich_text", "rich_text": {}},
                "Alternatives Rejected": {"type": "rich_text", "rich_text": {}},
                "Feature Link": {"type": "url", "url": {}},
                "ADR Link": {"type": "url", "url": {}},
            },
        },
    ]

    provisioner.provision("parent-page-id")

    assert any(
        "Automation Trace" in (kwargs.get("properties") or {})
        for _, kwargs in mock_client.update_database.call_args_list
    )


def test_provision_is_idempotent(provisioner, mock_client):
    mock_client.get_block_children.return_value = [
        {"type": "child_database", "id": "ex-db-1", "child_database": {"title": "Backlog"}},
        {"type": "child_database", "id": "ex-db-2", "child_database": {"title": "Decisions"}},
        {"type": "child_page", "id": "ex-p-1", "child_page": {"title": "README"}},
        {"type": "child_page", "id": "ex-p-2", "child_page": {"title": "Templates"}},
        {"type": "child_page", "id": "ex-p-3", "child_page": {"title": "Briefs"}},
        {"type": "child_page", "id": "ex-p-4", "child_page": {"title": "Release Notes"}},
    ]

    resource_ids, result = provisioner.provision("parent-page-id")

    assert resource_ids["backlog"] == "ex-db-1"
    assert resource_ids["decisions"] == "ex-db-2"
    assert resource_ids["readme"] == "ex-p-1"
    assert resource_ids["templates"] == "ex-p-2"
    assert resource_ids["briefs"] == "ex-p-3"  # Legacy page kept
    assert resource_ids["release_notes"] == "ex-p-4"
    assert mock_client.create_database.call_count == 0
    assert mock_client.create_page.call_count == 0
    # No section labels on idempotent run (workspace not fresh)
    assert mock_client.append_block_children.call_count == 0
    # update_database may be called for schema upgrades on found DBs
    assert len(result.databases_found) == 2


def test_provision_creates_only_missing(provisioner, mock_client):
    mock_client.get_block_children.return_value = [
        {"type": "child_database", "id": "ex-1", "child_database": {"title": "Backlog"}},
    ]

    resource_ids, result = provisioner.provision("parent-page-id")

    assert resource_ids["backlog"] == "ex-1"
    assert mock_client.create_database.call_count == 2  # decisions + briefs_db
    assert len(result.databases_found) == 1
    assert len(result.databases_created) == 2


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
    content = "# Heading\n\n## Subheading\n\n- Bullet\n- [ ] Todo\n- [x] Done\n\n---\n\nParagraph"
    blocks = NotionProvisioner._markdown_to_blocks(content)

    assert blocks[0]["type"] == "heading_1"
    assert blocks[1]["type"] == "paragraph"
    assert blocks[1]["paragraph"]["rich_text"] == []
    assert blocks[2]["type"] == "heading_2"
    assert blocks[4]["type"] == "bulleted_list_item"
    assert blocks[5]["type"] == "to_do"
    assert blocks[5]["to_do"]["checked"] is False
    assert blocks[6]["type"] == "to_do"
    assert blocks[6]["to_do"]["checked"] is True
    assert blocks[8]["type"] == "divider"
    assert blocks[10]["type"] == "paragraph"


# --- Preflight check tests ---


def test_preflight_check_passes_on_valid_page(provisioner, mock_client):
    """Preflight should not raise when the page is accessible."""
    provisioner.preflight_check("parent-page-id")
    mock_client.get_page.assert_called_once_with("parent-page-id")


def test_preflight_check_raises_lookup_error_on_404(provisioner, mock_client):
    mock_client.get_page.side_effect = Exception("Could not find page with ID: abc123")
    with pytest.raises(LookupError, match="Parent page not found"):
        provisioner.preflight_check("abc123")


def test_preflight_check_raises_permission_error_on_403(provisioner, mock_client):
    mock_client.get_page.side_effect = Exception("403: restricted_resource")
    with pytest.raises(PermissionError, match="No access to parent page"):
        provisioner.preflight_check("restricted-page")


def test_preflight_check_raises_runtime_error_on_other_failure(provisioner, mock_client):
    mock_client.get_page.side_effect = Exception("Connection timeout")
    with pytest.raises(RuntimeError, match="Failed to validate parent page"):
        provisioner.preflight_check("some-page")


def test_provision_calls_preflight_before_provisioning(provisioner, mock_client):
    """provision() should call preflight_check and fail early on bad page."""
    mock_client.get_page.side_effect = Exception("Could not find page")
    with pytest.raises(LookupError):
        provisioner.provision("bad-page-id")
    # Should not proceed to create anything
    mock_client.create_database.assert_not_called()
    mock_client.create_page.assert_not_called()


# --- README emoji test ---


def test_readme_page_uses_correct_briefs_emoji(provisioner, mock_client):
    """The Briefs bullet should use the clipboard emoji, not a replacement char."""
    page = provisioner._create_readme_page("parent-page-id")
    # Find the Briefs bullet (4th bulleted_list_item, index 5 in the blocks list)
    create_call = mock_client.create_page.call_args
    children = create_call[1]["children"]
    briefs_bullets = [
        b for b in children
        if b.get("type") == "bulleted_list_item"
        and "Briefs" in b["bulleted_list_item"]["rich_text"][0]["text"]["content"]
    ]
    assert len(briefs_bullets) == 1
    text = briefs_bullets[0]["bulleted_list_item"]["rich_text"][0]["text"]["content"]
    assert text.startswith("\U0001f4cb")  # 📋 clipboard emoji
    assert "\ufffd" not in text  # no replacement character
