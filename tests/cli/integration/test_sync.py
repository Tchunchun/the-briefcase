"""Tests for agent sync CLI commands."""

import subprocess
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


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )


def test_sync_shakedown_git_roundtrip_preserves_structured_fields(runner, tmp_path):
    remote = tmp_path / "artifacts-remote.git"
    _git(tmp_path, "init", "--bare", str(remote))

    project = tmp_path / "project"
    (project / "_project").mkdir(parents=True)
    (project / "docs" / "plan" / "shared-private-artifact-repo").mkdir(parents=True)
    (project / "docs" / "plan" / "_shared").mkdir(parents=True)
    (project / "docs" / "plan" / "shared-private-artifact-repo" / "brief.md").write_text(
        "# Shared private artifact repo\n\n**Status: implementation-ready**\n"
    )
    (project / "docs" / "plan" / "_shared" / "backlog.md").write_text(
        "# Backlog\n\n"
        "Cross-feature source of truth for task priority and execution status.\n\n"
        "| Type | Title | Status | Priority | Project | Notes |\n"
        "|---|---|---|---|---|---|\n"
        "| Feature | Shared private artifact repo | review-accepted | High | Briefcase | Delivery handoff preserved. <!-- briefcase-meta:eyJyZXZpZXdfdmVyZGljdCI6ImFjY2VwdGVkIiwicm91dGVfc3RhdGUiOiJyb3V0ZWQiLCJsYW5lIjoiZmVhdHVyZSIsInJlbGVhc2Vfbm90ZV9saW5rIjoiZG9jcy9wbGFuL19yZWxlYXNlcy92MC45LjQvcmVsZWFzZS1ub3Rlcy5tZCIsImF1dG9tYXRpb25fdHJhY2UiOiJbYXV0by1yZXZpZXctcmVhZHldIGRpc3BhdGNoZWQifQ==--> |\n"
    )
    (project / "_project" / "storage.yaml").write_text(
        yaml.safe_dump(
            {
                "backend": "git",
                "git": {
                    "remote": "origin",
                    "remote_url": str(remote),
                    "branch": "main",
                    "project_slug": "demo-project",
                    "paths": ["docs/plan/", "_project/"],
                },
            },
            sort_keys=False,
        )
    )

    result = runner.invoke(
        sync,
        [
            "shakedown-git",
            "--brief-name",
            "shared-private-artifact-repo",
            "--feature-title",
            "Shared private artifact repo",
            "--expected-status",
            "review-accepted",
            "--expected-review-verdict",
            "accepted",
            "--expected-route-state",
            "routed",
            "--expected-lane",
            "feature",
            "--expected-release-note-link",
            "docs/plan/_releases/v0.9.4/release-notes.md",
            "--expected-automation-trace-contains",
            "[auto-review-ready]",
            "--project-dir",
            str(project),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "success: true" in result.output
    assert "review_verdict: accepted" in result.output
    assert "route_state: routed" in result.output
