"""Unit tests for briefcase migrate notion-to-git (src/cli/commands/migrate.py)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from src.cli.commands.migrate import migrate


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def notion_project(tmp_path: Path) -> Path:
    """A minimal project directory configured with backend: notion."""
    project_dir = tmp_path / "_project"
    project_dir.mkdir()
    (project_dir / "storage.yaml").write_text(
        "backend: notion\n"
        "notion:\n"
        "  parent_page_id: abc123\n"
        "  parent_page_url: https://notion.so/abc123\n"
        "  databases: {}\n"
        "  seeded_template_versions: {}\n"
    )
    # Also create .env with NOTION_API_KEY so the command can proceed
    (tmp_path / ".env").write_text("NOTION_API_KEY=secret-token\n")
    return tmp_path


@pytest.fixture()
def git_project(tmp_path: Path) -> Path:
    """A minimal project directory configured with backend: git."""
    project_dir = tmp_path / "_project"
    project_dir.mkdir()
    (project_dir / "storage.yaml").write_text(
        "backend: git\n"
        "git:\n"
        "  remote: origin\n"
        "  remote_url: git@github.com:user/repo.git\n"
        "  branch: main\n"
        "  paths:\n"
        "    - docs/plan/\n"
        "    - _project/\n"
    )
    return tmp_path


# ---------------------------------------------------------------------------
# Abort conditions
# ---------------------------------------------------------------------------

class TestAbortConditions:
    def test_aborts_if_backend_is_not_notion(self, runner, git_project):
        result = runner.invoke(
            migrate,
            ["notion-to-git", "--project-dir", str(git_project), "--remote-url", "git@github.com:user/r.git"],
        )
        assert result.exit_code != 0
        assert "not 'notion'" in result.output

    def test_aborts_if_notion_api_key_missing(self, runner, tmp_path):
        project_dir = tmp_path / "_project"
        project_dir.mkdir()
        (project_dir / "storage.yaml").write_text(
            "backend: notion\nnotion:\n  parent_page_id: abc\n  parent_page_url: x\n  databases: {}\n  seeded_template_versions: {}\n"
        )
        # No .env file → no key
        with patch.dict("os.environ", {}, clear=True):
            result = runner.invoke(
                migrate,
                ["notion-to-git", "--project-dir", str(tmp_path), "--remote-url", "git@github.com:user/r.git"],
            )
        assert result.exit_code != 0
        assert "NOTION_API_KEY" in result.output


# ---------------------------------------------------------------------------
# Dry run
# ---------------------------------------------------------------------------

class TestDryRun:
    def test_dry_run_does_not_write_storage_yaml(self, runner, notion_project):
        original = (notion_project / "_project" / "storage.yaml").read_text()
        result = runner.invoke(
            migrate,
            [
                "notion-to-git",
                "--dry-run",
                "--project-dir", str(notion_project),
                "--remote-url", "git@github.com:user/r.git",
            ],
        )
        assert result.exit_code == 0, result.output
        # storage.yaml must not have changed
        assert (notion_project / "_project" / "storage.yaml").read_text() == original

    def test_dry_run_does_not_call_sync_to_local(self, runner, notion_project):
        with patch("src.cli.commands.migrate.notion_to_git") as mock_cmd:
            # We patch the whole Click command to ensure sync_to_local isn't imported/called
            pass

        # More precise: patch sync_to_local at the module level
        with patch("src.sync.to_local.sync_to_local") as mock_sync:
            result = runner.invoke(
                migrate,
                [
                    "notion-to-git",
                    "--dry-run",
                    "--project-dir", str(notion_project),
                    "--remote-url", "git@github.com:user/r.git",
                ],
            )
        assert result.exit_code == 0, result.output
        mock_sync.assert_not_called()


# ---------------------------------------------------------------------------
# Successful migration
# ---------------------------------------------------------------------------

class TestSuccessfulMigration:
    def _mock_sync_result(self):
        return {
            "fetched": 5, "created": 3, "skipped": 2,
            "failed": 0, "conflicts": 0, "snapshot_hash": "abc",
        }

    def _mock_push_result(self):
        return {"committed": 5, "pushed": True, "dry_run": False, "message": "Pushed 5 files."}

    def test_storage_yaml_is_rewritten_to_git(self, runner, notion_project):
        syncer_mock = MagicMock()
        syncer_mock.configure_remote.return_value = True
        syncer_mock.push.return_value = self._mock_push_result()

        with (
            patch("src.sync.to_local.sync_to_local", return_value=self._mock_sync_result()),
            patch("src.sync.git_sync.GitSync", return_value=syncer_mock),
            patch("click.confirm", return_value=True),
        ):
            result = runner.invoke(
                migrate,
                [
                    "notion-to-git",
                    "--project-dir", str(notion_project),
                    "--remote-url", "git@github.com:user/r.git",
                    "--branch", "main",
                    "--remote", "origin",
                ],
            )

        assert result.exit_code == 0, result.output
        new_yaml = (notion_project / "_project" / "storage.yaml").read_text()
        assert "backend: git" in new_yaml
        assert "notion" not in new_yaml.split("backend:")[1].split("\n")[0]

    def test_git_operations_called_after_rewrite(self, runner, notion_project):
        syncer_mock = MagicMock()
        syncer_mock.configure_remote.return_value = True
        syncer_mock.push.return_value = self._mock_push_result()

        with (
            patch("src.sync.to_local.sync_to_local", return_value=self._mock_sync_result()),
            patch("src.sync.git_sync.GitSync", return_value=syncer_mock),
            patch("click.confirm", return_value=True),
        ):
            result = runner.invoke(
                migrate,
                [
                    "notion-to-git",
                    "--project-dir", str(notion_project),
                    "--remote-url", "git@github.com:user/r.git",
                ],
            )

        assert result.exit_code == 0, result.output
        syncer_mock.configure_remote.assert_called_once_with("git@github.com:user/r.git")
        syncer_mock.push.assert_called_once_with(dry_run=False)

    def test_aborts_if_user_declines_confirmation(self, runner, notion_project):
        with (
            patch("src.sync.to_local.sync_to_local", return_value=self._mock_sync_result()),
            patch("click.confirm", return_value=False),
        ):
            result = runner.invoke(
                migrate,
                [
                    "notion-to-git",
                    "--project-dir", str(notion_project),
                    "--remote-url", "git@github.com:user/r.git",
                ],
            )
        assert result.exit_code == 0, result.output
        assert "Aborted" in result.output
        # storage.yaml should still be notion
        assert "backend: notion" in (notion_project / "_project" / "storage.yaml").read_text()

    def test_shows_notion_api_key_warning_when_env_present(self, runner, notion_project):
        """Verify the reminder to remove NOTION_API_KEY from .env is shown."""
        syncer_mock = MagicMock()
        syncer_mock.configure_remote.return_value = True
        syncer_mock.push.return_value = self._mock_push_result()

        with (
            patch("src.sync.to_local.sync_to_local", return_value=self._mock_sync_result()),
            patch("src.sync.git_sync.GitSync", return_value=syncer_mock),
            patch("click.confirm", return_value=True),
        ):
            result = runner.invoke(
                migrate,
                [
                    "notion-to-git",
                    "--project-dir", str(notion_project),
                    "--remote-url", "git@github.com:user/r.git",
                ],
            )

        assert result.exit_code == 0, result.output
        assert "NOTION_API_KEY" in result.output

    def test_aborts_if_notion_pull_has_failures(self, runner, notion_project):
        bad_result = {
            "fetched": 2, "created": 0, "skipped": 0,
            "failed": 1, "conflicts": 0, "snapshot_hash": "x",
        }
        with patch("src.sync.to_local.sync_to_local", return_value=bad_result):
            result = runner.invoke(
                migrate,
                [
                    "notion-to-git",
                    "--project-dir", str(notion_project),
                    "--remote-url", "git@github.com:user/r.git",
                ],
            )
        assert result.exit_code != 0
        assert "failed" in result.output.lower()
