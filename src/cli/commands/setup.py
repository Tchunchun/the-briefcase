"""CLI command: briefcase setup — initialize project with backend selection."""

from __future__ import annotations

from pathlib import Path

import click

from src.core.storage.config import (
    StorageConfig,
    NotionConfig,
    save_config,
    VALID_BACKENDS,
)
from src.core.gitignore import ensure_gitignore, entries_for_backend


@click.command()
@click.option(
    "--backend",
    type=click.Choice(VALID_BACKENDS, case_sensitive=False),
    default=None,
    help="Storage backend to use. If not specified, prompts interactively.",
)
@click.option(
    "--project-dir",
    type=click.Path(exists=True, file_okay=False, resolve_path=True),
    default=".",
    help="Project root directory (default: current directory).",
)
def setup(backend: str | None, project_dir: str) -> None:
    """Initialize project storage configuration.

    Creates _project/storage.yaml with the selected backend.
    For 'local' backend, no additional configuration is needed.
    For 'notion' backend, prompts for API token and parent page ID.
    """
    root = Path(project_dir)
    project_config_dir = root / "_project"

    # Interactive backend selection if not specified
    if backend is None:
        backend = click.prompt(
            "Choose storage backend",
            type=click.Choice(VALID_BACKENDS, case_sensitive=False),
            default="local",
        )

    config = StorageConfig(backend=backend)

    if backend == "notion":
        token = click.prompt(
            "Notion API token",
            hide_input=True,
        )
        parent_page_id = click.prompt("Notion parent page ID")

        # Save token to .env (not to storage.yaml)
        _save_env_token(root, token)

        config.notion = NotionConfig(
            parent_page_id=parent_page_id,
            parent_page_url=f"https://notion.so/{parent_page_id}",
        )

        # Provision Notion workspace: create databases + seed templates
        click.echo("\nProvisioning Notion workspace...")
        import os
        os.environ["NOTION_API_KEY"] = token

        from src.integrations.notion.client import NotionClient
        from src.integrations.notion.provisioner import NotionProvisioner

        client = NotionClient(token=token)
        provisioner = NotionProvisioner(client)

        template_dir = root / "template"
        # Preflight: validate parent page access before provisioning
        try:
            provisioner.preflight_check(parent_page_id)
        except (LookupError, PermissionError, RuntimeError) as e:
            raise click.ClickException(str(e))

        db_ids, result = provisioner.provision(
            parent_page_id,
            template_dir=template_dir if template_dir.exists() else None,
        )

        if not result.success:
            for err in result.errors:
                click.echo(f"  ✗ {err}", err=True)
            raise click.ClickException("Notion provisioning failed. See errors above.")

        # Store database IDs in config
        config.notion.databases = db_ids

        # Store seeded template versions
        if template_dir.exists():
            import re
            for md_file in sorted(template_dir.glob("*.md")):
                name = md_file.stem.lstrip("_")
                content = md_file.read_text()
                version_match = re.search(r"\(v(\d+)\)", content)
                version = f"v{version_match.group(1)}" if version_match else "v1"
                config.notion.seeded_template_versions[name] = version

        summary = result.summary()
        click.echo(f"  Databases created: {summary['databases_created']}")
        click.echo(f"  Databases found (existing): {summary['databases_found_existing']}")
        click.echo(f"  Pages created: {summary['pages_created']}")
        click.echo(f"  Templates seeded: {summary['templates_seeded']}")
        click.echo(f"\nNotion token saved to {root / '.env'}")

        # Initialize sync snapshot orphan branch
        try:
            from src.sync.snapshots import init_orphan_branch
            created = init_orphan_branch(root)
            if created:
                click.echo("  ✓ Created sync snapshot branch (notion-sync-snapshots)")
            else:
                click.echo("  ✓ Sync snapshot branch already exists")
        except Exception:
            click.echo("  ⚠ Could not create sync snapshot branch (non-fatal)")

    # Save config
    config_path = save_config(config, project_config_dir)

    # Update .gitignore with canonical entries for the selected backend
    ensure_gitignore(root, entries_for_backend(backend))

    click.echo(f"\n✓ Storage config saved to {config_path}")
    click.echo(f"  Backend: {backend}")

    if backend == "local":
        click.echo("  No additional configuration needed.")
        click.echo("  Artifacts will be stored in local markdown files.")
    elif backend == "notion":
        click.echo("\n  Next steps:")
        click.echo("  1. Open the Notion project page and create three board views:")
        click.echo("     - Idea Board: filter Type=Idea, grouped by Idea Status")
        click.echo("     - Feature Board: filter Type=Feature, grouped by Feature Status")
        click.echo("     - Task Board: filter Type=Task, grouped by Task Status")
        click.echo("  2. Run `./briefcase sync local` to pull Notion → local before working")
        click.echo("  3. Run `./briefcase sync notion` to push local → Notion after working")


def _save_env_token(project_root: Path, token: str) -> None:
    """Append NOTION_API_KEY to .env file (create if needed).

    Also checks for legacy NOTION_API_TOKEN and migrates it.
    Gitignore handling is delegated to ensure_gitignore().
    """
    env_path = project_root / ".env"
    env_content = ""
    if env_path.exists():
        env_content = env_path.read_text()

    # Migrate legacy NOTION_API_TOKEN → NOTION_API_KEY
    if "NOTION_API_TOKEN=" in env_content and "NOTION_API_KEY=" not in env_content:
        lines = env_content.splitlines()
        lines = [
            f"NOTION_API_KEY={token}" if l.startswith("NOTION_API_TOKEN=") else l
            for l in lines
        ]
        env_path.write_text("\n".join(lines) + "\n")
    elif "NOTION_API_KEY=" in env_content:
        lines = env_content.splitlines()
        lines = [
            f"NOTION_API_KEY={token}" if l.startswith("NOTION_API_KEY=") else l
            for l in lines
        ]
        env_path.write_text("\n".join(lines) + "\n")
    else:
        with open(env_path, "a") as f:
            f.write(f"NOTION_API_KEY={token}\n")
