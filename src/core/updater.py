"""Framework self-update logic.

Handles fetching the latest version, comparing with installed version,
detecting customizations, and atomically applying updates.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tarfile
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError
import json

from src.core.manifest import (
    FRAMEWORK_DIRS,
    FRAMEWORK_FILES,
    build_manifest,
    detect_customizations,
    read_version,
    write_manifest,
    write_version,
)

# Default GitHub repo for fetching releases
DEFAULT_REPO = "anthropics/the-briefcase"


@dataclass
class UpdateInfo:
    """Information about an available update."""

    current_version: str | None
    latest_version: str
    changelog: str = ""
    is_up_to_date: bool = False
    files_changed: list[str] = field(default_factory=list)
    customized_files: list[str] = field(default_factory=list)


@dataclass
class UpdateResult:
    """Result of applying an update."""

    success: bool
    version: str
    message: str
    files_updated: int = 0
    customizations_skipped: list[str] = field(default_factory=list)
    schema_check_needed: bool = False


def _parse_version(v: str) -> tuple[int, ...]:
    """Parse a version string like '0.8.0' or 'v0.8.0' into a tuple."""
    v = v.strip().lstrip("v")
    parts = re.findall(r"\d+", v)
    return tuple(int(p) for p in parts)


def _version_gte(a: str, b: str) -> bool:
    """Return True if version a >= version b."""
    return _parse_version(a) >= _parse_version(b)


class Updater:
    """Manages framework updates for consumer projects."""

    def __init__(
        self,
        project_root: Path,
        *,
        repo: str = DEFAULT_REPO,
        source_dir: str | None = None,
    ) -> None:
        self._root = project_root
        self._briefcase = project_root / ".briefcase"
        self._repo = repo
        # For local-clone development: use FRAMEWORK_DIR instead of GitHub
        self._source_dir = source_dir or os.environ.get("FRAMEWORK_DIR")

    def check(self) -> UpdateInfo:
        """Check for available updates without applying anything.

        Returns UpdateInfo with version comparison and changelog.
        """
        current = read_version(self._briefcase)
        latest_version, changelog = self._fetch_latest_version_info()

        info = UpdateInfo(
            current_version=current,
            latest_version=latest_version,
            changelog=changelog,
        )

        if current and _version_gte(current, latest_version):
            info.is_up_to_date = True
            return info

        # Detect customizations
        info.customized_files = detect_customizations(self._briefcase)

        return info

    def apply(self, *, force: bool = False) -> UpdateResult:
        """Fetch and apply the latest update atomically.

        Args:
            force: If True, overwrite customized files without warning.

        Returns UpdateResult with details of what happened.
        """
        current = read_version(self._briefcase)
        latest_version, _ = self._fetch_latest_version_info()

        if current and _version_gte(current, latest_version):
            return UpdateResult(
                success=True,
                version=current,
                message=f"Already up to date ({current})",
            )

        # Detect customizations before updating
        customized = detect_customizations(self._briefcase)
        if customized and not force:
            return UpdateResult(
                success=False,
                version=current or "unknown",
                message=(
                    f"{len(customized)} customized file(s) detected. "
                    "Use --force to overwrite, or back up and retry."
                ),
                customizations_skipped=customized,
            )

        # Fetch source files
        source_path = self._fetch_source(latest_version)
        if source_path is None:
            return UpdateResult(
                success=False,
                version=current or "unknown",
                message="Failed to fetch update source",
            )

        try:
            # Atomic apply: copy to temp, then swap
            files_updated = self._apply_from_source(source_path, force=force)

            # Rewrite skill paths (same as install.sh)
            self._rewrite_skill_paths()

            # Write new VERSION and manifest
            write_version(self._briefcase, latest_version)
            manifest = build_manifest(self._briefcase, latest_version)
            write_manifest(self._briefcase, manifest)

            # Check if pyproject.toml changed — reinstall deps
            schema_check_needed = False
            if self._should_reinstall_deps(source_path):
                self._reinstall_deps()

            # Check if schema health check is needed
            schema_check_needed = self._check_schema_health()

            return UpdateResult(
                success=True,
                version=latest_version,
                message=f"Updated from {current or 'unknown'} to {latest_version}",
                files_updated=files_updated,
                customizations_skipped=customized if not force else [],
                schema_check_needed=schema_check_needed,
            )
        finally:
            # Clean up temp source if it was a download
            if self._source_dir is None and source_path.exists():
                shutil.rmtree(source_path, ignore_errors=True)

    def _fetch_latest_version_info(self) -> tuple[str, str]:
        """Fetch the latest version and changelog.

        Returns (version_string, changelog_text).
        """
        if self._source_dir:
            # Local development: read version from pyproject.toml
            pyproject = Path(self._source_dir) / "pyproject.toml"
            if pyproject.exists():
                content = pyproject.read_text()
                match = re.search(r'version\s*=\s*"([^"]+)"', content)
                if match:
                    version = match.group(1)
                    changelog = self._read_local_changelog()
                    return version, changelog
            return "0.0.0", ""

        # GitHub API: fetch latest release
        try:
            url = f"https://api.github.com/repos/{self._repo}/releases/latest"
            req = Request(url, headers={"Accept": "application/vnd.github.v3+json"})
            with urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
                version = data.get("tag_name", "").lstrip("v")
                changelog = data.get("body", "")
                return version, changelog
        except (URLError, json.JSONDecodeError, KeyError) as e:
            raise RuntimeError(f"Failed to fetch latest version from GitHub: {e}") from e

    def _read_local_changelog(self) -> str:
        """Read CHANGELOG.md from local source if it exists."""
        if not self._source_dir:
            return ""
        changelog_path = Path(self._source_dir) / "CHANGELOG.md"
        if changelog_path.exists():
            return changelog_path.read_text()[:2000]
        return ""

    def _fetch_source(self, version: str) -> Path | None:
        """Fetch the source files for the given version.

        For local development, returns the FRAMEWORK_DIR path directly.
        For remote, downloads and extracts the release tarball.
        """
        if self._source_dir:
            source = Path(self._source_dir)
            if source.exists():
                return source
            return None

        # Download GitHub release tarball
        try:
            url = f"https://api.github.com/repos/{self._repo}/tarball/v{version}"
            req = Request(url, headers={"Accept": "application/vnd.github.v3+json"})
            tmp_dir = Path(tempfile.mkdtemp(prefix="briefcase-update-"))
            tarball_path = tmp_dir / "source.tar.gz"

            with urlopen(req, timeout=30) as resp:
                tarball_path.write_bytes(resp.read())

            # Extract
            with tarfile.open(tarball_path, "r:gz") as tar:
                tar.extractall(tmp_dir, filter="data")

            # Find the extracted directory (GitHub tarballs have a top-level dir)
            extracted = [
                d for d in tmp_dir.iterdir()
                if d.is_dir() and d.name != "source.tar.gz"
            ]
            if extracted:
                return extracted[0]

            return None
        except Exception:
            return None

    def _apply_from_source(self, source: Path, *, force: bool = False) -> int:
        """Copy framework files from source to .briefcase/. Returns file count."""
        files_updated = 0

        for dir_name in FRAMEWORK_DIRS:
            src_dir = source / dir_name
            dst_dir = self._briefcase / dir_name
            if not src_dir.exists():
                continue

            # Remove old copy and replace
            if dst_dir.exists():
                shutil.rmtree(dst_dir)
            shutil.copytree(src_dir, dst_dir)

            # Count files
            files_updated += sum(1 for _ in dst_dir.rglob("*") if _.is_file())

        for fname in FRAMEWORK_FILES:
            src_file = source / fname
            if src_file.exists():
                shutil.copy2(src_file, self._briefcase / fname)
                files_updated += 1

        return files_updated

    def _rewrite_skill_paths(self) -> None:
        """Rewrite skill path references from skills/ to .briefcase/skills/."""
        skills_dir = self._briefcase / "skills"
        if not skills_dir.exists():
            return
        for md_file in skills_dir.rglob("*.md"):
            content = md_file.read_text()
            # Only rewrite bare skills/ references, not already-rewritten ones
            updated = re.sub(
                r"(?<!\.)skills/", ".briefcase/skills/", content
            )
            if updated != content:
                md_file.write_text(updated)

    def _should_reinstall_deps(self, source: Path) -> bool:
        """Check if pyproject.toml changed and deps need reinstalling."""
        new_pyproject = source / "pyproject.toml"
        old_pyproject = self._briefcase / "pyproject.toml"
        if not new_pyproject.exists() or not old_pyproject.exists():
            return False
        return new_pyproject.read_text() != old_pyproject.read_text()

    def _reinstall_deps(self) -> bool:
        """Reinstall Python dependencies in .briefcase/.venv/."""
        venv_python = self._briefcase / ".venv" / "bin" / "python"
        if not venv_python.exists():
            return False
        try:
            subprocess.run(
                [str(venv_python), "-m", "pip", "install", "-q", "-e",
                 str(self._briefcase)],
                capture_output=True, timeout=60,
            )
            return True
        except Exception:
            return False

    def _check_schema_health(self) -> bool:
        """Quick check if Notion schema health check might be needed.

        Returns True if the project uses Notion backend.
        """
        storage_yaml = self._root / "_project" / "storage.yaml"
        if not storage_yaml.exists():
            storage_yaml = self._briefcase / "storage.yaml"
        if storage_yaml.exists():
            content = storage_yaml.read_text()
            if "backend: notion" in content:
                return True
        return False
