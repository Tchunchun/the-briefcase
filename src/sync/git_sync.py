"""Git-based sync: push/pull artifact directories to/from a private remote.

Used when backend = 'git'. Reads/writes remain local (via LocalBackend);
this module handles explicit push/pull operations triggered by the user via
`briefcase sync push` and `briefcase sync pull`.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path


DEFAULT_PATHS = ["docs/plan/", "_project/"]


@dataclass
class GitSyncConfig:
    """Runtime config for GitSync, derived from StorageConfig.git."""

    remote: str = "origin"
    remote_url: str = ""
    branch: str = "main"
    paths: list[str] = field(default_factory=lambda: list(DEFAULT_PATHS))


class GitSyncError(RuntimeError):
    """Raised when a git operation fails."""


class GitSync:
    """Manages push/pull of artifact directories via git.

    All operations are path-scoped: only the configured paths
    (default: docs/plan/ and _project/) are staged/compared.
    """

    def __init__(self, project_root: str | Path, config: GitSyncConfig) -> None:
        self.root = Path(project_root)
        self.cfg = config

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def status(self) -> dict:
        """Return the current sync status without modifying anything.

        Returns a dict:
            {
                "dirty_files": list[str],   # locally modified artifact files
                "incoming_files": list[str], # files changed on remote vs local
                "remote_reachable": bool,
            }
        """
        dirty = self._local_dirty_files()
        remote_reachable = self._check_remote_reachable()
        incoming: list[str] = []
        if remote_reachable:
            try:
                self._run(["git", "fetch", self.cfg.remote])
                incoming = self._incoming_files()
            except GitSyncError:
                pass
        return {
            "dirty_files": dirty,
            "incoming_files": incoming,
            "remote_reachable": remote_reachable,
        }

    def push(self, *, dry_run: bool = False) -> dict:
        """Stage artifact dirs, commit if dirty, push to remote.

        Returns:
            {committed: int, pushed: bool, dry_run: bool, message: str}
        """
        dirty = self._local_dirty_files()

        if not dirty:
            return {
                "committed": 0,
                "pushed": False,
                "dry_run": dry_run,
                "message": "Nothing to push — working tree is clean.",
            }

        if dry_run:
            return {
                "committed": len(dirty),
                "pushed": False,
                "dry_run": True,
                "message": f"{len(dirty)} file(s) would be committed.",
                "files": dirty,
            }

        self._run(["git", "add", "--"] + self.cfg.paths)
        self._run(
            ["git", "commit", "-m", f"chore: sync artifacts [briefcase]"]
        )
        self._run(["git", "push", self.cfg.remote, f"HEAD:{self.cfg.branch}"])

        return {
            "committed": len(dirty),
            "pushed": True,
            "dry_run": False,
            "message": f"Pushed {len(dirty)} file change(s) to {self.cfg.remote}/{self.cfg.branch}.",
        }

    def pull(self, *, dry_run: bool = False) -> dict:
        """Fetch from remote and merge into current branch (artifact paths only).

        Uses merge (not rebase) to avoid rewriting commit history.

        Returns:
            {incoming: list[str], applied: bool, dry_run: bool, conflicts: list[str]}
        """
        self._run(["git", "fetch", self.cfg.remote])
        incoming = self._incoming_files()

        if not incoming:
            return {
                "incoming": [],
                "applied": False,
                "dry_run": dry_run,
                "conflicts": [],
                "message": "Already up to date.",
            }

        if dry_run:
            return {
                "incoming": incoming,
                "applied": False,
                "dry_run": True,
                "conflicts": [],
                "message": f"{len(incoming)} file(s) would be updated.",
            }

        dirty = self._local_dirty_files()
        conflicts = [f for f in dirty if f in incoming]

        if conflicts:
            return {
                "incoming": incoming,
                "applied": False,
                "dry_run": False,
                "conflicts": conflicts,
                "message": (
                    f"{len(conflicts)} file(s) have local changes that conflict "
                    "with incoming changes. Commit or stash local changes first."
                ),
            }

        self._run(
            ["git", "merge", "--no-edit", f"{self.cfg.remote}/{self.cfg.branch}"]
        )

        return {
            "incoming": incoming,
            "applied": True,
            "dry_run": False,
            "conflicts": [],
            "message": f"Pulled {len(incoming)} file change(s) from {self.cfg.remote}/{self.cfg.branch}.",
        }

    def configure_remote(self, remote_url: str) -> bool:
        """Add or update the git remote.

        Returns True if the remote was added (new), False if updated (existing).
        """
        try:
            result = self._run(
                ["git", "remote", "get-url", self.cfg.remote], check=False
            )
            if result.returncode == 0:
                self._run(
                    ["git", "remote", "set-url", self.cfg.remote, remote_url]
                )
                return False
        except GitSyncError:
            pass

        self._run(["git", "remote", "add", self.cfg.remote, remote_url])
        return True

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _local_dirty_files(self) -> list[str]:
        """Return list of locally modified/added/deleted files within artifact paths."""
        result = self._run(
            ["git", "status", "--porcelain", "--"] + self.cfg.paths
        )
        lines = [l for l in result.stdout.splitlines() if l.strip()]
        # Strip the two-char status prefix and leading space
        return [l[3:].strip() for l in lines]

    def _incoming_files(self) -> list[str]:
        """Return files that differ between local HEAD and remote branch."""
        try:
            merge_base = self._run(
                [
                    "git",
                    "merge-base",
                    "HEAD",
                    f"{self.cfg.remote}/{self.cfg.branch}",
                ]
            ).stdout.strip()
        except GitSyncError:
            # No common ancestor — remote branch may be brand new
            merge_base = None

        if merge_base:
            diff_result = self._run(
                [
                    "git",
                    "diff",
                    "--name-only",
                    merge_base,
                    f"{self.cfg.remote}/{self.cfg.branch}",
                ]
            )
        else:
            diff_result = self._run(
                [
                    "git",
                    "diff",
                    "--name-only",
                    f"{self.cfg.remote}/{self.cfg.branch}",
                ]
            )

        all_changed = diff_result.stdout.splitlines()
        return [
            f
            for f in all_changed
            if any(f.startswith(p) for p in self.cfg.paths)
        ]

    def _check_remote_reachable(self) -> bool:
        """Return True if the remote can be reached (ls-remote succeeds)."""
        try:
            result = self._run(
                ["git", "ls-remote", "--exit-code", self.cfg.remote, "HEAD"],
                check=False,
            )
            return result.returncode == 0
        except GitSyncError:
            return False

    def _run(
        self, cmd: list[str], *, check: bool = True
    ) -> subprocess.CompletedProcess:
        """Run a git subprocess, raising GitSyncError on failure when check=True."""
        try:
            result = subprocess.run(
                cmd,
                cwd=self.root,
                capture_output=True,
                text=True,
                check=False,
            )
        except FileNotFoundError as e:
            raise GitSyncError(
                "git executable not found. Install git and try again."
            ) from e

        if check and result.returncode != 0:
            raise GitSyncError(
                f"git command failed: {' '.join(cmd)}\n"
                f"stdout: {result.stdout.strip()}\n"
                f"stderr: {result.stderr.strip()}"
            )
        return result


def git_sync_from_config(
    project_root: str | Path, config: "StorageConfig"  # noqa: F821
) -> GitSync:
    """Build a GitSync from a StorageConfig.

    Raises ValueError if the config does not specify a git backend.
    """
    if not config.is_git():
        raise ValueError(
            f"Backend is '{config.backend}', not 'git'. "
            "GitSync is only available for the git backend."
        )

    from src.core.storage.config import GitSyncConfig as _Cfg  # local import

    git_cfg = config.git
    if git_cfg is None:
        sync_cfg = _Cfg()
    else:
        sync_cfg = _Cfg(
            remote=git_cfg.remote,
            remote_url=git_cfg.remote_url,
            branch=git_cfg.branch,
            paths=list(git_cfg.paths),
        )

    return GitSync(project_root, sync_cfg)
