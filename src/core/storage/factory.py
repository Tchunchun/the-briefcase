"""Factory for creating storage backend instances from config."""

from __future__ import annotations

from src.core.storage.config import StorageConfig
from src.core.storage.local_backend import LocalBackend
from src.core.storage.protocol import ArtifactStore


def get_store(config: StorageConfig, project_root: str) -> ArtifactStore:
    """Return the appropriate storage backend based on configuration.

    Args:
        config: Loaded StorageConfig from _project/storage.yaml.
        project_root: Absolute path to the project root directory.

    Returns:
        An ArtifactStore implementation.

    Raises:
        ValueError: If the configured backend is not supported.
    """
    if config.is_local():
        return LocalBackend(project_root)

    if config.is_notion():
        # Defer import to avoid requiring notion-client when using local backend
        try:
            from src.integrations.notion.backend import NotionBackend
        except ImportError as e:
            raise ImportError(
                "Notion backend requires 'notion-client' package. "
                "Install with: pip install notion-client"
            ) from e

        if config.notion is None:
            raise ValueError(
                "Notion backend selected but no Notion configuration found in storage.yaml. "
                "Run `agent setup --backend notion` to configure."
            )
        return NotionBackend(config.notion, project_root)

    raise ValueError(
        f"Unknown backend: '{config.backend}'. Supported backends: local, notion"
    )
