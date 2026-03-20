"""Integration tests for the agent brief CLI command (local backend)."""

import json
import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner

import src.cli.commands.brief as brief_module
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


class BriefLinkStoreDouble:
    def __init__(self, *, ideas: list[dict], brief_title: str, brief_url: str):
        self.ideas = ideas
        self.brief_title = brief_title
        self.brief_url = brief_url
        self.updated_rows: list[dict] = []

    def read_brief(self, name: str) -> dict:
        return {
            "name": name,
            "title": self.brief_title,
            "status": "draft",
            "notion_url": self.brief_url,
        }

    def write_brief(self, name: str, data: dict) -> None:
        return None

    def read_backlog(self) -> list[dict]:
        return list(self.ideas)

    def write_backlog_row(self, row: dict) -> None:
        self.updated_rows.append(dict(row))
        row_id = row.get("notion_id") or row.get("id")
        for idx, idea in enumerate(self.ideas):
            idea_id = idea.get("notion_id") or idea.get("id")
            if row_id and row_id == idea_id:
                self.ideas[idx] = dict(row)
                return
            if (
                idea.get("type", "").lower() == row.get("type", "").lower()
                and idea.get("title", "") == row.get("title", "")
            ):
                self.ideas[idx] = dict(row)
                return


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


def test_brief_write_auto_links_matching_idea_when_unambiguous(runner, project, monkeypatch):
    store = BriefLinkStoreDouble(
        ideas=[
            {
                "title": "Bug: inbox add ignores priority field",
                "type": "Idea",
                "status": "exploring",
                "priority": "Medium",
                "brief_link": "",
                "notion_id": "idea-1",
            }
        ],
        brief_title="Inbox priority bug",
        brief_url="https://www.notion.so/inbox-priority-bug-329b5a09fa4a81a5bcd9ffe8d07a227b",
    )
    monkeypatch.setattr(brief_module, "get_store_from_dir", lambda _project_dir: store)

    result = runner.invoke(
        cli,
        [
            "brief",
            "write",
            "inbox-priority-bug",
            "--status",
            "draft",
            "--project-dir",
            str(project),
        ],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)["data"]
    assert payload["idea_linked"] is True
    assert payload["linked_idea_title"] == "Bug: inbox add ignores priority field"
    assert payload["notion_url"] == store.brief_url
    assert store.updated_rows[-1]["brief_link"] == store.brief_url


def test_brief_write_links_explicit_idea_title(runner, project, monkeypatch):
    store = BriefLinkStoreDouble(
        ideas=[
            {
                "title": "Completely different phrasing",
                "type": "Idea",
                "status": "exploring",
                "priority": "Medium",
                "brief_link": "",
                "notion_id": "idea-2",
            }
        ],
        brief_title="Inbox priority bug",
        brief_url="https://www.notion.so/inbox-priority-bug-329b5a09fa4a81a5bcd9ffe8d07a227b",
    )
    monkeypatch.setattr(brief_module, "get_store_from_dir", lambda _project_dir: store)

    result = runner.invoke(
        cli,
        [
            "brief",
            "write",
            "inbox-priority-bug",
            "--status",
            "draft",
            "--link-idea-title",
            "Completely different phrasing",
            "--project-dir",
            str(project),
        ],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)["data"]
    assert payload["idea_linked"] is True
    assert payload["link_reason"] == "matched by idea title"
    assert store.updated_rows[-1]["brief_link"] == store.brief_url


def test_brief_list_returns_grouped_output(runner, project):
    write_result = runner.invoke(
        cli,
        [
            "brief",
            "write",
            "grouping-check",
            "--status",
            "draft",
            "--problem",
            "Need grouped list output.",
            "--goal",
            "Show date headers.",
            "--project-dir",
            str(project),
        ],
    )
    assert write_result.exit_code == 0, write_result.output

    result = runner.invoke(
        cli,
        [
            "brief",
            "list",
            "--project-dir",
            str(project),
        ],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["success"] is True
    groups = payload["data"]["groups"]
    assert isinstance(groups, list)
    assert groups
    assert "date" in groups[0]
    assert "briefs" in groups[0]
