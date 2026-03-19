"""Shared schema-health helper for Notion database validation and additive repair.

Used by both the provisioner (at setup time) and the upgrade service
(for ongoing health checks).  One model, one repair path, two callers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class HealthStatus(str, Enum):
    """Outcome for a single schema-health finding."""

    OK = "ok"
    FIXED = "fixed"
    MANUAL = "manual"


@dataclass
class SchemaFinding:
    """A single schema-health observation."""

    database: str
    description: str
    status: HealthStatus

    def to_dict(self) -> dict[str, str]:
        return {
            "database": self.database,
            "description": self.description,
            "status": self.status.value,
        }


@dataclass
class SchemaHealthReport:
    """Aggregated schema-health findings across databases."""

    findings: list[SchemaFinding] = field(default_factory=list)

    def add(self, database: str, description: str, status: HealthStatus) -> None:
        self.findings.append(SchemaFinding(database, description, status))

    @property
    def has_issues(self) -> bool:
        return any(f.status != HealthStatus.OK for f in self.findings)

    @property
    def fixed_count(self) -> int:
        return sum(1 for f in self.findings if f.status == HealthStatus.FIXED)

    def to_dict(self) -> dict[str, Any]:
        return {
            "findings": [f.to_dict() for f in self.findings],
            "total": len(self.findings),
            "ok": sum(1 for f in self.findings if f.status == HealthStatus.OK),
            "fixed": self.fixed_count,
            "manual": sum(1 for f in self.findings if f.status == HealthStatus.MANUAL),
        }


# ---------------------------------------------------------------------------
# Core validation logic
# ---------------------------------------------------------------------------

def check_database_schema(
    db_key: str,
    display_name: str,
    expected_schema: dict[str, dict],
    existing_props: dict[str, Any],
) -> tuple[dict[str, dict], list[tuple[str, dict, dict]]]:
    """Compare expected schema against existing properties.

    Returns:
        (missing_props, select_gaps)
        missing_props: dict of ``{prop_name: prop_schema}`` to add.
        select_gaps: list of ``(prop_name, expected_schema, existing_prop)``
            tuples where select options are incomplete.
    """
    missing_props: dict[str, dict] = {}
    select_gaps: list[tuple[str, dict, dict]] = []

    existing_types = {name: prop.get("type") for name, prop in existing_props.items()}

    for prop_name, prop_schema in expected_schema.items():
        # Title properties — every DB has exactly one; name may differ.
        if "title" in prop_schema:
            has_title = any(t == "title" for t in existing_types.values())
            if not has_title:
                missing_props[prop_name] = prop_schema
            continue

        if prop_name not in existing_props:
            missing_props[prop_name] = prop_schema
            continue

        # Property exists — check select options if applicable.
        if "select" in prop_schema:
            existing_prop = existing_props[prop_name]
            if existing_prop.get("type") != "select":
                # Type mismatch — cannot auto-fix.
                continue
            expected_options = {
                o["name"]
                for o in prop_schema.get("select", {}).get("options", [])
            }
            existing_options = {
                o["name"]
                for o in existing_prop.get("select", {}).get("options", [])
            }
            if expected_options - existing_options:
                select_gaps.append((prop_name, prop_schema, existing_prop))

    return missing_props, select_gaps


def apply_missing_properties(
    client: Any,
    db_id: str,
    missing_props: dict[str, dict],
) -> None:
    """Patch-add missing properties to a Notion database."""
    if missing_props:
        client.update_database(db_id, properties=missing_props)


def apply_missing_select_options(
    client: Any,
    db_id: str,
    select_gaps: list[tuple[str, dict, dict]],
) -> None:
    """Patch-add missing select options for each gapped property."""
    for prop_name, prop_schema, existing_prop in select_gaps:
        expected_options = {
            o["name"]
            for o in prop_schema.get("select", {}).get("options", [])
        }
        existing_options_list = list(
            existing_prop.get("select", {}).get("options", [])
        )
        existing_names = {o["name"] for o in existing_options_list}
        missing = expected_options - existing_names
        if missing:
            new_options = existing_options_list + [{"name": n} for n in missing]
            client.update_database(
                db_id,
                properties={prop_name: {"select": {"options": new_options}}},
            )
