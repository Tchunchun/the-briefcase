"""CLI commands: agent inbox list, agent inbox add."""

from __future__ import annotations

from datetime import date, datetime

import click

from src.cli.helpers import get_store_from_dir, output_json, output_error, project_dir_option


def _resolve_since(since: str | None, today: bool) -> str | None:
    if since and today:
        raise ValueError("Use either --since or --today, not both.")
    if today:
        return date.today().isoformat()
    return since


def _group_by_date(items: list[dict]) -> list[dict]:
    grouped: dict[str, list[dict]] = {}
    for item in items:
        stamp = item.get("updated_at") or item.get("created_at") or ""
        bucket = stamp[:10] if stamp else "unknown"
        grouped.setdefault(bucket, []).append(item)
    def _sort_key(value: str) -> datetime:
        if value == "unknown":
            return datetime.min
        return datetime.fromisoformat(value)
    return [
        {"date": key, "items": grouped[key]}
        for key in sorted(grouped.keys(), key=_sort_key, reverse=True)
    ]


@click.group()
def inbox():
    """Manage inbox ideas."""
    pass


@inbox.command(name="list")
@click.option("--since", default=None, help="Filter by updated date on/after YYYY-MM-DD.")
@click.option("--today", is_flag=True, help="Shorthand for --since today's date.")
@click.option("--group-by-date", is_flag=True, help="Group output under date headers (newest first).")
@project_dir_option
def inbox_list(
    since: str | None,
    today: bool,
    group_by_date: bool,
    project_dir: str,
) -> None:
    """List all inbox entries as JSON."""
    try:
        store = get_store_from_dir(project_dir)
        since_value = _resolve_since(since, today)
        data = store.read_inbox(since=since_value)
        if group_by_date:
            data = _group_by_date(data)
        output_json(data)
    except Exception as e:
        output_error(str(e))


@inbox.command(name="add")
@click.option("--text", required=True, help="Short idea title (3-7 words).")
@click.option("--notes", default="", help="Longer description, context, or rationale.")
@click.option("--type", "entry_type", default="idea", help="Entry type (default: idea).")
@click.option(
    "--priority",
    default="Medium",
    type=click.Choice(["High", "Medium", "Low"], case_sensitive=False),
    help="Priority (default: Medium).",
)
@project_dir_option
def inbox_add(
    text: str, notes: str, entry_type: str, priority: str, project_dir: str
) -> None:
    """Add an idea to the inbox."""
    try:
        store = get_store_from_dir(project_dir)
        entry = {"text": text, "type": entry_type, "priority": priority.title()}
        if notes:
            entry["notes"] = notes
        store.append_inbox(entry)
        output_json({"added": text, "type": entry_type, "priority": entry["priority"]})
    except Exception as e:
        output_error(str(e))
