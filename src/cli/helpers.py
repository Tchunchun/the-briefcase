"""Shared CLI helpers for artifact commands.

Provides store initialization and JSON output formatting used
by all artifact command groups (inbox, brief, decision, backlog).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from src.core.storage.config import load_config
from src.core.storage.factory import get_store
from src.core.storage.protocol import ArtifactStore


def get_store_from_dir(project_dir: str = ".") -> ArtifactStore:
    """Load config and return the active ArtifactStore backend."""
    root = Path(project_dir).resolve()
    project_config_dir = root / "_project"
    config = load_config(project_config_dir)
    return get_store(config, str(root))


def output_json(data: dict | list, success: bool = True) -> None:
    """Print JSON result to stdout."""
    result = {"success": success, "data": data}
    click.echo(json.dumps(result, indent=2, default=str))


def output_error(message: str) -> None:
    """Print JSON error to stderr and exit."""
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
