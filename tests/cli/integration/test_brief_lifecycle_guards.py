"""Integration tests for brief lifecycle promotion guards (local backend)."""

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


def _write_full_brief(runner, project, name="test-brief"):
    """Helper: create a brief with all required sections filled."""
    result = runner.invoke(
        cli,
        [
            "brief", "write", name,
            "--title", "Test Brief",
            "--status", "draft",
            "--problem", "A real problem.",
            "--goal", "Fix the problem.",
            "--acceptance-criteria", "- [ ] Verify the fix works",
            "--project-dir", str(project),
        ],
    )
    assert result.exit_code == 0, result.output
    return result


def _write_sparse_brief(runner, project, name="sparse-brief"):
    """Helper: create a brief with only a problem — no goal or AC."""
    result = runner.invoke(
        cli,
        [
            "brief", "write", name,
            "--title", "Sparse Brief",
            "--status", "draft",
            "--problem", "Only this section filled.",
            "--project-dir", str(project),
        ],
    )
    assert result.exit_code == 0, result.output
    return result


class TestPromotionBlocked:
    """Promotion writes are blocked when required sections are missing."""

    def test_promotion_blocked_missing_goal_and_ac(self, runner, project):
        _write_sparse_brief(runner, project)

        result = runner.invoke(
            cli,
            [
                "brief", "write", "sparse-brief",
                "--status", "implementation-ready",
                "--project-dir", str(project),
            ],
        )
        assert result.exit_code == 1, result.output
        data = json.loads(result.output)
        assert data["success"] is False
        assert "blocked" in data["error"].lower()
        assert "goal" in data["error"]
        assert "acceptance_criteria" in data["error"]

    def test_promotion_blocked_status_from_file(self, runner, project, tmp_path):
        _write_sparse_brief(runner, project)

        brief_file = tmp_path / "promote.md"
        brief_file.write_text(
            "# Sparse Brief\n\n"
            "**Status: architect-review**\n\n"
            "## Problem\nOnly this section filled.\n"
        )

        result = runner.invoke(
            cli,
            [
                "brief", "write", "sparse-brief",
                "--file", str(brief_file),
                "--project-dir", str(project),
            ],
        )
        assert result.exit_code == 1, result.output
        data = json.loads(result.output)
        assert data["success"] is False
        assert "blocked" in data["error"].lower()

    def test_promotion_blocked_does_not_mutate_brief(self, runner, project):
        """When blocked, the brief on disk must remain unchanged."""
        _write_sparse_brief(runner, project)

        # Read current state
        result = runner.invoke(
            cli,
            ["brief", "read", "sparse-brief", "--project-dir", str(project)],
        )
        before = json.loads(result.output)["data"]
        assert before["status"] == "draft"

        # Attempt promotion — should be blocked
        runner.invoke(
            cli,
            [
                "brief", "write", "sparse-brief",
                "--status", "implementation-ready",
                "--project-dir", str(project),
            ],
        )

        # Read again — status should still be draft
        result = runner.invoke(
            cli,
            ["brief", "read", "sparse-brief", "--project-dir", str(project)],
        )
        after = json.loads(result.output)["data"]
        assert after["status"] == "draft"


class TestPromotionForced:
    """--force bypasses the validation gate but still reports warnings."""

    def test_force_allows_promotion_with_missing_sections(self, runner, project):
        _write_sparse_brief(runner, project)

        result = runner.invoke(
            cli,
            [
                "brief", "write", "sparse-brief",
                "--status", "implementation-ready",
                "--force",
                "--project-dir", str(project),
            ],
        )
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert data["success"] is True
        assert data["data"]["status"] == "implementation-ready"
        # field_validation shows per-section status
        fv = data["data"]["field_validation"]
        assert fv["problem"] == "populated"
        assert fv["goal"] == "blank"
        assert fv["acceptance_criteria"] == "blank"
        assert data["data"]["field_validation_bypassed"] is True

    def test_force_writes_the_brief(self, runner, project):
        _write_sparse_brief(runner, project)

        runner.invoke(
            cli,
            [
                "brief", "write", "sparse-brief",
                "--status", "implementation-ready",
                "--force",
                "--project-dir", str(project),
            ],
        )

        result = runner.invoke(
            cli,
            ["brief", "read", "sparse-brief", "--project-dir", str(project)],
        )
        brief = json.loads(result.output)["data"]
        assert brief["status"] == "implementation-ready"


class TestPromotionPasses:
    """Promotion succeeds when all required sections are present."""

    def test_promotion_passes_with_full_brief(self, runner, project):
        _write_full_brief(runner, project)

        result = runner.invoke(
            cli,
            [
                "brief", "write", "test-brief",
                "--status", "implementation-ready",
                "--project-dir", str(project),
            ],
        )
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert data["success"] is True
        assert data["data"]["status"] == "implementation-ready"
        fv = data["data"]["field_validation"]
        assert fv["problem"] == "populated"
        assert fv["goal"] == "populated"
        assert fv["acceptance_criteria"] == "populated"
        assert "field_validation_bypassed" not in data["data"]

    def test_draft_write_always_passes_without_guard(self, runner, project):
        """Writing at draft status never triggers the guard."""
        result = runner.invoke(
            cli,
            [
                "brief", "write", "empty-brief",
                "--title", "Empty Brief",
                "--status", "draft",
                "--project-dir", str(project),
            ],
        )
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert data["success"] is True
        # draft writes have empty field_validation (no sections checked)
        fv = data["data"]["field_validation"]
        assert fv == {}

    def test_field_validation_in_all_promotion_statuses(self, runner, project):
        """All promotion statuses include field_validation in output."""
        _write_full_brief(runner, project, name="multi-status")

        for status in ("architect-review", "implementation-ready", "review-ready", "done"):
            result = runner.invoke(
                cli,
                [
                    "brief", "write", "multi-status",
                    "--status", status,
                    "--project-dir", str(project),
                ],
            )
            assert result.exit_code == 0, result.output
            data = json.loads(result.output)
            assert data["success"] is True, f"Failed for status {status}: {data}"
            fv = data["data"]["field_validation"]
            assert fv["problem"] == "populated", f"Failed for status {status}"
            assert fv["goal"] == "populated", f"Failed for status {status}"
            assert fv["acceptance_criteria"] == "populated", f"Failed for status {status}"
