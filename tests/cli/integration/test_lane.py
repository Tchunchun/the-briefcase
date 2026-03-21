"""Integration tests for lane support in backlog and inbox CLI."""

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


class TestBacklogLane:
    def test_upsert_with_lane(self, runner, project):
        result = runner.invoke(
            cli,
            [
                "backlog", "upsert",
                "--title", "Fix typo in README",
                "--type", "Task",
                "--status", "to-do",
                "--lane", "quick-fix",
                "--project-dir", str(project),
            ],
        )
        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["success"] is True
        assert payload["data"]["upserted"] == "Fix typo in README"

    def test_lane_persists_in_backlog(self, runner, project):
        # Upsert with lane
        runner.invoke(
            cli,
            [
                "backlog", "upsert",
                "--title", "Small UI tweak",
                "--type", "Feature",
                "--status", "draft",
                "--lane", "small",
                "--project-dir", str(project),
            ],
        )

        # Read backlog and check lane is present
        result = runner.invoke(
            cli,
            ["backlog", "list", "--project-dir", str(project)],
        )
        assert result.exit_code == 0
        payload = json.loads(result.output)
        items = payload["data"]
        matching = [i for i in items if i["title"] == "Small UI tweak"]
        assert len(matching) == 1
        assert matching[0]["lane"] == "small"

    def test_upsert_without_lane_defaults_empty(self, runner, project):
        runner.invoke(
            cli,
            [
                "backlog", "upsert",
                "--title", "Normal feature",
                "--type", "Feature",
                "--status", "draft",
                "--project-dir", str(project),
            ],
        )

        result = runner.invoke(
            cli,
            ["backlog", "list", "--project-dir", str(project)],
        )
        payload = json.loads(result.output)
        items = payload["data"]
        matching = [i for i in items if i["title"] == "Normal feature"]
        assert len(matching) == 1
        # Lane should be empty/dash for items without explicit lane
        assert matching[0].get("lane", "") in ("", "—")

    def test_lane_choice_rejects_invalid(self, runner, project):
        result = runner.invoke(
            cli,
            [
                "backlog", "upsert",
                "--title", "Bad lane",
                "--type", "Task",
                "--status", "to-do",
                "--lane", "invalid-lane",
                "--project-dir", str(project),
            ],
        )
        assert result.exit_code != 0


class TestInboxLane:
    def test_inbox_add_with_lane(self, runner, project):
        result = runner.invoke(
            cli,
            [
                "inbox", "add",
                "--type", "idea",
                "--text", "Fix broken link",
                "--lane", "quick-fix",
                "--project-dir", str(project),
            ],
        )
        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["success"] is True
        assert payload["data"]["lane"] == "quick-fix"

    def test_inbox_add_lane_tag_in_notes(self, runner, project):
        runner.invoke(
            cli,
            [
                "inbox", "add",
                "--type", "idea",
                "--text", "Fix broken link",
                "--notes", "The link in footer is 404",
                "--lane", "quick-fix",
                "--project-dir", str(project),
            ],
        )

        result = runner.invoke(
            cli,
            ["inbox", "list", "--project-dir", str(project)],
        )
        payload = json.loads(result.output)
        entries = payload["data"]
        matching = [e for e in entries if "Fix broken link" in e.get("text", "")]
        assert len(matching) == 1
        assert "[lane: quick-fix]" in matching[0].get("notes", "")

    def test_inbox_add_without_lane(self, runner, project):
        result = runner.invoke(
            cli,
            [
                "inbox", "add",
                "--type", "idea",
                "--text", "New feature idea",
                "--project-dir", str(project),
            ],
        )
        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert "lane" not in payload["data"]

    def test_inbox_add_lane_rejects_invalid(self, runner, project):
        result = runner.invoke(
            cli,
            [
                "inbox", "add",
                "--type", "idea",
                "--text", "Bad lane",
                "--lane", "mega",
                "--project-dir", str(project),
            ],
        )
        assert result.exit_code != 0


class TestSchemaLane:
    def test_lane_in_backlog_schema(self):
        from src.integrations.notion.schemas import BACKLOG_SCHEMA
        assert "Lane" in BACKLOG_SCHEMA
        options = BACKLOG_SCHEMA["Lane"]["select"]["options"]
        option_names = [o["name"] for o in options]
        assert "quick-fix" in option_names
        assert "small" in option_names
        assert "feature" in option_names
