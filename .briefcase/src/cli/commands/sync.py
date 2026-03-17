"""CLI commands: agent sync local, agent sync notion, agent sync templates."""

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
    """Pull from cloud backend to local markdown files (Notion → local)."""
    try:
        result = sync_to_local(project_dir, dry_run=dry_run)
    except ValueError as e:
        raise click.ClickException(str(e))

    if dry_run:
        click.echo("[dry-run] No files were written.\n")

    # Warn about conflicts
    conflicts = result.get("conflicts", [])
    if conflicts:
        click.echo(
            click.style(
                f"\n⚠ {len(conflicts)} file(s) changed locally since last sync:",
                fg="yellow",
            )
        )
        for c in conflicts:
            click.echo(f"  - {c}")
        click.echo(
            "  These files were overwritten by the pull. "
            "Check the snapshot branch for previous versions.\n"
        )

    click.echo(f"Sync complete:")
    click.echo(f"  Fetched:  {result['fetched']}")
    click.echo(f"  Created:  {result['created']}")
    click.echo(f"  Skipped:  {result['skipped']}")
    click.echo(f"  Failed:   {result['failed']}")

    snapshot = result.get("snapshot_hash")
    if snapshot:
        click.echo(f"  Snapshot: {snapshot[:12]}")

    if result["failed"] > 0:
        raise click.ClickException(
            f"{result['failed']} item(s) failed to sync. Check logs."
        )


@sync.command(name="notion")
@click.option("--dry-run", is_flag=True, help="Preview changes without writing.")
@click.option(
    "--project-dir",
    type=click.Path(exists=True, file_okay=False, resolve_path=True),
    default=".",
    help="Project root directory.",
)
def sync_notion(dry_run: bool, project_dir: str) -> None:
    """Push local markdown files to cloud backend (local → Notion)."""
    from src.sync.to_notion import sync_to_notion

    try:
        result = sync_to_notion(project_dir, dry_run=dry_run)
    except ValueError as e:
        raise click.ClickException(str(e))

    if dry_run:
        click.echo("[dry-run] No changes were pushed.\n")

    click.echo(f"Push complete:")
    click.echo(f"  Pushed:   {result['pushed']}")
    click.echo(f"  Skipped:  {result['skipped']}")
    click.echo(f"  Failed:   {result['failed']}")

    if result["failed"] > 0:
        raise click.ClickException(
            f"{result['failed']} item(s) failed to push. Check logs."
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
