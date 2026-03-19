"""Unit tests for review-ready automation."""

from __future__ import annotations

from datetime import datetime, timezone

from src.core.automation.review_ready import ReviewReadyAutomationService


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
        return {"command": "fake-review", "returncode": 0, "stdout": "ok"}


def test_dispatches_review_ready_feature():
    dispatcher = FakeDispatcher()
    store = FakeStore(
        rows=[{
            "title": "Login UI",
            "type": "Feature",
            "status": "review-ready",
            "notes": "",
            "brief_link": "",
            "parent_ids": [],
            "notion_id": "feat-1",
        }],
        briefs=[{"name": "login-ui", "title": "Login UI", "notion_id": "b1"}],
    )
    result = ReviewReadyAutomationService(store, dispatcher=dispatcher).scan(
        now=datetime(2026, 3, 19, 15, 0, tzinfo=timezone.utc)
    )
    assert result["dispatched_count"] == 1
    assert result["dispatches"][0]["brief_name"] == "login-ui"
    assert "[auto-review-ready]" in store.writes[0]["automation_trace"]


def test_blocks_when_no_brief_found():
    store = FakeStore(
        rows=[{
            "title": "Unknown Feature",
            "type": "Feature",
            "status": "review-ready",
            "notes": "",
            "brief_link": "",
            "parent_ids": [],
            "notion_id": "feat-2",
        }],
        briefs=[],
    )
    result = ReviewReadyAutomationService(store).scan(
        now=datetime(2026, 3, 19, 15, 0, tzinfo=timezone.utc)
    )
    assert result["dispatched_count"] == 0
    assert result["blocked_count"] == 1
    assert "No matching brief" in result["blocked"][0]["reason"]


def test_idempotent_second_run():
    dispatcher = FakeDispatcher()
    store = FakeStore(
        rows=[{
            "title": "Login UI",
            "type": "Feature",
            "status": "review-ready",
            "notes": "",
            "brief_link": "",
            "parent_ids": [],
            "notion_id": "feat-1",
        }],
        briefs=[{"name": "login-ui", "title": "Login UI", "notion_id": "b1"}],
    )
    service = ReviewReadyAutomationService(store, dispatcher=dispatcher)
    first = service.scan(now=datetime(2026, 3, 19, 15, 0, tzinfo=timezone.utc))
    assert first["dispatched_count"] == 1

    second = service.scan(now=datetime(2026, 3, 19, 15, 5, tzinfo=timezone.utc))
    assert second["dispatched_count"] == 0


def test_blocks_when_child_tasks_are_incomplete():
    store = FakeStore(
        rows=[
            {
                "title": "Login UI",
                "type": "Feature",
                "status": "review-ready",
                "notes": "",
                "brief_link": "",
                "parent_ids": [],
                "notion_id": "feat-1",
            },
            {
                "title": "Build form",
                "type": "Task",
                "status": "done",
                "feature": "login-ui",
                "parent_ids": ["feat-1"],
            },
            {
                "title": "Wire submit",
                "type": "Task",
                "status": "in-progress",
                "feature": "login-ui",
                "parent_ids": ["feat-1"],
            },
        ],
        briefs=[{"name": "login-ui", "title": "Login UI", "notion_id": "b1"}],
    )

    result = ReviewReadyAutomationService(store).scan(
        now=datetime(2026, 3, 19, 15, 0, tzinfo=timezone.utc)
    )

    assert result["dispatched_count"] == 0
    assert result["blocked_count"] == 1
    assert "incomplete tasks" in result["blocked"][0]["reason"]
    assert "Wire submit" in result["blocked"][0]["reason"]


def test_skips_non_review_ready():
    store = FakeStore(
        rows=[{
            "title": "In Progress Feature",
            "type": "Feature",
            "status": "in-progress",
            "notes": "",
            "brief_link": "",
            "parent_ids": [],
            "notion_id": "feat-3",
        }],
        briefs=[],
    )
    result = ReviewReadyAutomationService(store).scan(
        now=datetime(2026, 3, 19, 15, 0, tzinfo=timezone.utc)
    )
    assert result["dispatched_count"] == 0
    assert result["blocked_count"] == 0
