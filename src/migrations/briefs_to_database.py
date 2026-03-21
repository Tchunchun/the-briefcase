"""Migrate briefs from container page (v3) to database (v4).

Reads all brief child pages from the legacy Briefs container page,
creates corresponding database rows with structured properties, and
reparents history pages. Idempotent — skips briefs that already exist
in the database by Slug match.
"""

from __future__ import annotations

import re
from typing import Any

from src.core.storage.briefs import extract_brief_status
from src.integrations.notion.client import NotionClient


def migrate_briefs_to_database(
    client: NotionClient,
    briefs_page_id: str,
    briefs_db_id: str,
    *,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Migrate brief pages from container page to database.

    Args:
        client: Notion API client.
        briefs_page_id: ID of the legacy Briefs container page.
        briefs_db_id: ID of the new Briefs database.
        dry_run: If True, report what would happen without making changes.

    Returns:
        Summary dict with counts and details.
    """
    result: dict[str, Any] = {
        "migrated": [],
        "skipped": [],
        "errors": [],
        "dry_run": dry_run,
    }

    # Find existing slugs in database to avoid duplicates
    existing_slugs: set[str] = set()
    existing_rows = client.query_database(briefs_db_id)
    for row in existing_rows:
        props = row.get("properties", {})
        slug_items = props.get("Slug", {}).get("rich_text", [])
        if slug_items:
            existing_slugs.add(slug_items[0].get("plain_text", ""))

    # Scan legacy container page for brief child pages
    children = client.get_block_children(briefs_page_id)
    skip_titles = {"README", "Templates", "Briefs", "Release Notes"}

    for child in children:
        if child.get("type") != "child_page":
            continue
        title = child.get("child_page", {}).get("title", "")
        if title in skip_titles:
            continue
        if title.endswith(" History"):
            continue

        slug = _title_to_slug(title)

        if slug in existing_slugs:
            result["skipped"].append({"name": slug, "reason": "already exists in database"})
            continue

        try:
            page_id = child["id"]

            # Read brief content
            blocks = client.get_block_children(page_id)
            body_text = _blocks_to_text(blocks)
            status = extract_brief_status(body_text)
            edited_at = child.get("last_edited_time", "")
            date_value = edited_at[:10] if edited_at else ""

            if dry_run:
                result["migrated"].append({
                    "name": slug,
                    "title": title,
                    "status": status,
                    "date": date_value,
                })
                continue

            # Create database row with properties
            props: dict[str, Any] = {
                "Name": {"title": [{"text": {"content": title}}]},
                "Slug": {"rich_text": [{"text": {"content": slug}}]},
            }
            if status:
                props["Status"] = {"select": {"name": status}}
            if date_value:
                props["Date"] = {"date": {"start": date_value}}

            # Copy page content blocks to the new database row
            new_row = client.create_database_page(
                briefs_db_id,
                props,
                children=blocks[:100],
            )
            new_page_id = new_row["id"]

            # Reparent history pages to the new database row
            _reparent_history_pages(client, page_id, new_page_id, slug)

            result["migrated"].append({
                "name": slug,
                "title": title,
                "status": status,
                "date": date_value,
                "new_page_id": new_page_id,
            })

        except Exception as e:
            result["errors"].append({"name": slug, "error": str(e)})

    # Rename old container page
    if not dry_run and result["migrated"]:
        try:
            client.update_page(
                briefs_page_id,
                {"title": [{"text": {"content": "Briefs (archived)"}}]},
            )
        except Exception as e:
            result["errors"].append({
                "name": "_archive_rename",
                "error": f"Failed to rename old Briefs page: {e}",
            })

    return result


def _reparent_history_pages(
    client: NotionClient,
    old_parent_id: str,
    new_parent_id: str,
    brief_slug: str,
) -> None:
    """Move history pages from old brief page to new database row page."""
    children = client.get_block_children(old_parent_id)
    for child in children:
        if child.get("type") != "child_page":
            continue
        title = child.get("child_page", {}).get("title", "")
        if title.endswith(" History"):
            # Recreate history content under new parent
            # (Notion API doesn't support moving pages between parents directly,
            # so we copy the history page reference)
            history_blocks = client.get_block_children(child["id"])
            if history_blocks:
                client.create_page(
                    new_parent_id,
                    title,
                    icon="🕘",
                    children=history_blocks[:100],
                )


def _title_to_slug(title: str) -> str:
    """Convert a page title to a kebab-case slug."""
    name = re.sub(r"\s*\(v\d+\)\s*$", "", title)
    name = name.lower().strip()
    name = re.sub(r"[^a-z0-9]+", "-", name)
    return name.strip("-")


def _blocks_to_text(blocks: list[dict]) -> str:
    """Minimal block-to-text conversion for status extraction."""
    lines = []
    for block in blocks:
        block_type = block.get("type", "")
        content = block.get(block_type, {})
        rich_text = content.get("rich_text", [])
        text = "".join(rt.get("plain_text", "") for rt in rich_text)

        if block_type.startswith("heading"):
            level = block_type[-1]
            lines.append(f"{'#' * int(level)} {text}")
        elif block_type == "divider":
            lines.append("---")
        elif block_type == "to_do":
            checked = content.get("checked", False)
            marker = "[x]" if checked else "[ ]"
            lines.append(f"- {marker} {text}")
        elif block_type == "bulleted_list_item":
            lines.append(f"- {text}")
        elif block_type == "numbered_list_item":
            lines.append(f"1. {text}")
        else:
            lines.append(text)
    return "\n".join(lines)
