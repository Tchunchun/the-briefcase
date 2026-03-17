"""Root CLI group for the agent command."""

from __future__ import annotations

import click

from src.cli.commands.setup import setup
from src.cli.commands.sync import sync
from src.cli.commands.inbox import inbox
from src.cli.commands.brief import brief
from src.cli.commands.decision import decision
from src.cli.commands.backlog import backlog
from src.cli.commands.release import release


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


if __name__ == "__main__":
    cli()
