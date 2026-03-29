"""CLI commands: briefcase release write, read, list, gate."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import click

from src.cli.helpers import get_store_from_dir, output_json, output_error, project_dir_option


def _bump_pyproject_version(project_dir: str, version: str) -> bool:
    """Update version field in pyproject.toml if present. Returns True if bumped."""
    # Strip leading 'v' — pyproject.toml uses bare semver (PEP 440)
    bare_version = version.lstrip("v")
    pyproject = Path(project_dir) / "pyproject.toml"
    if not pyproject.exists():
        return False
    content = pyproject.read_text()
    updated, count = re.subn(
        r'(?m)^(version\s*=\s*")[^"]*(")',
        rf"\g<1>{bare_version}\g<2>",
        content,
    )
    if count == 0:
        return False
    pyproject.write_text(updated)
    return True


def _read_pyproject_version(project_dir: str) -> str | None:
    """Return the version string from pyproject.toml, or None if not found."""
    pyproject = Path(project_dir) / "pyproject.toml"
    if not pyproject.exists():
        return None
    content = pyproject.read_text()
    match = re.search(r'(?m)^version\s*=\s*"([^"]*)"', content)
    return match.group(1) if match else None


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
    """Write a release note for a version and bump pyproject.toml. Idempotent."""
    try:
        store = get_store_from_dir(project_dir)
        store.write_release_note(version, notes)
        version_bumped = _bump_pyproject_version(project_dir, version)
        output_json({"written": version, "version_bumped": version_bumped})
    except Exception as e:
        output_error(str(e))


@release.command(name="check-version")
@project_dir_option
def release_check_version(project_dir: str) -> None:
    """Check whether pyproject.toml version matches the latest release note."""
    try:
        store = get_store_from_dir(project_dir)
        notes = store.list_release_notes()
        if not notes:
            output_error("No release notes found.")
            return
        latest = sorted(notes, key=lambda r: r.get("version", ""))[-1]
        latest_version = latest.get("version", "")
        pyproject_version = _read_pyproject_version(project_dir)
        # Normalise: strip leading 'v' for comparison
        latest_bare = latest_version.lstrip("v")
        pyproject_bare = (pyproject_version or "").lstrip("v")
        in_sync = latest_bare == pyproject_bare
        output_json({
            "in_sync": in_sync,
            "latest_release": latest_version,
            "pyproject_version": pyproject_version,
        })
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
