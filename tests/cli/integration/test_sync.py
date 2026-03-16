"""Tests for agent sync CLI commands."""

import pytest
import yaml
from pathlib import Path
from unittest.mock import MagicMock, patch
from click.testing import CliRunner

from src.cli.commands.sync import sync


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def local_project(tmp_path):
    """Project configured with local backend — sync should fail."""
    project_dir = tmp_path / "_project"
    project_dir.mkdir()
    (project_dir / "storage.yaml").write_text("backend: local\n")
    (tmp_path / "docs" / "plan").mkdir(parents=True)
    (tmp_path / "template").mkdir()
    return tmp_path


@pytest.fixture
def notion_project(tmp_path):
    """Project configured with notion backend."""
    project_dir = tmp_path / "_project"
    project_dir.mkdir()
    config = {
        "backend": "notion",
        "notion": {
            "parent_page_id": "parent-1",
            "parent_page_url": "https://notion.so/parent-1",
            "databases": {
                "intake": "db-i",
                "briefs": "db-b",
                "decisions": "db-d",
                "backlog": "db-bl",
                "templates": "db-t",
            },
        },
    }
    (project_dir / "storage.yaml").write_text(yaml.dump(config))
    plan = tmp_path / "docs" / "plan"
    plan.mkdir(parents=True)
    (plan / "_inbox.md").write_text("# Inbox\n\n## Entries\n\n")
    (plan / "_shared").mkdir()
    (tmp_path / "template").mkdir()
    return tmp_path


# --- agent sync local ---


def test_sync_local_fails_for_local_backend(runner, local_project):
    result = runner.invoke(
        sync, ["local", "--project-dir", str(local_project)]
    )
    assert result.exit_code != 0
    assert "does not support sync" in result.output.lower()


def test_sync_local_runs_for_notion_backend(runner, notion_project):
    with patch("src.integrations.notion.backend.NotionClient") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client

        # Mock: empty results from all databases
        mock_client.query_database.return_value = []

        result = runner.invoke(
            sync, ["local", "--project-dir", str(notion_project)]
        )

    assert result.exit_code == 0
    assert "Sync complete" in result.output
    assert "Fetched:" in result.output


def test_sync_local_dry_run(runner, notion_project):
    with patch("src.integrations.notion.backend.NotionClient") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        mock_client.query_database.return_value = []

        result = runner.invoke(
            sync, ["local", "--dry-run", "--project-dir", str(notion_project)]
        )

    assert result.exit_code == 0
    assert "[dry-run]" in result.output


# --- agent sync templates ---


def test_sync_templates_fails_for_local_backend(runner, local_project):
    result = runner.invoke(
        sync, ["templates", "--project-dir", str(local_project)]
    )
    assert result.exit_code != 0
    assert "does not support" in result.output.lower()


def test_sync_templates_runs_for_notion_backend(runner, notion_project):
    with patch("src.integrations.notion.backend.NotionClient") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        mock_client.query_database.return_value = []

        result = runner.invoke(
            sync, ["templates", "--project-dir", str(notion_project)]
        )

    assert result.exit_code == 0
    assert "Template sync complete" in result.output
