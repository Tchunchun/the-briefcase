"""Integration tests for the agent upgrade CLI command."""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from src.cli.main import cli
from src.core.storage.config import StorageConfig, NotionConfig, save_config


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def notion_project(tmp_path):
    """Create a Notion-backed project for upgrade testing."""
    root = tmp_path / "project"
    root.mkdir()
    project_dir = root / "_project"
    project_dir.mkdir()

    config = StorageConfig(
        backend="notion",
        notion=NotionConfig(
            parent_page_id="parent-abc",
            databases={
                "backlog": "db-backlog",
                "decisions": "db-decisions",
                "readme": "page-readme",
                "templates": "page-templates",
            },
        ),
    )
    save_config(config, project_dir)
    return root


@pytest.fixture
def local_project(tmp_path):
    """Create a local-backend project — upgrade should reject this."""
    root = tmp_path / "project"
    root.mkdir()
    project_dir = root / "_project"
    project_dir.mkdir()
    save_config(StorageConfig(backend="local"), project_dir)
    return root


def _make_select_prop(options: list[str]) -> dict:
    return {
        "type": "select",
        "select": {"options": [{"name": o} for o in options]},
    }


FULL_BACKLOG_PROPS = {
    "Title": {"type": "title", "title": {}},
    "Type": _make_select_prop(["Idea", "Feature", "Task"]),
    "Idea Status": _make_select_prop(["new", "exploring", "promoted", "rejected", "shipped"]),
    "Feature Status": _make_select_prop(["draft", "architect-review", "implementation-ready", "in-progress",
                                          "review-ready", "review-accepted", "done", "shipped"]),
    "Task Status": _make_select_prop(["to-do", "in-progress", "blocked", "done"]),
    "Priority": _make_select_prop(["High", "Medium", "Low"]),
    "Review Verdict": _make_select_prop(["pending", "accepted", "changes-requested"]),
    "Route State": _make_select_prop(["routed", "returned", "blocked"]),
    "Brief Link": {"type": "url", "url": {}},
    "Release Note Link": {"type": "url", "url": {}},
    "Notes": {"type": "rich_text", "rich_text": {}},
    "Automation Trace": {"type": "rich_text", "rich_text": {}},
    "Parent": {"type": "relation", "relation": {}},
}

FULL_DECISIONS_PROPS = {
    "Title": {"type": "title", "title": {}},
    "ID": {"type": "rich_text", "rich_text": {}},
    "Date": {"type": "date", "date": {}},
    "Status": _make_select_prop(["proposed", "accepted", "superseded"]),
    "Why": {"type": "rich_text", "rich_text": {}},
    "Alternatives Rejected": {"type": "rich_text", "rich_text": {}},
    "Feature Link": {"type": "url", "url": {}},
    "ADR Link": {"type": "url", "url": {}},
}


def _mock_healthy_client() -> MagicMock:
    client = MagicMock()
    client.get_page.return_value = {"id": "parent-abc"}
    client.get_database.side_effect = [
        {"id": "db-backlog", "properties": FULL_BACKLOG_PROPS},
        {"id": "db-decisions", "properties": FULL_DECISIONS_PROPS},
    ]
    return client


# -- Tests --


class TestUpgradeCheck:
    def test_check_healthy_exits_zero(self, runner, notion_project, monkeypatch):
        monkeypatch.setenv("NOTION_API_KEY", "test-key")
        client = _mock_healthy_client()

        with patch("src.integrations.notion.client.NotionClient", return_value=client):
            result = runner.invoke(
                cli,
                ["upgrade", "--check", "--project-dir", str(notion_project)],
            )

        assert result.exit_code == 0
        assert "OK" in result.output

    def test_check_missing_props_exits_nonzero(self, runner, notion_project, monkeypatch):
        monkeypatch.setenv("NOTION_API_KEY", "test-key")

        client = MagicMock()
        client.get_page.return_value = {"id": "parent-abc"}
        # Backlog missing "Notes"
        partial = {k: v for k, v in FULL_BACKLOG_PROPS.items() if k != "Notes"}
        client.get_database.side_effect = [
            {"id": "db-backlog", "properties": partial},
            {"id": "db-decisions", "properties": FULL_DECISIONS_PROPS},
        ]

        with patch("src.integrations.notion.client.NotionClient", return_value=client):
            result = runner.invoke(
                cli,
                ["upgrade", "--check", "--project-dir", str(notion_project)],
            )

        assert result.exit_code != 0
        assert "Notes" in result.output

    def test_check_local_backend_rejected(self, runner, local_project, monkeypatch):
        monkeypatch.setenv("NOTION_API_KEY", "test-key")

        result = runner.invoke(
            cli,
            ["upgrade", "--check", "--project-dir", str(local_project)],
        )

        assert result.exit_code != 0
        assert "local" in result.output.lower() or "not applicable" in result.output.lower()


class TestUpgradeApply:
    def test_upgrade_yes_healthy_exits_zero(self, runner, notion_project, monkeypatch):
        monkeypatch.setenv("NOTION_API_KEY", "test-key")
        client = _mock_healthy_client()

        with patch("src.integrations.notion.client.NotionClient", return_value=client):
            result = runner.invoke(
                cli,
                ["upgrade", "--yes", "--project-dir", str(notion_project)],
            )

        assert result.exit_code == 0
        assert "healthy" in result.output.lower() or "No repairs" in result.output

    def test_upgrade_yes_fixes_missing_props(self, runner, notion_project, monkeypatch):
        monkeypatch.setenv("NOTION_API_KEY", "test-key")

        client = MagicMock()
        client.get_page.return_value = {"id": "parent-abc"}
        partial = {
            k: v for k, v in FULL_BACKLOG_PROPS.items()
            if k not in ("Notes", "Automation Trace")
        }

        # First call is inspect, second is repair — each calls get_database
        client.get_database.side_effect = [
            {"id": "db-backlog", "properties": partial},
            {"id": "db-decisions", "properties": FULL_DECISIONS_PROPS},
            {"id": "db-backlog", "properties": partial},
            {"id": "db-decisions", "properties": FULL_DECISIONS_PROPS},
        ]
        client.update_database.return_value = {}

        with patch("src.integrations.notion.client.NotionClient", return_value=client):
            result = runner.invoke(
                cli,
                ["upgrade", "--yes", "--project-dir", str(notion_project)],
            )

        assert "FIXED" in result.output
        assert "Notes" in result.output
        assert "Automation Trace" in result.output


class TestUpgradeEdgeCases:
    def test_no_project_dir(self, runner):
        result = runner.invoke(
            cli,
            ["upgrade", "--check", "--project-dir", "/nonexistent/path"],
        )
        assert result.exit_code != 0
