"""Sync manifest for tracking pull/push state and detecting conflicts.

Reads and writes `.sync-manifest.json` under docs/plan/ with timestamps,
direction, artifact list, and SHA-256 checksums for conflict detection.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MANIFEST_FILENAME = ".sync-manifest.json"


def _manifest_path(plan_dir: str | Path) -> Path:
    return Path(plan_dir) / MANIFEST_FILENAME


def compute_checksum(file_path: str | Path) -> str:
    """Compute SHA-256 hex digest of a file's contents."""
    h = hashlib.sha256()
    path = Path(file_path)
    if not path.exists():
        return ""
    h.update(path.read_bytes())
    return f"sha256:{h.hexdigest()}"


def compute_checksums(plan_dir: str | Path) -> dict[str, str]:
    """Compute checksums for all markdown files under plan_dir.

    Returns a dict mapping relative paths to SHA-256 checksums.
    """
    root = Path(plan_dir)
    checksums: dict[str, str] = {}
    if not root.exists():
        return checksums
    for md_file in sorted(root.rglob("*.md")):
        rel = str(md_file.relative_to(root))
        checksums[rel] = compute_checksum(md_file)
    return checksums


def read_manifest(plan_dir: str | Path) -> dict[str, Any] | None:
    """Read the sync manifest. Returns None if it doesn't exist."""
    path = _manifest_path(plan_dir)
    if not path.exists():
        return None
    with open(path, "r") as f:
        return json.load(f)


def write_manifest(
    plan_dir: str | Path,
    *,
    direction: str,
    backend: str,
    artifacts_synced: list[str],
    checksums: dict[str, str],
) -> dict[str, Any]:
    """Write the sync manifest after a pull or push.

    Returns the manifest dict that was written.
    """
    manifest = {
        "last_sync": datetime.now(timezone.utc).isoformat(),
        "direction": direction,
        "backend": backend,
        "artifacts_synced": sorted(artifacts_synced),
        "checksums": checksums,
    }
    path = _manifest_path(plan_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")
    return manifest


def detect_conflicts(
    plan_dir: str | Path,
) -> list[str]:
    """Detect files that changed locally since the last sync.

    Compares current file checksums against the manifest's stored
    checksums. Returns a list of relative paths that have changed
    (potential conflicts if a pull would overwrite them).
    """
    manifest = read_manifest(plan_dir)
    if manifest is None:
        return []  # No previous sync — no conflicts possible

    stored = manifest.get("checksums", {})
    current = compute_checksums(plan_dir)
    conflicts: list[str] = []

    for rel_path, old_checksum in stored.items():
        new_checksum = current.get(rel_path, "")
        if new_checksum and new_checksum != old_checksum:
            conflicts.append(rel_path)

    return conflicts
