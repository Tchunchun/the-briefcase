"""Unit tests for version tracking and file manifest."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.core.manifest import (
    build_manifest,
    detect_customizations,
    file_hash,
    read_manifest,
    read_version,
    write_manifest,
    write_version,
)


@pytest.fixture
def briefcase_dir(tmp_path):
    """Create a minimal .briefcase/ directory structure."""
    bc = tmp_path / ".briefcase"
    bc.mkdir()
    (bc / "src").mkdir()
    (bc / "src" / "main.py").write_text("print('hello')")
    (bc / "skills").mkdir()
    (bc / "skills" / "SKILL.md").write_text("# Skill")
    (bc / "template").mkdir()
    (bc / "template" / "brief.md").write_text("# Brief")
    (bc / "pyproject.toml").write_text('version = "0.8.0"')
    return bc


class TestVersion:
    def test_read_version_returns_none_when_missing(self, tmp_path):
        assert read_version(tmp_path) is None

    def test_write_and_read_version(self, tmp_path):
        write_version(tmp_path, "0.8.0")
        assert read_version(tmp_path) == "0.8.0"

    def test_write_version_overwrites(self, tmp_path):
        write_version(tmp_path, "0.7.0")
        write_version(tmp_path, "0.8.0")
        assert read_version(tmp_path) == "0.8.0"


class TestFileHash:
    def test_hash_is_deterministic(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hello world")
        h1 = file_hash(f)
        h2 = file_hash(f)
        assert h1 == h2
        assert len(h1) == 64  # SHA-256 hex

    def test_different_content_different_hash(self, tmp_path):
        f1 = tmp_path / "a.txt"
        f2 = tmp_path / "b.txt"
        f1.write_text("hello")
        f2.write_text("world")
        assert file_hash(f1) != file_hash(f2)


class TestManifest:
    def test_build_manifest_includes_all_framework_files(self, briefcase_dir):
        manifest = build_manifest(briefcase_dir, "0.8.0")
        assert manifest["version"] == "0.8.0"
        files = manifest["files"]
        assert "src/main.py" in files
        assert "skills/SKILL.md" in files
        assert "template/brief.md" in files
        assert "pyproject.toml" in files

    def test_write_and_read_manifest(self, briefcase_dir):
        manifest = build_manifest(briefcase_dir, "0.8.0")
        write_manifest(briefcase_dir, manifest)
        loaded = read_manifest(briefcase_dir)
        assert loaded == manifest

    def test_read_manifest_returns_none_when_missing(self, tmp_path):
        assert read_manifest(tmp_path) is None


class TestDetectCustomizations:
    def test_no_customizations_when_files_match(self, briefcase_dir):
        manifest = build_manifest(briefcase_dir, "0.8.0")
        write_manifest(briefcase_dir, manifest)
        assert detect_customizations(briefcase_dir) == []

    def test_detects_modified_file(self, briefcase_dir):
        manifest = build_manifest(briefcase_dir, "0.8.0")
        write_manifest(briefcase_dir, manifest)

        # Modify a file
        (briefcase_dir / "src" / "main.py").write_text("print('modified')")

        modified = detect_customizations(briefcase_dir)
        assert "src/main.py" in modified

    def test_no_manifest_returns_empty(self, briefcase_dir):
        assert detect_customizations(briefcase_dir) == []

    def test_multiple_modifications(self, briefcase_dir):
        manifest = build_manifest(briefcase_dir, "0.8.0")
        write_manifest(briefcase_dir, manifest)

        (briefcase_dir / "src" / "main.py").write_text("changed1")
        (briefcase_dir / "skills" / "SKILL.md").write_text("changed2")

        modified = detect_customizations(briefcase_dir)
        assert len(modified) == 2
