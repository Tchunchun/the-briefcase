"""Unit tests for implementation-ready automation."""

from __future__ import annotations

from datetime import datetime, timezone

from src.core.automation.implementation_ready import ImplementationReadyAutomationService


class FakeStore:
    def __init__(self, rows: list[dict], briefs: list[dict]) -> None:
        self.rows = rows
        self.briefs = briefs
        self.writes: list[dict] = []

    def read_backlog(self) -> list[dict]:
        return [dict(row) for row in self.rows]

    def list_briefs(self) -> list[dict]:
        return list(self.briefs)

    def read_brief(self, brief_name: str) -> dict:
        for brief in self.briefs:
            if brief.get("name") == brief_name:
                return dict(brief)
        raise KeyError(brief_name)

    def write_backlog_row(self, row: dict) -> None:
        self.writes.append(dict(row))
        for idx, existing in enumerate(self.rows):
            if existing.get("title") == row.get("title") and existing.get("type") == row.get("type"):
                self.rows[idx] = dict(row)
                break


class FakeDispatcher:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def __call__(self, payload: dict) -> dict:
        self.calls.append(dict(payload))
        return {"command": "fake-impl", "returncode": 0, "stdout": "ok"}


def test_dispatches_implementation_ready_feature():
    dispatcher = FakeDispatcher()
    store = FakeStore(
        rows=[{
            "title": "Build Login UI",
            "type": "Feature",
            "status": "implementation-ready",
            "notes": "",
            "brief_link": "",
            "parent_ids": [],
            "notion_id": "feat-1",
        }],
        briefs=[{
            "name": "build-login-ui",
            "title": "Build Login UI",
            "status": "implementation-ready",
            "notion_id": "b1",
        }],
    )
    result = ImplementationReadyAutomationService(store, dispatcher=dispatcher).scan(
        now=datetime(2026, 3, 19, 14, 0, tzinfo=timezone.utc)
    )
    assert result["dispatched_count"] == 1
    assert result["dispatches"][0]["brief_name"] == "build-login-ui"
    assert "[auto-impl-ready]" in store.writes[0]["automation_trace"]


def test_blocks_when_no_brief_found():
    store = FakeStore(
        rows=[{
            "title": "Mystery Feature",
            "type": "Feature",
            "status": "implementation-ready",
            "notes": "",
            "brief_link": "",
            "parent_ids": [],
            "notion_id": "feat-2",
        }],
        briefs=[],  # no matching brief
    )
    result = ImplementationReadyAutomationService(store).scan(
        now=datetime(2026, 3, 19, 14, 0, tzinfo=timezone.utc)
    )
    assert result["dispatched_count"] == 0
    assert result["blocked_count"] == 1
    assert "No matching brief" in result["blocked"][0]["reason"]


def test_blocks_when_brief_status_is_not_implementation_ready():
    store = FakeStore(
        rows=[{
            "title": "Build Login UI",
            "type": "Feature",
            "status": "implementation-ready",
            "notes": "",
            "brief_link": "",
            "parent_ids": [],
            "notion_id": "feat-1",
        }],
        briefs=[{
            "name": "build-login-ui",
            "title": "Build Login UI",
            "status": "draft",
            "notion_id": "b1",
        }],
    )

    result = ImplementationReadyAutomationService(store).scan(
        now=datetime(2026, 3, 19, 14, 0, tzinfo=timezone.utc)
    )

    assert result["dispatched_count"] == 0
    assert result["blocked_count"] == 1
    assert "expected brief status 'implementation-ready'" in result["blocked"][0]["reason"]


def test_skips_non_implementation_ready():
    store = FakeStore(
        rows=[{
            "title": "Draft Feature",
            "type": "Feature",
            "status": "draft",
            "notes": "",
            "brief_link": "",
            "parent_ids": [],
            "notion_id": "feat-3",
        }],
        briefs=[],
    )
    result = ImplementationReadyAutomationService(store).scan(
        now=datetime(2026, 3, 19, 14, 0, tzinfo=timezone.utc)
    )
    assert result["dispatched_count"] == 0
    assert result["blocked_count"] == 0
