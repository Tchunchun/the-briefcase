"""CLI commands: briefcase release write, read, list, gate."""

from __future__ import annotations

import sys

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


@release.command(name="gate")
@click.option("--version", required=True, help="Version to validate (e.g., v0.8.1).")
@click.option("--dry-run", "dry_run", is_flag=True, default=True,
              help="Read-only check (default).")
@click.option("--apply", "apply_", is_flag=True, default=False,
              help="Perform safe artifact updates, then print git commands.")
@project_dir_option
def release_gate(version: str, dry_run: bool, apply_: bool, project_dir: str) -> None:
    """Validate release readiness for a version.

    Checks feature statuses, release notes, git state, and more.
    Exits non-zero if any check fails.
    """
    from src.core.release_gate import ReleaseGate

    try:
        store = get_store_from_dir(project_dir)
        gate = ReleaseGate(store, version, project_root=project_dir)
        report = gate.run(apply=apply_)

        output_json(report.to_dict())

        if apply_ and report.overall_passed:
            click.echo("\nSuggested git commands:", err=True)
            click.echo(f"  git tag {version}", err=True)
            click.echo(f"  git push origin {version}", err=True)

        if not report.overall_passed:
            sys.exit(1)
    except Exception as e:
        output_error(str(e))
