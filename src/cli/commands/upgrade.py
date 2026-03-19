"""CLI command: agent upgrade.

Validates and optionally repairs a Notion workspace without re-provisioning.
Only valid for backend: notion projects.
"""

from __future__ import annotations

import sys

import click

from src.cli.helpers import output_error, project_dir_option
from src.core.storage.config import load_config, save_config
from src.integrations.notion.upgrade import FindingStatus


@click.command()
@click.option(
    "--check",
    is_flag=True,
    default=False,
    help="Inspect only — do not apply repairs.",
)
@click.option(
    "--yes",
    is_flag=True,
    default=False,
    help="Skip interactive confirmation and apply repairs.",
)
@project_dir_option
def upgrade(check: bool, yes: bool, project_dir: str) -> None:
    """Validate and repair an existing Notion workspace.

    --check: report only, exit non-zero if issues found.
    --yes: apply safe repairs without prompting.
    Default (no flags): inspect, show plan, prompt for confirmation.
    """
    from pathlib import Path

    root = Path(project_dir).resolve()
    project_config_dir = root / "_project"

    try:
        config = load_config(project_config_dir)
    except (FileNotFoundError, ValueError) as e:
        output_error(str(e))
        sys.exit(1)

    if not config.is_notion():
        output_error(
            "Upgrade is only applicable to Notion backends. "
            f"Current backend: '{config.backend}'."
        )
        sys.exit(1)

    if not config.notion or not config.notion.parent_page_id:
        output_error(
            "Notion configuration is incomplete: parent_page_id is missing. "
            "Run `agent setup` first."
        )
        sys.exit(1)

    # Lazy import to avoid requiring notion-client when not needed
    from src.integrations.notion.client import NotionClient
    from src.integrations.notion.upgrade import NotionUpgradeService

    try:
        client = NotionClient()
    except ValueError as e:
        output_error(str(e))
        sys.exit(1)

    service = NotionUpgradeService(client, config)

    if check:
        report = service.inspect()
        _print_report(report)
        sys.exit(report.exit_code)

    # Run inspection first to show what will be done
    report = service.inspect()

    if not report.has_issues:
        _print_report(report)
        click.echo("\nWorkspace is healthy. No repairs needed.")
        sys.exit(0)

    # Show the plan
    _print_report(report)

    fixable = [
        f for f in report.findings if f.status == FindingStatus.MANUAL
    ]
    click.echo(f"\nFound {len(fixable)} issue(s) that can be auto-fixed.")

    if not yes:
        if not click.confirm("Apply safe repairs?"):
            click.echo("Aborted.")
            sys.exit(1)

    # Apply repairs
    repair_report = service.upgrade()

    # Save config if page IDs were restored
    config_changed = any(
        f.status == FindingStatus.FIXED and f.category.startswith("page:")
        for f in repair_report.findings
    )
    if config_changed:
        save_config(config, project_config_dir)

    click.echo("\n--- Repair Results ---")
    _print_report(repair_report)

    if repair_report.has_unfixed:
        click.echo("\nSome issues require manual action (see above).")
        sys.exit(2)
    else:
        click.echo("\nAll fixable issues resolved.")
        sys.exit(0)


def _print_report(report) -> None:
    """Print findings grouped by status."""
    for finding in report.findings:
        marker = finding.status.value
        click.echo(f"  {marker}: {finding.description}")
