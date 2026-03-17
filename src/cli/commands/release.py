"""CLI commands: agent release write, agent release read, agent release list."""

from __future__ import annotations

import click

from src.cli.helpers import get_store_from_dir, output_json, output_error, project_dir_option


@click.group()
def release():
    """Manage release notes."""
    pass


@release.command(name="list")
@project_dir_option
def release_list(project_dir: str) -> None:
    """List all release notes as JSON."""
    try:
        store = get_store_from_dir(project_dir)
        data = store.list_release_notes()
        output_json(data)
    except Exception as e:
        output_error(str(e))


@release.command(name="read")
@click.option("--version", required=True, help="Version string (e.g., v0.5.0).")
@project_dir_option
def release_read(version: str, project_dir: str) -> None:
    """Read a release note by version. Returns structured JSON."""
    try:
        store = get_store_from_dir(project_dir)
        data = store.read_release_note(version)
        output_json(data)
    except KeyError:
        output_error(f"Release note not found: {version}")
    except Exception as e:
        output_error(str(e))


@release.command(name="write")
@click.option("--version", required=True, help="Version string (e.g., v0.5.0).")
@click.option("--notes", required=True, help="Release note content (markdown).")
@project_dir_option
def release_write(version: str, notes: str, project_dir: str) -> None:
    """Write a release note for a version. Idempotent: overwrites if exists."""
    try:
        store = get_store_from_dir(project_dir)
        store.write_release_note(version, notes)
        output_json({"written": version})
    except Exception as e:
        output_error(str(e))
