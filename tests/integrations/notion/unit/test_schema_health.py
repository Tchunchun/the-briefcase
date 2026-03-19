"""Unit tests for src.integrations.notion.schema_health — shared schema-health helper."""

import pytest

from src.integrations.notion.schema_health import (
    HealthStatus,
    SchemaFinding,
    SchemaHealthReport,
    apply_missing_properties,
    apply_missing_select_options,
    check_database_schema,
)


# -- Fixtures -----------------------------------------------------------------

SAMPLE_SCHEMA = {
    "Title": {"title": {}},
    "Type": {
        "select": {"options": [{"name": "Idea"}, {"name": "Feature"}, {"name": "Task"}]},
    },
    "Priority": {
        "select": {"options": [{"name": "High"}, {"name": "Medium"}, {"name": "Low"}]},
    },
    "Notes": {"rich_text": {}},
}


def _existing_props(names: list[str], *, title_name: str = "Title") -> dict:
    """Build a minimal existing-properties dict."""
    props: dict = {}
    for name in names:
        if name == title_name:
            props[name] = {"type": "title"}
        elif name == "Type":
            props[name] = {
                "type": "select",
                "select": {"options": [{"name": "Idea"}, {"name": "Feature"}, {"name": "Task"}]},
            }
        elif name == "Priority":
            props[name] = {
                "type": "select",
                "select": {"options": [{"name": "High"}, {"name": "Medium"}, {"name": "Low"}]},
            }
        elif name == "Notes":
            props[name] = {"type": "rich_text"}
        else:
            props[name] = {"type": "rich_text"}
    return props


# -- check_database_schema tests -----------------------------------------------

class TestCheckDatabaseSchema:
    def test_healthy_schema_returns_no_gaps(self):
        existing = _existing_props(["Title", "Type", "Priority", "Notes"])
        missing, gaps = check_database_schema("backlog", "Backlog", SAMPLE_SCHEMA, existing)
        assert missing == {}
        assert gaps == []

    def test_missing_property_detected(self):
        existing = _existing_props(["Title", "Type"])  # Missing Priority, Notes
        missing, gaps = check_database_schema("backlog", "Backlog", SAMPLE_SCHEMA, existing)
        assert "Priority" in missing
        assert "Notes" in missing

    def test_title_renamed_is_ok(self):
        """Notion DBs may rename title to 'Name'; that's fine."""
        existing = _existing_props(["Name", "Type", "Priority", "Notes"], title_name="Name")
        missing, gaps = check_database_schema("backlog", "Backlog", SAMPLE_SCHEMA, existing)
        assert "Title" not in missing  # Should be skipped

    def test_no_title_at_all_detected(self):
        existing = {"Type": {"type": "select", "select": {"options": []}}}
        missing, _ = check_database_schema("backlog", "Backlog", SAMPLE_SCHEMA, existing)
        assert "Title" in missing

    def test_select_option_gap_detected(self):
        existing = _existing_props(["Title", "Type", "Priority", "Notes"])
        # Remove one option from Priority
        existing["Priority"]["select"]["options"] = [{"name": "High"}]
        missing, gaps = check_database_schema("backlog", "Backlog", SAMPLE_SCHEMA, existing)
        assert missing == {}
        assert len(gaps) == 1
        assert gaps[0][0] == "Priority"

    def test_type_mismatch_skipped(self):
        """If a select property was created as rich_text, don't report as gap."""
        existing = _existing_props(["Title", "Type", "Priority", "Notes"])
        existing["Priority"] = {"type": "rich_text"}  # Wrong type
        missing, gaps = check_database_schema("backlog", "Backlog", SAMPLE_SCHEMA, existing)
        assert missing == {}
        assert gaps == []  # Type mismatch — not a select gap


# -- apply functions tests ------------------------------------------------------

class FakeClient:
    """Minimal mock to capture update_database calls."""

    def __init__(self):
        self.calls: list[tuple] = []

    def update_database(self, db_id: str, *, properties: dict) -> None:
        self.calls.append((db_id, properties))


class TestApplyMissingProperties:
    def test_patches_missing(self):
        client = FakeClient()
        missing = {"Notes": {"rich_text": {}}}
        apply_missing_properties(client, "db-1", missing)
        assert len(client.calls) == 1
        assert "Notes" in client.calls[0][1]

    def test_noop_when_nothing_missing(self):
        client = FakeClient()
        apply_missing_properties(client, "db-1", {})
        assert client.calls == []


class TestApplyMissingSelectOptions:
    def test_adds_missing_options(self):
        client = FakeClient()
        gaps = [
            (
                "Priority",
                {"select": {"options": [{"name": "High"}, {"name": "Medium"}, {"name": "Low"}]}},
                {"type": "select", "select": {"options": [{"name": "High"}]}},
            )
        ]
        apply_missing_select_options(client, "db-1", gaps)
        assert len(client.calls) == 1
        updated_options = client.calls[0][1]["Priority"]["select"]["options"]
        option_names = {o["name"] for o in updated_options}
        assert {"High", "Medium", "Low"} <= option_names


# -- SchemaHealthReport tests ---------------------------------------------------

class TestSchemaHealthReport:
    def test_empty_report(self):
        r = SchemaHealthReport()
        assert not r.has_issues
        assert r.fixed_count == 0

    def test_mixed_report(self):
        r = SchemaHealthReport()
        r.add("backlog", "Schema OK", HealthStatus.OK)
        r.add("backlog", "Fixed Priority", HealthStatus.FIXED)
        r.add("decisions", "Manual fix needed", HealthStatus.MANUAL)
        assert r.has_issues
        assert r.fixed_count == 1
        d = r.to_dict()
        assert d["total"] == 3
        assert d["ok"] == 1
        assert d["fixed"] == 1
        assert d["manual"] == 1
