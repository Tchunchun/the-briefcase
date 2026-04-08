"""Integration tests for backlog CLI list options."""

import json
import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner

import src.cli.commands.backlog as backlog_module
from src.cli.main import cli
from src.core.storage.config import ProjectConfig, StorageConfig, save_config


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


def test_backlog_upsert_defaults_project_from_config(runner, project):
    save_config(
        StorageConfig(backend="local", project=ProjectConfig(name="Briefcase")),
        project / "_project",
    )

    result = runner.invoke(
        cli,
        [
            "backlog",
            "upsert",
            "--title",
            "Project-tagged task",
            "--type",
            "Task",
            "--status",
            "to-do",
            "--project-dir",
            str(project),
        ],
    )

    assert result.exit_code == 0, result.output

    result = runner.invoke(
        cli,
        ["backlog", "list", "--project-dir", str(project)],
    )
    payload = json.loads(result.output)
    rows = [row for row in payload["data"] if row["title"] == "Project-tagged task"]
    assert rows
    assert rows[0]["project"] == "Briefcase"


def test_backlog_upsert_preserves_existing_project_without_override(runner, project):
    first = runner.invoke(
        cli,
        [
            "backlog",
            "upsert",
            "--title",
            "Existing project task",
            "--type",
            "Task",
            "--status",
            "to-do",
            "--project",
            "Skunkworks",
            "--project-dir",
            str(project),
        ],
    )
    assert first.exit_code == 0, first.output

    second = runner.invoke(
        cli,
        [
            "backlog",
            "upsert",
            "--title",
            "Existing project task",
            "--type",
            "Task",
            "--status",
            "in-progress",
            "--project-dir",
            str(project),
        ],
    )
    assert second.exit_code == 0, second.output

    result = runner.invoke(
        cli,
        ["backlog", "list", "--project-dir", str(project)],
    )
    payload = json.loads(result.output)
    rows = [row for row in payload["data"] if row["title"] == "Existing project task"]
    assert rows
    assert rows[0]["project"] == "Skunkworks"
    assert rows[0]["status"] == "in-progress"


def test_backlog_upsert_accepts_bug_type(runner, project):
    result = runner.invoke(
        cli,
        [
            "backlog",
            "upsert",
            "--title",
            "Fix crash on empty input",
            "--type",
            "Bug",
            "--status",
            "to-do",
            "--project-dir",
            str(project),
        ],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["data"]["type"] == "Bug"

    listing = runner.invoke(
        cli, ["backlog", "list", "--project-dir", str(project)]
    )
    rows = json.loads(listing.output)["data"]
    bug_rows = [r for r in rows if r["title"] == "Fix crash on empty input"]
    assert bug_rows
    assert bug_rows[0]["type"] == "Bug"


def test_backlog_upsert_persists_automation_trace(runner, project):
    result = runner.invoke(
        cli,
        [
            "backlog",
            "upsert",
            "--title",
            "Shipped feature",
            "--type",
            "Feature",
            "--status",
            "done",
            "--automation-trace",
            "[auto-ship-dispatch] routed shipped feature to release closeout",
            "--project-dir",
            str(project),
        ],
    )
    assert result.exit_code == 0, result.output

    listing = runner.invoke(
        cli, ["backlog", "list", "--project-dir", str(project)]
    )
    rows = json.loads(listing.output)["data"]
    target_rows = [r for r in rows if r["title"] == "Shipped feature"]
    assert target_rows
    assert target_rows[0]["automation_trace"] == (
        "[auto-ship-dispatch] routed shipped feature to release closeout"
    )


def test_backlog_upsert_append_notes_concatenates(runner, project):
    runner.invoke(
        cli,
        [
            "backlog",
            "upsert",
            "--title",
            "Append test item",
            "--type",
            "Task",
            "--status",
            "to-do",
            "--notes",
            "Initial note.",
            "--project-dir",
            str(project),
        ],
    )

    result = runner.invoke(
        cli,
        [
            "backlog",
            "upsert",
            "--title",
            "Append test item",
            "--type",
            "Task",
            "--status",
            "in-progress",
            "--append-notes",
            "Second note.",
            "--project-dir",
            str(project),
        ],
    )
    assert result.exit_code == 0, result.output

    listing = runner.invoke(
        cli, ["backlog", "list", "--project-dir", str(project)]
    )
    rows = json.loads(listing.output)["data"]
    item = [r for r in rows if r["title"] == "Append test item"][0]
    assert "Initial note." in item["notes"]
    assert "Second note." in item["notes"]
    assert " · " in item["notes"]


def test_backlog_upsert_preserves_parent_ids_on_update(runner, project, monkeypatch):
    class StoreDouble:
        def __init__(self):
            self._rows = [
                {
                    "title": "Child feature",
                    "type": "Feature",
                    "status": "draft",
                    "parent_ids": ["parent-abc"],
                    "notes": "",
                    "project": "TestProj",
                }
            ]
            self.last_written = None

        def read_backlog(self, since=None):
            return list(self._rows)

        def write_backlog_row(self, row):
            self.last_written = row
            self._rows = [row]

    store = StoreDouble()
    monkeypatch.setattr(
        backlog_module, "get_store_from_dir", lambda _: store
    )

    result = runner.invoke(
        cli,
        [
            "backlog",
            "upsert",
            "--title",
            "Child feature",
            "--type",
            "Feature",
            "--status",
            "in-progress",
            "--project-dir",
            str(project),
        ],
    )
    assert result.exit_code == 0, result.output
    assert store.last_written["parent_ids"] == ["parent-abc"]
