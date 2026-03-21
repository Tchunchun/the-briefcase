"""Tests for the briefcase ship CLI command."""

from __future__ import annotations

from unittest.mock import patch, MagicMock
import subprocess

from click.testing import CliRunner

from src.cli.main import cli


def _mock_run(returncode=0, stdout="", stderr=""):
    result = MagicMock(spec=subprocess.CompletedProcess)
    result.returncode = returncode
    result.stdout = stdout
    result.stderr = stderr
    return result


class TestShipCommand:
    def setup_method(self):
        self.runner = CliRunner()

    @patch("src.cli.commands.ship.subprocess.run")
    def test_ship_clean_working_directory_full_flow(self, mock_run):
        mock_run.side_effect = [
            _mock_run(stdout=""),  # git status --porcelain (clean)
            _mock_run(stdout="main\n"),  # git rev-parse (on main)
            _mock_run(stdout="Already up to date.\n"),  # git pull --rebase
            _mock_run(stdout="465 passed in 90s\n"),  # pytest
            _mock_run(stdout=""),  # git push
        ]
        result = self.runner.invoke(cli, ["ship"])
        assert result.exit_code == 0
        assert "Shipped to main" in result.output

    @patch("src.cli.commands.ship.subprocess.run")
    def test_ship_warns_on_dirty_working_directory(self, mock_run):
        mock_run.side_effect = [
            _mock_run(stdout=" M src/foo.py\n?? bar.txt\n"),  # dirty
            _mock_run(stdout="main\n"),  # on main
            _mock_run(stdout="Already up to date.\n"),  # rebase
            _mock_run(stdout="465 passed\n"),  # tests
            _mock_run(stdout=""),  # push
        ]
        result = self.runner.invoke(cli, ["ship"])
        assert result.exit_code == 0
        assert "uncommitted changes" in result.output
        assert "M src/foo.py" in result.output

    @patch("src.cli.commands.ship.subprocess.run")
    def test_ship_aborts_on_rebase_failure(self, mock_run):
        mock_run.side_effect = [
            _mock_run(stdout=""),  # clean
            _mock_run(stdout="main\n"),  # on main
            _mock_run(returncode=1, stderr="CONFLICT in foo.py"),  # rebase fails
        ]
        result = self.runner.invoke(cli, ["ship"])
        assert result.exit_code != 0
        assert "Rebase failed" in result.output

    @patch("src.cli.commands.ship.subprocess.run")
    def test_ship_aborts_on_test_failure(self, mock_run):
        mock_run.side_effect = [
            _mock_run(stdout=""),  # clean
            _mock_run(stdout="main\n"),  # on main
            _mock_run(stdout="Already up to date.\n"),  # rebase ok
            _mock_run(returncode=1, stdout="FAILED test_foo.py::test_bar\n1 failed\n", stderr=""),  # tests fail
        ]
        result = self.runner.invoke(cli, ["ship"])
        assert result.exit_code != 0
        assert "Tests failed" in result.output

    @patch("src.cli.commands.ship.subprocess.run")
    def test_ship_push_failure(self, mock_run):
        mock_run.side_effect = [
            _mock_run(stdout=""),  # clean
            _mock_run(stdout="main\n"),  # on main
            _mock_run(stdout="Already up to date.\n"),  # rebase
            _mock_run(stdout="465 passed\n"),  # tests pass
            _mock_run(returncode=1, stderr="rejected: fetch first"),  # push fails
        ]
        result = self.runner.invoke(cli, ["ship"])
        assert result.exit_code != 0
        assert "Push failed" in result.output

    @patch("src.cli.commands.ship.subprocess.run")
    def test_ship_custom_branch(self, mock_run):
        mock_run.side_effect = [
            _mock_run(stdout=""),  # clean
            _mock_run(stdout="develop\n"),  # on develop
            _mock_run(stdout="Already up to date.\n"),  # rebase
            _mock_run(stdout="465 passed\n"),  # tests
            _mock_run(stdout=""),  # push
        ]
        result = self.runner.invoke(cli, ["ship", "develop"])
        assert result.exit_code == 0
        assert "Shipped to develop" in result.output

    @patch("src.cli.commands.ship.subprocess.run")
    def test_ship_skip_tests(self, mock_run):
        mock_run.side_effect = [
            _mock_run(stdout=""),  # clean
            _mock_run(stdout="main\n"),  # on main
            _mock_run(stdout="Already up to date.\n"),  # rebase
            # no pytest call
            _mock_run(stdout=""),  # push
        ]
        result = self.runner.invoke(cli, ["ship", "--skip-tests"])
        assert result.exit_code == 0
        assert "Skipping tests" in result.output
        assert mock_run.call_count == 4  # no pytest call

    @patch("src.cli.commands.ship.subprocess.run")
    def test_ship_from_feature_branch_merges_first(self, mock_run):
        mock_run.side_effect = [
            _mock_run(stdout=""),  # clean
            _mock_run(stdout="feature/foo\n"),  # on feature branch
            _mock_run(stdout=""),  # checkout main
            _mock_run(stdout="Fast-forward\n"),  # merge feature/foo
            _mock_run(stdout="Already up to date.\n"),  # rebase
            _mock_run(stdout="465 passed\n"),  # tests
            _mock_run(stdout=""),  # push
        ]
        result = self.runner.invoke(cli, ["ship"])
        assert result.exit_code == 0
        assert "Merging feature/foo into main" in result.output
        assert "Shipped to main" in result.output

    @patch("src.cli.commands.ship.subprocess.run")
    def test_ship_merge_failure_returns_to_feature_branch(self, mock_run):
        mock_run.side_effect = [
            _mock_run(stdout=""),  # clean
            _mock_run(stdout="feature/foo\n"),  # on feature branch
            _mock_run(stdout=""),  # checkout main
            _mock_run(returncode=1, stderr="CONFLICT"),  # merge fails
            _mock_run(stdout=""),  # merge --abort
            _mock_run(stdout=""),  # checkout feature/foo
        ]
        result = self.runner.invoke(cli, ["ship"])
        assert result.exit_code != 0
        assert "Merge failed" in result.output
