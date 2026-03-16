"""Notion workspace provisioner.

Creates the page tree and databases for a project. Idempotent — re-running
against the same parent page does not duplicate pages or databases.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from src.integrations.notion.client import NotionClient
from src.integrations.notion.schemas import DATABASE_REGISTRY


class ProvisionResult:
    """Summary of what was provisioned."""

    def __init__(self) -> None:
        self.pages_created: list[str] = []
        self.databases_created: list[str] = []
        self.databases_found: list[str] = []
        self.templates_seeded: list[str] = []
        self.errors: list[str] = []

    @property
    def success(self) -> bool:
        return len(self.errors) == 0

    def summary(self) -> dict:
        return {
            "pages_created": len(self.pages_created),
            "databases_created": len(self.databases_created),
            "databases_found_existing": len(self.databases_found),
            "templates_seeded": len(self.templates_seeded),
            "errors": self.errors,
        }


class NotionProvisioner:
    """Provisions a Notion workspace for a project."""

    def __init__(self, client: NotionClient) -> None:
        self._client = client

    def provision(
        self,
        parent_page_id: str,
        *,
        template_dir: str | Path | None = None,
    ) -> tuple[dict[str, str], ProvisionResult]:
        """Provision the full workspace under the given parent page.

        Returns:
            (database_ids, result) where database_ids maps
            name → Notion database ID, and result has details.
        """
        result = ProvisionResult()
        database_ids: dict[str, str] = {}

        # Check for existing databases to ensure idempotency
        existing = self._find_existing_databases(parent_page_id)

        for db_key, (schema, icon, display_title) in DATABASE_REGISTRY.items():
            if db_key in existing:
                database_ids[db_key] = existing[db_key]
                result.databases_found.append(db_key)
            else:
                try:
                    db = self._client.create_database(
                        parent_page_id, display_title, schema, icon=icon
                    )
                    database_ids[db_key] = db["id"]
                    result.databases_created.append(db_key)
                except Exception as e:
                    result.errors.append(f"Failed to create database '{db_key}': {e}")

        # Seed templates if template_dir provided and templates DB exists
        if template_dir and "templates" in database_ids:
            self._seed_templates(
                database_ids["templates"], Path(template_dir), result
            )

        return database_ids, result

    def _find_existing_databases(self, parent_page_id: str) -> dict[str, str]:
        """Find databases already created under the parent page."""
        existing: dict[str, str] = {}
        try:
            children = self._client.get_block_children(parent_page_id)
            for child in children:
                if child.get("type") == "child_database":
                    title = child.get("child_database", {}).get("title", "")
                    # Match by display title → db_key
                    for db_key, (_, _, display_title) in DATABASE_REGISTRY.items():
                        if title == display_title:
                            existing[db_key] = child["id"]
                            break
        except Exception:
            pass  # If we can't list children, assume nothing exists
        return existing

    def _seed_templates(
        self, templates_db_id: str, template_dir: Path, result: ProvisionResult
    ) -> None:
        """Seed templates from local template/ directory into Notion."""
        import re

        if not template_dir.exists():
            return

        # Check what's already seeded
        existing_names: set[str] = set()
        try:
            rows = self._client.query_database(templates_db_id)
            for row in rows:
                title_prop = row.get("properties", {}).get("Name", {})
                title_items = title_prop.get("title", [])
                if title_items:
                    existing_names.add(title_items[0].get("plain_text", ""))
        except Exception:
            pass

        today = date.today().isoformat()

        for md_file in sorted(template_dir.glob("*.md")):
            name = md_file.stem.lstrip("_")
            if name in existing_names:
                continue

            content = md_file.read_text()
            version = "v1"
            version_match = re.search(r"\(v(\d+)\)", content)
            if version_match:
                version = f"v{version_match.group(1)}"

            try:
                # Create body content as paragraph blocks
                blocks = self._markdown_to_blocks(content)

                self._client.create_database_page(
                    templates_db_id,
                    properties={
                        "Name": {"title": [{"text": {"content": name}}]},
                        "Version": {"rich_text": [{"text": {"content": version}}]},
                        "Last Seeded": {"date": {"start": today}},
                    },
                    children=blocks[:100],  # Notion limit: 100 blocks per request
                )
                result.templates_seeded.append(name)
            except Exception as e:
                result.errors.append(f"Failed to seed template '{name}': {e}")

    @staticmethod
    def _markdown_to_blocks(content: str) -> list[dict]:
        """Convert markdown text to Notion block objects (simplified)."""
        blocks = []
        for line in content.split("\n"):
            if not line.strip():
                continue
            if line.startswith("# "):
                blocks.append({
                    "type": "heading_1",
                    "heading_1": {
                        "rich_text": [{"text": {"content": line[2:].strip()}}]
                    },
                })
            elif line.startswith("## "):
                blocks.append({
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"text": {"content": line[3:].strip()}}]
                    },
                })
            elif line.startswith("### "):
                blocks.append({
                    "type": "heading_3",
                    "heading_3": {
                        "rich_text": [{"text": {"content": line[4:].strip()}}]
                    },
                })
            elif line.startswith("- [ ] ") or line.startswith("- [x] "):
                checked = line.startswith("- [x] ")
                blocks.append({
                    "type": "to_do",
                    "to_do": {
                        "rich_text": [{"text": {"content": line[6:].strip()}}],
                        "checked": checked,
                    },
                })
            elif line.startswith("- "):
                blocks.append({
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"text": {"content": line[2:].strip()}}]
                    },
                })
            else:
                blocks.append({
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"text": {"content": line}}]
                    },
                })
        return blocks
