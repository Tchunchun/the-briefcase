"""Unit tests for GitSync (src/sync/git_sync.py).

All git subprocess calls are mocked — no real git repository required.
"""

from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, call, patch

import pytest

from src.sync.git_sync import GitSync, GitSyncConfig, GitSyncError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_proc(returncode: int = 0, stdout: str = "", stderr: str = "") -> MagicMock:
    """Return a mock CompletedProcess."""
    m = MagicMock(spec=subprocess.CompletedProcess)
    m.returncode = returncode
    m.stdout = stdout
    m.stderr = stderr
    return m


def _syncer(tmp_path) -> GitSync:
    cfg = GitSyncConfig(
        remote="origin",
        remote_url="git@github.com:user/repo.git",
        branch="main",
        paths=["docs/plan/", "_project/"],
    )
    return GitSync(tmp_path, cfg)


# ---------------------------------------------------------------------------
# _run
# ---------------------------------------------------------------------------

class TestRun:
    def test_run_success_returns_process(self, tmp_path):
        syncer = _syncer(tmp_path)
        proc = _make_proc(0, stdout="ok\n")
        with patch("subprocess.run", return_value=proc) as mock_run:
            result = syncer._run(["git", "status"])
        mock_run.assert_called_once()
        assert result.stdout == "ok\n"

    def test_run_nonzero_raises_without_check(self, tmp_path):
        """check=False should not raise even on non-zero exit."""
        syncer = _syncer(tmp_path)
        proc = _make_proc(1, stderr="error")
        with patch("subprocess.run", return_value=proc):
            result = syncer._run(["git", "bad"], check=False)
        assert result.returncode == 1

    def test_run_nonzero_raises_with_check(self, tmp_path):
        syncer = _syncer(tmp_path)
        proc = _make_proc(1, stderr="fatal: not a git repo")
        with patch("subprocess.run", return_value=proc):
            with pytest.raises(GitSyncError, match="git command failed"):
                syncer._run(["git", "status"])

    def test_run_raises_when_git_not_found(self, tmp_path):
        syncer = _syncer(tmp_path)
        with patch("subprocess.run", side_effect=FileNotFoundError):
            with pytest.raises(GitSyncError, match="git executable not found"):
                syncer._run(["git", "status"])


# ---------------------------------------------------------------------------
# push
# ---------------------------------------------------------------------------

class TestPush:
    def test_push_clean_returns_no_changes(self, tmp_path):
        syncer = _syncer(tmp_path)
        # status --porcelain → empty output = clean
        status_proc = _make_proc(0, stdout="")
        with patch("subprocess.run", return_value=status_proc):
            result = syncer.push()
        assert result["committed"] == 0
        assert result["pushed"] is False
        assert "Nothing to push" in result["message"]

    def test_push_dirty_commits_and_pushes(self, tmp_path):
        syncer = _syncer(tmp_path)
        # First call: git status --porcelain → dirty files
        # Subsequent calls: git add, git commit, git push
        dirty_proc = _make_proc(0, stdout=" M docs/plan/backlog.md\n?? _project/notes.md")
        ok_proc = _make_proc(0)
        with patch("subprocess.run", side_effect=[dirty_proc, ok_proc, ok_proc, ok_proc]) as mock_run:
            result = syncer.push()

        assert result["committed"] == 2
        assert result["pushed"] is True
        # Verify commit and push were called
        calls = [c.args[0] for c in mock_run.call_args_list]
        assert any("add" in c for c in calls)
        assert any("commit" in c for c in calls)
        assert any("push" in c for c in calls)

    def test_push_dry_run_returns_count_without_writing(self, tmp_path):
        syncer = _syncer(tmp_path)
        dirty_proc = _make_proc(0, stdout=" M docs/plan/backlog.md\n M _project/storage.yaml")
        with patch("subprocess.run", return_value=dirty_proc) as mock_run:
            result = syncer.push(dry_run=True)

        assert result["dry_run"] is True
        assert result["committed"] == 2
        assert result["pushed"] is False
        # Only the status call should have been made
        assert mock_run.call_count == 1

    def test_push_raises_git_sync_error_on_failure(self, tmp_path):
        syncer = _syncer(tmp_path)
        dirty_proc = _make_proc(0, stdout=" M docs/plan/backlog.md")
        fail_proc = _make_proc(1, stderr="push rejected")
        # status → dirty, add → ok, commit → ok, push → fail
        with patch("subprocess.run", side_effect=[dirty_proc, _make_proc(0), _make_proc(0), fail_proc]):
            with pytest.raises(GitSyncError, match="git command failed"):
                syncer.push()


# ---------------------------------------------------------------------------
# pull
# ---------------------------------------------------------------------------

class TestPull:
    def test_pull_up_to_date(self, tmp_path):
        syncer = _syncer(tmp_path)
        # fetch → ok, incoming_files → empty diff
        fetch_proc = _make_proc(0)
        merge_base_proc = _make_proc(0, stdout="abc123\n")
        diff_proc = _make_proc(0, stdout="")
        with patch("subprocess.run", side_effect=[fetch_proc, merge_base_proc, diff_proc]):
            result = syncer.pull()

        assert result["applied"] is False
        assert result["incoming"] == []
        assert "up to date" in result["message"].lower()

    def test_pull_applies_new_files(self, tmp_path):
        syncer = _syncer(tmp_path)
        fetch_proc = _make_proc(0)
        merge_base_proc = _make_proc(0, stdout="abc123\n")
        diff_proc = _make_proc(0, stdout="docs/plan/inbox.md\n_project/decisions.md")
        # local dirty check → clean
        dirty_proc = _make_proc(0, stdout="")
        merge_proc = _make_proc(0)

        with patch("subprocess.run", side_effect=[
            fetch_proc, merge_base_proc, diff_proc, dirty_proc, merge_proc
        ]):
            result = syncer.pull()

        assert result["applied"] is True
        assert len(result["incoming"]) == 2
        assert result["conflicts"] == []

    def test_pull_dry_run_returns_incoming_without_merging(self, tmp_path):
        syncer = _syncer(tmp_path)
        fetch_proc = _make_proc(0)
        merge_base_proc = _make_proc(0, stdout="abc123\n")
        diff_proc = _make_proc(0, stdout="docs/plan/inbox.md")

        with patch("subprocess.run", side_effect=[fetch_proc, merge_base_proc, diff_proc]) as mock_run:
            result = syncer.pull(dry_run=True)

        assert result["dry_run"] is True
        assert result["applied"] is False
        assert "docs/plan/inbox.md" in result["incoming"]
        # No merge call should have been made
        calls = [c.args[0] for c in mock_run.call_args_list]
        assert not any("merge" in c for c in calls)

    def test_pull_aborts_on_conflicts(self, tmp_path):
        """When local dirty files overlap with incoming, pull should abort."""
        syncer = _syncer(tmp_path)
        fetch_proc = _make_proc(0)
        merge_base_proc = _make_proc(0, stdout="abc123\n")
        diff_proc = _make_proc(0, stdout="docs/plan/inbox.md")
        # local dirty shows same file
        dirty_proc = _make_proc(0, stdout=" M docs/plan/inbox.md")

        with patch("subprocess.run", side_effect=[fetch_proc, merge_base_proc, diff_proc, dirty_proc]):
            result = syncer.pull()

        assert result["applied"] is False
        assert "docs/plan/inbox.md" in result["conflicts"]
        assert "conflict" in result["message"].lower()


# ---------------------------------------------------------------------------
# status
# ---------------------------------------------------------------------------

class TestStatus:
    def test_status_clean_reachable(self, tmp_path):
        syncer = _syncer(tmp_path)
        ls_remote_proc = _make_proc(0, stdout="abc123\trefs/heads/main")
        dirty_proc = _make_proc(0, stdout="")
        fetch_proc = _make_proc(0)
        merge_base_proc = _make_proc(0, stdout="abc123\n")
        diff_proc = _make_proc(0, stdout="")

        with patch("subprocess.run", side_effect=[
            dirty_proc, ls_remote_proc, fetch_proc, merge_base_proc, diff_proc
        ]):
            status = syncer.status()

        assert status["remote_reachable"] is True
        assert status["dirty_files"] == []
        assert status["incoming_files"] == []

    def test_status_unreachable_remote(self, tmp_path):
        syncer = _syncer(tmp_path)
        dirty_proc = _make_proc(0, stdout="")
        ls_remote_proc = _make_proc(1, stderr="could not connect")

        with patch("subprocess.run", side_effect=[dirty_proc, ls_remote_proc]):
            status = syncer.status()

        assert status["remote_reachable"] is False
        assert status["incoming_files"] == []


# ---------------------------------------------------------------------------
# configure_remote
# ---------------------------------------------------------------------------

class TestConfigureRemote:
    def test_adds_new_remote(self, tmp_path):
        syncer = _syncer(tmp_path)
        get_url_proc = _make_proc(1)  # remote doesn't exist
        add_proc = _make_proc(0)

        with patch("subprocess.run", side_effect=[get_url_proc, add_proc]):
            added = syncer.configure_remote("git@github.com:user/new-repo.git")

        assert added is True

    def test_updates_existing_remote(self, tmp_path):
        syncer = _syncer(tmp_path)
        get_url_proc = _make_proc(0, stdout="git@github.com:user/old-repo.git")
        set_url_proc = _make_proc(0)

        with patch("subprocess.run", side_effect=[get_url_proc, set_url_proc]):
            added = syncer.configure_remote("git@github.com:user/new-repo.git")

        assert added is False
