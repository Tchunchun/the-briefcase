"""Integration tests for automation CLI commands (local backend)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner

from src.cli.commands import automate as automate_module
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


def test_automate_architect_review_dispatches_once_and_records_trace(runner, project):
    runner.invoke(
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
            "Problem.",
            "--goal",
            "Goal.",
            "--acceptance-criteria",
            "- [ ] AC",
            "--project-dir",
            str(project),
        ],
    )
    runner.invoke(
        cli,
        [
            "backlog",
            "upsert",
            "--title",
            "Architect-review Automation",
            "--type",
            "Feature",
            "--status",
            "architect-review",
            "--priority",
            "High",
            "--feature",
            "architect-review-automation",
            "--notes",
            "",
            "--project-dir",
            str(project),
        ],
    )

    dispatch_log = project / "architect-dispatch.log"

    result = runner.invoke(
        cli,
        [
            "automate",
            "architect-review",
            "--dispatch-command",
            f"python3 -c \"from pathlib import Path; Path(r'{dispatch_log}').write_text('first-run')\"",
            "--project-dir",
            str(project),
        ],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)["data"]
    assert payload["dispatched_count"] == 1
    assert payload["dispatches"][0]["brief_name"] == "architect-review-automation"
    assert dispatch_log.exists()

    second = runner.invoke(
        cli,
        [
            "automate",
            "architect-review",
            "--dispatch-command",
            f"python3 -c \"from pathlib import Path; Path(r'{dispatch_log}').write_text('second-run')\"",
            "--project-dir",
            str(project),
        ],
    )
    assert second.exit_code == 0, second.output
    second_payload = json.loads(second.output)["data"]
    assert second_payload["dispatched_count"] == 0
    assert dispatch_log.read_text() != "second-run"

    backlog = runner.invoke(
        cli,
        ["backlog", "list", "--project-dir", str(project)],
    )
    rows = json.loads(backlog.output)["data"]
    row = next(r for r in rows if r["title"] == "Architect-review Automation")
    assert "Architect-review automation dispatched" in row["automation_trace"]
    assert "[auto-architect-review]" in row["automation_trace"]


def _setup_feature(runner, project, brief_name, title, status, *, brief_status="draft"):
    """Helper: create a brief + Feature at the given status."""
    runner.invoke(
        cli,
        [
            "brief", "write", brief_name,
            "--title", title,
            "--status", brief_status,
            "--problem", "Problem.",
            "--goal", "Goal.",
            "--acceptance-criteria", "- [ ] AC",
            "--project-dir", str(project),
        ],
    )
    runner.invoke(
        cli,
        [
            "backlog", "upsert",
            "--title", title,
            "--type", "Feature",
            "--status", status,
            "--priority", "High",
            "--feature", brief_name,
            "--notes", "",
            "--project-dir", str(project),
        ],
    )


class AutomationStoreDouble:
    def __init__(self, rows: list[dict], briefs: list[dict]) -> None:
        self.rows = [dict(row) for row in rows]
        self.briefs = [dict(brief) for brief in briefs]

    def read_backlog(self) -> list[dict]:
        return [dict(row) for row in self.rows]

    def list_briefs(self) -> list[dict]:
        return [dict(brief) for brief in self.briefs]

    def write_backlog_row(self, row: dict) -> None:
        for idx, existing in enumerate(self.rows):
            existing_id = existing.get("notion_id") or existing.get("id")
            row_id = row.get("notion_id") or row.get("id")
            if row_id and existing_id == row_id:
                self.rows[idx] = dict(row)
                return
            if (
                existing.get("type") == row.get("type")
                and existing.get("title") == row.get("title")
            ):
                self.rows[idx] = dict(row)
                return
        self.rows.append(dict(row))


def test_automate_implementation_ready_dispatches_and_is_idempotent(runner, project):
    _setup_feature(
        runner,
        project,
        "impl-test",
        "Impl Test",
        "implementation-ready",
        brief_status="implementation-ready",
    )

    result = runner.invoke(
        cli,
        ["automate", "implementation-ready", "--notes-only", "--project-dir", str(project)],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)["data"]
    assert payload["dispatched_count"] == 1
    assert payload["dispatches"][0]["brief_name"] == "impl-test"
    assert payload["dispatches"][0]["brief_name_resolved"] is True

    second = runner.invoke(
        cli,
        ["automate", "implementation-ready", "--notes-only", "--project-dir", str(project)],
    )
    assert json.loads(second.output)["data"]["dispatched_count"] == 0

    backlog = runner.invoke(cli, ["backlog", "list", "--project-dir", str(project)])
    rows = json.loads(backlog.output)["data"]
    row = next(r for r in rows if r["title"] == "Impl Test")
    assert "[auto-impl-ready]" in row["automation_trace"]


def test_automate_implementation_ready_marks_feature_in_progress_on_dispatch(runner, project):
    _setup_feature(
        runner,
        project,
        "impl-entry",
        "Impl Entry",
        "implementation-ready",
        brief_status="implementation-ready",
    )

    result = runner.invoke(
        cli,
        [
            "automate",
            "implementation-ready",
            "--dispatch-command",
            "python3 -c \"print('impl')\"",
            "--project-dir",
            str(project),
        ],
    )
    assert result.exit_code == 0, result.output

    backlog = runner.invoke(cli, ["backlog", "list", "--project-dir", str(project)])
    rows = json.loads(backlog.output)["data"]
    row = next(r for r in rows if r["title"] == "Impl Entry")
    assert row["status"] == "in-progress"


def test_automate_implementation_ready_promotes_to_review_ready_when_tasks_done(runner, project):
    _setup_feature(
        runner,
        project,
        "impl-finish",
        "Impl Finish",
        "implementation-ready",
        brief_status="implementation-ready",
    )
    runner.invoke(
        cli,
        [
            "backlog",
            "upsert",
            "--title",
            "Build task",
            "--type",
            "Task",
            "--status",
            "done",
            "--priority",
            "High",
            "--feature",
            "impl-finish",
            "--project-dir",
            str(project),
        ],
    )

    result = runner.invoke(
        cli,
        [
            "automate",
            "implementation-ready",
            "--dispatch-command",
            "python3 -c \"print('impl')\"",
            "--project-dir",
            str(project),
        ],
    )
    assert result.exit_code == 0, result.output

    backlog = runner.invoke(cli, ["backlog", "list", "--project-dir", str(project)])
    rows = json.loads(backlog.output)["data"]
    row = next(r for r in rows if r["title"] == "Impl Finish")
    assert row["status"] == "review-ready"


def test_automate_implementation_ready_blocks_without_brief(runner, project):
    runner.invoke(
        cli,
        [
            "backlog", "upsert",
            "--title", "No Brief Feature",
            "--type", "Feature",
            "--status", "implementation-ready",
            "--priority", "High",
            "--notes", "",
            "--project-dir", str(project),
        ],
    )
    result = runner.invoke(
        cli,
        ["automate", "implementation-ready", "--notes-only", "--project-dir", str(project)],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)["data"]
    assert payload["dispatched_count"] == 0
    assert payload["blocked_count"] == 1


def test_automate_ship_routing_updates_route_state_and_is_idempotent(runner, project):
    _setup_feature(runner, project, "ship-route", "Ship Route", "review-accepted")
    runner.invoke(
        cli,
        [
            "backlog",
            "upsert",
            "--title",
            "Ship Route",
            "--type",
            "Feature",
            "--status",
            "review-accepted",
            "--review-verdict",
            "accepted",
            "--priority",
            "High",
            "--feature",
            "ship-route",
            "--notes",
            "",
            "--project-dir",
            str(project),
        ],
    )

    result = runner.invoke(
        cli,
        [
            "automate",
            "ship-routing",
            "--dispatch-command",
            "python3 -c \"print('ship-routing')\"",
            "--project-dir",
            str(project),
        ],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)["data"]
    assert payload["dispatched_count"] == 1

    backlog = runner.invoke(cli, ["backlog", "list", "--project-dir", str(project)])
    rows = json.loads(backlog.output)["data"]
    row = next(r for r in rows if r["title"] == "Ship Route")
    assert row["route_state"] == "routed"

    second = runner.invoke(
        cli,
        [
            "automate",
            "ship-routing",
            "--dispatch-command",
            "python3 -c \"print('ship-routing-again')\"",
            "--project-dir",
            str(project),
        ],
    )
    assert second.exit_code == 0, second.output
    assert json.loads(second.output)["data"]["dispatched_count"] == 0


def test_automate_ship_dispatch_writes_release_note_link(runner, project):
    _setup_feature(runner, project, "ship-dispatch", "Ship Dispatch", "review-accepted")
    runner.invoke(
        cli,
        [
            "backlog",
            "upsert",
            "--title",
            "Ship Dispatch",
            "--type",
            "Feature",
            "--status",
            "review-accepted",
            "--review-verdict",
            "accepted",
            "--priority",
            "High",
            "--feature",
            "ship-dispatch",
            "--notes",
            "",
            "--project-dir",
            str(project),
        ],
    )

    command = (
        "python3 -c \"import json; "
        "print(json.dumps({{'release_note_link': 'https://example.com/releases/v0.9.0'}}))\""
    )
    result = runner.invoke(
        cli,
        [
            "automate",
            "ship-dispatch",
            "--dispatch-command",
            command,
            "--project-dir",
            str(project),
        ],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)["data"]
    assert payload["dispatched_count"] == 1

    backlog = runner.invoke(cli, ["backlog", "list", "--project-dir", str(project)])
    rows = json.loads(backlog.output)["data"]
    row = next(r for r in rows if r["title"] == "Ship Dispatch")
    assert row["route_state"] == "routed"
    assert row["release_note_link"] == "https://example.com/releases/v0.9.0"

    second = runner.invoke(
        cli,
        [
            "automate",
            "ship-dispatch",
            "--dispatch-command",
            command,
            "--project-dir",
            str(project),
        ],
    )
    assert second.exit_code == 0, second.output
    assert json.loads(second.output)["data"]["dispatched_count"] == 0


def test_automate_review_ready_dispatches_and_is_idempotent(runner, project):
    _setup_feature(runner, project, "review-test", "Review Test", "review-ready")

    result = runner.invoke(
        cli,
        ["automate", "review-ready", "--notes-only", "--project-dir", str(project)],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)["data"]
    assert payload["dispatched_count"] == 1
    assert payload["dispatches"][0]["brief_name"] == "review-test"

    second = runner.invoke(
        cli,
        ["automate", "review-ready", "--notes-only", "--project-dir", str(project)],
    )
    assert json.loads(second.output)["data"]["dispatched_count"] == 0

    backlog = runner.invoke(cli, ["backlog", "list", "--project-dir", str(project)])
    rows = json.loads(backlog.output)["data"]
    row = next(r for r in rows if r["title"] == "Review Test")
    assert "[auto-review-ready]" in row["automation_trace"]


def test_automate_fix_cycle_dispatch_filters_by_verdict_and_marks_in_progress(
    runner,
    project,
    monkeypatch,
):
    store = AutomationStoreDouble(
        rows=[
            {
                "title": "Fix Cycle Pass",
                "type": "Feature",
                "status": "review-ready",
                "priority": "High",
                "review_verdict": "changes-requested",
                "brief_link": "",
                "notes": "",
                "automation_trace": "",
                "parent_ids": [],
                "notion_id": "feat-pass",
            },
            {
                "title": "Fix Cycle Skip",
                "type": "Feature",
                "status": "review-ready",
                "priority": "High",
                "review_verdict": "accepted",
                "brief_link": "",
                "notes": "",
                "automation_trace": "",
                "parent_ids": [],
                "notion_id": "feat-skip",
            },
        ],
        briefs=[
            {"name": "fix-cycle-pass", "title": "Fix Cycle Pass", "notion_id": "brief-pass"},
            {"name": "fix-cycle-skip", "title": "Fix Cycle Skip", "notion_id": "brief-skip"},
        ],
    )
    monkeypatch.setattr(automate_module, "get_store_from_dir", lambda _project_dir: store)

    result = runner.invoke(
        cli,
        [
            "automate",
            "fix-cycle-dispatch",
            "--dispatch-command",
            "python3 -c \"print('fix')\"",
            "--project-dir",
            str(project),
        ],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)["data"]
    assert payload["dispatched_count"] == 1
    assert payload["blocked_count"] == 1
    assert payload["dispatches"][0]["brief_name"] == "fix-cycle-pass"

    passed = next(r for r in store.rows if r["title"] == "Fix Cycle Pass")
    assert passed["status"] == "in-progress"
    assert "[auto-fix-cycle]" in passed["automation_trace"]

    skipped = next(r for r in store.rows if r["title"] == "Fix Cycle Skip")
    assert skipped["status"] == "review-ready"
    assert skipped["route_state"] == "blocked"
