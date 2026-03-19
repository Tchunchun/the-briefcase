"""Unit tests for fix-cycle dispatch automation."""

from __future__ import annotations

from datetime import datetime, timezone

from src.core.automation.fix_cycle import FixCycleAutomationService


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
        return {"command": "fake-fix-cycle", "returncode": 0, "stdout": "ok"}


NOW = datetime(2026, 3, 19, 15, 0, tzinfo=timezone.utc)


def _feature(title="Fix Me", verdict="changes-requested", status="review-ready", notion_id="feat-1"):
    return {
        "title": title,
        "type": "Feature",
        "status": status,
        "review_verdict": verdict,
        "notes": "",
        "brief_link": "",
        "parent_ids": [],
        "notion_id": notion_id,
    }


def _brief(name="fix-me", title="Fix Me", notion_id="b1"):
    return {"name": name, "title": title, "notion_id": notion_id}


def test_dispatches_changes_requested_feature():
    dispatcher = FakeDispatcher()
    store = FakeStore(rows=[_feature()], briefs=[_brief()])
    result = FixCycleAutomationService(store, dispatcher=dispatcher).scan(now=NOW)
    assert result["dispatched_count"] == 1
    assert result["dispatches"][0]["brief_name"] == "fix-me"
    assert "[auto-fix-cycle]" in store.writes[0]["automation_trace"]
    assert len(dispatcher.calls) == 1


def test_skips_accepted_verdict():
    store = FakeStore(rows=[_feature(verdict="accepted")], briefs=[_brief()])
    result = FixCycleAutomationService(store).scan(now=NOW)
    assert result["dispatched_count"] == 0
    assert result["blocked_count"] == 1
    assert "changes-requested" in result["blocked"][0]["reason"]


def test_skips_pending_verdict():
    store = FakeStore(rows=[_feature(verdict="pending")], briefs=[_brief()])
    result = FixCycleAutomationService(store).scan(now=NOW)
    assert result["dispatched_count"] == 0
    assert result["blocked_count"] == 1


def test_skips_empty_verdict():
    store = FakeStore(rows=[_feature(verdict="")], briefs=[_brief()])
    result = FixCycleAutomationService(store).scan(now=NOW)
    assert result["dispatched_count"] == 0
    assert result["blocked_count"] == 1


def test_blocks_when_no_brief_found():
    store = FakeStore(rows=[_feature()], briefs=[])
    result = FixCycleAutomationService(store).scan(now=NOW)
    assert result["dispatched_count"] == 0
    assert result["blocked_count"] == 1
    assert "No matching brief" in result["blocked"][0]["reason"]


def test_skips_non_review_ready_status():
    store = FakeStore(rows=[_feature(status="in-progress", verdict="changes-requested")], briefs=[_brief()])
    result = FixCycleAutomationService(store).scan(now=NOW)
    assert result["dispatched_count"] == 0
    assert result["blocked_count"] == 0


def test_idempotent_second_run():
    dispatcher = FakeDispatcher()
    store = FakeStore(rows=[_feature()], briefs=[_brief()])
    service = FixCycleAutomationService(store, dispatcher=dispatcher)
    first = service.scan(now=NOW)
    assert first["dispatched_count"] == 1

    second = service.scan(now=datetime(2026, 3, 19, 15, 5, tzinfo=timezone.utc))
    assert second["dispatched_count"] == 0
    assert len(dispatcher.calls) == 1


def test_dispatch_payload_has_required_fields():
    dispatcher = FakeDispatcher()
    store = FakeStore(rows=[_feature()], briefs=[_brief()])
    result = FixCycleAutomationService(store, dispatcher=dispatcher).scan(now=NOW)
    dispatch = result["dispatches"][0]
    for field in ("feature_title", "feature_id", "brief_name", "dispatch_token", "detected_at", "command_hint"):
        assert field in dispatch, f"Missing field: {field}"
    assert dispatch["brief_name"] == "fix-me"
    assert dispatch["command_hint"] == "agent brief read fix-me"


def test_multiple_features_only_dispatches_changes_requested():
    dispatcher = FakeDispatcher()
    store = FakeStore(
        rows=[
            _feature("Alpha", verdict="changes-requested", notion_id="f1"),
            _feature("Beta", verdict="accepted", notion_id="f2"),
            _feature("Gamma", verdict="pending", notion_id="f3"),
            _feature("Delta", verdict="changes-requested", notion_id="f4"),
        ],
        briefs=[
            _brief("alpha", "Alpha", "b1"),
            _brief("beta", "Beta", "b2"),
            _brief("gamma", "Gamma", "b3"),
            _brief("delta", "Delta", "b4"),
        ],
    )
    result = FixCycleAutomationService(store, dispatcher=dispatcher).scan(now=NOW)
    assert result["dispatched_count"] == 2
    titles = {d["feature_title"] for d in result["dispatches"]}
    assert titles == {"Alpha", "Delta"}
    assert len(dispatcher.calls) == 2


def test_dry_run_does_not_write_trace():
    store = FakeStore(rows=[_feature()], briefs=[_brief()])
    result = FixCycleAutomationService(store).scan(apply=False, now=NOW)
    assert result["dry_run"] is True
    assert result["dispatched_count"] == 1
    assert store.writes == []


def test_notes_only_writes_trace_without_dispatching():
    """With dispatcher=None (notes-only mode), trace is written but no shell command runs."""
    store = FakeStore(rows=[_feature()], briefs=[_brief()])
    result = FixCycleAutomationService(store, dispatcher=None).scan(now=NOW)
    assert result["dispatched_count"] == 1
    assert store.writes
    assert "[auto-fix-cycle]" in store.writes[0]["automation_trace"]
