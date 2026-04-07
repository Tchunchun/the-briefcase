"""CLI command group: briefcase migrate

Provides data migration commands between backends, e.g.:
  briefcase migrate notion-to-git   -- Pull all Notion data to local, switch backend to git
"""

from __future__ import annotations

from pathlib import Path

import click


@click.group()
def migrate() -> None:
    """Migrate project data between storage backends."""


@migrate.command(name="notion-to-git")
@click.option("--dry-run", is_flag=True, help="Preview without writing any files.")
@click.option(
    "--remote-url",
    default=None,
    help="Git remote URL. Prompts interactively if not provided.",
)
@click.option(
    "--branch",
    default="main",
    show_default=True,
    help="Branch to push artifacts to.",
)
@click.option(
    "--remote",
    "remote_name",
    default="origin",
    show_default=True,
    help="Git remote name.",
)
@click.option(
    "--project-dir",
    type=click.Path(exists=True, file_okay=False, resolve_path=True),
    default=".",
    help="Project root directory.",
)
def notion_to_git(
    dry_run: bool,
    remote_url: str | None,
    branch: str,
    remote_name: str,
    project_dir: str,
) -> None:
    """Migrate from Notion backend to git backend.

    Steps:
      1. Verify current backend is 'notion'.
      2. Pull all Notion data to local markdown (briefcase sync local).
      3. Ask for confirmation.
      4. Rewrite _project/storage.yaml to backend: git.
      5. Commit the migrated artifacts.
      6. Push to the git remote.

    This is non-destructive: your Notion data is left untouched.
    """
    from src.core.storage.config import (
        GitConfig,
        StorageConfig,
        load_config,
        resolve_config_dir,
        save_config,
    )
    from src.sync.git_sync import GitSync, GitSyncConfig, GitSyncError

    root = Path(project_dir)

    # --- 1. Verify backend is notion ----------------------------------
    config = load_config(resolve_config_dir(root))
    if not config.is_notion():
        raise click.ClickException(
            f"Current backend is '{config.backend}', not 'notion'. "
            "This command is only for migrating away from Notion."
        )

    # Check NOTION_API_KEY is available for the pull step
    import os
    notion_key = (
        os.environ.get("NOTION_API_KEY")
        or os.environ.get("NOTION_API_TOKEN")
        or _read_env_key(root, "NOTION_API_KEY")
        or _read_env_key(root, "NOTION_API_TOKEN")
    )
    if not notion_key:
        raise click.ClickException(
            "NOTION_API_KEY not found. Set it in .env or as an environment variable "
            "so this command can pull data from Notion."
        )

    # --- 2. Pull Notion data to local ---------------------------------
    click.echo("Step 1/4: Pulling data from Notion → local files...")
    if not dry_run:
        try:
            from src.sync.to_local import sync_to_local

            result = sync_to_local(project_dir, dry_run=False)
        except Exception as e:
            raise click.ClickException(f"Failed to pull from Notion: {e}")

        click.echo(f"  Fetched:   {result['fetched']}")
        click.echo(f"  Created:   {result['created']}")
        click.echo(f"  Skipped:   {result['skipped']}")
        click.echo(f"  Failed:    {result['failed']}")
        click.echo(f"  Conflicts: {result['conflicts']}")

        if result["failed"] > 0:
            raise click.ClickException(
                f"{result['failed']} item(s) failed to pull from Notion. "
                "Resolve these before migrating."
            )
        if result["conflicts"] > 0:
            raise click.ClickException(
                f"{result['conflicts']} conflict(s) detected. "
                "Resolve conflicts before migrating."
            )
    else:
        click.echo("  [dry-run] Skipping Notion pull.")

    # --- 3. Confirm ---------------------------------------------------
    if not dry_run:
        click.echo(
            "\nStep 2/4: Ready to switch backend from 'notion' → 'git'."
        )
        if not click.confirm(
            "Continue? (This rewrites _project/storage.yaml and commits)", default=True
        ):
            click.echo("Aborted.")
            return

    # --- 4. Get remote URL if not provided ----------------------------
    if not remote_url:
        remote_url = click.prompt(
            "Git remote URL (e.g. git@github.com:you/private-project.git)"
        )

    click.echo(f"\nStep 3/4: Rewriting _project/storage.yaml (backend: git)...")

    if not dry_run:
        new_config = StorageConfig(
            backend="git",
            git=GitConfig(
                remote=remote_name,
                remote_url=remote_url,
                branch=branch,
            ),
            upstream=config.upstream,
            project=config.project,
        )
        save_config(new_config, root / "_project")
    else:
        click.echo("  [dry-run] Would rewrite storage.yaml to backend: git.")

    # --- 5 & 6. Commit + push -----------------------------------------
    click.echo("Step 4/4: Committing and pushing to git remote...")

    sync_cfg = GitSyncConfig(
        remote=remote_name,
        remote_url=remote_url,
        branch=branch,
    )
    syncer = GitSync(root, sync_cfg)

    if not dry_run:
        # Configure remote if needed
        try:
            added = syncer.configure_remote(remote_url)
            if added:
                click.echo(f"  Added remote '{remote_name}' → {remote_url}")
            else:
                click.echo(f"  Updated remote '{remote_name}' → {remote_url}")
        except GitSyncError as e:
            raise click.ClickException(f"Failed to configure git remote: {e}")

        try:
            push_result = syncer.push(dry_run=False)
        except GitSyncError as e:
            raise click.ClickException(f"Failed to push: {e}")
        click.echo(f"  {push_result['message']}")
    else:
        click.echo(
            f"  [dry-run] Would commit artifact files and push to {remote_name}/{branch}."
        )

    # --- Summary ------------------------------------------------------
    click.echo("\n✓ Migration complete!")
    if not dry_run:
        click.echo(f"  Backend is now: git (remote: {remote_name}/{branch})")
        click.echo("\n  Next steps:")
        click.echo("  - Update your team's local configs: `briefcase setup --backend git`")
        click.echo("  - Use `briefcase sync push` / `briefcase sync pull` going forward")
        env_path = root / ".env"
        if env_path.exists() and "NOTION_API_KEY=" in env_path.read_text():
            click.echo(
                "\n  ⚠️  Reminder: remove NOTION_API_KEY from .env — it's no longer needed."
            )


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _read_env_key(project_root: Path, key: str) -> str | None:
    """Read a key=value from .env file. Returns the value or None."""
    env_path = project_root / ".env"
    if not env_path.exists():
        return None
    for line in env_path.read_text().splitlines():
        if line.startswith(f"{key}="):
            return line.split("=", 1)[1].strip()
    return None
