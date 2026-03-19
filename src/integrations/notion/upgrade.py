"""Notion workspace upgrade service.

Inspects a provisioned Notion workspace for schema gaps, missing pages,
and config staleness. Classifies findings as ok / fixable / manual and
applies only safe additive repairs.

Used by:
- `agent upgrade` CLI command (standalone workspace health check + repair)
- `NotionProvisioner._ensure_schema()` (can delegate here for shared logic)
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from src.core.storage.config import StorageConfig
from src.integrations.notion.client import NotionClient
from src.integrations.notion.schemas import DATABASE_REGISTRY


class FindingStatus(str, Enum):
    OK = "OK"
    FIXED = "FIXED"
    MANUAL = "NEEDS MANUAL ACTION"


@dataclass
class Finding:
    """A single inspection finding."""

    category: str
    description: str
    status: FindingStatus

    def to_dict(self) -> dict[str, str]:
        return {
            "category": self.category,
            "status": self.status.value,
            "description": self.description,
        }


@dataclass
class UpgradeReport:
    """Aggregated results from an upgrade inspection + optional repair."""

    findings: list[Finding] = field(default_factory=list)

    @property
    def has_issues(self) -> bool:
        return any(
            f.status in (FindingStatus.FIXED, FindingStatus.MANUAL)
            for f in self.findings
        )

    @property
    def has_unfixed(self) -> bool:
        return any(f.status == FindingStatus.MANUAL for f in self.findings)

    @property
    def exit_code(self) -> int:
        if self.has_unfixed:
            return 2
        if self.has_issues:
            return 1
        return 0

    def add(self, category: str, description: str, status: FindingStatus) -> None:
        self.findings.append(Finding(category, description, status))

    def to_dict(self) -> dict[str, Any]:
        grouped: dict[str, list[dict]] = {}
        for f in self.findings:
            grouped.setdefault(f.status.value, []).append(f.to_dict())
        return {
            "findings": [f.to_dict() for f in self.findings],
            "summary": {
                "total": len(self.findings),
                "ok": sum(1 for f in self.findings if f.status == FindingStatus.OK),
                "fixed": sum(1 for f in self.findings if f.status == FindingStatus.FIXED),
                "manual": sum(1 for f in self.findings if f.status == FindingStatus.MANUAL),
            },
        }


class NotionUpgradeService:
    """Inspects and optionally repairs a Notion workspace."""

    def __init__(self, client: NotionClient, config: StorageConfig) -> None:
        self._client = client
        self._config = config

    def inspect(self) -> UpgradeReport:
        """Run all checks without applying any repairs."""
        report = UpgradeReport()
        self._check_token_env(report)
        self._check_config_validity(report)
        self._check_parent_page(report)
        self._check_database_schemas(report, apply=False)
        self._check_page_ids(report, apply=False)
        return report

    def upgrade(self) -> UpgradeReport:
        """Run all checks and apply safe additive repairs."""
        report = UpgradeReport()
        self._check_token_env(report)
        self._check_config_validity(report)
        self._check_parent_page(report)
        self._check_database_schemas(report, apply=True)
        self._check_page_ids(report, apply=True)
        return report

    # -- Individual checks --

    def _check_token_env(self, report: UpgradeReport) -> None:
        """Check Notion API token environment variables."""
        has_key = bool(os.environ.get("NOTION_API_KEY"))
        has_legacy = bool(os.environ.get("NOTION_API_TOKEN"))

        if has_key:
            report.add("token", "NOTION_API_KEY is set", FindingStatus.OK)
        elif has_legacy:
            report.add(
                "token",
                "Only legacy NOTION_API_TOKEN is set. "
                "Rename to NOTION_API_KEY for forward compatibility.",
                FindingStatus.MANUAL,
            )
        else:
            report.add(
                "token",
                "Neither NOTION_API_KEY nor NOTION_API_TOKEN is set. "
                "Set NOTION_API_KEY in your environment.",
                FindingStatus.MANUAL,
            )

    def _check_config_validity(self, report: UpgradeReport) -> None:
        """Validate _project/storage.yaml structure."""
        if not self._config.is_notion():
            report.add(
                "config",
                f"Backend is '{self._config.backend}', not 'notion'. "
                "Upgrade is only applicable to Notion backends.",
                FindingStatus.MANUAL,
            )
            return

        notion = self._config.notion
        if not notion or not notion.parent_page_id:
            report.add(
                "config",
                "parent_page_id is missing from storage.yaml.",
                FindingStatus.MANUAL,
            )
            return

        report.add("config", "storage.yaml is valid", FindingStatus.OK)

        # Check database IDs
        for db_key in DATABASE_REGISTRY:
            if db_key in (notion.databases or {}):
                report.add(
                    "config",
                    f"Database ID for '{db_key}' is configured",
                    FindingStatus.OK,
                )
            else:
                report.add(
                    "config",
                    f"Database ID for '{db_key}' is missing from storage.yaml. "
                    "Run `agent setup` to provision.",
                    FindingStatus.MANUAL,
                )

    def _check_parent_page(self, report: UpgradeReport) -> None:
        """Verify the parent page is accessible."""
        notion = self._config.notion
        if not notion or not notion.parent_page_id:
            return  # Already flagged in config check

        try:
            self._client.get_page(notion.parent_page_id)
            report.add(
                "workspace",
                "Parent page is accessible",
                FindingStatus.OK,
            )
        except Exception as e:
            report.add(
                "workspace",
                f"Cannot access parent page ({notion.parent_page_id}): {e}. "
                "Check that the integration has access to this page.",
                FindingStatus.MANUAL,
            )

    def _check_database_schemas(
        self, report: UpgradeReport, *, apply: bool
    ) -> None:
        """Check database schemas match expected properties and options."""
        notion = self._config.notion
        if not notion:
            return

        for db_key, (expected_schema, _, display_name) in DATABASE_REGISTRY.items():
            db_id = (notion.databases or {}).get(db_key)
            if not db_id:
                continue  # Already flagged in config check

            try:
                db_meta = self._client.get_database(db_id)
            except Exception as e:
                report.add(
                    f"schema:{db_key}",
                    f"Cannot access {display_name} database: {e}",
                    FindingStatus.MANUAL,
                )
                continue

            existing_props = db_meta.get("properties", {})
            self._check_properties(
                db_key, db_id, display_name,
                expected_schema, existing_props,
                report, apply=apply,
            )

    def _check_properties(
        self,
        db_key: str,
        db_id: str,
        display_name: str,
        expected_schema: dict[str, dict],
        existing_props: dict[str, Any],
        report: UpgradeReport,
        *,
        apply: bool,
    ) -> None:
        """Check individual properties and select options via shared helper."""
        from src.integrations.notion.schema_health import (
            apply_missing_properties,
            apply_missing_select_options,
            check_database_schema,
        )

        missing_props, select_gaps = check_database_schema(
            db_key, display_name, expected_schema, existing_props,
        )

        # Also detect type mismatches for select properties (manual-only).
        existing_types = {
            name: prop.get("type") for name, prop in existing_props.items()
        }
        for prop_name, prop_schema in expected_schema.items():
            if "select" in prop_schema and prop_name in existing_props:
                if existing_props[prop_name].get("type") != "select":
                    report.add(
                        f"schema:{db_key}",
                        f"Property '{prop_name}' in {display_name} is type "
                        f"'{existing_props[prop_name].get('type')}', expected 'select'. Cannot auto-fix.",
                        FindingStatus.MANUAL,
                    )

        # Report and apply missing properties.
        if not missing_props and not select_gaps:
            report.add(
                f"schema:{db_key}",
                f"{display_name} schema matches expected properties",
                FindingStatus.OK,
            )
        elif apply:
            try:
                if missing_props:
                    apply_missing_properties(self._client, db_id, missing_props)
                    for name in missing_props:
                        report.add(
                            f"schema:{db_key}",
                            f"Added missing property '{name}' to {display_name}",
                            FindingStatus.FIXED,
                        )
            except Exception as e:
                report.add(
                    f"schema:{db_key}",
                    f"Failed to add missing properties to {display_name}: {e}",
                    FindingStatus.MANUAL,
                )
            # Select option gaps
            self._apply_select_gaps(
                db_key, db_id, display_name, select_gaps, report, apply=True,
            )
        else:
            for name in missing_props:
                report.add(
                    f"schema:{db_key}",
                    f"Missing property '{name}' in {display_name}",
                    FindingStatus.MANUAL,
                )
            self._apply_select_gaps(
                db_key, db_id, display_name, select_gaps, report, apply=False,
            )

    def _apply_select_gaps(
        self,
        db_key: str,
        db_id: str,
        display_name: str,
        select_gaps: list[tuple[str, dict, dict]],
        report: UpgradeReport,
        *,
        apply: bool,
    ) -> None:
        """Report or fix select-option gaps."""
        from src.integrations.notion.schema_health import apply_missing_select_options

        for prop_name, prop_schema, existing_prop in select_gaps:
            expected_options = {
                o["name"]
                for o in prop_schema.get("select", {}).get("options", [])
            }
            existing_options = {
                o["name"]
                for o in existing_prop.get("select", {}).get("options", [])
            }
            missing_options = expected_options - existing_options

            if apply:
                try:
                    apply_missing_select_options(
                        self._client, db_id, [(prop_name, prop_schema, existing_prop)],
                    )
                    report.add(
                        f"schema:{db_key}",
                        f"Added missing options {sorted(missing_options)} "
                        f"to '{prop_name}' in {display_name}",
                        FindingStatus.FIXED,
                    )
                except Exception as e:
                    report.add(
                        f"schema:{db_key}",
                        f"Failed to add options to '{prop_name}' "
                        f"in {display_name}: {e}",
                        FindingStatus.MANUAL,
                    )
            else:
                report.add(
                    f"schema:{db_key}",
                    f"Missing options {sorted(missing_options)} "
                    f"in '{prop_name}' of {display_name}",
                    FindingStatus.MANUAL,
                )

    def _check_page_ids(
        self, report: UpgradeReport, *, apply: bool
    ) -> None:
        """Check that readme and templates page IDs are in config."""
        notion = self._config.notion
        if not notion or not notion.parent_page_id:
            return

        expected_pages = {"readme": "README", "templates": "Templates"}
        databases = notion.databases or {}
        missing_keys: dict[str, str] = {}

        for key, title in expected_pages.items():
            if key in databases and databases[key]:
                report.add(
                    f"page:{key}",
                    f"{title} page ID is configured",
                    FindingStatus.OK,
                )
            else:
                missing_keys[key] = title

        if not missing_keys:
            return

        # Try to discover missing pages under parent
        try:
            children = self._client.get_block_children(notion.parent_page_id)
        except Exception as e:
            for key, title in missing_keys.items():
                report.add(
                    f"page:{key}",
                    f"{title} page ID missing and cannot scan parent: {e}",
                    FindingStatus.MANUAL,
                )
            return

        page_titles_to_keys = {v: k for k, v in missing_keys.items()}
        discovered: dict[str, str] = {}

        for child in children:
            if child.get("type") == "child_page":
                child_title = child.get("child_page", {}).get("title", "")
                if child_title in page_titles_to_keys:
                    key = page_titles_to_keys[child_title]
                    discovered[key] = child["id"]

        for key, title in missing_keys.items():
            if key in discovered:
                if apply:
                    notion.databases[key] = discovered[key]
                    report.add(
                        f"page:{key}",
                        f"Restored {title} page ID in storage.yaml",
                        FindingStatus.FIXED,
                    )
                else:
                    report.add(
                        f"page:{key}",
                        f"{title} page exists but ID is missing from storage.yaml",
                        FindingStatus.MANUAL,
                    )
            else:
                report.add(
                    f"page:{key}",
                    f"{title} page not found under parent. "
                    "Run `agent setup` to provision.",
                    FindingStatus.MANUAL,
                )
