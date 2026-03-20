"""Integration tests for inbox CLI commands."""

import json
import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner

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
    return root


@pytest.fixture
def runner():
    return CliRunner()


def test_inbox_add_defaults_priority_to_medium(runner, project):
    result = runner.invoke(
        cli,
        [
            "inbox",
            "add",
            "--type",
            "idea",
            "--text",
            "Test default priority",
            "--project-dir",
            str(project),
        ],
    )
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["success"] is True
    assert payload["data"]["priority"] == "Medium"

    list_result = runner.invoke(
        cli,
        ["inbox", "list", "--project-dir", str(project)],
    )
    entries = json.loads(list_result.output)["data"]
    assert entries[-1]["priority"] == "Medium"


def test_inbox_add_accepts_priority(runner, project):
    result = runner.invoke(
        cli,
        [
            "inbox",
            "add",
            "--type",
            "idea",
            "--text",
            "Test explicit priority",
            "--priority",
            "high",
            "--project-dir",
            str(project),
        ],
    )
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["success"] is True
    assert payload["data"]["priority"] == "High"

    list_result = runner.invoke(
        cli,
        ["inbox", "list", "--project-dir", str(project)],
    )
    entries = json.loads(list_result.output)["data"]
    assert entries[-1]["priority"] == "High"


def test_inbox_list_since_filters_and_returns_timestamps(runner, project):
    list_result = runner.invoke(
        cli,
        [
            "inbox",
            "list",
            "--since",
            "2020-01-01",
            "--project-dir",
            str(project),
        ],
    )
    assert list_result.exit_code == 0
    payload = json.loads(list_result.output)
    assert payload["success"] is True
    assert payload["data"]
    assert "created_at" in payload["data"][0]
    assert "updated_at" in payload["data"][0]


def test_inbox_list_group_by_date(runner, project):
    result = runner.invoke(
        cli,
        [
            "inbox",
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


def test_inbox_list_rejects_since_and_today_together(runner, project):
    result = runner.invoke(
        cli,
        [
            "inbox",
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
