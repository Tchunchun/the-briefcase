"""Unit tests for ship-dispatch automation."""

from __future__ import annotations

from datetime import datetime, timezone

from src.core.automation.ship_dispatch import ShipDispatchAutomationService


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


NOW = datetime(2026, 3, 19, 15, 0, tzinfo=timezone.utc)


def _accepted_feature(title="Login UI", notion_id="feat-1"):
    return {
        "title": title,
        "type": "Feature",
        "status": "review-accepted",
        "review_verdict": "accepted",
        "notes": "",
        "brief_link": "",
        "parent_ids": [],
        "notion_id": notion_id,
    }


def _brief(name="login-ui"):
    return {"name": name, "title": "Login UI", "notion_id": "b1"}


def test_dispatches_review_accepted_feature():
    dispatcher = FakeDispatcher()
    store = FakeStore(rows=[_accepted_feature()], briefs=[_brief()])
    result = ShipDispatchAutomationService(store, dispatcher=dispatcher).scan(now=NOW)

    assert result["dispatched_count"] == 1
    assert result["dispatches"][0]["brief_name"] == "login-ui"
    assert "[auto-ship-dispatch]" in store.writes[-1].get("automation_trace", "")


def test_blocks_when_verdict_not_accepted():
    store = FakeStore(
        rows=[{**_accepted_feature(), "review_verdict": "changes-requested"}],
        briefs=[_brief()],
    )
    result = ShipDispatchAutomationService(store).scan(now=NOW)
    assert result["dispatched_count"] == 0
    assert result["blocked_count"] == 1
    assert "expected 'accepted'" in result["blocked"][0]["reason"]


def test_blocks_when_no_brief_found():
    store = FakeStore(
        rows=[_accepted_feature(title="Unknown Feature", notion_id="feat-2")],
        briefs=[],
    )
    result = ShipDispatchAutomationService(store).scan(now=NOW)
    assert result["dispatched_count"] == 0
    assert result["blocked_count"] == 1
    assert "No matching brief" in result["blocked"][0]["reason"]


def test_idempotent_second_run():
    dispatcher = FakeDispatcher()
    store = FakeStore(rows=[_accepted_feature()], briefs=[_brief()])
    svc = ShipDispatchAutomationService(store, dispatcher=dispatcher)

    first = svc.scan(now=NOW)
    assert first["dispatched_count"] == 1

    second = svc.scan(now=datetime(2026, 3, 19, 15, 5, tzinfo=timezone.utc))
    assert second["dispatched_count"] == 0


def test_skips_non_review_accepted():
    store = FakeStore(
        rows=[{**_accepted_feature(), "status": "in-progress", "review_verdict": ""}],
        briefs=[_brief()],
    )
    result = ShipDispatchAutomationService(store).scan(now=NOW)
    assert result["dispatched_count"] == 0


def test_marker_is_auto_ship_dispatch():
    """Ship-dispatch marker must be [auto-ship-dispatch], not [auto-ship-routing]."""
    dispatcher = FakeDispatcher()
    store = FakeStore(rows=[_accepted_feature()], briefs=[_brief()])
    ShipDispatchAutomationService(store, dispatcher=dispatcher).scan(now=NOW)

    trace = store.writes[-1].get("automation_trace", "")
    assert "[auto-ship-dispatch]" in trace
    assert "[auto-ship-routing]" not in trace
