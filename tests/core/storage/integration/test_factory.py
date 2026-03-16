"""Tests for storage factory."""

import pytest

from src.core.storage.config import StorageConfig
from src.core.storage.factory import get_store
from src.core.storage.local_backend import LocalBackend
from src.core.storage.protocol import ArtifactStore


@pytest.fixture
def project(tmp_path):
    """Minimal project structure for factory tests."""
    (tmp_path / "docs" / "plan" / "_shared").mkdir(parents=True)
    (tmp_path / "_project").mkdir()
    (tmp_path / "template").mkdir()
    return tmp_path


def test_factory_returns_local_backend(project):
    config = StorageConfig(backend="local")
    store = get_store(config, str(project))
    assert isinstance(store, LocalBackend)
    assert isinstance(store, ArtifactStore)


def test_factory_raises_on_unknown_backend(project):
    config = StorageConfig(backend="airtable")
    with pytest.raises(ValueError, match="Unknown backend"):
        get_store(config, str(project))


def test_factory_raises_on_notion_without_config(project):
    config = StorageConfig(backend="notion", notion=None)
    with pytest.raises((ValueError, ImportError)):
        get_store(config, str(project))
