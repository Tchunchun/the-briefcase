"""Tests for sync manifest and git snapshot helpers."""

import json
import pytest
from pathlib import Path

from src.sync.manifest import (
    compute_checksum,
    compute_checksums,
    read_manifest,
    write_manifest,
    detect_conflicts,
    MANIFEST_FILENAME,
)


def test_compute_checksum(tmp_path):
    f = tmp_path / "test.md"
    f.write_text("hello world")
    cs = compute_checksum(f)
    assert cs.startswith("sha256:")
    assert len(cs) > 10


def test_compute_checksum_missing_file(tmp_path):
    cs = compute_checksum(tmp_path / "does_not_exist.md")
    assert cs == ""


def test_compute_checksums(tmp_path):
    (tmp_path / "a.md").write_text("alpha")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "b.md").write_text("beta")

    checksums = compute_checksums(tmp_path)
    assert "a.md" in checksums
    assert "sub/b.md" in checksums
    assert all(v.startswith("sha256:") for v in checksums.values())


def test_write_and_read_manifest(tmp_path):
    manifest = write_manifest(
        tmp_path,
        direction="pull",
        backend="notion",
        artifacts_synced=["a.md", "b.md"],
        checksums={"a.md": "sha256:aaa", "b.md": "sha256:bbb"},
    )

    assert manifest["direction"] == "pull"
    assert manifest["backend"] == "notion"
    assert len(manifest["artifacts_synced"]) == 2

    loaded = read_manifest(tmp_path)
    assert loaded is not None
    assert loaded["direction"] == "pull"
    assert loaded["checksums"]["a.md"] == "sha256:aaa"


def test_read_manifest_missing(tmp_path):
    assert read_manifest(tmp_path) is None


def test_detect_conflicts_no_manifest(tmp_path):
    (tmp_path / "a.md").write_text("content")
    assert detect_conflicts(tmp_path) == []


def test_detect_conflicts_no_changes(tmp_path):
    f = tmp_path / "a.md"
    f.write_text("content")
    cs = compute_checksum(f)
    write_manifest(
        tmp_path,
        direction="pull",
        backend="notion",
        artifacts_synced=["a.md"],
        checksums={"a.md": cs},
    )
    assert detect_conflicts(tmp_path) == []


def test_detect_conflicts_with_change(tmp_path):
    f = tmp_path / "a.md"
    f.write_text("original")
    cs = compute_checksum(f)
    write_manifest(
        tmp_path,
        direction="pull",
        backend="notion",
        artifacts_synced=["a.md"],
        checksums={"a.md": cs},
    )

    # Modify file after manifest was written
    f.write_text("modified!")
    conflicts = detect_conflicts(tmp_path)
    assert "a.md" in conflicts
