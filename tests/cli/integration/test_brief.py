"""Integration tests for the agent brief CLI command (local backend)."""

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

    (root / "_project").mkdir()
    plan = root / "docs" / "plan"
    (plan / "_shared").mkdir(parents=True)

    shutil.copy(root / "template" / "_inbox.md", plan / "_inbox.md")
    shutil.copy(root / "template" / "backlog.md", plan / "_shared" / "backlog.md")
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


def test_brief_write_updates_existing_fields_without_wiping_unspecified_content(runner, project):
    result = runner.invoke(
        cli,
        [
            "brief",
            "write",
            "architect-review-automation",
            "--title",
            "Architect-review Automation",
            "--status",
            "draft",
            "--problem",
            "Original problem.",
            "--goal",
            "Original goal.",
            "--acceptance-criteria",
            "- [ ] Original AC",
            "--out-of-scope",
            "- Original OOS",
            "--open-questions",
            "- Original OQ",
            "--technical-approach",
            "Original technical approach.",
            "--project-dir",
            str(project),
        ],
    )
    assert result.exit_code == 0, result.output

    result = runner.invoke(
        cli,
        [
            "brief",
            "write",
            "architect-review-automation",
            "--status",
            "implementation-ready",
            "--open-questions",
            "- Resolved",
            "--project-dir",
            str(project),
        ],
    )
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["success"] is True
    assert data["data"]["status"] == "implementation-ready"

    result = runner.invoke(
        cli,
        ["brief", "read", "architect-review-automation", "--project-dir", str(project)],
    )
    assert result.exit_code == 0, result.output
    brief = json.loads(result.output)["data"]
    assert brief["status"] == "implementation-ready"
    assert brief["problem"] == "Original problem."
    assert brief["goal"] == "Original goal."
    assert brief["acceptance_criteria"] == "- [ ] Original AC"
    assert brief["out_of_scope"] == "- Original OOS"
    assert brief["open_questions"] == "- Resolved"
    assert brief["technical_approach"] == "Original technical approach."


def test_brief_write_accepts_technical_approach_inline(runner, project):
    result = runner.invoke(
        cli,
        [
            "brief",
            "write",
            "brief-with-technical-approach",
            "--title",
            "Brief With Technical Approach",
            "--problem",
            "Need a durable update path.",
            "--technical-approach",
            "Use partial-merge updates in the CLI.",
            "--project-dir",
            str(project),
        ],
    )
    assert result.exit_code == 0, result.output

    result = runner.invoke(
        cli,
        [
            "brief",
            "read",
            "brief-with-technical-approach",
            "--project-dir",
            str(project),
        ],
    )
    assert result.exit_code == 0, result.output
    brief = json.loads(result.output)["data"]
    assert brief["technical_approach"] == "Use partial-merge updates in the CLI."
    assert brief["problem"] == "Need a durable update path."
    assert brief["status"] == "draft"


def test_brief_write_roundtrips_nfr_and_inline_newlines(runner, project):
    result = runner.invoke(
        cli,
        [
            "brief",
            "write",
            "notion-brief-body-updates",
            "--title",
            "Notion Brief Body Updates",
            "--acceptance-criteria",
            "- [ ] First line\\n- [ ] Second line",
            "--non-functional-requirements",
            "- **Latency / response time:** best-effort\\n- **Other constraints:** preserve content",
            "--project-dir",
            str(project),
        ],
    )
    assert result.exit_code == 0, result.output

    result = runner.invoke(
        cli,
        ["brief", "read", "notion-brief-body-updates", "--project-dir", str(project)],
    )
    assert result.exit_code == 0, result.output
    brief = json.loads(result.output)["data"]
    assert brief["acceptance_criteria"] == "- [ ] First line\n- [ ] Second line"
    assert (
        brief["non_functional_requirements"]
        == "- **Latency / response time:** best-effort\n- **Other constraints:** preserve content"
    )


def test_brief_history_and_restore_commands(runner, project):
    result = runner.invoke(
        cli,
        [
            "brief",
            "write",
            "brief-version-control",
            "--title",
            "Brief Version Control",
            "--status",
            "draft",
            "--problem",
            "Original problem.",
            "--goal",
            "Original goal.",
            "--acceptance-criteria",
            "- [ ] Original AC",
            "--project-dir",
            str(project),
        ],
    )
    assert result.exit_code == 0, result.output

    result = runner.invoke(
        cli,
        [
            "brief",
            "write",
            "brief-version-control",
            "--problem",
            "Updated problem.",
            "--change-summary",
            "Clarify scope.",
            "--project-dir",
            str(project),
        ],
    )
    assert result.exit_code == 0, result.output

    result = runner.invoke(
        cli,
        ["brief", "history", "brief-version-control", "--project-dir", str(project)],
    )
    assert result.exit_code == 0, result.output
    history = json.loads(result.output)["data"]
    assert len(history) == 1
    assert history[0]["change_summary"] == "Clarify scope."

    revision_id = history[0]["revision_id"]
    result = runner.invoke(
        cli,
        [
            "brief",
            "revision",
            "brief-version-control",
            revision_id,
            "--project-dir",
            str(project),
        ],
    )
    assert result.exit_code == 0, result.output
    revision = json.loads(result.output)["data"]
    assert revision["snapshot"]["problem"] == "Original problem."

    result = runner.invoke(
        cli,
        [
            "brief",
            "restore",
            "brief-version-control",
            revision_id,
            "--change-summary",
            "Undo accidental rewrite.",
            "--project-dir",
            str(project),
        ],
    )
    assert result.exit_code == 0, result.output

    result = runner.invoke(
        cli,
        ["brief", "read", "brief-version-control", "--project-dir", str(project)],
    )
    restored = json.loads(result.output)["data"]
    assert restored["problem"] == "Original problem."
