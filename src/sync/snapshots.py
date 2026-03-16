"""Git orphan branch snapshot helpers for sync version tracking.

Manages the `notion-sync-snapshots` orphan branch that stores a
commit per sync pull, giving unlimited local history even when
Notion free tier only retains 7 days.
"""

from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from pathlib import Path


SNAPSHOT_BRANCH = "notion-sync-snapshots"

# Files tracked in snapshots (relative to project root)
SNAPSHOT_PATHS = ["docs/plan/", "_project/decisions.md", "template/"]


def _run_git(
    args: list[str], cwd: str | Path, *, check: bool = True
) -> subprocess.CompletedProcess:
    """Run a git command, capturing output."""
    return subprocess.run(
        ["git"] + args,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=check,
    )


def branch_exists(project_root: str | Path) -> bool:
    """Check if the snapshot orphan branch exists."""
    result = _run_git(
        ["rev-parse", "--verify", SNAPSHOT_BRANCH],
        project_root,
        check=False,
    )
    return result.returncode == 0


def init_orphan_branch(project_root: str | Path) -> bool:
    """Create the snapshot orphan branch if it doesn't exist.

    Returns True if the branch was created, False if it already existed.
    """
    if branch_exists(project_root):
        return False

    root = Path(project_root)

    # Save current branch to return to it
    current = _run_git(
        ["rev-parse", "--abbrev-ref", "HEAD"], root
    ).stdout.strip()

    # Stash any dirty state
    stash_result = _run_git(["stash", "--include-untracked"], root, check=False)
    stashed = "No local changes" not in stash_result.stdout

    try:
        _run_git(["checkout", "--orphan", SNAPSHOT_BRANCH], root)
        _run_git(["rm", "-rf", "."], root, check=False)
        _run_git(
            ["commit", "--allow-empty", "-m", "init sync snapshots"],
            root,
        )
    finally:
        _run_git(["checkout", current], root)
        if stashed:
            _run_git(["stash", "pop"], root, check=False)

    return True


def commit_snapshot(project_root: str | Path) -> str | None:
    """Commit current sync state to the orphan branch.

    Copies tracked paths into the orphan branch and commits.
    Returns the commit hash, or None if nothing changed.
    """
    root = Path(project_root)

    if not branch_exists(root):
        init_orphan_branch(root)

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Save current branch
    current = _run_git(
        ["rev-parse", "--abbrev-ref", "HEAD"], root
    ).stdout.strip()

    # Stash any dirty state
    stash_result = _run_git(["stash", "--include-untracked"], root, check=False)
    stashed = "No local changes" not in stash_result.stdout

    commit_hash = None
    try:
        _run_git(["checkout", SNAPSHOT_BRANCH], root)

        # Add tracked paths
        for path in SNAPSHOT_PATHS:
            full = root / path
            if full.exists():
                _run_git(["add", "--force", path], root, check=False)

        # Check if there's anything to commit
        diff = _run_git(["diff", "--cached", "--quiet"], root, check=False)
        if diff.returncode != 0:
            _run_git(
                ["commit", "-m", f"sync: pull from Notion {timestamp}"],
                root,
            )
            result = _run_git(["rev-parse", "HEAD"], root)
            commit_hash = result.stdout.strip()
    finally:
        _run_git(["checkout", current], root)
        if stashed:
            _run_git(["stash", "pop"], root, check=False)

    return commit_hash


def list_snapshots(
    project_root: str | Path, *, limit: int = 10
) -> list[dict[str, str]]:
    """List recent snapshot commits.

    Returns list of dicts with {hash, date, message}.
    """
    root = Path(project_root)

    if not branch_exists(root):
        return []

    result = _run_git(
        [
            "log",
            SNAPSHOT_BRANCH,
            f"--max-count={limit}",
            "--format=%H|%aI|%s",
        ],
        root,
        check=False,
    )

    if result.returncode != 0:
        return []

    snapshots = []
    for line in result.stdout.strip().splitlines():
        if not line:
            continue
        parts = line.split("|", 2)
        if len(parts) == 3:
            snapshots.append({
                "hash": parts[0],
                "date": parts[1],
                "message": parts[2],
            })

    return snapshots
