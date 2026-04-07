"""Shared CLI helpers for artifact commands.

Provides store initialization and JSON output formatting used
by all artifact command groups (inbox, brief, decision, backlog).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from src.core.storage.config import StorageConfig, load_config, resolve_config_dir
from src.core.storage.factory import get_store
from src.core.storage.protocol import ArtifactStore


def get_store_from_dir(project_dir: str = ".") -> ArtifactStore:
    """Load config and return the active ArtifactStore backend.

    Resolves config from the given directory.
    Canonical precedence is _project/storage.yaml, with .briefcase/storage.yaml
    as installer bootstrap fallback (D-036 dual-mode).
    """
    root = Path(project_dir).resolve()
    config_dir = resolve_config_dir(root)
    config = load_config(config_dir)

    return get_store(config, str(root))


def load_config_from_dir(project_dir: str = ".") -> StorageConfig:
    """Load StorageConfig using the same resolution as get_store_from_dir."""
    root = Path(project_dir).resolve()
    config_dir = resolve_config_dir(root)
    return load_config(config_dir)


def default_project_name_from_dir(project_dir: str = ".") -> str:
    """Return the configured default project name for the project, if any."""
    return load_config_from_dir(project_dir).default_project_name()


def output_json(data: dict | list, success: bool = True) -> None:
    """Print JSON result to stdout."""
    result = {"success": success, "data": data}
    click.echo(json.dumps(result, indent=2, default=str))


def output_error(message: str) -> None:
    """Print JSON error to stderr and exit with code 1.

    Outputs ``{"success": false, "error": "..."}`` to **stderr** then
    calls ``sys.exit(1)``.  In Click test runners with the default
    ``mix_stderr=True``, this output appears in ``result.output`` and
    ``result.exit_code`` will be ``1``.
    """
    result = {"success": False, "error": message}
    click.echo(json.dumps(result, indent=2), err=True)
    sys.exit(1)


# Common Click option for project directory
project_dir_option = click.option(
    "--project-dir",
    type=click.Path(exists=True, file_okay=False, resolve_path=True),
    default=".",
    help="Project root directory.",
)
