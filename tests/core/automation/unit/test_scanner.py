"""Unit tests for the shared StatusEntryScanner."""

from __future__ import annotations

from datetime import datetime, timezone

from src.core.automation.scanner import (
    StatusEntryScanner,
    _is_slug_prefix,
    resolve_brief_context,
)


class FakeStore:
    def __init__(self, rows: list[dict], briefs: list[dict]) -> None:
        self.rows = rows
        self.briefs = briefs
        self.writes: list[dict] = []

    def read_backlog(self) -> list[dict]:
        return [dict(row) for row in self.rows]

    def list_briefs(self) -> list[dict]:
        return list(self.briefs)

    def write_backlog_row(self, row: dict) -> None:
        self.writes.append(dict(row))
        for idx, existing in enumerate(self.rows):
            if (
                existing.get("title") == row.get("title")
                and existing.get("type") == row.get("type")
            ):
                self.rows[idx] = dict(row)
                break


class FakeDispatcher:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def __call__(self, payload: dict) -> dict:
        self.calls.append(dict(payload))
        return {"command": "fake", "returncode": 0, "stdout": "ok"}


def _make_scanner(store, *, dispatcher=None, gating_check=None):
    return StatusEntryScanner(
        store,
        target_status="test-status",
        marker_prefix="[auto-test]",
        token_prefix="test",
        log_label="Test automation",
        dispatcher=dispatcher,
        gating_check=gating_check,
    )


def test_scanner_dispatches_on_new_entry():
    dispatcher = FakeDispatcher()
    store = FakeStore(
        rows=[{
            "title": "My Feature",
            "type": "Feature",
            "status": "test-status",
            "notes": "",
            "brief_link": "",
            "parent_ids": [],
            "notion_id": "f1",
            "notion_url": "https://notion.so/f1",
        }],
        briefs=[{"name": "my-feature", "title": "My Feature", "notion_id": "b1"}],
    )
    result = _make_scanner(store, dispatcher=dispatcher).scan(
        now=datetime(2026, 3, 19, 12, 0, tzinfo=timezone.utc)
    )
    assert result["dispatched_count"] == 1
    assert result["dispatches"][0]["brief_name"] == "my-feature"
    assert result["dispatches"][0]["brief_name_resolved"] is True
    assert dispatcher.calls


def test_scanner_skips_already_dispatched():
    store = FakeStore(
        rows=[{
            "title": "My Feature",
            "type": "Feature",
            "status": "test-status",
            "notes": "",
            "automation_trace": (
                "Test automation dispatched test-f1-20260319T120000Z "
                "at 2026-03-19T12:00:00Z for brief my-feature. // "
                "[auto-test] last_status=test-status "
                "active_entry_token=test-f1-20260319T120000Z "
                "dispatched_token=test-f1-20260319T120000Z "
                "dispatched_at=2026-03-19T12:00:00Z"
            ),
            "brief_link": "",
            "parent_ids": [],
            "notion_id": "f1",
        }],
        briefs=[],
    )
    result = _make_scanner(store, dispatcher=FakeDispatcher()).scan(
        now=datetime(2026, 3, 19, 12, 5, tzinfo=timezone.utc)
    )
    assert result["dispatched_count"] == 0


def test_scanner_notes_only_writes_without_dispatcher():
    store = FakeStore(
        rows=[{
            "title": "Notes Feature",
            "type": "Feature",
            "status": "test-status",
            "notes": "",
            "brief_link": "",
            "parent_ids": [],
            "notion_id": "f2",
        }],
        briefs=[{"name": "notes-feature", "title": "Notes Feature", "notion_id": "b2"}],
    )
    result = _make_scanner(store).scan(
        now=datetime(2026, 3, 19, 12, 0, tzinfo=timezone.utc)
    )
    assert result["dispatched_count"] == 1
    assert result["dry_run"] is False
    assert "dispatch_result" not in result["dispatches"][0]
    assert store.writes
    assert "[auto-test]" in store.writes[0]["automation_trace"]


def test_scanner_gating_check_blocks_dispatch():
    def gate(row, briefs):
        return {"reason": "missing prerequisite"}

    store = FakeStore(
        rows=[{
            "title": "Blocked Feature",
            "type": "Feature",
            "status": "test-status",
            "notes": "",
            "brief_link": "",
            "parent_ids": [],
            "notion_id": "f3",
        }],
        briefs=[],
    )
    result = _make_scanner(store, gating_check=gate).scan(
        now=datetime(2026, 3, 19, 12, 0, tzinfo=timezone.utc)
    )
    assert result["dispatched_count"] == 0
    assert result["blocked_count"] == 1
    assert result["blocked"][0]["reason"] == "missing prerequisite"
    assert store.rows[0]["route_state"] == "blocked"


def test_scanner_reentry_dispatches_again():
    store = FakeStore(
        rows=[{
            "title": "Re-entry Feature",
            "type": "Feature",
            "status": "other-status",
            "notes": "",
            "automation_trace": (
                "Test automation dispatched test-f4-20260319T120000Z "
                "at 2026-03-19T12:00:00Z for brief re-entry-feature. // "
                "[auto-test] last_status=test-status "
                "active_entry_token=test-f4-20260319T120000Z "
                "dispatched_token=test-f4-20260319T120000Z "
                "dispatched_at=2026-03-19T12:00:00Z"
            ),
            "brief_link": "",
            "parent_ids": [],
            "notion_id": "f4",
        }],
        briefs=[{"name": "re-entry-feature", "title": "Re-entry Feature", "notion_id": "b4"}],
    )
    scanner = _make_scanner(store, dispatcher=FakeDispatcher())

    # First scan: status is "other-status", clears marker
    first = scanner.scan(now=datetime(2026, 3, 19, 12, 10, tzinfo=timezone.utc))
    assert first["dispatched_count"] == 0

    # Re-enter target status
    store.rows[0]["status"] = "test-status"
    second = scanner.scan(now=datetime(2026, 3, 19, 12, 15, tzinfo=timezone.utc))
    assert second["dispatched_count"] == 1
    assert second["dispatches"][0]["dispatch_token"].endswith("20260319T121500Z")


def test_scanner_preserves_status_changes_made_during_dispatch():
    class StatusChangingDispatcher(FakeDispatcher):
        def __init__(self, store: FakeStore) -> None:
            super().__init__()
            self._store = store

        def __call__(self, payload: dict) -> dict:
            feature = self._store.rows[0]
            feature["status"] = "review-ready"
            return super().__call__(payload)

    store = FakeStore(
        rows=[{
            "title": "Mutable Feature",
            "type": "Feature",
            "status": "test-status",
            "notes": "",
            "brief_link": "",
            "parent_ids": [],
            "notion_id": "f5",
        }],
        briefs=[{"name": "mutable-feature", "title": "Mutable Feature", "notion_id": "b5"}],
    )

    result = _make_scanner(
        store, dispatcher=StatusChangingDispatcher(store),
    ).scan(now=datetime(2026, 3, 19, 12, 0, tzinfo=timezone.utc))

    assert result["dispatched_count"] == 1
    assert store.rows[0]["status"] == "review-ready"
    assert "[auto-test]" in store.rows[0]["automation_trace"]


# -- resolve_brief_context tests --


def test_resolve_brief_context_exact_match():
    row = {"title": "Lazy Import Notion", "brief_link": ""}
    briefs = [{"name": "lazy-import-notion", "title": "Lazy Import Notion", "notion_id": "b1"}]
    ctx = resolve_brief_context(row, briefs)
    assert ctx["brief_name_resolved"] is True
    assert ctx["brief_name"] == "lazy-import-notion"


def test_resolve_brief_context_prefix_match_brief_shorter():
    """Feature 'Lazy-import Notion modules' should match brief 'lazy-import-notion'."""
    row = {"title": "Lazy-import Notion modules", "brief_link": ""}
    briefs = [{"name": "lazy-import-notion", "title": "Lazy Import Notion", "notion_id": "b1"}]
    ctx = resolve_brief_context(row, briefs)
    assert ctx["brief_name_resolved"] is True
    assert ctx["brief_name"] == "lazy-import-notion"


def test_resolve_brief_context_prefix_match_selects_longest():
    """When multiple briefs match as prefix, the longest (most specific) wins."""
    row = {"title": "Lazy-import Notion modules v2", "brief_link": ""}
    briefs = [
        {"name": "lazy-import", "title": "Lazy Import", "notion_id": "b0"},
        {"name": "lazy-import-notion-modules", "title": "Lazy Import Notion Modules", "notion_id": "b2"},
        {"name": "lazy-import-notion", "title": "Lazy Import Notion", "notion_id": "b1"},
    ]
    ctx = resolve_brief_context(row, briefs)
    assert ctx["brief_name_resolved"] is True
    assert ctx["brief_name"] == "lazy-import-notion-modules"


def test_resolve_brief_context_no_match():
    row = {"title": "Completely Different Feature", "brief_link": ""}
    briefs = [{"name": "lazy-import-notion", "title": "Lazy Import Notion", "notion_id": "b1"}]
    ctx = resolve_brief_context(row, briefs)
    assert ctx["brief_name_resolved"] is False


def test_resolve_brief_context_notion_id_match():
    row = {"title": "Wrong Title", "brief_link": "https://notion.so/abc12345678901234567890123456789"}
    briefs = [{"name": "my-brief", "title": "My Brief", "notion_id": "abc12345-6789-0123-4567-890123456789"}]
    ctx = resolve_brief_context(row, briefs)
    assert ctx["brief_name_resolved"] is True
    assert ctx["brief_name"] == "my-brief"


# -- _is_slug_prefix tests --


def test_is_slug_prefix_true():
    assert _is_slug_prefix("lazy-import-notion", "lazy-import-notion-modules") is True


def test_is_slug_prefix_exact():
    assert _is_slug_prefix("lazy-import-notion", "lazy-import-notion") is True


def test_is_slug_prefix_false_partial_segment():
    """Prefix must align on hyphen boundaries, not mid-word."""
    assert _is_slug_prefix("lazy-import-not", "lazy-import-notion") is False


def test_is_slug_prefix_empty():
    assert _is_slug_prefix("", "lazy-import-notion") is False
    assert _is_slug_prefix("lazy-import-notion", "") is False
