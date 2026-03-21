"""Unit tests for NotionUpgradeService (mocked Notion client)."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from src.core.storage.config import StorageConfig, NotionConfig
from src.integrations.notion.upgrade import (
    FindingStatus,
    NotionUpgradeService,
    UpgradeReport,
)


# -- Fixtures --


@pytest.fixture
def healthy_config() -> StorageConfig:
    """Config for a fully-provisioned Notion project."""
    return StorageConfig(
        backend="notion",
        notion=NotionConfig(
            parent_page_id="parent-abc",
            parent_page_url="https://notion.so/parent-abc",
            databases={
                "backlog": "db-backlog",
                "decisions": "db-decisions",
                "briefs_db": "db-briefs",
                "readme": "page-readme",
                "templates": "page-templates",
            },
        ),
    )


@pytest.fixture
def mock_client() -> MagicMock:
    """Mocked NotionClient."""
    client = MagicMock()
    return client


def _db_response(properties: dict) -> dict:
    """Build a fake get_database() response."""
    return {"id": "db-123", "properties": properties}


def _make_props(*names_and_types: tuple[str, str]) -> dict:
    """Build a Notion-style properties dict. Each entry is (name, type)."""
    result = {}
    for name, typ in names_and_types:
        if typ == "title":
            result[name] = {"type": "title", "title": {}}
        elif typ == "select":
            result[name] = {
                "type": "select",
                "select": {"options": []},
            }
        elif typ == "rich_text":
            result[name] = {"type": "rich_text", "rich_text": {}}
        elif typ == "url":
            result[name] = {"type": "url", "url": {}}
        elif typ == "date":
            result[name] = {"type": "date", "date": {}}
        elif typ == "relation":
            result[name] = {"type": "relation", "relation": {}}
        else:
            result[name] = {"type": typ}
    return result


def _make_select_prop(options: list[str]) -> dict:
    """Build a Notion-style select property with named options."""
    return {
        "type": "select",
        "select": {"options": [{"name": o} for o in options]},
    }


FULL_BACKLOG_PROPS = {
    "Title": {"type": "title", "title": {}},
    "Type": _make_select_prop(["Idea", "Feature", "Task"]),
    "Idea Status": _make_select_prop(["new", "exploring", "promoted", "rejected", "shipped"]),
    "Feature Status": _make_select_prop(["draft", "architect-review", "implementation-ready", "in-progress",
                                          "review-ready", "review-accepted", "done", "shipped"]),
    "Task Status": _make_select_prop(["to-do", "in-progress", "blocked", "done"]),
    "Priority": _make_select_prop(["High", "Medium", "Low"]),
    "Review Verdict": _make_select_prop(["pending", "accepted", "changes-requested"]),
    "Route State": _make_select_prop(["routed", "returned", "blocked"]),
    "Lane": _make_select_prop(["quick-fix", "small", "feature"]),
    "Brief Link": {"type": "url", "url": {}},
    "Release Note Link": {"type": "url", "url": {}},
    "Notes": {"type": "rich_text", "rich_text": {}},
    "Automation Trace": {"type": "rich_text", "rich_text": {}},
    "Parent": {"type": "relation", "relation": {}},
}

FULL_DECISIONS_PROPS = {
    "Title": {"type": "title", "title": {}},
    "ID": {"type": "rich_text", "rich_text": {}},
    "Date": {"type": "date", "date": {}},
    "Status": _make_select_prop(["proposed", "accepted", "superseded"]),
    "Why": {"type": "rich_text", "rich_text": {}},
    "Alternatives Rejected": {"type": "rich_text", "rich_text": {}},
    "Feature Link": {"type": "url", "url": {}},
    "ADR Link": {"type": "url", "url": {}},
}

FULL_BRIEFS_PROPS = {
    "Name": {"type": "title", "title": {}},
    "Slug": {"type": "rich_text", "rich_text": {}},
    "Status": _make_select_prop(["draft", "implementation-ready"]),
    "Date": {"type": "date", "date": {}},
    "Linked Feature": {"type": "url", "url": {}},
    "Author": {"type": "rich_text", "rich_text": {}},
}


# -- Tests: healthy workspace (no-op) --


class TestHealthyWorkspace:
    def test_inspect_all_ok(self, mock_client, healthy_config, monkeypatch):
        monkeypatch.setenv("NOTION_API_KEY", "test-key")

        mock_client.get_page.return_value = {"id": "parent-abc"}
        mock_client.get_database.side_effect = [
            _db_response(FULL_BACKLOG_PROPS),
            _db_response(FULL_DECISIONS_PROPS),
            _db_response(FULL_BRIEFS_PROPS),
        ]

        service = NotionUpgradeService(mock_client, healthy_config)
        report = service.inspect()

        assert report.exit_code == 0
        assert not report.has_issues
        assert all(f.status == FindingStatus.OK for f in report.findings)

    def test_upgrade_idempotent(self, mock_client, healthy_config, monkeypatch):
        monkeypatch.setenv("NOTION_API_KEY", "test-key")

        mock_client.get_page.return_value = {"id": "parent-abc"}
        mock_client.get_database.side_effect = [
            _db_response(FULL_BACKLOG_PROPS),
            _db_response(FULL_DECISIONS_PROPS),
            _db_response(FULL_BRIEFS_PROPS),
        ]

        service = NotionUpgradeService(mock_client, healthy_config)
        report = service.upgrade()

        assert report.exit_code == 0
        mock_client.update_database.assert_not_called()


# -- Tests: missing properties (auto-fix) --


class TestMissingProperties:
    def test_inspect_detects_missing_props(self, mock_client, healthy_config, monkeypatch):
        monkeypatch.setenv("NOTION_API_KEY", "test-key")

        # Backlog missing Notes and Brief Link
        partial_backlog = {k: v for k, v in FULL_BACKLOG_PROPS.items() if k not in ("Notes", "Brief Link")}
        mock_client.get_page.return_value = {"id": "parent-abc"}
        mock_client.get_database.side_effect = [
            _db_response(partial_backlog),
            _db_response(FULL_DECISIONS_PROPS),
            _db_response(FULL_BRIEFS_PROPS),
        ]

        service = NotionUpgradeService(mock_client, healthy_config)
        report = service.inspect()

        assert report.exit_code == 2  # has manual items (inspect mode)
        manual = [f for f in report.findings if f.status == FindingStatus.MANUAL]
        descriptions = [f.description for f in manual]
        assert any("Notes" in d for d in descriptions)
        assert any("Brief Link" in d for d in descriptions)

    def test_upgrade_fixes_missing_props(self, mock_client, healthy_config, monkeypatch):
        monkeypatch.setenv("NOTION_API_KEY", "test-key")

        partial_backlog = {
            k: v for k, v in FULL_BACKLOG_PROPS.items()
            if k not in ("Notes", "Automation Trace")
        }
        mock_client.get_page.return_value = {"id": "parent-abc"}
        mock_client.get_database.side_effect = [
            _db_response(partial_backlog),
            _db_response(FULL_DECISIONS_PROPS),
            _db_response(FULL_BRIEFS_PROPS),
        ]
        mock_client.update_database.return_value = {}

        service = NotionUpgradeService(mock_client, healthy_config)
        report = service.upgrade()

        fixed = [f for f in report.findings if f.status == FindingStatus.FIXED]
        assert any("Notes" in f.description for f in fixed)
        assert any("Automation Trace" in f.description for f in fixed)
        mock_client.update_database.assert_called()


# -- Tests: missing select options --


class TestMissingSelectOptions:
    def test_inspect_detects_missing_options(self, mock_client, healthy_config, monkeypatch):
        monkeypatch.setenv("NOTION_API_KEY", "test-key")

        # Priority select missing "Low" option
        partial_backlog = dict(FULL_BACKLOG_PROPS)
        partial_backlog["Priority"] = {
            "type": "select",
            "select": {"options": [{"name": "High"}, {"name": "Medium"}]},
        }
        mock_client.get_page.return_value = {"id": "parent-abc"}
        mock_client.get_database.side_effect = [
            _db_response(partial_backlog),
            _db_response(FULL_DECISIONS_PROPS),
            _db_response(FULL_BRIEFS_PROPS),
        ]

        service = NotionUpgradeService(mock_client, healthy_config)
        report = service.inspect()

        manual = [f for f in report.findings if f.status == FindingStatus.MANUAL]
        assert any("Low" in f.description for f in manual)

    def test_upgrade_fixes_missing_options(self, mock_client, healthy_config, monkeypatch):
        monkeypatch.setenv("NOTION_API_KEY", "test-key")

        partial_backlog = dict(FULL_BACKLOG_PROPS)
        partial_backlog["Priority"] = {
            "type": "select",
            "select": {"options": [{"name": "High"}, {"name": "Medium"}]},
        }
        mock_client.get_page.return_value = {"id": "parent-abc"}
        mock_client.get_database.side_effect = [
            _db_response(partial_backlog),
            _db_response(FULL_DECISIONS_PROPS),
            _db_response(FULL_BRIEFS_PROPS),
        ]
        mock_client.update_database.return_value = {}

        service = NotionUpgradeService(mock_client, healthy_config)
        report = service.upgrade()

        fixed = [f for f in report.findings if f.status == FindingStatus.FIXED]
        assert any("Low" in f.description for f in fixed)


# -- Tests: missing config page IDs (auto-fix) --


class TestMissingPageIds:
    def test_inspect_detects_missing_readme_id(self, mock_client, monkeypatch):
        monkeypatch.setenv("NOTION_API_KEY", "test-key")

        config = StorageConfig(
            backend="notion",
            notion=NotionConfig(
                parent_page_id="parent-abc",
                databases={"backlog": "db-backlog", "decisions": "db-decisions"},
            ),
        )
        mock_client.get_page.return_value = {"id": "parent-abc"}
        mock_client.get_database.side_effect = [
            _db_response(FULL_BACKLOG_PROPS),
            _db_response(FULL_DECISIONS_PROPS),
            _db_response(FULL_BRIEFS_PROPS),
        ]
        # Parent has README page child
        mock_client.get_block_children.return_value = [
            {"type": "child_page", "child_page": {"title": "README"}, "id": "page-readme-found"},
        ]

        service = NotionUpgradeService(mock_client, config)
        report = service.inspect()

        manual = [f for f in report.findings if f.status == FindingStatus.MANUAL]
        assert any("README" in f.description for f in manual)

    def test_upgrade_restores_missing_readme_id(self, mock_client, monkeypatch):
        monkeypatch.setenv("NOTION_API_KEY", "test-key")

        config = StorageConfig(
            backend="notion",
            notion=NotionConfig(
                parent_page_id="parent-abc",
                databases={"backlog": "db-backlog", "decisions": "db-decisions"},
            ),
        )
        mock_client.get_page.return_value = {"id": "parent-abc"}
        mock_client.get_database.side_effect = [
            _db_response(FULL_BACKLOG_PROPS),
            _db_response(FULL_DECISIONS_PROPS),
            _db_response(FULL_BRIEFS_PROPS),
        ]
        mock_client.get_block_children.return_value = [
            {"type": "child_page", "child_page": {"title": "README"}, "id": "page-readme-found"},
            {"type": "child_page", "child_page": {"title": "Templates"}, "id": "page-tpl-found"},
        ]

        service = NotionUpgradeService(mock_client, config)
        report = service.upgrade()

        fixed = [f for f in report.findings if f.status == FindingStatus.FIXED]
        assert any("README" in f.description for f in fixed)
        assert config.notion.databases["readme"] == "page-readme-found"
        assert config.notion.databases["templates"] == "page-tpl-found"

    def test_upgrade_reports_unfound_pages(self, mock_client, monkeypatch):
        monkeypatch.setenv("NOTION_API_KEY", "test-key")

        config = StorageConfig(
            backend="notion",
            notion=NotionConfig(
                parent_page_id="parent-abc",
                databases={"backlog": "db-backlog", "decisions": "db-decisions"},
            ),
        )
        mock_client.get_page.return_value = {"id": "parent-abc"}
        mock_client.get_database.side_effect = [
            _db_response(FULL_BACKLOG_PROPS),
            _db_response(FULL_DECISIONS_PROPS),
            _db_response(FULL_BRIEFS_PROPS),
        ]
        mock_client.get_block_children.return_value = []  # No child pages

        service = NotionUpgradeService(mock_client, config)
        report = service.upgrade()

        manual = [f for f in report.findings if f.status == FindingStatus.MANUAL]
        assert any("README" in f.description for f in manual)
        assert any("Templates" in f.description for f in manual)


# -- Tests: token environment (report only) --


class TestTokenDiagnostics:
    def test_ok_with_notion_api_key(self, mock_client, healthy_config, monkeypatch):
        monkeypatch.setenv("NOTION_API_KEY", "test-key")
        monkeypatch.delenv("NOTION_API_TOKEN", raising=False)

        service = NotionUpgradeService(mock_client, healthy_config)
        report = UpgradeReport()
        service._check_token_env(report)

        assert report.findings[0].status == FindingStatus.OK

    def test_manual_with_legacy_token_only(self, mock_client, healthy_config, monkeypatch):
        monkeypatch.delenv("NOTION_API_KEY", raising=False)
        monkeypatch.setenv("NOTION_API_TOKEN", "legacy-key")

        service = NotionUpgradeService(mock_client, healthy_config)
        report = UpgradeReport()
        service._check_token_env(report)

        assert report.findings[0].status == FindingStatus.MANUAL
        assert "legacy" in report.findings[0].description.lower()

    def test_manual_with_no_token(self, mock_client, healthy_config, monkeypatch):
        monkeypatch.delenv("NOTION_API_KEY", raising=False)
        monkeypatch.delenv("NOTION_API_TOKEN", raising=False)

        service = NotionUpgradeService(mock_client, healthy_config)
        report = UpgradeReport()
        service._check_token_env(report)

        assert report.findings[0].status == FindingStatus.MANUAL
        assert "NOTION_API_KEY" in report.findings[0].description


# -- Tests: title property edge case --


class TestTitlePropertyHandling:
    def test_title_named_differently_is_ok(self, mock_client, healthy_config, monkeypatch):
        """Database has title property under 'Name' instead of 'Title'."""
        monkeypatch.setenv("NOTION_API_KEY", "test-key")

        # Backlog with title property named "Name" instead of "Title"
        props = dict(FULL_BACKLOG_PROPS)
        del props["Title"]
        props["Name"] = {"type": "title", "title": {}}

        mock_client.get_page.return_value = {"id": "parent-abc"}
        mock_client.get_database.side_effect = [
            _db_response(props),
            _db_response(FULL_DECISIONS_PROPS),
            _db_response(FULL_BRIEFS_PROPS),
        ]

        service = NotionUpgradeService(mock_client, healthy_config)
        report = service.inspect()

        # Should not flag missing "Title" since a title-type property exists
        title_issues = [
            f for f in report.findings
            if f.status != FindingStatus.OK and "Title" in f.description
        ]
        assert len(title_issues) == 0


# -- Tests: UpgradeReport --


class TestUpgradeReport:
    def test_exit_code_zero_when_all_ok(self):
        report = UpgradeReport()
        report.add("config", "test", FindingStatus.OK)
        assert report.exit_code == 0

    def test_exit_code_one_when_fixed(self):
        report = UpgradeReport()
        report.add("config", "test", FindingStatus.FIXED)
        assert report.exit_code == 1

    def test_exit_code_two_when_manual(self):
        report = UpgradeReport()
        report.add("config", "test", FindingStatus.MANUAL)
        assert report.exit_code == 2

    def test_to_dict_summary(self):
        report = UpgradeReport()
        report.add("a", "ok item", FindingStatus.OK)
        report.add("b", "fixed item", FindingStatus.FIXED)
        report.add("c", "manual item", FindingStatus.MANUAL)
        d = report.to_dict()
        assert d["summary"]["total"] == 3
        assert d["summary"]["ok"] == 1
        assert d["summary"]["fixed"] == 1
        assert d["summary"]["manual"] == 1


# -- Tests: config persistence boundary --


class TestConfigPersistenceBoundary:
    """Verify that NotionUpgradeService does NOT own config persistence.

    The service may modify config in-memory (e.g. restoring page IDs)
    but must not expose any method that writes config to disk.
    Callers (CLI / setup) own the save decision.
    """

    def test_service_has_no_save_method(self, mock_client, healthy_config, monkeypatch):
        """Service must not expose a save/persist/write config API."""
        monkeypatch.setenv("NOTION_API_KEY", "test-key")
        service = NotionUpgradeService(mock_client, healthy_config)
        assert not hasattr(service, "save_config_if_changed")
        assert not hasattr(service, "save_config")
        assert not hasattr(service, "persist_config")

    def test_upgrade_mutates_config_in_memory_only(self, mock_client, monkeypatch):
        """After upgrade restores page IDs, changes are in the config object
        — not persisted to disk. The caller decides whether to save."""
        monkeypatch.setenv("NOTION_API_KEY", "test-key")

        config = StorageConfig(
            backend="notion",
            notion=NotionConfig(
                parent_page_id="parent-abc",
                databases={"backlog": "db-backlog", "decisions": "db-decisions"},
            ),
        )
        mock_client.get_page.return_value = {"id": "parent-abc"}
        mock_client.get_database.side_effect = [
            _db_response(FULL_BACKLOG_PROPS),
            _db_response(FULL_DECISIONS_PROPS),
            _db_response(FULL_BRIEFS_PROPS),
        ]
        mock_client.get_block_children.return_value = [
            {"type": "child_page", "child_page": {"title": "README"}, "id": "page-readme-found"},
            {"type": "child_page", "child_page": {"title": "Templates"}, "id": "page-tpl-found"},
        ]

        service = NotionUpgradeService(mock_client, config)
        report = service.upgrade()

        # Config was mutated in-memory
        assert config.notion.databases["readme"] == "page-readme-found"
        assert config.notion.databases["templates"] == "page-tpl-found"

        # Report signals changes so the caller can decide to save
        fixed = [f for f in report.findings if f.status == FindingStatus.FIXED]
        page_fixes = [f for f in fixed if f.category.startswith("page:")]
        assert len(page_fixes) >= 1

    def test_caller_can_detect_config_changes_from_findings(self, mock_client, healthy_config, monkeypatch):
        """Callers determine whether to save config by inspecting findings,
        not by calling a service method."""
        monkeypatch.setenv("NOTION_API_KEY", "test-key")

        mock_client.get_page.return_value = {"id": "parent-abc"}
        mock_client.get_database.side_effect = [
            _db_response(FULL_BACKLOG_PROPS),
            _db_response(FULL_DECISIONS_PROPS),
            _db_response(FULL_BRIEFS_PROPS),
        ]

        service = NotionUpgradeService(mock_client, healthy_config)
        report = service.upgrade()

        # The caller-side pattern: check for page: FIXED findings
        config_changed = any(
            f.status == FindingStatus.FIXED and f.category.startswith("page:")
            for f in report.findings
        )
        # Healthy workspace → no config changes needed
        assert config_changed is False
