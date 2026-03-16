"""CLI commands: agent sync local, agent sync templates."""

from __future__ import annotations

from pathlib import Path

import click

from src.sync.to_local import sync_to_local, sync_templates_to_local


@click.group()
def sync():
    """Sync artifacts between cloud backend and local files."""
    pass


@sync.command(name="local")
@click.option("--dry-run", is_flag=True, help="Preview changes without writing.")
@click.option(
    "--project-dir",
    type=click.Path(exists=True, file_okay=False, resolve_path=True),
    default=".",
    help="Project root directory.",
)
def sync_local(dry_run: bool, project_dir: str) -> None:
    """Generate local markdown files from the cloud backend (Notion → local)."""
    try:
        result = sync_to_local(project_dir, dry_run=dry_run)
    except ValueError as e:
        raise click.ClickException(str(e))

    if dry_run:
        click.echo("[dry-run] No files were written.\n")

    click.echo(f"Sync complete:")
    click.echo(f"  Fetched:  {result['fetched']}")
    click.echo(f"  Created:  {result['created']}")
    click.echo(f"  Skipped:  {result['skipped']}")
    click.echo(f"  Failed:   {result['failed']}")

    if result["failed"] > 0:
        raise click.ClickException(
            f"{result['failed']} item(s) failed to sync. Check logs."
        )


@sync.command(name="templates")
@click.option("--dry-run", is_flag=True, help="Preview changes without writing.")
@click.option(
    "--project-dir",
    type=click.Path(exists=True, file_okay=False, resolve_path=True),
    default=".",
    help="Project root directory.",
)
def sync_templates(dry_run: bool, project_dir: str) -> None:
    """Pull updated templates from the cloud backend to local template/ files."""
    try:
        result = sync_templates_to_local(project_dir, dry_run=dry_run)
    except ValueError as e:
        raise click.ClickException(str(e))

    if dry_run:
        click.echo("[dry-run] No files were written.\n")

    click.echo(f"Template sync complete:")
    click.echo(f"  Fetched:  {result['fetched']}")
    click.echo(f"  Updated:  {result['updated']}")
    click.echo(f"  Skipped:  {result['skipped']}")
    click.echo(f"  Failed:   {result['failed']}")
