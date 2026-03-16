"""Tests for storage config loader/saver."""

import pytest
import yaml
from pathlib import Path

from src.core.storage.config import (
    StorageConfig,
    NotionConfig,
    load_config,
    save_config,
    DEFAULT_BACKEND,
    STORAGE_CONFIG_FILENAME,
)


@pytest.fixture
def project_dir(tmp_path):
    """Create a temporary _project/ directory."""
    d = tmp_path / "_project"
    d.mkdir()
    return d


# --- load_config tests ---


def test_load_config_returns_local_default_when_file_missing(project_dir):
    config = load_config(project_dir)
    assert config.backend == "local"
    assert config.notion is None
    assert config.is_local()
    assert not config.is_notion()


def test_load_config_returns_local_default_when_file_empty(project_dir):
    (project_dir / STORAGE_CONFIG_FILENAME).write_text("")
    config = load_config(project_dir)
    assert config.backend == "local"


def test_load_config_reads_local_backend(project_dir):
    (project_dir / STORAGE_CONFIG_FILENAME).write_text("backend: local\n")
    config = load_config(project_dir)
    assert config.backend == "local"
    assert config.is_local()


def test_load_config_reads_notion_backend(project_dir):
    data = {
        "backend": "notion",
        "notion": {
            "parent_page_id": "abc123",
            "parent_page_url": "https://notion.so/abc123",
            "databases": {
                "intake": "db-1",
                "briefs": "db-2",
                "decisions": "db-3",
            },
            "seeded_template_versions": {"brief": "v3", "tasks": "v2"},
        },
    }
    (project_dir / STORAGE_CONFIG_FILENAME).write_text(yaml.dump(data))
    config = load_config(project_dir)

    assert config.backend == "notion"
    assert config.is_notion()
    assert config.notion is not None
    assert config.notion.parent_page_id == "abc123"
    assert config.notion.databases["intake"] == "db-1"
    assert config.notion.seeded_template_versions["brief"] == "v3"


def test_load_config_raises_on_unknown_backend(project_dir):
    (project_dir / STORAGE_CONFIG_FILENAME).write_text("backend: airtable\n")
    with pytest.raises(ValueError, match="Unknown backend 'airtable'"):
        load_config(project_dir)


def test_load_config_notion_without_notion_section(project_dir):
    (project_dir / STORAGE_CONFIG_FILENAME).write_text("backend: notion\n")
    config = load_config(project_dir)
    assert config.backend == "notion"
    assert config.notion is None


# --- save_config tests ---


def test_save_config_local_creates_file(project_dir):
    config = StorageConfig(backend="local")
    path = save_config(config, project_dir)

    assert path.exists()
    with open(path) as f:
        data = yaml.safe_load(f)
    assert data["backend"] == "local"
    assert "notion" not in data


def test_save_config_notion_creates_file_with_all_fields(project_dir):
    config = StorageConfig(
        backend="notion",
        notion=NotionConfig(
            parent_page_id="abc123",
            parent_page_url="https://notion.so/abc123",
            databases={"intake": "db-1", "briefs": "db-2"},
            seeded_template_versions={"brief": "v3"},
        ),
    )
    path = save_config(config, project_dir)

    with open(path) as f:
        data = yaml.safe_load(f)

    assert data["backend"] == "notion"
    assert data["notion"]["parent_page_id"] == "abc123"
    assert data["notion"]["databases"]["intake"] == "db-1"
    assert data["notion"]["seeded_template_versions"]["brief"] == "v3"


def test_save_config_creates_directory_if_missing(tmp_path):
    new_dir = tmp_path / "_project"
    config = StorageConfig(backend="local")
    path = save_config(config, new_dir)

    assert new_dir.exists()
    assert path.exists()


# --- Round-trip test ---


def test_save_then_load_roundtrip(project_dir):
    original = StorageConfig(
        backend="notion",
        notion=NotionConfig(
            parent_page_id="xyz",
            parent_page_url="https://notion.so/xyz",
            databases={"intake": "i1", "briefs": "b1", "decisions": "d1"},
            seeded_template_versions={"brief": "v3", "tasks": "v2"},
        ),
    )
    save_config(original, project_dir)
    loaded = load_config(project_dir)

    assert loaded.backend == original.backend
    assert loaded.notion is not None
    assert loaded.notion.parent_page_id == original.notion.parent_page_id
    assert loaded.notion.databases == original.notion.databases
    assert (
        loaded.notion.seeded_template_versions
        == original.notion.seeded_template_versions
    )
