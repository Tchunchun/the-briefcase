"""Root CLI group for the agent command."""

from __future__ import annotations

from pathlib import Path

import click
from dotenv import load_dotenv

# Auto-load .env from project root so callers don't need to export manually.
_env_path = Path(__file__).resolve().parents[2] / ".env"
if _env_path.exists():
    load_dotenv(_env_path)

from src.cli.commands.setup import setup
from src.cli.commands.sync import sync
from src.cli.commands.inbox import inbox
from src.cli.commands.brief import brief
from src.cli.commands.decision import decision
from src.cli.commands.backlog import backlog
from src.cli.commands.release import release
from src.cli.commands.automate import automate
from src.cli.commands.upgrade import upgrade
from src.cli.commands.update import update
from src.cli.commands.ship import ship


@click.group()
def cli():
    """Agent workflow CLI — manage project setup, storage, and sync."""
    pass


cli.add_command(setup)
cli.add_command(sync)
cli.add_command(inbox)
cli.add_command(brief)
cli.add_command(decision)
cli.add_command(backlog)
cli.add_command(release)
cli.add_command(automate)
cli.add_command(upgrade)
cli.add_command(update)
cli.add_command(ship)


if __name__ == "__main__":
    cli()
