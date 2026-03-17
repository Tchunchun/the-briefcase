"""CLI commands: agent decision list, agent decision add."""

from __future__ import annotations

import click

from src.cli.helpers import get_store_from_dir, output_json, output_error, project_dir_option


@click.group()
def decision():
    """Manage architectural decisions."""
    pass


@decision.command(name="list")
@project_dir_option
def decision_list(project_dir: str) -> None:
    """List all decisions as JSON."""
    try:
        store = get_store_from_dir(project_dir)
        data = store.read_decisions()
        output_json(data)
    except Exception as e:
        output_error(str(e))


@decision.command(name="add")
@click.option("--id", "dec_id", required=True, help="Decision ID (e.g., D-001).")
@click.option("--title", required=True, help="Decision summary.")
@click.option("--date", required=True, help="Decision date (YYYY-MM-DD).")
@click.option("--status", default="accepted", help="Status (default: accepted).")
@click.option("--why", default="", help="Rationale.")
@click.option("--alternatives", "alts", default="", help="Alternatives rejected.")
@click.option("--feature-link", default="", help="URL to related feature (optional).")
@click.option("--adr-link", default="", help="URL to full ADR (optional).")
@project_dir_option
def decision_add(
    dec_id: str,
    title: str,
    date: str,
    status: str,
    why: str,
    alts: str,
    feature_link: str,
    adr_link: str,
    project_dir: str,
) -> None:
    """Add an architectural decision."""
    try:
        store = get_store_from_dir(project_dir)
        entry = {
            "id": dec_id,
            "title": title,
            "date": date,
            "status": status,
            "why": why,
            "alternatives_rejected": alts,
        }
        if feature_link:
            entry["feature_link"] = feature_link
        if adr_link:
            entry["adr_link"] = adr_link
        store.append_decision(entry)
        output_json({"added": dec_id, "title": title})
    except Exception as e:
        output_error(str(e))
