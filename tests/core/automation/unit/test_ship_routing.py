"""Unit tests for ship-routing automation."""

from __future__ import annotations

from datetime import datetime, timezone

from src.core.automation.ship_routing import ShipRoutingAutomationService


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
            if existing.get("title") == row.get("title") and existing.get("type") == row.get("type"):
                self.rows[idx] = dict(row)
                break


class FakeDispatcher:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def __call__(self, payload: dict) -> dict:
        self.calls.append(dict(payload))
        return {"command": "fake-ship", "returncode": 0, "stdout": "ok"}


def test_dispatches_review_accepted_feature():
    dispatcher = FakeDispatcher()
    store = FakeStore(
        rows=[{
            "title": "Login UI",
            "type": "Feature",
            "status": "review-accepted",
            "review_verdict": "accepted",
            "notes": "",
            "brief_link": "",
            "parent_ids": [],
            "notion_id": "feat-1",
        }],
        briefs=[{"name": "login-ui", "title": "Login UI", "notion_id": "b1"}],
    )
    result = ShipRoutingAutomationService(store, dispatcher=dispatcher).scan(
        now=datetime(2026, 3, 19, 15, 0, tzinfo=timezone.utc)
    )
    assert result["dispatched_count"] == 1
    assert result["dispatches"][0]["brief_name"] == "login-ui"
    assert "[auto-ship-routing]" in store.writes[0]["automation_trace"]


def test_blocks_when_verdict_not_accepted():
    store = FakeStore(
        rows=[{
            "title": "Login UI",
            "type": "Feature",
            "status": "review-accepted",
            "review_verdict": "changes-requested",
            "notes": "",
            "brief_link": "",
            "parent_ids": [],
            "notion_id": "feat-1",
        }],
        briefs=[{"name": "login-ui", "title": "Login UI", "notion_id": "b1"}],
    )
    result = ShipRoutingAutomationService(store).scan(
        now=datetime(2026, 3, 19, 15, 0, tzinfo=timezone.utc)
    )
    assert result["dispatched_count"] == 0
    assert result["blocked_count"] == 1
    assert "expected 'accepted'" in result["blocked"][0]["reason"]


def test_blocks_when_no_brief_found():
    store = FakeStore(
        rows=[{
            "title": "Unknown Feature",
            "type": "Feature",
            "status": "review-accepted",
            "review_verdict": "accepted",
            "notes": "",
            "brief_link": "",
            "parent_ids": [],
            "notion_id": "feat-2",
        }],
        briefs=[],
    )
    result = ShipRoutingAutomationService(store).scan(
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
            "status": "review-accepted",
            "review_verdict": "accepted",
            "notes": "",
            "brief_link": "",
            "parent_ids": [],
            "notion_id": "feat-1",
        }],
        briefs=[{"name": "login-ui", "title": "Login UI", "notion_id": "b1"}],
    )
    service = ShipRoutingAutomationService(store, dispatcher=dispatcher)
    first = service.scan(now=datetime(2026, 3, 19, 15, 0, tzinfo=timezone.utc))
    assert first["dispatched_count"] == 1

    second = service.scan(now=datetime(2026, 3, 19, 15, 5, tzinfo=timezone.utc))
    assert second["dispatched_count"] == 0


def test_skips_non_review_accepted():
    store = FakeStore(
        rows=[{
            "title": "In Progress Feature",
            "type": "Feature",
            "status": "in-progress",
            "review_verdict": "",
            "notes": "",
            "brief_link": "",
            "parent_ids": [],
            "notion_id": "feat-3",
        }],
        briefs=[],
    )
    result = ShipRoutingAutomationService(store).scan(
        now=datetime(2026, 3, 19, 15, 0, tzinfo=timezone.utc)
    )
    assert result["dispatched_count"] == 0
    assert result["blocked_count"] == 0
