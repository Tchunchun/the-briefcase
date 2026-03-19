"""Notion workspace provisioner.

Creates the page tree and databases for a project. Idempotent — re-running
against the same parent page does not duplicate pages or databases.

v3: Unified Backlog (Idea/Feature/Task) + Decisions database +
Briefs page + Release Notes page + Templates page + README page.
Section-label paragraphs organize the visual layout.

Provisioned layout:
  📁 Project Root
  ├── PARA "Backlog"
  ├── 📊 Backlog (database)
  ├── PARA ""
  ├── PARA "Documentations"
  ├── 📋 Briefs (page)
  ├── ⚖️ Decisions (database)
  ├── 🚀 Release Notes (page)
  ├── 📄 Templates (page)
  └── 📄 README (page)
"""

from __future__ import annotations

import re
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

        Creates databases and pages in visual order with section labels.
        Idempotent — skips items that already exist.

        Returns:
            (resource_ids, result) where resource_ids maps
            name → Notion ID (databases and pages), and result has details.
        """
        result = ProvisionResult()
        resource_ids: dict[str, str] = {}

        # Check for existing databases and pages
        existing_dbs = self._find_existing_databases(parent_page_id)
        existing_pages = self._find_existing_pages(parent_page_id)

        is_fresh = not existing_dbs and not existing_pages

        # -- "Backlog" section label (only on fresh provision) --
        if is_fresh:
            self._append_paragraph(parent_page_id, "Backlog")

        # -- Backlog database --
        self._provision_database(
            "backlog", parent_page_id, existing_dbs, resource_ids, result
        )

        # -- Self-relation on Backlog (two-step, only when freshly created) --
        if "backlog" in resource_ids and "backlog" in result.databases_created:
            try:
                self._add_self_relation(resource_ids["backlog"])
            except Exception as e:
                result.errors.append(
                    f"Failed to add Parent self-relation to Backlog: {e}"
                )

        # -- Spacer + "Documentations" section label --
        if is_fresh:
            self._append_paragraph(parent_page_id, "")
            self._append_paragraph(parent_page_id, "Documentations")

        # -- Briefs page --
        self._provision_page(
            "briefs", "Briefs", "📋",
            parent_page_id, existing_pages, resource_ids, result,
        )

        # -- Decisions database --
        self._provision_database(
            "decisions", parent_page_id, existing_dbs, resource_ids, result
        )

        # -- Release Notes page --
        self._provision_page(
            "release_notes", "Release Notes", "🚀",
            parent_page_id, existing_pages, resource_ids, result,
        )

        # -- Templates page --
        self._provision_page(
            "templates", "Templates", "📄",
            parent_page_id, existing_pages, resource_ids, result,
        )

        # -- README page --
        if "readme" in existing_pages:
            resource_ids["readme"] = existing_pages["readme"]
        else:
            try:
                readme = self._create_readme_page(parent_page_id)
                resource_ids["readme"] = readme["id"]
                result.pages_created.append("readme")
            except Exception as e:
                result.errors.append(f"Failed to create README page: {e}")

        # Seed templates if template_dir provided and Templates page exists
        if template_dir and "templates" in resource_ids:
            self._seed_templates(
                resource_ids["templates"], Path(template_dir), result
            )

        return resource_ids, result

    # -- Provision helpers --

    def _provision_database(
        self,
        db_key: str,
        parent_page_id: str,
        existing_dbs: dict[str, str],
        resource_ids: dict[str, str],
        result: ProvisionResult,
    ) -> None:
        """Provision a single database, skipping if it already exists."""
        schema, icon, display_title = DATABASE_REGISTRY[db_key]
        if db_key in existing_dbs:
            resource_ids[db_key] = existing_dbs[db_key]
            result.databases_found.append(db_key)
            self._ensure_schema(db_key, existing_dbs[db_key], result)
        else:
            try:
                db = self._client.create_database(
                    parent_page_id, display_title, schema, icon=icon
                )
                resource_ids[db_key] = db["id"]
                result.databases_created.append(db_key)
            except Exception as e:
                result.errors.append(
                    f"Failed to create database '{db_key}': {e}"
                )

    def _provision_page(
        self,
        key: str,
        title: str,
        icon: str,
        parent_page_id: str,
        existing_pages: dict[str, str],
        resource_ids: dict[str, str],
        result: ProvisionResult,
    ) -> None:
        """Provision a single container page, skipping if it already exists."""
        if key in existing_pages:
            resource_ids[key] = existing_pages[key]
        else:
            try:
                page = self._client.create_page(
                    parent_page_id, title, icon=icon
                )
                resource_ids[key] = page["id"]
                result.pages_created.append(key)
            except Exception as e:
                result.errors.append(f"Failed to create {title} page: {e}")

    def _append_paragraph(self, parent_page_id: str, text: str) -> None:
        """Append a paragraph block to the parent page."""
        block = {
            "type": "paragraph",
            "paragraph": {
                "rich_text": (
                    [{"type": "text", "text": {"content": text}}]
                    if text
                    else []
                )
            },
        }
        self._client.append_block_children(parent_page_id, [block])

    def _add_self_relation(self, backlog_db_id: str) -> None:
        """Add the Parent self-relation property to the Backlog database."""
        self._client.update_database(
            backlog_db_id,
            properties={
                "Parent": {
                    "relation": {
                        "database_id": backlog_db_id,
                        "single_property": {},
                    }
                }
            },
        )

    def _create_readme_page(self, parent_page_id: str) -> dict:
        """Create the README page with project structure and view guide."""
        blocks = [
            {
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"text": {"content": "Project Structure"}}]
                },
            },
            {
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "text": {
                                "content": (
                                    "This Notion workspace is organized as follows:"
                                )
                            }
                        }
                    ]
                },
            },
            {
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [
                        {
                            "text": {
                                "content": (
                                    "📊 Backlog — unified database for Ideas, "
                                    "Features, and Tasks"
                                )
                            }
                        }
                    ]
                },
            },
            {
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [
                        {
                            "text": {
                                "content": (
                                    "⚖️ Decisions — architectural decisions log"
                                )
                            }
                        }
                    ]
                },
            },
            {
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [
                        {
                            "text": {
                                "content": (
                                    "📄 Templates — reference templates "
                                    "(one sub-page per template)"
                                )
                            }
                        }
                    ]
                },
            },
            {
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [
                        {
                            "text": {
                                "content": (
                                    "� Briefs — feature briefs "
                                    "(one sub-page per feature)"
                                )
                            }
                        }
                    ]
                },
            },
            {
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [
                        {
                            "text": {
                                "content": (
                                    "🚀 Release Notes — release history "
                                    "(one sub-page per version)"
                                )
                            }
                        }
                    ]
                },
            },
            {
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [
                        {"text": {"content": "Recommended Board Views"}}
                    ]
                },
            },
            {
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "text": {
                                "content": (
                                    "Create three views on the Backlog database "
                                    "(Notion API cannot create views — do this "
                                    "manually):"
                                )
                            }
                        }
                    ]
                },
            },
            {
                "type": "numbered_list_item",
                "numbered_list_item": {
                    "rich_text": [
                        {
                            "text": {
                                "content": (
                                    "Idea Board — filter Type = Idea, "
                                    "Board view grouped by Idea Status"
                                )
                            }
                        }
                    ]
                },
            },
            {
                "type": "numbered_list_item",
                "numbered_list_item": {
                    "rich_text": [
                        {
                            "text": {
                                "content": (
                                    "Feature Board — filter Type = Feature, "
                                    "Board view grouped by Feature Status"
                                )
                            }
                        }
                    ]
                },
            },
            {
                "type": "numbered_list_item",
                "numbered_list_item": {
                    "rich_text": [
                        {
                            "text": {
                                "content": (
                                    "Task Board — filter Type = Task, "
                                    "Board view grouped by Task Status"
                                )
                            }
                        }
                    ]
                },
            },
        ]
        return self._client.create_page(
            parent_page_id, "README", icon="📄", children=blocks
        )

    def _find_existing_databases(self, parent_page_id: str) -> dict[str, str]:
        """Find databases already created under the parent page."""
        existing: dict[str, str] = {}
        try:
            children = self._client.get_block_children(parent_page_id)
            for child in children:
                if child.get("type") == "child_database":
                    title = child.get("child_database", {}).get("title", "")
                    for db_key, (_, _, display_title) in DATABASE_REGISTRY.items():
                        if title == display_title:
                            existing[db_key] = child["id"]
                            break
        except Exception:
            pass
        return existing

    def _ensure_schema(
        self, db_key: str, db_id: str, result: ProvisionResult
    ) -> None:
        """Ensure an existing database has all required properties.

        Delegates to the shared schema-health helper so setup and upgrade
        use the same validation logic (decision D-028).
        """
        from src.integrations.notion.schema_health import (
            apply_missing_properties,
            apply_missing_select_options,
            check_database_schema,
        )

        expected_schema = DATABASE_REGISTRY[db_key][0]
        try:
            db_meta = self._client.get_database(db_id)
            existing_props = db_meta.get("properties", {})
            missing, select_gaps = check_database_schema(
                db_key, db_key, expected_schema, existing_props,
            )
            total_fixes = len(missing) + len(select_gaps)
            if missing:
                apply_missing_properties(self._client, db_id, missing)
            if select_gaps:
                apply_missing_select_options(self._client, db_id, select_gaps)
            if total_fixes:
                result.pages_created.append(
                    f"schema-upgrade:{db_key}({total_fixes} fixes applied)"
                )
        except Exception as e:
            result.errors.append(
                f"Failed to verify/upgrade schema for '{db_key}': {e}"
            )

    def _find_existing_pages(self, parent_page_id: str) -> dict[str, str]:
        """Find named pages already created under the parent page."""
        page_titles = {
            "README": "readme",
            "Templates": "templates",
            "Briefs": "briefs",
            "Release Notes": "release_notes",
        }
        existing: dict[str, str] = {}
        try:
            children = self._client.get_block_children(parent_page_id)
            for child in children:
                if child.get("type") == "child_page":
                    title = child.get("child_page", {}).get("title", "")
                    key = page_titles.get(title)
                    if key:
                        existing[key] = child["id"]
        except Exception:
            pass
        return existing

    def _seed_templates(
        self, templates_page_id: str, template_dir: Path, result: ProvisionResult
    ) -> None:
        """Seed templates from local template/ directory as child pages."""
        if not template_dir.exists():
            return

        # Check what's already seeded (child pages of Templates page)
        existing_names: set[str] = set()
        try:
            children = self._client.get_block_children(templates_page_id)
            for child in children:
                if child.get("type") == "child_page":
                    title = child.get("child_page", {}).get("title", "")
                    existing_names.add(title)
        except Exception:
            pass

        for md_file in sorted(template_dir.glob("*.md")):
            name = md_file.stem.lstrip("_")
            if name in existing_names:
                continue

            content = md_file.read_text()
            version = "v1"
            version_match = re.search(r"\(v(\d+)\)", content)
            if version_match:
                version = f"v{version_match.group(1)}"

            page_title = f"{name} ({version})"
            if page_title in existing_names:
                continue

            try:
                blocks = self._markdown_to_blocks(content)
                self._client.create_page(
                    templates_page_id,
                    page_title,
                    children=blocks[:100],
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
