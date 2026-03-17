"""CLI commands: agent inbox list, agent inbox add."""

from __future__ import annotations

import click

from src.cli.helpers import get_store_from_dir, output_json, output_error, project_dir_option


@click.group()
def inbox():
    """Manage inbox ideas."""
    pass


@inbox.command(name="list")
@project_dir_option
def inbox_list(project_dir: str) -> None:
    """List all inbox entries as JSON."""
    try:
        store = get_store_from_dir(project_dir)
        data = store.read_inbox()
        output_json(data)
    except Exception as e:
        output_error(str(e))


@inbox.command(name="add")
@click.option("--text", required=True, help="Short idea title (3-7 words).")
@click.option("--notes", default="", help="Longer description, context, or rationale.")
@click.option("--type", "entry_type", default="idea", help="Entry type (default: idea).")
@project_dir_option
def inbox_add(text: str, notes: str, entry_type: str, project_dir: str) -> None:
    """Add an idea to the inbox."""
    try:
        store = get_store_from_dir(project_dir)
        entry = {"text": text, "type": entry_type}
        if notes:
            entry["notes"] = notes
        store.append_inbox(entry)
        output_json({"added": text, "type": entry_type})
    except Exception as e:
        output_error(str(e))
