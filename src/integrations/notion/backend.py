"""Notion backend implementing ArtifactStore and SyncableStore protocols.

Reads/writes planning artifacts directly to Notion databases via the API.
When Notion is the active backend, this is the source of truth.

v3: Unified Backlog (Idea/Feature/Task) + Decisions database +
brief pages stored in the dedicated Briefs container + Templates as child
pages.
"""

from __future__ import annotations

import fcntl
import os
import re
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from src.core.storage.briefs import (
    build_revision_id,
    extract_brief_status,
    parse_brief_sections,
    parse_revision_markdown,
    render_brief_markdown,
    render_revision_markdown,
)
from src.core.storage.config import NotionConfig
from src.integrations.notion.client import NotionClient


class NotionBackend:
    """ArtifactStore + SyncableStore backed by Notion databases."""

    def __init__(self, config: NotionConfig, project_root: str | Path) -> None:
        self._config = config
        self._root = Path(project_root)
        self._client = NotionClient()
        self._dbs = config.databases
        self._parent_page_id = config.parent_page_id

    def _db(self, name: str) -> str:
        db_id = self._dbs.get(name)
        if not db_id:
            raise ValueError(
                f"Notion resource '{name}' not configured. "
                "Run `agent setup --backend notion` to provision."
        )
        return db_id

    def _backlog_lock_path(self) -> Path:
        lock_dir = self._root / ".agent"
        lock_dir.mkdir(parents=True, exist_ok=True)
        return lock_dir / "notion-backlog.lock"

    @contextmanager
    def _backlog_write_lock(self):
        lock_path = self._backlog_lock_path()
        with open(lock_path, "w", encoding="utf-8") as lock_file:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

    def _briefs_page_id(self) -> str:
        """Return the Briefs container page ID, falling back to parent page."""
        return self._dbs.get("briefs") or self._parent_page_id

    def _release_notes_page_id(self) -> str:
        """Return the Release Notes container page ID, falling back to parent page."""
        return self._dbs.get("release_notes") or self._parent_page_id

    # -- Helpers for Notion property extraction --

    @staticmethod
    def _get_title(props: dict, key: str = "Title") -> str:
        title_items = props.get(key, {}).get("title", [])
        return title_items[0].get("plain_text", "") if title_items else ""

    @staticmethod
    def _get_rich_text(props: dict, key: str) -> str:
        items = props.get(key, {}).get("rich_text", [])
        return items[0].get("plain_text", "") if items else ""

    @staticmethod
    def _get_select(props: dict, key: str) -> str:
        sel = props.get(key, {}).get("select")
        return sel.get("name", "") if sel else ""

    @staticmethod
    def _get_date(props: dict, key: str) -> str:
        d = props.get(key, {}).get("date")
        return d.get("start", "") if d else ""

    @staticmethod
    def _get_url(props: dict, key: str) -> str:
        return props.get(key, {}).get("url", "") or ""

    @staticmethod
    def _get_relation_ids(props: dict, key: str) -> list[str]:
        items = props.get(key, {}).get("relation", [])
        return [item["id"] for item in items if "id" in item]

    # -- Property builders --

    @staticmethod
    def _title_prop(text: str) -> dict:
        return {"title": [{"text": {"content": text}}]}

    @staticmethod
    def _rich_text_prop(text: str) -> dict:
        return {"rich_text": [{"text": {"content": text}}]}

    @staticmethod
    def _select_prop(value: str) -> dict:
        return {"select": {"name": value}}

    @staticmethod
    def _date_prop(iso_date: str) -> dict:
        return {"date": {"start": iso_date}}

    @staticmethod
    def _url_prop(url: str) -> dict:
        return {"url": url if url else None}

    @staticmethod
    def _relation_prop(page_ids: list[str]) -> dict:
        return {"relation": [{"id": pid} for pid in page_ids]}

    # -- Status helpers for unified Backlog --

    @staticmethod
    def _status_key_for_type(item_type: str) -> str:
        """Return the status property name for a given work item type."""
        mapping = {
            "Idea": "Idea Status",
            "Feature": "Feature Status",
            "Task": "Task Status",
        }
        return mapping.get(item_type, "Task Status")

    def _get_status_for_row(self, props: dict) -> str:
        """Extract the relevant status based on the row's Type."""
        item_type = self._get_select(props, "Type")
        status_key = self._status_key_for_type(item_type)
        return self._get_select(props, status_key)

    # -- Inbox (Backlog rows where Type = Idea) --

    def read_inbox(self, since: str | None = None) -> list[dict]:
        filters: list[dict[str, Any]] = [
            {"property": "Type", "select": {"equals": "Idea"}}
        ]
        if since:
            filters.append(
                {
                    "timestamp": "last_edited_time",
                    "last_edited_time": {"on_or_after": since},
                }
            )
        query_filter: dict[str, Any]
        if len(filters) == 1:
            query_filter = filters[0]
        else:
            query_filter = {"and": filters}
        rows = self._client.query_database(
            self._db("backlog"),
            filter=query_filter,
        )
        return [
            {
                "text": self._get_title(r["properties"]),
                "type": "idea",
                "status": self._get_select(r["properties"], "Idea Status"),
                "priority": self._get_select(r["properties"], "Priority") or "Medium",
                "notes": self._get_rich_text(r["properties"], "Notes"),
                "notion_id": r["id"],
                "created_at": r.get("created_time", ""),
                "updated_at": r.get("last_edited_time", ""),
            }
            for r in rows
        ]

    def append_inbox(self, entry: dict) -> None:
        props = {
            "Title": self._title_prop(entry["text"]),
            "Type": self._select_prop("Idea"),
            "Idea Status": self._select_prop(entry.get("status", "new")),
        }
        if entry.get("notes"):
            props["Notes"] = self._rich_text_prop(entry["notes"])
        props["Priority"] = self._select_prop(entry.get("priority", "Medium"))
        self._client.create_database_page(self._db("backlog"), props)

    # -- Briefs (standalone pages under project root) --

    def read_brief(self, brief_name: str) -> dict:
        page_id = self._find_brief_page(brief_name)
        if not page_id:
            raise KeyError(f"Brief not found: {brief_name}")

        page = self._client.get_page(page_id)
        blocks = self._client.get_block_children(page_id)
        body_text = self._blocks_to_markdown(blocks)

        # Extract title from page properties
        title_items = page.get("properties", {}).get("title", {}).get("title", [])
        title = title_items[0].get("plain_text", brief_name) if title_items else brief_name

        data = {
            "name": brief_name,
            "title": title,
            "raw": body_text,
            "notion_id": page_id,
            "notion_url": page.get("url", ""),
        }

        # Parse status from body text
        data["status"] = extract_brief_status(body_text)

        # Parse sections from body
        data.update(parse_brief_sections(body_text))

        return data

    def write_brief(self, brief_name: str, data: dict) -> None:
        from src.integrations.notion.provisioner import NotionProvisioner

        existing_id = self._find_brief_page(brief_name)
        if existing_id:
            current = self.read_brief(brief_name)
            merged_data = dict(current)
            merged_data.update(data)
            body = self._render_brief_body(brief_name, merged_data)
            blocks = NotionProvisioner._markdown_to_blocks(body)
            self._store_brief_revision(
                brief_name,
                current,
                actor=data.get("_actor", ""),
                change_summary=data.get("_change_summary", ""),
            )
            # Keep the page identity stable while replacing the brief body.
            self._client.update_page(
                existing_id,
                {"title": self._title_prop(merged_data.get("title", brief_name))["title"]},
            )
            self._replace_page_body(existing_id, blocks)
        else:
            body = self._render_brief_body(brief_name, data)
            blocks = NotionProvisioner._markdown_to_blocks(body)
            self._client.create_page(
                self._briefs_page_id(),
                data.get("title", brief_name),
                icon="📄",
                children=blocks[:100],
            )

    def list_briefs(self) -> list[dict]:
        """List brief pages under the Briefs container page.

        Only briefs created in the dedicated Briefs container are supported.
        Legacy root-level brief pages are intentionally out of scope.
        """
        briefs = []
        briefs_page = self._briefs_page_id()
        children = self._client.get_block_children(briefs_page)
        skip_titles = {"README", "Templates", "Briefs", "Release Notes"}

        for child in children:
            if child.get("type") != "child_page":
                continue
            title = child.get("child_page", {}).get("title", "")
            if title in skip_titles:
                continue
            if title.endswith(" History"):
                continue
            if title.endswith(self._RELEASE_NOTE_TITLE_SUFFIX):
                continue
            # Read status from page content
            try:
                blocks = self._client.get_block_children(child["id"])
                body = self._blocks_to_markdown(blocks)
                status = extract_brief_status(body)
            except Exception:
                status = "draft"
            edited_at = child.get("last_edited_time", "")
            date_value = edited_at[:10] if edited_at else ""
            briefs.append({
                "name": self._title_to_brief_name(title),
                "status": status,
                "title": title,
                "date": date_value,
                "notion_id": child["id"],
            })
        briefs.sort(key=lambda item: item.get("date", ""), reverse=True)
        return briefs

    def list_brief_revisions(self, brief_name: str) -> list[dict]:
        history_page_id = self._find_brief_history_page(brief_name)
        if not history_page_id:
            return []

        revisions = []
        for child in self._client.get_block_children(history_page_id):
            if child.get("type") != "child_page":
                continue
            page_id = child["id"]
            title = child.get("child_page", {}).get("title", "")
            if not title.startswith("Revision "):
                continue
            blocks = self._client.get_block_children(page_id)
            parsed = parse_revision_markdown(self._blocks_to_markdown(blocks))
            snapshot = parsed.get("snapshot", {})
            revisions.append(
                {
                    "revision_id": parsed.get("revision_id", title.removeprefix("Revision ")),
                    "captured_at": parsed.get("captured_at", ""),
                    "actor": parsed.get("actor", ""),
                    "change_summary": parsed.get("change_summary", ""),
                    "title": snapshot.get("title", ""),
                    "status": snapshot.get("status", ""),
                    "notion_id": page_id,
                }
            )
        revisions.sort(key=lambda item: item["revision_id"], reverse=True)
        return revisions

    def read_brief_revision(self, brief_name: str, revision_id: str) -> dict:
        page_id = self._find_revision_page(brief_name, revision_id)
        if not page_id:
            raise KeyError(f"Brief revision not found: {brief_name}@{revision_id}")

        blocks = self._client.get_block_children(page_id)
        parsed = parse_revision_markdown(self._blocks_to_markdown(blocks))
        page = self._client.get_page(page_id)
        return {
            "brief_name": brief_name,
            "revision_id": parsed.get("revision_id", revision_id),
            "captured_at": parsed.get("captured_at", ""),
            "actor": parsed.get("actor", ""),
            "change_summary": parsed.get("change_summary", ""),
            "snapshot": parsed["snapshot"],
            "raw": parsed["raw"],
            "notion_id": page_id,
            "notion_url": page.get("url", ""),
        }

    def restore_brief_revision(
        self,
        brief_name: str,
        revision_id: str,
        *,
        actor: str = "",
        change_summary: str = "",
    ) -> dict:
        revision = self.read_brief_revision(brief_name, revision_id)
        snapshot = dict(revision["snapshot"])
        snapshot["_actor"] = actor
        snapshot["_change_summary"] = (
            change_summary or f"Restored from revision {revision_id}"
        )
        self.write_brief(brief_name, snapshot)
        return self.read_brief(brief_name)

    def _find_brief_page(self, brief_name: str) -> str | None:
        """Find a supported brief page by name under the Briefs container."""
        briefs_page = self._briefs_page_id()
        children = self._client.get_block_children(briefs_page)
        for child in children:
            if child.get("type") != "child_page":
                continue
            title = child.get("child_page", {}).get("title", "")
            if self._title_to_brief_name(title) == brief_name:
                return child["id"]
        return None

    @staticmethod
    def _title_to_brief_name(title: str) -> str:
        """Convert a page title to a kebab-case brief name."""
        # Strip version suffix like "(v3)"
        name = re.sub(r"\s*\(v\d+\)\s*$", "", title)
        # Convert to kebab-case
        name = name.lower().strip()
        name = re.sub(r"[^a-z0-9]+", "-", name)
        return name.strip("-")

    def _brief_history_page_title(self, brief_name: str, title: str = "") -> str:
        brief_title = title or brief_name.replace("-", " ").title()
        return f"{brief_title} History"

    def _find_brief_history_page(self, brief_name: str, title: str = "") -> str | None:
        # Look for the History page as a child of the brief page first.
        brief_page_id = self._find_brief_page(brief_name)
        if brief_page_id:
            preferred_title = self._brief_history_page_title(brief_name, title) if title else ""
            for child in self._client.get_block_children(brief_page_id):
                if child.get("type") != "child_page":
                    continue
                child_title = child.get("child_page", {}).get("title", "")
                if preferred_title and child_title == preferred_title:
                    return child["id"]
                if not child_title.endswith(" History"):
                    continue
                ct_brief = child_title[: -len(" History")]
                if self._title_to_brief_name(ct_brief) == brief_name:
                    return child["id"]

        # Fallback: check the legacy location (sibling under Briefs container).
        preferred_title = self._brief_history_page_title(brief_name, title) if title else ""
        for child in self._client.get_block_children(self._briefs_page_id()):
            if child.get("type") != "child_page":
                continue
            child_title = child.get("child_page", {}).get("title", "")
            if preferred_title and child_title == preferred_title:
                return child["id"]
            if not child_title.endswith(" History"):
                continue
            brief_title = child_title[: -len(" History")]
            if self._title_to_brief_name(brief_title) == brief_name:
                return child["id"]
        return None

    def _ensure_brief_history_page(self, brief_name: str, title: str = "") -> str:
        page_id = self._find_brief_history_page(brief_name, title)
        if page_id:
            return page_id
        # Create the History page as a child of the brief page itself,
        # keeping it out of the top-level Briefs listing.
        brief_page_id = self._find_brief_page(brief_name)
        parent_id = brief_page_id or self._briefs_page_id()
        result = self._client.create_page(
            parent_id,
            self._brief_history_page_title(brief_name, title),
            icon="🕘",
        )
        return result["id"]

    def _find_revision_page(self, brief_name: str, revision_id: str) -> str | None:
        history_page_id = self._find_brief_history_page(brief_name)
        if not history_page_id:
            return None
        for child in self._client.get_block_children(history_page_id):
            if child.get("type") != "child_page":
                continue
            if child.get("child_page", {}).get("title", "") == f"Revision {revision_id}":
                return child["id"]
        return None

    def _store_brief_revision(
        self,
        brief_name: str,
        snapshot: dict,
        *,
        actor: str = "",
        change_summary: str = "",
    ) -> dict:
        from src.integrations.notion.provisioner import NotionProvisioner

        revision_id = build_revision_id()
        metadata = {
            "revision_id": revision_id,
            "captured_at": revision_id,
            "actor": actor or os.environ.get("USER", ""),
            "change_summary": change_summary,
        }
        history_page_id = self._ensure_brief_history_page(
            brief_name, snapshot.get("title", "")
        )
        body = render_revision_markdown(brief_name, snapshot, metadata)
        blocks = NotionProvisioner._markdown_to_blocks(body)
        self._client.create_page(
            history_page_id,
            f"Revision {revision_id}",
            icon="📝",
            children=blocks[:100],
        )
        return metadata

    # -- Decisions --

    def read_decisions(self) -> list[dict]:
        rows = self._client.query_database(self._db("decisions"))
        return [
            {
                "id": self._get_rich_text(r["properties"], "ID"),
                "title": self._get_title(r["properties"]),
                "date": self._get_date(r["properties"], "Date"),
                "status": self._get_select(r["properties"], "Status"),
                "why": self._get_rich_text(r["properties"], "Why"),
                "alternatives_rejected": self._get_rich_text(
                    r["properties"], "Alternatives Rejected"
                ),
                "feature_link": self._get_url(r["properties"], "Feature Link"),
                "adr_link": self._get_url(r["properties"], "ADR Link"),
                "notion_id": r["id"],
            }
            for r in rows
        ]

    def append_decision(self, entry: dict) -> None:
        props = {
            "Title": self._title_prop(entry["title"]),
            "ID": self._rich_text_prop(entry["id"]),
            "Date": self._date_prop(entry["date"]),
            "Status": self._select_prop(entry.get("status", "accepted")),
            "Why": self._rich_text_prop(entry.get("why", "")),
            "Alternatives Rejected": self._rich_text_prop(
                entry.get("alternatives_rejected", "")
            ),
        }
        if entry.get("feature_link"):
            props["Feature Link"] = self._url_prop(entry["feature_link"])
        if entry.get("adr_link"):
            props["ADR Link"] = self._url_prop(entry["adr_link"])
        self._client.create_database_page(self._db("decisions"), props)

    # -- Backlog (unified: Idea/Feature/Task) --

    def read_backlog(self, since: str | None = None) -> list[dict]:
        query_filter = None
        if since:
            query_filter = {
                "timestamp": "last_edited_time",
                "last_edited_time": {"on_or_after": since},
            }
        rows = self._client.query_database(self._db("backlog"), filter=query_filter)
        return [
            {
                "title": self._get_title(r["properties"]),
                "type": self._get_select(r["properties"], "Type"),
                "status": self._get_status_for_row(r["properties"]),
                "priority": self._get_select(r["properties"], "Priority"),
                "review_verdict": self._get_select(r["properties"], "Review Verdict"),
                "route_state": self._get_select(r["properties"], "Route State"),
                "brief_link": self._get_url(r["properties"], "Brief Link"),
                "release_note_link": self._get_url(r["properties"], "Release Note Link"),
                "notes": self._get_rich_text(r["properties"], "Notes"),
                "automation_trace": self._get_rich_text(r["properties"], "Automation Trace"),
                "parent_ids": self._get_relation_ids(r["properties"], "Parent"),
                "notion_id": r["id"],
                "notion_url": r.get("url", ""),
                "created_at": r.get("created_time", ""),
                "updated_at": r.get("last_edited_time", ""),
            }
            for r in rows
        ]

    def write_backlog_row(self, row: dict) -> None:
        item_type = row.get("type", "Task")
        status_key = self._status_key_for_type(item_type)

        props: dict[str, Any] = {
            "Title": self._title_prop(row["title"]),
            "Type": self._select_prop(item_type),
            status_key: self._select_prop(row.get("status", "to-do")),
            "Priority": self._select_prop(row.get("priority", "Medium")),
            "Notes": self._rich_text_prop(row.get("notes", "")),
            "Automation Trace": self._rich_text_prop(row.get("automation_trace", "")),
        }
        if row.get("brief_link"):
            props["Brief Link"] = self._url_prop(row["brief_link"])
        if row.get("release_note_link"):
            props["Release Note Link"] = self._url_prop(row["release_note_link"])
        if row.get("review_verdict"):
            props["Review Verdict"] = self._select_prop(row["review_verdict"])
        if row.get("route_state"):
            props["Route State"] = self._select_prop(row["route_state"])
        if row.get("parent_ids"):
            props["Parent"] = self._relation_prop(row["parent_ids"])

        with self._backlog_write_lock():
            page_id = row.get("notion_id") or row.get("id") or ""
            if page_id:
                self._client.update_database_page(page_id, props)
                return

            existing = self._client.query_database(
                self._db("backlog"),
                filter={
                    "and": [
                        {"property": "Title", "title": {"equals": row["title"]}},
                        {"property": "Type", "select": {"equals": item_type}},
                    ]
                },
            )

            if existing:
                self._client.update_database_page(existing[0]["id"], props)
            else:
                self._client.create_database_page(self._db("backlog"), props)

    def list_children(self, parent_id: str) -> list[dict]:
        """Return direct child Feature rows for a parent backlog item id."""
        rows = self._client.query_database(
            self._db("backlog"),
            filter={
                "and": [
                    {"property": "Type", "select": {"equals": "Feature"}},
                    {"property": "Parent", "relation": {"contains": parent_id}},
                ]
            },
        )
        return [
            {
                "title": self._get_title(r["properties"]),
                "type": self._get_select(r["properties"], "Type"),
                "status": self._get_status_for_row(r["properties"]),
                "priority": self._get_select(r["properties"], "Priority"),
                "review_verdict": self._get_select(r["properties"], "Review Verdict"),
                "route_state": self._get_select(r["properties"], "Route State"),
                "brief_link": self._get_url(r["properties"], "Brief Link"),
                "release_note_link": self._get_url(r["properties"], "Release Note Link"),
                "notes": self._get_rich_text(r["properties"], "Notes"),
                "automation_trace": self._get_rich_text(
                    r["properties"], "Automation Trace"
                ),
                "parent_ids": self._get_relation_ids(r["properties"], "Parent"),
                "notion_id": r["id"],
                "notion_url": r.get("url", ""),
                "created_at": r.get("created_time", ""),
                "updated_at": r.get("last_edited_time", ""),
            }
            for r in rows
        ]

    # -- Templates (child pages of Templates page) --

    def read_templates(self) -> list[dict]:
        templates_page_id = self._dbs.get("templates")
        if not templates_page_id:
            return []

        children = self._client.get_block_children(templates_page_id)
        templates = []
        for child in children:
            if child.get("type") != "child_page":
                continue
            title = child.get("child_page", {}).get("title", "")
            blocks = self._client.get_block_children(child["id"])
            content = self._blocks_to_markdown(blocks)

            # Parse version from title like "brief (v3)"
            version_match = re.search(r"\(v(\d+)\)", title)
            version = f"v{version_match.group(1)}" if version_match else "v1"
            name = re.sub(r"\s*\(v\d+\)\s*$", "", title).strip()

            templates.append({
                "name": name,
                "version": version,
                "content": content,
                "notion_id": child["id"],
            })
        return templates

    def write_template(self, name: str, content: str, version: str) -> None:
        from src.integrations.notion.provisioner import NotionProvisioner

        templates_page_id = self._dbs.get("templates")
        if not templates_page_id:
            raise ValueError(
                "Templates page not configured. "
                "Run `agent setup --backend notion` to provision."
            )

        blocks = NotionProvisioner._markdown_to_blocks(content)
        page_title = f"{name} ({version})"

        # Check if template page exists
        children = self._client.get_block_children(templates_page_id)
        existing_id = None
        for child in children:
            if child.get("type") != "child_page":
                continue
            title = child.get("child_page", {}).get("title", "")
            child_name = re.sub(r"\s*\(v\d+\)\s*$", "", title).strip()
            if child_name == name:
                existing_id = child["id"]
                break

        if existing_id:
            self._client.update_page(
                existing_id,
                {"title": {"title": [{"text": {"content": page_title}}]}},
            )
        else:
            self._client.create_page(
                templates_page_id,
                page_title,
                children=blocks[:100],
            )

    # -- Release Notes --

    _RELEASE_NOTE_TITLE_SUFFIX = " Release Notes"

    def _replace_page_body(self, page_id: str, blocks: list[dict]) -> None:
        """Replace all top-level page blocks with the provided blocks."""
        old_blocks = self._client.get_block_children(page_id)
        for block in old_blocks:
            if block.get("archived") or block.get("in_trash"):
                continue
            self._client.delete_block(block["id"])
        if blocks:
            self._client.append_block_children(page_id, blocks[:100])

    def write_release_note(self, version: str, content: str) -> None:
        from src.integrations.notion.provisioner import NotionProvisioner

        page_title = f"{version}{self._RELEASE_NOTE_TITLE_SUFFIX}"
        blocks = NotionProvisioner._markdown_to_blocks(content)
        release_notes_page_id = self._release_notes_page_id()

        existing_id = self._find_release_note_page(version)
        if existing_id:
            self._replace_page_body(existing_id, blocks)
        else:
            result = self._client.create_page(
                release_notes_page_id,
                page_title,
                icon="📦",
                children=blocks[:100],
            )
            existing_id = result["id"]

        # Ensure README index has a link for this version
        self._ensure_readme_release_link(version, existing_id)

    def read_release_note(self, version: str) -> dict:
        page_id = self._find_release_note_page(version)
        if not page_id:
            raise KeyError(f"Release note not found: {version}")
        blocks = self._client.get_block_children(page_id)
        content = self._blocks_to_markdown(blocks)
        return {
            "version": version,
            "title": f"{version}{self._RELEASE_NOTE_TITLE_SUFFIX}",
            "content": content,
            "notion_id": page_id,
        }

    def list_release_notes(self) -> list[dict]:
        children = self._client.get_block_children(self._release_notes_page_id())
        notes = []
        for child in children:
            if child.get("type") != "child_page":
                continue
            title = child.get("child_page", {}).get("title", "")
            if title.endswith(self._RELEASE_NOTE_TITLE_SUFFIX):
                version = title[: -len(self._RELEASE_NOTE_TITLE_SUFFIX)]
                notes.append({
                    "version": version,
                    "title": title,
                    "notion_id": child["id"],
                })
        return notes

    def _find_release_note_page(self, version: str) -> str | None:
        page_title = f"{version}{self._RELEASE_NOTE_TITLE_SUFFIX}"
        children = self._client.get_block_children(self._release_notes_page_id())
        for child in children:
            if child.get("type") != "child_page":
                continue
            title = child.get("child_page", {}).get("title", "")
            if title == page_title:
                return child["id"]
        return None

    def _ensure_readme_release_link(
        self, version: str, release_page_id: str
    ) -> None:
        readme_id = self._dbs.get("readme")
        if not readme_id:
            return

        blocks = self._client.get_block_children(readme_id)

        # Find the "Release Notes" heading
        heading_idx = None
        for i, block in enumerate(blocks):
            btype = block.get("type", "")
            if btype == "heading_2":
                text_items = block.get("heading_2", {}).get("rich_text", [])
                text = "".join(t.get("plain_text", "") for t in text_items)
                if text.strip() == "Release Notes":
                    heading_idx = i
                    break

        # If heading not found, append it
        if heading_idx is None:
            self._client.append_block_children(readme_id, [
                {
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"text": {"content": "Release Notes"}}],
                    },
                },
            ])
            # Re-fetch to find the heading block for after_id positioning
            blocks = self._client.get_block_children(readme_id)
            for i, block in enumerate(blocks):
                btype = block.get("type", "")
                if btype == "heading_2":
                    text_items = block.get("heading_2", {}).get("rich_text", [])
                    text = "".join(t.get("plain_text", "") for t in text_items)
                    if text.strip() == "Release Notes":
                        heading_idx = i
                        break

        # Check if a bullet for this version already exists
        link_text = f"{version} Release Notes"
        for block in blocks:
            if block.get("type") == "bulleted_list_item":
                text_items = block.get("bulleted_list_item", {}).get(
                    "rich_text", []
                )
                text = "".join(t.get("plain_text", "") for t in text_items)
                if version in text:
                    return  # Already linked

        # Add bulleted list item linking to the release-note page
        notion_link = f"https://notion.so/{release_page_id.replace('-', '')}"
        bullet = {
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": link_text,
                            "link": {"url": notion_link},
                        },
                    }
                ],
            },
        }
        self._client.append_block_children(readme_id, [bullet])

    # -- SyncableStore methods --

    def sync_to_local(self, target_dir: str, *, dry_run: bool = False) -> dict:
        """Generate local markdown from Notion."""
        target = Path(target_dir)
        summary = {"fetched": 0, "created": 0, "skipped": 0, "failed": 0}

        # Sync Ideas → _inbox.md
        try:
            ideas = self.read_inbox()
            summary["fetched"] += len(ideas)
            inbox_path = target / "docs" / "plan" / "_inbox.md"
            inbox_path.parent.mkdir(parents=True, exist_ok=True)
            existing_text = inbox_path.read_text() if inbox_path.exists() else ""
            for entry in ideas:
                status_tag = ""
                if entry["status"] not in ("new", ""):
                    status_tag = f" [{entry['status']}]"
                line = f"- [idea] {entry['text']}{status_tag}"
                if entry["text"] not in existing_text:
                    if not dry_run:
                        with open(inbox_path, "a") as f:
                            f.write(line + "\n")
                    summary["created"] += 1
                else:
                    summary["skipped"] += 1
        except Exception:
            summary["failed"] += 1

        # Sync briefs → docs/plan/{brief-name}/brief.md
        try:
            briefs = self.list_briefs()
            for brief_summary in briefs:
                summary["fetched"] += 1
                try:
                    brief = self.read_brief(brief_summary["name"])
                    brief_dir = target / "docs" / "plan" / brief_summary["name"]
                    if not dry_run:
                        brief_dir.mkdir(parents=True, exist_ok=True)
                        path = brief_dir / "brief.md"
                        path.write_text(brief.get("raw", ""))
                    summary["created"] += 1
                except Exception:
                    summary["failed"] += 1
        except Exception:
            summary["failed"] += 1

        # Sync backlog (Feature + Task rows) → backlog.md
        try:
            rows = self._client.query_database(
                self._db("backlog"),
                filter={
                    "or": [
                        {"property": "Type", "select": {"equals": "Feature"}},
                        {"property": "Type", "select": {"equals": "Task"}},
                    ]
                },
            )
            summary["fetched"] += len(rows)
            backlog_path = target / "docs" / "plan" / "_shared" / "backlog.md"
            backlog_path.parent.mkdir(parents=True, exist_ok=True)
            if not dry_run:
                lines = [
                    "# Backlog\n",
                    "\nCross-feature source of truth for task priority "
                    "and execution status.\n",
                    "\n| Type | Title | Status | Priority | Notes |",
                    "\n|---|---|---|---|---|",
                ]
                for r in rows:
                    props = r["properties"]
                    item_type = self._get_select(props, "Type")
                    title = self._get_title(props)
                    status = self._get_status_for_row(props)
                    priority = self._get_select(props, "Priority")
                    notes = self._get_rich_text(props, "Notes")
                    lines.append(
                        f"\n| {item_type} | {title} | {status} "
                        f"| {priority} | {notes} |"
                    )
                backlog_path.write_text("".join(lines) + "\n")
            summary["created"] += 1
        except Exception:
            summary["failed"] += 1

        # Sync decisions → _project/decisions.md
        try:
            decisions = self.read_decisions()
            summary["fetched"] += len(decisions)
            decisions_path = target / "_project" / "decisions.md"
            existing_text = (
                decisions_path.read_text() if decisions_path.exists() else ""
            )
            for d in decisions:
                if d["id"] and d["id"] in existing_text:
                    summary["skipped"] += 1
                else:
                    if not dry_run:
                        row = (
                            f"| {d['id']} | {d['date']} | {d['title']} "
                            f"| {d['why']} | {d['alternatives_rejected']} "
                            f"| {d.get('adr_link') or '—'} |\n"
                        )
                        with open(decisions_path, "a") as f:
                            f.write(row)
                    summary["created"] += 1
        except Exception:
            summary["failed"] += 1

        return summary

    def sync_templates_to_local(
        self, template_dir: str, *, dry_run: bool = False
    ) -> dict:
        """Pull templates from Notion back to local template/ files."""
        target = Path(template_dir)
        summary = {"fetched": 0, "updated": 0, "skipped": 0, "failed": 0}

        try:
            templates = self.read_templates()
            for tpl in templates:
                summary["fetched"] += 1
                name = tpl["name"]
                filename = f"_{name}.md" if name == "inbox" else f"{name}.md"
                local_path = target / filename

                if local_path.exists():
                    local_content = local_path.read_text()
                    version_match = re.search(r"\(v(\d+)\)", local_content)
                    local_version = (
                        f"v{version_match.group(1)}" if version_match else "v0"
                    )
                    if local_version >= tpl["version"]:
                        summary["skipped"] += 1
                        continue

                if not dry_run:
                    target.mkdir(parents=True, exist_ok=True)
                    local_path.write_text(tpl["content"])
                summary["updated"] += 1
        except Exception:
            summary["failed"] += 1

        return summary

    # -- Internal helpers --

    @staticmethod
    def _blocks_to_markdown(blocks: list[dict]) -> str:
        """Convert Notion blocks back to markdown (simplified)."""
        def _render_rich_text(items: list[dict]) -> str:
            rendered = []
            for item in items:
                text = item.get("plain_text")
                if text is None:
                    text = item.get("text", {}).get("content", "")
                annotations = item.get("annotations", {})
                if annotations.get("bold"):
                    text = f"**{text}**"
                if annotations.get("italic"):
                    text = f"*{text}*"
                rendered.append(text)
            return "".join(rendered)

        lines = []
        for block in blocks:
            btype = block.get("type", "")
            data = block.get(btype, {})
            text_items = data.get("rich_text", [])
            text = _render_rich_text(text_items)

            if btype == "heading_1":
                lines.append(f"# {text}")
            elif btype == "heading_2":
                lines.append(f"## {text}")
            elif btype == "heading_3":
                lines.append(f"### {text}")
            elif btype == "bulleted_list_item":
                lines.append(f"- {text}")
            elif btype == "numbered_list_item":
                lines.append(f"1. {text}")
            elif btype == "to_do":
                checked = data.get("checked", False)
                mark = "x" if checked else " "
                lines.append(f"- [{mark}] {text}")
            elif btype == "divider":
                lines.append("---")
            elif btype == "paragraph":
                lines.append(text if text else "")
            else:
                lines.append(text)
        return "\n".join(lines) + "\n" if lines else ""

    @staticmethod
    def _render_brief_body(
        brief_name: str,
        data: dict,
        *,
        history: list[dict] | None = None,
    ) -> str:
        """Render brief sections to markdown for Notion block content."""
        return render_brief_markdown(
            brief_name, data, include_title=False, history=history,
        ).rstrip()
