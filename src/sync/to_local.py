"""Notion → local markdown sync logic.

Delegates to the NotionBackend's sync_to_local and sync_templates_to_local
methods, wrapping them with summary formatting and error handling.
"""

from __future__ import annotations

from pathlib import Path

from src.core.storage.config import StorageConfig, load_config
from src.core.storage.factory import get_store
from src.core.storage.protocol import SyncableStore


def sync_to_local(
    project_root: str | Path, *, dry_run: bool = False
) -> dict:
    """Sync all artifacts from the cloud backend to local markdown files.

    Returns summary dict: {fetched, created, skipped, failed}.
    Raises ValueError if the active backend doesn't support sync.
    """
    root = Path(project_root)
    config = load_config(root / "_project")
    store = get_store(config, str(root))

    if not isinstance(store, SyncableStore):
        raise ValueError(
            f"Backend '{config.backend}' does not support sync to local. "
            "Sync is only available for cloud backends (e.g., notion)."
        )

    return store.sync_to_local(str(root), dry_run=dry_run)


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
