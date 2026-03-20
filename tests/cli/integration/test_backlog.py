"""Integration tests for backlog CLI list options."""

import json
import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner

import src.cli.commands.backlog as backlog_module
from src.cli.main import cli
from src.core.storage.config import StorageConfig, save_config


@pytest.fixture
def project(tmp_path):
    root = tmp_path / "project"
    root.mkdir()

    upstream_templates = Path(__file__).resolve().parents[3] / "template"
    shutil.copytree(upstream_templates, root / "template")

    plan = root / "docs" / "plan"
    (plan / "_shared").mkdir(parents=True)
    shutil.copy(root / "template" / "_inbox.md", plan / "_inbox.md")
    shutil.copy(root / "template" / "backlog.md", plan / "_shared" / "backlog.md")
    (root / "_project").mkdir()
    (root / "_project" / "decisions.md").write_text(
        "# Decisions Log\n\n"
        "| ID | Date | Decision | Why | Alternatives Rejected | ADR |\n"
        "|---|---|---|---|---|---|\n"
    )
    save_config(StorageConfig(backend="local"), root / "_project")

    runner = CliRunner()
    runner.invoke(
        cli,
        [
            "backlog",
            "upsert",
            "--title",
            "Backlog timestamp test",
            "--type",
            "Task",
            "--status",
            "to-do",
            "--project-dir",
            str(root),
        ],
    )
    return root


@pytest.fixture
def runner():
    return CliRunner()


def test_backlog_list_since_filters_and_returns_timestamps(runner, project):
    result = runner.invoke(
        cli,
        [
            "backlog",
            "list",
            "--since",
            "2020-01-01",
            "--project-dir",
            str(project),
        ],
    )
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["success"] is True
    assert payload["data"]
    assert "created_at" in payload["data"][0]
    assert "updated_at" in payload["data"][0]


def test_backlog_list_group_by_date(runner, project):
    result = runner.invoke(
        cli,
        [
            "backlog",
            "list",
            "--group-by-date",
            "--project-dir",
            str(project),
        ],
    )
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["success"] is True
    assert isinstance(payload["data"], list)
    assert payload["data"]
    assert "date" in payload["data"][0]
    assert "items" in payload["data"][0]


def test_backlog_list_rejects_since_and_today_together(runner, project):
    result = runner.invoke(
        cli,
        [
            "backlog",
            "list",
            "--since",
            "2020-01-01",
            "--today",
            "--project-dir",
            str(project),
        ],
    )
    assert result.exit_code != 0
    assert "Use either --since or --today" in result.output


def test_backlog_children_returns_summary(runner, project, monkeypatch):
    class StoreDouble:
        def list_children(self, parent_id: str) -> list[dict]:
            assert parent_id == "idea-1"
            return [
                {"title": "Feature A", "type": "Feature", "status": "done"},
                {"title": "Feature B", "type": "Feature", "status": "in-progress"},
            ]

    monkeypatch.setattr(
        backlog_module, "get_store_from_dir", lambda _project_dir: StoreDouble()
    )

    result = runner.invoke(
        cli,
        [
            "backlog",
            "children",
            "--parent-id",
            "idea-1",
            "--project-dir",
            str(project),
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["success"] is True
    assert payload["data"]["parent_id"] == "idea-1"
    assert len(payload["data"]["children"]) == 2
    assert payload["data"]["summary"]["total"] == 2
    assert payload["data"]["summary"]["done"] == 1
    assert payload["data"]["summary"]["in_progress"] == 1
    assert payload["data"]["summary"]["ship_ready"] is False
    assert payload["data"]["summary"]["readiness"] == "partially done"
