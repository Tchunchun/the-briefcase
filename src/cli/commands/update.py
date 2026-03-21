"""CLI command: briefcase update — self-update the framework in a consumer project."""

from __future__ import annotations

import sys
from pathlib import Path

import click


@click.command()
@click.option("--check", "check_only", is_flag=True, default=False,
              help="Show what would change without applying. Exit 2 if update available.")
@click.option("--yes", "-y", "skip_confirm", is_flag=True, default=False,
              help="Skip confirmation prompt.")
@click.option("--force", is_flag=True, default=False,
              help="Overwrite locally customized framework files.")
@click.option("--source", default=None,
              help="Override update source (local path or GitHub repo).")
@click.option("--project-dir", type=click.Path(exists=True, file_okay=False,
              resolve_path=True), default=".",
              help="Project root directory.")
def update(check_only: bool, skip_confirm: bool, force: bool,
           source: str | None, project_dir: str) -> None:
    """Update the briefcase framework to the latest version.

    Pulls new skills, CLI code, templates, and bug fixes from the source repo.
    Consumer-owned files (AGENTS.md, CLAUDE.md, _project/, .env) are never touched.

    Exit codes: 0 = up to date or update applied, 1 = error, 2 = update available (--check).
    """
    from src.core.updater import Updater
    from src.core.manifest import read_version

    root = Path(project_dir)
    briefcase_dir = root / ".briefcase"

    if not briefcase_dir.exists():
        click.echo("Error: .briefcase/ not found. Run install.sh first.", err=True)
        sys.exit(1)

    # Determine source
    source_dir = source if source and Path(source).is_dir() else None
    repo = source if source and not source_dir else None

    kwargs = {}
    if source_dir:
        kwargs["source_dir"] = source_dir
    if repo:
        kwargs["repo"] = repo

    updater = Updater(root, **kwargs)

    try:
        info = updater.check()
    except RuntimeError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    current = info.current_version or "unknown"
    click.echo(f"Current version: {current}")
    click.echo(f"Latest version:  {info.latest_version}")

    if info.is_up_to_date:
        click.echo("\nAlready up to date.")
        sys.exit(0)

    click.echo(f"\nUpdate available: {current} → {info.latest_version}")

    if info.changelog:
        click.echo("\nChangelog:")
        # Show first 40 lines of changelog
        for line in info.changelog.splitlines()[:40]:
            click.echo(f"  {line}")

    if info.customized_files:
        click.echo(f"\n⚠ {len(info.customized_files)} locally customized file(s):")
        for f in info.customized_files[:10]:
            click.echo(f"  - {f}")
        if not force:
            click.echo("  Use --force to overwrite these files.")

    if check_only:
        sys.exit(2)

    # Confirm
    if not skip_confirm:
        if not click.confirm("\nApply update?"):
            click.echo("Update declined.")
            sys.exit(2)

    # Apply
    result = updater.apply(force=force)

    if not result.success:
        click.echo(f"\nUpdate failed: {result.message}", err=True)
        if result.customizations_skipped:
            click.echo("Customized files that would be overwritten:", err=True)
            for f in result.customizations_skipped:
                click.echo(f"  - {f}", err=True)
        sys.exit(1)

    click.echo(f"\n✓ {result.message}")
    click.echo(f"  Files updated: {result.files_updated}")

    if result.customizations_skipped:
        click.echo(f"  Customizations preserved: {len(result.customizations_skipped)}")

    if result.schema_check_needed:
        click.echo("\n  Notion backend detected. Run 'briefcase upgrade --check' to verify schema.")
