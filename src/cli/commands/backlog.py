"""CLI commands: agent backlog list, agent backlog upsert."""

from __future__ import annotations

from datetime import date, datetime

import click

from src.cli.helpers import (
    default_project_name_from_dir,
    get_store_from_dir,
    output_json,
    output_error,
    project_dir_option,
)


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


def _build_children_summary(children: list[dict]) -> dict:
    total = len(children)
    done = sum(1 for row in children if row.get("status", "").lower() == "done")
    in_progress = total - done
    if done == total and total > 0:
        readiness = "all done"
    elif done > 0:
        readiness = "partially done"
    else:
        readiness = "none done"
    return {
        "total": total,
        "done": done,
        "in_progress": in_progress,
        "ship_ready": total > 0 and done == total,
        "readiness": readiness,
    }


def _find_existing_row(
    rows: list[dict],
    *,
    item_id: str,
    title: str,
    item_type: str,
) -> dict | None:
    if item_id:
        for row in rows:
            candidate_id = row.get("notion_id") or row.get("id") or ""
            if candidate_id == item_id:
                return row
    for row in rows:
        if (
            row.get("type", "").lower() == item_type.lower()
            and row.get("title", "") == title
        ):
            return row
    return None


@click.group()
def backlog():
    """Manage backlog items (Ideas, Features, Tasks)."""
    pass


@backlog.command(name="list")
@click.option("--type", "item_type", default=None, help="Filter by type: Idea, Feature, Task.")
@click.option("--since", default=None, help="Filter by updated date on/after YYYY-MM-DD.")
@click.option("--today", is_flag=True, help="Shorthand for --since today's date.")
@click.option("--group-by-date", is_flag=True, help="Group output under date headers (newest first).")
@project_dir_option
def backlog_list(
    item_type: str | None,
    since: str | None,
    today: bool,
    group_by_date: bool,
    project_dir: str,
) -> None:
    """List backlog items as JSON. Optionally filter by type."""
    try:
        store = get_store_from_dir(project_dir)
        since_value = _resolve_since(since, today)
        data = store.read_backlog(since=since_value)
        if item_type:
            data = [r for r in data if r.get("type", "").lower() == item_type.lower()]
        if group_by_date:
            data = _group_by_date(data)
        output_json(data)
    except Exception as e:
        output_error(str(e))


@backlog.command(name="children")
@click.option("--parent-id", required=True, help="Parent backlog row id/notion_id.")
@project_dir_option
def backlog_children(parent_id: str, project_dir: str) -> None:
    """List child Features for a parent Idea/Feature row with readiness summary."""
    try:
        store = get_store_from_dir(project_dir)
        children = store.list_children(parent_id)
        output_json({
            "parent_id": parent_id,
            "children": children,
            "summary": _build_children_summary(children),
        })
    except Exception as e:
        output_error(str(e))


@backlog.command(name="upsert")
@click.option("--title", required=True, help="Item title.")
@click.option("--type", "item_type", required=True, type=click.Choice(["Idea", "Feature", "Task", "Bug"], case_sensitive=False), help="Item type.")
@click.option("--status", required=True, help="Status value (e.g., to-do, draft, new).")
@click.option("--priority", default="Medium", type=click.Choice(["High", "Medium", "Low"], case_sensitive=False), help="Priority.")
@click.option("--project", default=None, help="Project name override.")
@click.option("--notes", default="", help="Notes or context.")
@click.option("--append-notes", default="", help="Text to append to existing notes (preserves current content).")
@click.option("--brief-link", default="", help="URL to brief page (Features only).")
@click.option("--release-note-link", default="", help="URL to release note page (done Features after ship wrap-up).")
@click.option("--review-verdict", default="", type=click.Choice(["", "pending", "accepted", "changes-requested"], case_sensitive=False), help="Review verdict (Features only).")
@click.option("--route-state", default="", type=click.Choice(["", "routed", "returned", "blocked"], case_sensitive=False), help="Route state set by delivery-manager.")
@click.option("--lane", default="", type=click.Choice(["", "quick-fix", "small", "feature"], case_sensitive=False), help="Processing lane: quick-fix, small, or feature.")
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
    project: str | None,
    notes: str,
    append_notes: str,
    brief_link: str,
    release_note_link: str,
    review_verdict: str,
    route_state: str,
    lane: str,
    parent_id: str | None,
    item_id: str,
    feature: str,
    use_case: str,
    project_dir: str,
) -> None:
    """Create or update a backlog item."""
    try:
        store = get_store_from_dir(project_dir)
        existing_row = _find_existing_row(
            store.read_backlog(),
            item_id=item_id,
            title=title,
            item_type=item_type,
        )
        default_project = default_project_name_from_dir(project_dir)
        effective_notes = notes
        if append_notes and existing_row:
            prev = (existing_row.get("notes") or "").rstrip()
            if prev and prev != "—":
                effective_notes = f"{prev} · {append_notes}"
            else:
                effective_notes = append_notes
        elif append_notes:
            effective_notes = append_notes
        row = {
            "title": title,
            "type": item_type.capitalize(),
            "status": status,
            "priority": priority.capitalize(),
            "notes": effective_notes,
            "project": (
                project
                if project is not None
                else (existing_row or {}).get("project", "") or default_project
            ),
        }
        if brief_link:
            row["brief_link"] = brief_link
        if release_note_link:
            row["release_note_link"] = release_note_link
        if review_verdict:
            row["review_verdict"] = review_verdict
        if route_state:
            row["route_state"] = route_state
        if lane:
            row["lane"] = lane
        if parent_id:
            row["parent_ids"] = [parent_id]
        elif existing_row and existing_row.get("parent_ids"):
            row["parent_ids"] = existing_row["parent_ids"]
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
