"""Notion → local markdown sync logic.

Delegates to the NotionBackend's sync_to_local and sync_templates_to_local
methods, wrapping them with manifest tracking, snapshot commits, conflict
detection, and error handling.
"""

from __future__ import annotations

from pathlib import Path

from src.core.storage.config import StorageConfig, load_config
from src.core.storage.factory import get_store
from src.core.storage.protocol import SyncableStore
from src.sync.manifest import (
    compute_checksums,
    detect_conflicts,
    write_manifest,
)
from src.sync.snapshots import commit_snapshot


def sync_to_local(
    project_root: str | Path, *, dry_run: bool = False
) -> dict:
    """Sync all artifacts from the cloud backend to local markdown files.

    Flow:
    1. Detect conflicts (local changes since last sync)
    2. Pull from Notion via SyncableStore.sync_to_local()
    3. Commit snapshot to orphan branch
    4. Write sync manifest

    Returns summary dict with keys:
    {fetched, created, skipped, failed, conflicts, snapshot_hash}.
    """
    root = Path(project_root)
    config = load_config(root / "_project")
    store = get_store(config, str(root))

    if not isinstance(store, SyncableStore):
        raise ValueError(
            f"Backend '{config.backend}' does not support sync to local. "
            "Sync is only available for cloud backends (e.g., notion)."
        )

    plan_dir = root / "docs" / "plan"

    # Step 1: Detect conflicts
    conflicts = detect_conflicts(plan_dir)

    # Step 2: Pull from Notion
    result = store.sync_to_local(str(root), dry_run=dry_run)
    result["conflicts"] = conflicts
    result["snapshot_hash"] = None

    if dry_run:
        return result

    # Step 3: Commit snapshot to orphan branch
    try:
        snapshot_hash = commit_snapshot(root)
        result["snapshot_hash"] = snapshot_hash
    except Exception:
        pass  # Snapshot failure shouldn't block sync

    # Step 4: Write sync manifest
    try:
        checksums = compute_checksums(plan_dir)
        artifacts = list(checksums.keys())
        write_manifest(
            plan_dir,
            direction="pull",
            backend=config.backend,
            artifacts_synced=artifacts,
            checksums=checksums,
        )
    except Exception:
        pass  # Manifest failure shouldn't block sync

    return result


def sync_templates_to_local(
    project_root: str | Path, *, dry_run: bool = False
) -> dict:
    """Pull templates from the cloud backend to local template/ files.

    Returns summary dict: {fetched, updated, skipped, failed}.
    """
    root = Path(project_root)
    config = load_config(root / "_project")
    store = get_store(config, str(root))

    if not isinstance(store, SyncableStore):
        raise ValueError(
            f"Backend '{config.backend}' does not support template sync. "
            "Sync is only available for cloud backends (e.g., notion)."
        )

    template_dir = root / "template"
    return store.sync_templates_to_local(str(template_dir), dry_run=dry_run)
