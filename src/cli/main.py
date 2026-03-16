"""Root CLI group for the agent command."""

from __future__ import annotations

import click

from src.cli.commands.setup import setup
from src.cli.commands.sync import sync


@click.group()
def cli():
    """Agent workflow CLI — manage project setup, storage, and sync."""
    pass


cli.add_command(setup)
cli.add_command(sync)


if __name__ == "__main__":
    cli()
