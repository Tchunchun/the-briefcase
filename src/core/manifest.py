"""Version tracking and file manifest for the briefcase framework.

Manages .briefcase/VERSION and .briefcase/manifest.json to track installed
version and detect local customizations to framework-owned files.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

# Framework-owned directories inside .briefcase/ that get updated
FRAMEWORK_DIRS = ["src", "skills", "template"]

# Files inside .briefcase/ that get updated (relative to .briefcase/)
FRAMEWORK_FILES = ["pyproject.toml"]


def read_version(briefcase_dir: Path) -> str | None:
    """Read the installed version from .briefcase/VERSION."""
    version_file = briefcase_dir / "VERSION"
    if version_file.exists():
        return version_file.read_text().strip()
    return None


def write_version(briefcase_dir: Path, version: str) -> None:
    """Write the version to .briefcase/VERSION."""
    (briefcase_dir / "VERSION").write_text(version + "\n")


def file_hash(path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def build_manifest(briefcase_dir: Path, version: str) -> dict:
    """Build a manifest of all framework-owned files with their hashes.

    Returns dict with {version, files: {relative_path: sha256_hash}}.
    """
    files: dict[str, str] = {}

    for dir_name in FRAMEWORK_DIRS:
        dir_path = briefcase_dir / dir_name
        if not dir_path.exists():
            continue
        for f in sorted(dir_path.rglob("*")):
            if f.is_file() and not f.name.startswith("."):
                rel = str(f.relative_to(briefcase_dir))
                files[rel] = file_hash(f)

    for fname in FRAMEWORK_FILES:
        fpath = briefcase_dir / fname
        if fpath.exists():
            files[fname] = file_hash(fpath)

    return {"version": version, "files": files}


def write_manifest(briefcase_dir: Path, manifest: dict) -> None:
    """Write manifest.json to .briefcase/."""
    manifest_path = briefcase_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")


def read_manifest(briefcase_dir: Path) -> dict | None:
    """Read manifest.json from .briefcase/. Returns None if not found."""
    manifest_path = briefcase_dir / "manifest.json"
    if manifest_path.exists():
        return json.loads(manifest_path.read_text())
    return None


def detect_customizations(briefcase_dir: Path) -> list[str]:
    """Compare current files against manifest to detect local modifications.

    Returns list of relative paths that have been modified since install/update.
    """
    manifest = read_manifest(briefcase_dir)
    if not manifest:
        return []

    modified = []
    for rel_path, expected_hash in manifest.get("files", {}).items():
        full_path = briefcase_dir / rel_path
        if full_path.exists():
            current = file_hash(full_path)
            if current != expected_hash:
                modified.append(rel_path)
        # Missing files are not flagged as customizations — they may have
        # been removed intentionally or the file was deleted upstream.

    return modified
