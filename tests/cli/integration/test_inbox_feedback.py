"""Integration tests for inbox feedback forwarding."""

import json
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner

from src.cli.main import cli
from src.core.storage.config import StorageConfig, UpstreamConfig, save_config


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
    save_config(StorageConfig(backend="local"), root / "_project")
    return root


@pytest.fixture
def project_with_upstream(tmp_path):
    root = tmp_path / "project"
    root.mkdir()

    upstream_templates = Path(__file__).resolve().parents[3] / "template"
    shutil.copytree(upstream_templates, root / "template")

    plan = root / "docs" / "plan"
    (plan / "_shared").mkdir(parents=True)
    shutil.copy(root / "template" / "_inbox.md", plan / "_inbox.md")
    shutil.copy(root / "template" / "backlog.md", plan / "_shared" / "backlog.md")
    (root / "_project").mkdir()
    save_config(
        StorageConfig(
            backend="local",
            upstream=UpstreamConfig(feedback_repo="owner/framework-repo"),
        ),
        root / "_project",
    )
    return root


@pytest.fixture
def runner():
    return CliRunner()


class TestFeedbackWithoutUpstream:
    def test_feedback_warns_when_no_upstream_configured(self, runner, project):
        result = runner.invoke(
            cli,
            [
                "inbox", "add",
                "--type", "feedback",
                "--text", "Missing feature",
                "--project-dir", str(project),
            ],
        )
        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["success"] is True
        assert payload["data"]["stored"] == "local-project"
        assert "upstream_warning" in payload["data"]
        assert "No upstream.feedback_repo configured" in payload["data"]["upstream_warning"]

    def test_idea_type_has_no_upstream_warning(self, runner, project):
        result = runner.invoke(
            cli,
            [
                "inbox", "add",
                "--type", "idea",
                "--text", "Regular idea",
                "--project-dir", str(project),
            ],
        )
        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["success"] is True
        assert "upstream_warning" not in payload["data"]


class TestFeedbackWithUpstream:
    def test_feedback_forwards_to_upstream_on_success(self, runner, project_with_upstream):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "https://github.com/owner/framework-repo/issues/99\n"

        with (
            patch("src.core.feedback.shutil.which", return_value="/usr/bin/gh"),
            patch("src.core.feedback.subprocess.run", return_value=mock_result),
        ):
            result = runner.invoke(
                cli,
                [
                    "inbox", "add",
                    "--type", "feedback",
                    "--text", "Bug in workflow",
                    "--notes", "Steps to reproduce",
                    "--project-dir", str(project_with_upstream),
                ],
            )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["success"] is True
        assert payload["data"]["stored"] == "local-project + upstream"
        assert payload["data"]["upstream"]["forwarded"] is True
        assert "issues/99" in payload["data"]["upstream"]["url"]

    def test_feedback_warns_on_upstream_failure(self, runner, project_with_upstream):
        with patch("src.core.feedback.shutil.which", return_value=None):
            result = runner.invoke(
                cli,
                [
                    "inbox", "add",
                    "--type", "feedback",
                    "--text", "Another bug",
                    "--project-dir", str(project_with_upstream),
                ],
            )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["success"] is True
        assert payload["data"]["stored"] == "local-project"
        assert "upstream_warning" in payload["data"]
        assert "upstream forwarding failed" in payload["data"]["upstream_warning"]

    def test_feedback_still_stored_locally_even_on_upstream_failure(
        self, runner, project_with_upstream
    ):
        with patch("src.core.feedback.shutil.which", return_value=None):
            runner.invoke(
                cli,
                [
                    "inbox", "add",
                    "--type", "feedback",
                    "--text", "Local persist test",
                    "--project-dir", str(project_with_upstream),
                ],
            )

        list_result = runner.invoke(
            cli,
            ["inbox", "list", "--project-dir", str(project_with_upstream)],
        )
        entries = json.loads(list_result.output)["data"]
        assert any(e["text"] == "Local persist test" for e in entries)
