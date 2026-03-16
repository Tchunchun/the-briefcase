"""CLI command: agent setup — initialize project with backend selection."""

from __future__ import annotations

from pathlib import Path

import click

from src.core.storage.config import (
    StorageConfig,
    NotionConfig,
    save_config,
    VALID_BACKENDS,
)


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
        os.environ["NOTION_API_TOKEN"] = token

        from src.integrations.notion.client import NotionClient
        from src.integrations.notion.provisioner import NotionProvisioner

        client = NotionClient(token=token)
        provisioner = NotionProvisioner(client)

        template_dir = root / "template"
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
        click.echo(f"  Templates seeded: {summary['templates_seeded']}")
        click.echo(f"\nNotion token saved to {root / '.env'}")

    # Save config
    config_path = save_config(config, project_config_dir)

    click.echo(f"\n✓ Storage config saved to {config_path}")
    click.echo(f"  Backend: {backend}")

    if backend == "local":
        click.echo("  No additional configuration needed.")
        click.echo("  Artifacts will be stored in local markdown files.")


def _save_env_token(project_root: Path, token: str) -> None:
    """Append NOTION_API_TOKEN to .env file (create if needed)."""
    env_path = project_root / ".env"
    env_content = ""
    if env_path.exists():
        env_content = env_path.read_text()

    # Replace existing token or append
    if "NOTION_API_TOKEN=" in env_content:
        lines = env_content.splitlines()
        lines = [
            f"NOTION_API_TOKEN={token}" if l.startswith("NOTION_API_TOKEN=") else l
            for l in lines
        ]
        env_path.write_text("\n".join(lines) + "\n")
    else:
        with open(env_path, "a") as f:
            f.write(f"NOTION_API_TOKEN={token}\n")

    # Ensure .env is in .gitignore
    gitignore_path = project_root / ".gitignore"
    if gitignore_path.exists():
        gitignore = gitignore_path.read_text()
        if ".env" not in gitignore:
            with open(gitignore_path, "a") as f:
                f.write("\n.env\n")
    else:
        gitignore_path.write_text(".env\n")
