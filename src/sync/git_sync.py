"""Git-based sync: export artifact directories to/from a shared private remote.

Used when backend = 'git'. Reads/writes remain local (via LocalBackend);
this module handles explicit push/pull operations triggered by the user via
`briefcase sync push` and `briefcase sync pull`.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.storage.config import StorageConfig


DEFAULT_PATHS = ["docs/plan/", "_project/"]
BOOTSTRAP_ARTIFACTS = {"_project/storage.yaml"}


@dataclass
class GitSyncConfig:
    """Runtime config for GitSync, derived from StorageConfig.git."""

    remote: str = "origin"
    remote_url: str = ""
    branch: str = "main"
    project_slug: str = ""
    paths: list[str] = field(default_factory=lambda: list(DEFAULT_PATHS))


class GitSyncError(RuntimeError):
    """Raised when a git operation fails."""


class GitSync:
    """Manages artifact-only sync via a dedicated mirror repository.

    The working repository remains the local source of truth for edits. Sync
    operations copy configured artifact paths into a mirror repository under
    `.briefcase/git-sync/<project-slug>/`, commit those exported files under
    `projects/<project-slug>/` on the shared remote, and pull them back into
    the local artifact paths when requested.
    """

    def __init__(self, project_root: str | Path, config: GitSyncConfig) -> None:
        self.root = Path(project_root)
        self.cfg = config

    def status(self) -> dict:
        """Return the current sync status without modifying local artifacts."""
        dirty = self._local_dirty_files()
        remote_reachable = self._check_remote_reachable()
        incoming: list[str] = []
        if remote_reachable:
            try:
                self._ensure_mirror_repo()
                self._fetch_remote()
                incoming = self._incoming_files()
            except GitSyncError:
                pass
        return {
            "dirty_files": dirty,
            "incoming_files": incoming,
            "remote_reachable": remote_reachable,
        }

    def push(self, *, dry_run: bool = False) -> dict:
        """Export local artifacts, commit them in the mirror repo, and push."""
        project_slug = self._ensure_project_slug()
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
                "message": (
                    f"{len(dirty)} file(s) would be exported to "
                    f"projects/{project_slug}/."
                ),
                "files": dirty,
            }

        self._ensure_mirror_repo()
        self._fetch_remote()
        self._checkout_remote_state()
        self._export_local_artifacts_to_mirror()
        changed_files = self._mirror_dirty_files()

        if not changed_files:
            return {
                "committed": 0,
                "pushed": False,
                "dry_run": False,
                "message": (
                    f"Artifact mirror is already up to date for projects/{project_slug}/."
                ),
            }

        self._run_in_mirror(["git", "add", "--", self._namespace_arg()])
        self._run_in_mirror(
            ["git", "commit", "-m", "chore: sync artifacts [briefcase]"]
        )
        self._run_in_mirror(
            ["git", "push", self.cfg.remote, f"HEAD:{self.cfg.branch}"]
        )

        return {
            "committed": len(changed_files),
            "pushed": True,
            "dry_run": False,
            "message": (
                f"Pushed artifact snapshot for {project_slug} to "
                f"{self.cfg.remote}/{self.cfg.branch}. Remote path: "
                f"projects/{project_slug}/"
            ),
        }

    def pull(self, *, dry_run: bool = False) -> dict:
        """Fetch from the shared remote and restore local artifact files."""
        project_slug = self._ensure_project_slug()
        self._ensure_mirror_repo()
        self._fetch_remote()
        incoming = self._incoming_files()
        dirty_before_checkout = self._local_dirty_files()
        self._checkout_remote_state()
        restorable = self._restorable_files()

        if not incoming and not restorable:
            return {
                "incoming": [],
                "applied": False,
                "dry_run": dry_run,
                "conflicts": [],
                "message": "Already up to date.",
            }

        if dry_run:
            planned = sorted(set(incoming) | set(restorable))
            return {
                "incoming": planned,
                "applied": False,
                "dry_run": True,
                "conflicts": [],
                "message": (
                    f"{len(planned)} file(s) would be updated from "
                    f"projects/{project_slug}/."
                ),
            }

        conflicts = [
            path
            for path in dirty_before_checkout
            if path in incoming and path not in BOOTSTRAP_ARTIFACTS
        ]
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

        self._import_mirror_artifacts_to_local()

        return {
            "incoming": sorted(set(incoming) | set(restorable)),
            "applied": True,
            "dry_run": False,
            "conflicts": [],
            "message": (
                f"Pulled artifact snapshot for {project_slug} from "
                f"{self.cfg.remote}/{self.cfg.branch}. Remote path: "
                f"projects/{project_slug}/"
            ),
        }

    def configure_remote(self, remote_url: str) -> bool:
        """Add or update the mirror repository remote."""
        self._ensure_project_slug()
        self._ensure_mirror_repo()
        try:
            result = self._run_in_mirror(
                ["git", "remote", "get-url", self.cfg.remote],
                check=False,
            )
            if result.returncode == 0:
                self._run_in_mirror(
                    ["git", "remote", "set-url", self.cfg.remote, remote_url]
                )
                self.cfg.remote_url = remote_url
                return False
        except GitSyncError:
            pass

        self._run_in_mirror(
            ["git", "remote", "add", self.cfg.remote, remote_url]
        )
        self.cfg.remote_url = remote_url
        return True

    def _ensure_project_slug(self) -> str:
        project_slug = self.cfg.project_slug.strip()
        if not project_slug:
            raise GitSyncError(
                "Git sync requires git.project_slug in _project/storage.yaml. "
                "Run `briefcase setup --backend git` again or update the config."
            )
        return project_slug

    def _mirror_dir(self) -> Path:
        return self.root / ".briefcase" / "git-sync" / self._ensure_project_slug()

    def _namespace_root(self) -> Path:
        return Path("projects") / self._ensure_project_slug()

    def _namespace_arg(self) -> str:
        return self._namespace_root().as_posix()

    def _ensure_mirror_repo(self) -> None:
        mirror_dir = self._mirror_dir()
        mirror_dir.mkdir(parents=True, exist_ok=True)
        if not (mirror_dir / ".git").exists():
            self._run_in_mirror(["git", "init", "-b", self.cfg.branch])
            self._run_in_mirror(["git", "config", "user.name", "briefcase-sync"])
            self._run_in_mirror(["git", "config", "user.email", "briefcase-sync@local"])

        if self.cfg.remote_url:
            result = self._run_in_mirror(
                ["git", "remote", "get-url", self.cfg.remote],
                check=False,
            )
            if result.returncode == 0:
                self._run_in_mirror(
                    ["git", "remote", "set-url", self.cfg.remote, self.cfg.remote_url]
                )
            else:
                self._run_in_mirror(
                    ["git", "remote", "add", self.cfg.remote, self.cfg.remote_url]
                )

    def _fetch_remote(self) -> None:
        self._run_in_mirror(["git", "fetch", self.cfg.remote], check=False)

    def _remote_branch_exists(self) -> bool:
        result = self._run_in_mirror(
            ["git", "rev-parse", "--verify", f"{self.cfg.remote}/{self.cfg.branch}"],
            check=False,
        )
        return result.returncode == 0

    def _mirror_has_head(self) -> bool:
        result = self._run_in_mirror(
            ["git", "rev-parse", "--verify", "HEAD"],
            check=False,
        )
        return result.returncode == 0

    def _checkout_remote_state(self) -> None:
        if self._remote_branch_exists():
            self._run_in_mirror(
                ["git", "checkout", "-B", self.cfg.branch, f"{self.cfg.remote}/{self.cfg.branch}"]
            )
            return

        local_branch = self._run_in_mirror(
            ["git", "rev-parse", "--verify", self.cfg.branch],
            check=False,
        )
        if local_branch.returncode == 0:
            self._run_in_mirror(["git", "checkout", self.cfg.branch])
            return

        self._run_in_mirror(["git", "checkout", "--orphan", self.cfg.branch])

    def _export_local_artifacts_to_mirror(self) -> None:
        namespace_dir = self._mirror_dir() / self._namespace_root()
        if namespace_dir.exists():
            shutil.rmtree(namespace_dir)
        namespace_dir.mkdir(parents=True, exist_ok=True)

        for configured_path in self.cfg.paths:
            relative_path = Path(configured_path.rstrip("/"))
            source = self.root / relative_path
            destination = namespace_dir / relative_path
            if not source.exists():
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            if source.is_dir():
                shutil.copytree(source, destination, dirs_exist_ok=True)
            else:
                shutil.copy2(source, destination)

    def _import_mirror_artifacts_to_local(self) -> None:
        namespace_dir = self._mirror_dir() / self._namespace_root()
        for configured_path in self.cfg.paths:
            relative_path = Path(configured_path.rstrip("/"))
            source = namespace_dir / relative_path
            destination = self.root / relative_path
            if destination.exists():
                if destination.is_dir():
                    shutil.rmtree(destination)
                else:
                    destination.unlink()
            if not source.exists():
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            if source.is_dir():
                shutil.copytree(source, destination)
            else:
                shutil.copy2(source, destination)

    def _local_dirty_files(self) -> list[str]:
        """Return artifact files that differ from the last synced mirror state."""
        local_files = self._list_artifact_files(self.root)
        mirror_files = self._list_artifact_files(
            self._mirror_dir() / self._namespace_root(),
        )

        dirty: list[str] = []
        for relative_path in sorted(local_files | mirror_files):
            local_path = self.root / relative_path
            mirror_path = self._mirror_dir() / self._namespace_root() / relative_path
            if not local_path.exists() or not mirror_path.exists():
                dirty.append(relative_path.as_posix())
                continue
            if local_path.read_bytes() != mirror_path.read_bytes():
                dirty.append(relative_path.as_posix())
        return dirty

    def _restorable_files(self) -> list[str]:
        """Return artifact files that exist in the mirror but not locally."""
        local_files = self._list_artifact_files(self.root)
        mirror_files = self._list_artifact_files(
            self._mirror_dir() / self._namespace_root(),
        )
        missing = []
        for relative_path in sorted(mirror_files - local_files):
            missing.append(relative_path.as_posix())
        return missing

    def _list_artifact_files(self, base_dir: Path) -> set[Path]:
        files: set[Path] = set()
        if not base_dir.exists():
            return files

        for configured_path in self.cfg.paths:
            relative_path = Path(configured_path.rstrip("/"))
            search_root = base_dir / relative_path
            if search_root.is_file():
                files.add(relative_path)
                continue
            if not search_root.exists():
                continue
            for candidate in search_root.rglob("*"):
                if candidate.is_file():
                    files.add(candidate.relative_to(base_dir))
        return files

    def _mirror_dirty_files(self) -> list[str]:
        result = self._run_in_mirror(
            ["git", "status", "--porcelain", "--", self._namespace_arg()]
        )
        lines = [line for line in result.stdout.splitlines() if line.strip()]
        namespace_prefix = f"{self._namespace_arg().rstrip('/')}/"
        dirty: list[str] = []
        for line in lines:
            path = line[3:].strip()
            if path.startswith(namespace_prefix):
                dirty.append(path.removeprefix(namespace_prefix))
        return dirty

    def _incoming_files(self) -> list[str]:
        if not self._remote_branch_exists():
            return []
        if not self._mirror_has_head():
            return self._remote_namespace_files()

        try:
            merge_base = self._run_in_mirror(
                [
                    "git",
                    "merge-base",
                    "HEAD",
                    f"{self.cfg.remote}/{self.cfg.branch}",
                ]
            ).stdout.strip()
        except GitSyncError:
            merge_base = None

        if merge_base:
            diff_result = self._run_in_mirror(
                [
                    "git",
                    "diff",
                    "--name-only",
                    merge_base,
                    f"{self.cfg.remote}/{self.cfg.branch}",
                ]
            )
        else:
            diff_result = self._run_in_mirror(
                [
                    "git",
                    "diff",
                    "--name-only",
                    f"{self.cfg.remote}/{self.cfg.branch}",
                ]
            )

        incoming: list[str] = []
        namespace_prefix = f"{self._namespace_arg().rstrip('/')}/"
        for changed in diff_result.stdout.splitlines():
            if changed.startswith(namespace_prefix):
                incoming.append(changed.removeprefix(namespace_prefix))
        return incoming

    def _remote_namespace_files(self) -> list[str]:
        result = self._run_in_mirror(
            [
                "git",
                "ls-tree",
                "-r",
                "--name-only",
                f"{self.cfg.remote}/{self.cfg.branch}",
                "--",
                self._namespace_arg(),
            ],
            check=False,
        )
        if result.returncode != 0:
            return []

        namespace_prefix = f"{self._namespace_arg().rstrip('/')}/"
        files: list[str] = []
        for line in result.stdout.splitlines():
            if line.startswith(namespace_prefix):
                files.append(line.removeprefix(namespace_prefix))
        return files

    def _check_remote_reachable(self) -> bool:
        try:
            self._ensure_mirror_repo()
            result = self._run_in_mirror(
                ["git", "ls-remote", "--exit-code", self.cfg.remote, "HEAD"],
                check=False,
            )
            return result.returncode == 0
        except GitSyncError:
            return False

    def _run_in_mirror(
        self, cmd: list[str], *, check: bool = True
    ) -> subprocess.CompletedProcess:
        return self._run(cmd, cwd=self._mirror_dir(), check=check)

    def _run(
        self,
        cmd: list[str],
        *,
        cwd: Path | None = None,
        check: bool = True,
    ) -> subprocess.CompletedProcess:
        """Run a git subprocess, raising GitSyncError on failure when check=True."""
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd or self.root,
                capture_output=True,
                text=True,
                check=False,
            )
        except FileNotFoundError as exc:
            raise GitSyncError(
                "git executable not found. Install git and try again."
            ) from exc

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
    """Build a GitSync from a StorageConfig."""
    if not config.is_git():
        raise ValueError(
            f"Backend is '{config.backend}', not 'git'. "
            "GitSync is only available for the git backend."
        )

    git_cfg = config.git
    if git_cfg is None:
        sync_cfg = GitSyncConfig()
    else:
        sync_cfg = GitSyncConfig(
            remote=git_cfg.remote,
            remote_url=git_cfg.remote_url,
            branch=git_cfg.branch,
            project_slug=git_cfg.project_slug,
            paths=list(git_cfg.paths),
        )

    return GitSync(project_root, sync_cfg)
