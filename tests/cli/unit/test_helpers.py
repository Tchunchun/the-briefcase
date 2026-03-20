"""Unit tests for CLI helpers."""

from __future__ import annotations

import pytest

from src.cli.helpers import get_store_from_dir
from src.core.storage.local_backend import LocalBackend


def test_get_store_from_dir_uses_briefcase_fallback(tmp_path):
    briefcase = tmp_path / ".briefcase"
    briefcase.mkdir()
    (briefcase / "storage.yaml").write_text("backend: local\n")

    store = get_store_from_dir(str(tmp_path))
    assert isinstance(store, LocalBackend)


def test_get_store_from_dir_returns_default_local_when_missing(tmp_path):
    store = get_store_from_dir(str(tmp_path))
    assert isinstance(store, LocalBackend)


def test_get_store_from_dir_raises_on_config_mismatch(tmp_path):
    briefcase = tmp_path / ".briefcase"
    briefcase.mkdir()
    (briefcase / "storage.yaml").write_text("backend: local\n")

    project = tmp_path / "_project"
    project.mkdir()
    (project / "storage.yaml").write_text("backend: notion\n")

    with pytest.raises(ValueError, match="Config mismatch detected"):
        get_store_from_dir(str(tmp_path))
