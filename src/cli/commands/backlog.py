"""CLI commands: agent backlog list, agent backlog upsert."""

from __future__ import annotations

import click

from src.cli.helpers import get_store_from_dir, output_json, output_error, project_dir_option


@click.group()
def backlog():
    """Manage backlog items (Ideas, Features, Tasks)."""
    pass


@backlog.command(name="list")
@click.option("--type", "item_type", default=None, help="Filter by type: Idea, Feature, Task.")
@project_dir_option
def backlog_list(item_type: str | None, project_dir: str) -> None:
    """List backlog items as JSON. Optionally filter by type."""
    try:
        store = get_store_from_dir(project_dir)
        data = store.read_backlog()
        if item_type:
            data = [r for r in data if r.get("type", "").lower() == item_type.lower()]
        output_json(data)
    except Exception as e:
        output_error(str(e))


@backlog.command(name="upsert")
@click.option("--title", required=True, help="Item title.")
@click.option("--type", "item_type", required=True, type=click.Choice(["Idea", "Feature", "Task"], case_sensitive=False), help="Item type.")
@click.option("--status", required=True, help="Status value (e.g., to-do, draft, new).")
@click.option("--priority", default="Medium", type=click.Choice(["High", "Medium", "Low"], case_sensitive=False), help="Priority.")
@click.option("--notes", default="", help="Notes or context.")
@click.option("--brief-link", default="", help="URL to brief page (Features only).")
@click.option("--release-note-link", default="", help="URL to release note page (done Features after ship wrap-up).")
@click.option("--review-verdict", default="", type=click.Choice(["", "pending", "accepted", "changes-requested"], case_sensitive=False), help="Review verdict (Features only).")
@click.option("--route-state", default="", type=click.Choice(["", "routed", "returned", "blocked"], case_sensitive=False), help="Route state set by delivery-manager.")
@click.option("--parent-id", default=None, help="Notion page ID of parent item (for Task→Feature or Feature→Idea linking).")
@click.option("--id", "item_id", default="", help="Local ID (e.g., T-027). Used by local backend.")
@click.option("--feature", default="", help="Feature name. Used by local backend for the Feature column.")
@click.option("--use-case", default="", help="Use case description. Used by local backend.")
@project_dir_option
def backlog_upsert(
    title: str,
    item_type: str,
    status: str,
    priority: str,
    notes: str,
    brief_link: str,
    release_note_link: str,
    review_verdict: str,
    route_state: str,
    parent_id: str | None,
    item_id: str,
    feature: str,
    use_case: str,
    project_dir: str,
) -> None:
    """Create or update a backlog item."""
    try:
        store = get_store_from_dir(project_dir)
        row = {
            "title": title,
            "type": item_type.capitalize(),
            "status": status,
            "priority": priority.capitalize(),
            "notes": notes,
        }
        if brief_link:
            row["brief_link"] = brief_link
        if release_note_link:
            row["release_note_link"] = release_note_link
        if review_verdict:
            row["review_verdict"] = review_verdict
        if route_state:
            row["route_state"] = route_state
        if parent_id:
            row["parent_ids"] = [parent_id]
        # Local backend fields
        if item_id:
            row["id"] = item_id
        if feature:
            row["feature"] = feature
        if use_case:
            row["use_case"] = use_case
        store.write_backlog_row(row)
        output_json({"upserted": title, "type": item_type, "status": status})
    except Exception as e:
        output_error(str(e))
