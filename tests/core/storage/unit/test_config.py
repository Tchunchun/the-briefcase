"""Tests for storage config loader/saver."""

import pytest
import yaml
from pathlib import Path

from src.core.storage.config import (
    StorageConfig,
    NotionConfig,
    load_config,
    save_config,
    _find_config_dir,
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


# --- _find_config_dir dual-mode tests (D-036) ---


def test_find_config_dir_prefers_briefcase(tmp_path):
    """When both .briefcase/ and _project/ have storage.yaml, .briefcase/ wins."""
    briefcase = tmp_path / ".briefcase"
    briefcase.mkdir()
    (briefcase / STORAGE_CONFIG_FILENAME).write_text("backend: notion\n")

    project = tmp_path / "_project"
    project.mkdir()
    (project / STORAGE_CONFIG_FILENAME).write_text("backend: local\n")

    result = _find_config_dir(tmp_path)
    assert result == briefcase


def test_find_config_dir_falls_back_to_project(tmp_path):
    """When only _project/ has storage.yaml, use that."""
    project = tmp_path / "_project"
    project.mkdir()
    (project / STORAGE_CONFIG_FILENAME).write_text("backend: local\n")

    result = _find_config_dir(tmp_path)
    assert result == project


def test_find_config_dir_from_subdirectory(tmp_path):
    """Walking up from a subdirectory finds .briefcase/ at root."""
    briefcase = tmp_path / ".briefcase"
    briefcase.mkdir()
    (briefcase / STORAGE_CONFIG_FILENAME).write_text("backend: local\n")

    sub = tmp_path / "src" / "deep"
    sub.mkdir(parents=True)

    result = _find_config_dir(sub)
    assert result == briefcase


def test_find_config_dir_raises_when_neither_found(tmp_path):
    """Raises FileNotFoundError when no config directory is found."""
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(FileNotFoundError, match="storage.yaml not found"):
        _find_config_dir(empty)


def test_find_config_dir_ignores_briefcase_without_yaml(tmp_path):
    """A .briefcase/ dir without storage.yaml is skipped."""
    briefcase = tmp_path / ".briefcase"
    briefcase.mkdir()
    # No storage.yaml inside

    project = tmp_path / "_project"
    project.mkdir()
    (project / STORAGE_CONFIG_FILENAME).write_text("backend: local\n")

    result = _find_config_dir(tmp_path)
    assert result == project


def test_load_config_auto_resolves_briefcase(tmp_path, monkeypatch):
    """load_config() without explicit dir uses _find_config_dir."""
    briefcase = tmp_path / ".briefcase"
    briefcase.mkdir()
    (briefcase / STORAGE_CONFIG_FILENAME).write_text("backend: notion\nnotion:\n  parent_page_id: abc\n")

    monkeypatch.chdir(tmp_path)
    config = load_config()
    assert config.is_notion()
    assert config.notion.parent_page_id == "abc"
