"""Notion backend implementing ArtifactStore and SyncableStore protocols.

Reads/writes planning artifacts directly to Notion databases via the API.
When Notion is the active backend, this is the source of truth.
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Any

from src.core.storage.config import NotionConfig
from src.integrations.notion.client import NotionClient


class NotionBackend:
    """ArtifactStore + SyncableStore backed by Notion databases."""

    def __init__(self, config: NotionConfig, project_root: str | Path) -> None:
        self._config = config
        self._root = Path(project_root)
        self._client = NotionClient()
        self._dbs = config.databases

    def _db(self, name: str) -> str:
        db_id = self._dbs.get(name)
        if not db_id:
            raise ValueError(
                f"Notion database '{name}' not configured. "
                "Run `agent setup --backend notion` to provision."
            )
        return db_id

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

    # -- Inbox --

    def read_inbox(self) -> list[dict]:
        rows = self._client.query_database(self._db("intake"))
        return [
            {
                "text": self._get_title(r["properties"]),
                "type": self._get_select(r["properties"], "Type"),
                "status": self._get_select(r["properties"], "Status"),
                "notion_id": r["id"],
            }
            for r in rows
        ]

    def append_inbox(self, entry: dict) -> None:
        props = {
            "Title": self._title_prop(entry["text"]),
            "Type": self._select_prop(entry.get("type", "idea")),
            "Status": self._select_prop(entry.get("status", "new")),
        }
        self._client.create_database_page(self._db("intake"), props)

    # -- Briefs --

    def read_brief(self, brief_name: str) -> dict:
        rows = self._client.query_database(
            self._db("briefs"),
            filter={
                "property": "Brief Name",
                "rich_text": {"equals": brief_name},
            },
        )
        if not rows:
            raise KeyError(f"Brief not found: {brief_name}")
        row = rows[0]
        props = row["properties"]

        # Get page body content
        blocks = self._client.get_block_children(row["id"])
        body_text = self._blocks_to_markdown(blocks)

        data = {
            "name": brief_name,
            "status": self._get_select(props, "Status"),
            "title": self._get_title(props),
            "raw": body_text,
            "notion_id": row["id"],
        }

        # Parse sections from body
        sections = {
            "problem": r"## Problem\s*\n(.*?)(?=\n## |\Z)",
            "goal": r"## Goal\s*\n(.*?)(?=\n## |\Z)",
            "acceptance_criteria": r"## Acceptance Criteria\s*\n(.*?)(?=\n## |\Z)",
            "out_of_scope": r"## Out of Scope\s*\n(.*?)(?=\n## |\Z)",
            "open_questions": r"## Open Questions[^\n]*\n(.*?)(?=\n## |\Z)",
            "technical_approach": r"## Technical Approach\s*\n(.*?)(?=\n## |\Z)",
        }
        for key, pattern in sections.items():
            match = re.search(pattern, body_text, re.DOTALL)
            data[key] = match.group(1).strip() if match else ""

        return data

    def write_brief(self, brief_name: str, data: dict) -> None:
        # Check if brief exists
        existing = self._client.query_database(
            self._db("briefs"),
            filter={
                "property": "Brief Name",
                "rich_text": {"equals": brief_name},
            },
        )

        props = {
            "Title": self._title_prop(data.get("title", brief_name)),
            "Brief Name": self._rich_text_prop(brief_name),
            "Status": self._select_prop(data.get("status", "draft")),
        }

        from src.integrations.notion.provisioner import NotionProvisioner

        body = self._render_brief_body(brief_name, data)
        blocks = NotionProvisioner._markdown_to_blocks(body)

        if existing:
            self._client.update_database_page(existing[0]["id"], props)
        else:
            self._client.create_database_page(
                self._db("briefs"), props, children=blocks[:100]
            )

    def list_briefs(self) -> list[dict]:
        rows = self._client.query_database(self._db("briefs"))
        return [
            {
                "name": self._get_rich_text(r["properties"], "Brief Name"),
                "status": self._get_select(r["properties"], "Status"),
                "title": self._get_title(r["properties"]),
            }
            for r in rows
        ]

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
        if entry.get("adr_link"):
            props["ADR Link"] = self._url_prop(entry["adr_link"])
        self._client.create_database_page(self._db("decisions"), props)

    # -- Backlog --

    def read_backlog(self) -> list[dict]:
        rows = self._client.query_database(self._db("backlog"))
        return [
            {
                "id": self._get_rich_text(r["properties"], "ID"),
                "type": self._get_select(r["properties"], "Type"),
                "use_case": self._get_rich_text(r["properties"], "Use Case"),
                "feature": self._get_rich_text(r["properties"], "Feature"),
                "title": self._get_title(r["properties"]),
                "priority": self._get_select(r["properties"], "Priority"),
                "status": self._get_select(r["properties"], "Status"),
                "notes": self._get_rich_text(r["properties"], "Notes"),
                "notion_id": r["id"],
            }
            for r in rows
        ]

    def write_backlog_row(self, row: dict) -> None:
        # Check if row exists by ID
        existing = self._client.query_database(
            self._db("backlog"),
            filter={"property": "ID", "rich_text": {"equals": row["id"]}},
        )

        props = {
            "Title": self._title_prop(row["title"]),
            "ID": self._rich_text_prop(row["id"]),
            "Type": self._select_prop(row["type"]),
            "Use Case": self._rich_text_prop(row.get("use_case", "")),
            "Feature": self._rich_text_prop(row["feature"]),
            "Priority": self._select_prop(row["priority"]),
            "Status": self._select_prop(row["status"]),
            "Notes": self._rich_text_prop(row.get("notes", "")),
        }

        if existing:
            self._client.update_database_page(existing[0]["id"], props)
        else:
            self._client.create_database_page(self._db("backlog"), props)

    # -- Templates --

    def read_templates(self) -> list[dict]:
        rows = self._client.query_database(self._db("templates"))
        templates = []
        for r in rows:
            props = r["properties"]
            blocks = self._client.get_block_children(r["id"])
            content = self._blocks_to_markdown(blocks)
            templates.append(
                {
                    "name": self._get_title(props, "Name"),
                    "version": self._get_rich_text(props, "Version"),
                    "content": content,
                    "notion_id": r["id"],
                }
            )
        return templates

    def write_template(self, name: str, content: str, version: str) -> None:
        existing = self._client.query_database(
            self._db("templates"),
            filter={"property": "Name", "title": {"equals": name}},
        )

        from src.integrations.notion.provisioner import NotionProvisioner

        props = {
            "Name": self._title_prop(name),
            "Version": self._rich_text_prop(version),
            "Last Seeded": self._date_prop(date.today().isoformat()),
        }
        blocks = NotionProvisioner._markdown_to_blocks(content)

        if existing:
            self._client.update_database_page(existing[0]["id"], props)
        else:
            self._client.create_database_page(
                self._db("templates"), props, children=blocks[:100]
            )

    # -- SyncableStore methods --

    def sync_to_local(self, target_dir: str, *, dry_run: bool = False) -> dict:
        """Generate local markdown from Notion for git audit trail."""
        target = Path(target_dir)
        summary = {"fetched": 0, "created": 0, "skipped": 0, "failed": 0}

        # Sync inbox (append-only)
        try:
            entries = self.read_inbox()
            summary["fetched"] += len(entries)
            inbox_path = target / "docs" / "plan" / "_inbox.md"
            if inbox_path.exists():
                existing_text = inbox_path.read_text()
            else:
                existing_text = ""
            for entry in entries:
                line = f"- [{entry['type']}] {entry['text']}"
                if line not in existing_text:
                    if not dry_run:
                        with open(inbox_path, "a") as f:
                            f.write(line + "\n")
                    summary["created"] += 1
                else:
                    summary["skipped"] += 1
        except Exception:
            summary["failed"] += 1

        # Sync briefs (overwrite)
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

        # Sync decisions (append-only)
        try:
            decisions = self.read_decisions()
            summary["fetched"] += len(decisions)
            decisions_path = target / "_project" / "decisions.md"
            if decisions_path.exists():
                existing_text = decisions_path.read_text()
            else:
                existing_text = ""
            for d in decisions:
                if d["id"] and d["id"] in existing_text:
                    summary["skipped"] += 1
                else:
                    if not dry_run:
                        row = (
                            f"| {d['id']} | {d['date']} | {d['title']} "
                            f"| {d['why']} | {d['alternatives_rejected']} "
                            f"| {d.get('adr_link', '—')} |\n"
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

                # Compare versions
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
        lines = []
        for block in blocks:
            btype = block.get("type", "")
            data = block.get(btype, {})
            text_items = data.get("rich_text", [])
            text = "".join(t.get("plain_text", "") for t in text_items)

            if btype == "heading_1":
                lines.append(f"# {text}")
            elif btype == "heading_2":
                lines.append(f"## {text}")
            elif btype == "heading_3":
                lines.append(f"### {text}")
            elif btype == "bulleted_list_item":
                lines.append(f"- {text}")
            elif btype == "to_do":
                checked = data.get("checked", False)
                mark = "x" if checked else " "
                lines.append(f"- [{mark}] {text}")
            elif btype == "paragraph":
                lines.append(text if text else "")
            else:
                lines.append(text)
        return "\n".join(lines) + "\n" if lines else ""

    @staticmethod
    def _render_brief_body(brief_name: str, data: dict) -> str:
        """Render brief sections to markdown for Notion block content."""
        return "\n".join(
            [
                f"## Problem",
                data.get("problem", ""),
                "",
                "## Goal",
                data.get("goal", ""),
                "",
                "## Acceptance Criteria",
                data.get("acceptance_criteria", ""),
                "",
                "## Out of Scope",
                data.get("out_of_scope", ""),
                "",
                "## Open Questions",
                data.get("open_questions", ""),
                "",
                "## Technical Approach",
                data.get("technical_approach", "*Owned by architect agent.*"),
            ]
        )
