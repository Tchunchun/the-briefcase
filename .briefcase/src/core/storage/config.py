"""Load and save _project/storage.yaml configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


STORAGE_CONFIG_FILENAME = "storage.yaml"
DEFAULT_BACKEND = "local"
VALID_BACKENDS = ("local", "notion")


@dataclass
class NotionConfig:
    """Notion-specific backend configuration."""

    parent_page_id: str = ""
    parent_page_url: str = ""
    databases: dict[str, str] = field(default_factory=dict)
    seeded_template_versions: dict[str, str] = field(default_factory=dict)


@dataclass
class StorageConfig:
    """Top-level storage configuration."""

    backend: str = DEFAULT_BACKEND
    notion: NotionConfig | None = None

    def is_notion(self) -> bool:
        return self.backend == "notion"

    def is_local(self) -> bool:
        return self.backend == "local"


def _find_project_dir(start: str | Path | None = None) -> Path:
    """Locate the _project/ directory by walking up from start (or cwd)."""
    current = Path(start) if start else Path.cwd()
    while True:
        candidate = current / "_project"
        if candidate.is_dir():
            return candidate
        parent = current.parent
        if parent == current:
            break
        current = parent
    raise FileNotFoundError(
        "_project/ directory not found. Run `agent setup` to initialize."
    )


def load_config(project_dir: str | Path | None = None) -> StorageConfig:
    """Load storage configuration from _project/storage.yaml.

    If the file does not exist, returns a default local config.
    Raises ValueError if the backend value is not recognized.
    """
    if project_dir is None:
        project_dir = _find_project_dir()
    else:
        project_dir = Path(project_dir)

    config_path = project_dir / STORAGE_CONFIG_FILENAME

    if not config_path.exists():
        return StorageConfig()

    with open(config_path, "r") as f:
        raw = yaml.safe_load(f)

    if raw is None:
        return StorageConfig()

    backend = raw.get("backend", DEFAULT_BACKEND)
    if backend not in VALID_BACKENDS:
        raise ValueError(
            f"Unknown backend '{backend}' in {config_path}. "
            f"Valid backends: {', '.join(VALID_BACKENDS)}"
        )

    notion_config = None
    if backend == "notion" and "notion" in raw:
        notion_raw = raw["notion"]
        notion_config = NotionConfig(
            parent_page_id=notion_raw.get("parent_page_id", ""),
            parent_page_url=notion_raw.get("parent_page_url", ""),
            databases=notion_raw.get("databases", {}),
            seeded_template_versions=notion_raw.get(
                "seeded_template_versions", {}
            ),
        )

    return StorageConfig(backend=backend, notion=notion_config)


def save_config(config: StorageConfig, project_dir: str | Path) -> Path:
    """Save storage configuration to _project/storage.yaml.

    Creates the file if it doesn't exist. Returns the path written.
    """
    project_dir = Path(project_dir)
    project_dir.mkdir(parents=True, exist_ok=True)
    config_path = project_dir / STORAGE_CONFIG_FILENAME

    data: dict[str, Any] = {"backend": config.backend}

    if config.notion is not None:
        data["notion"] = {
            "parent_page_id": config.notion.parent_page_id,
            "parent_page_url": config.notion.parent_page_url,
            "databases": config.notion.databases,
            "seeded_template_versions": config.notion.seeded_template_versions,
        }

    with open(config_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    return config_path
