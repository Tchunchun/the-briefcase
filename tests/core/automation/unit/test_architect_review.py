"""Unit tests for architect-review automation."""

from __future__ import annotations

from datetime import datetime, timezone

from src.core.automation.architect_review import ArchitectReviewAutomationService


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
        return {"command": "fake-architect", "returncode": 0, "stdout": "ok"}


def test_dispatches_new_architect_review_entry_and_writes_trace():
    dispatcher = FakeDispatcher()
    store = FakeStore(
        rows=[
            {
                "title": "Architect-review Automation",
                "type": "Feature",
                "status": "architect-review",
                "priority": "High",
                "notes": "",
                "brief_link": "https://www.notion.so/Architect-review-Automation-326b5a09fa4a816e81fcec4b318ef27e",
                "parent_ids": ["idea-1"],
                "notion_id": "feature-1",
                "notion_url": "https://www.notion.so/feature-1",
            }
        ],
        briefs=[
            {
                "name": "architect-review-automation",
                "title": "Architect-review Automation",
                "status": "draft",
                "notion_id": "326b5a09-fa4a-816e-81fc-ec4b318ef27e",
            }
        ],
    )

    result = ArchitectReviewAutomationService(store, dispatcher=dispatcher).scan(
        now=datetime(2026, 3, 17, 19, 0, tzinfo=timezone.utc)
    )

    assert result["dispatched_count"] == 1
    dispatch = result["dispatches"][0]
    assert dispatch["brief_name"] == "architect-review-automation"
    assert dispatch["command_hint"] == "agent brief read architect-review-automation"
    assert dispatcher.calls[0]["brief_name"] == "architect-review-automation"
    assert dispatch["dispatch_result"]["returncode"] == 0
    assert store.writes
    assert "Architect-review automation dispatched" in store.writes[0]["automation_trace"]
    assert "[auto-architect-review]" in store.writes[0]["automation_trace"]


def test_skips_unchanged_architect_review_entry_with_same_dispatch_token():
    store = FakeStore(
        rows=[
            {
                "title": "Architect-review Automation",
                "type": "Feature",
                "status": "architect-review",
                "priority": "High",
                "notes": "",
                "automation_trace": (
                    "Architect-review automation dispatched archrev-feature-1-20260317T190000Z "
                    "at 2026-03-17T19:00:00Z for brief architect-review-automation. // "
                    "[auto-architect-review] last_status=architect-review "
                    "active_entry_token=archrev-feature-1-20260317T190000Z "
                    "dispatched_token=archrev-feature-1-20260317T190000Z "
                    "dispatched_at=2026-03-17T19:00:00Z"
                ),
                "brief_link": "",
                "parent_ids": [],
                "notion_id": "feature-1",
            }
        ],
        briefs=[],
    )

    result = ArchitectReviewAutomationService(store, dispatcher=FakeDispatcher()).scan(
        now=datetime(2026, 3, 17, 19, 5, tzinfo=timezone.utc)
    )

    assert result["dispatched_count"] == 0
    assert store.writes == []


def test_reentry_dispatches_again_after_leaving_architect_review():
    store = FakeStore(
        rows=[
            {
                "title": "Architect-review Automation",
                "type": "Feature",
                "status": "in-progress",
                "priority": "High",
                "notes": "",
                "automation_trace": (
                    "Architect-review automation dispatched archrev-feature-1-20260317T190000Z "
                    "at 2026-03-17T19:00:00Z for brief architect-review-automation. // "
                    "[auto-architect-review] last_status=architect-review "
                    "active_entry_token=archrev-feature-1-20260317T190000Z "
                    "dispatched_token=archrev-feature-1-20260317T190000Z "
                    "dispatched_at=2026-03-17T19:00:00Z"
                ),
                "brief_link": "",
                "parent_ids": [],
                "notion_id": "feature-1",
            }
        ],
        briefs=[
            {
                "name": "architect-review-automation",
                "title": "Architect-review Automation",
                "status": "draft",
                "notion_id": "brief-1",
            }
        ],
    )
    dispatcher = FakeDispatcher()
    service = ArchitectReviewAutomationService(store, dispatcher=dispatcher)

    first = service.scan(
        apply=False,
        now=datetime(2026, 3, 17, 19, 10, tzinfo=timezone.utc),
    )
    assert first["dispatched_count"] == 0
    store.rows[0]["automation_trace"] = (
        "Architect-review automation dispatched archrev-feature-1-20260317T190000Z "
        "at 2026-03-17T19:00:00Z for brief architect-review-automation. // "
        "[auto-architect-review] last_status=in-progress "
        "active_entry_token=- dispatched_token=- dispatched_at=-"
    )

    store.rows[0]["status"] = "architect-review"
    second = service.scan(now=datetime(2026, 3, 17, 19, 15, tzinfo=timezone.utc))

    assert second["dispatched_count"] == 1
    assert second["dispatches"][0]["dispatch_token"].endswith("20260317T191500Z")
    assert dispatcher.calls


def test_notes_only_writes_trace_without_dispatcher():
    """Live mode without dispatcher writes trace notes and returns payloads."""
    store = FakeStore(
        rows=[
            {
                "title": "Notes Only Feature",
                "type": "Feature",
                "status": "architect-review",
                "priority": "High",
                "notes": "",
                "brief_link": "",
                "parent_ids": [],
                "notion_id": "feature-notes",
            }
        ],
        briefs=[
            {
                "name": "notes-only-feature",
                "title": "Notes Only Feature",
                "status": "draft",
                "notion_id": "b1",
            }
        ],
    )

    result = ArchitectReviewAutomationService(store).scan(
        now=datetime(2026, 3, 19, 12, 0, tzinfo=timezone.utc)
    )

    assert result["dispatched_count"] == 1
    assert result["dry_run"] is False
    assert "dispatch_result" not in result["dispatches"][0]
    assert result["dispatches"][0]["brief_name"] == "notes-only-feature"
    assert result["dispatches"][0]["command_hint"] == "agent brief read notes-only-feature"
    assert store.writes
    assert "Architect-review automation dispatched" in store.writes[0]["automation_trace"]
    assert "[auto-architect-review]" in store.writes[0]["automation_trace"]


def test_dispatch_failure_propagates_error():
    def failing_dispatcher(payload: dict) -> dict:
        raise RuntimeError("Architect dispatch failed (1): connection refused")

    store = FakeStore(
        rows=[
            {
                "title": "Failing Feature",
                "type": "Feature",
                "status": "architect-review",
                "priority": "High",
                "notes": "",
                "brief_link": "",
                "parent_ids": [],
                "notion_id": "feature-fail",
            }
        ],
        briefs=[
            {
                "name": "failing-feature",
                "title": "Failing Feature",
                "status": "draft",
                "notion_id": "brief-fail",
            }
        ],
    )

    try:
        ArchitectReviewAutomationService(store, dispatcher=failing_dispatcher).scan(
            now=datetime(2026, 3, 18, 10, 0, tzinfo=timezone.utc)
        )
    except RuntimeError as exc:
        assert "connection refused" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError from failing dispatcher")

    assert store.writes == []


def test_brief_name_resolved_flag_when_brief_found():
    dispatcher = FakeDispatcher()
    store = FakeStore(
        rows=[
            {
                "title": "Known Feature",
                "type": "Feature",
                "status": "architect-review",
                "priority": "High",
                "notes": "",
                "brief_link": "",
                "parent_ids": [],
                "notion_id": "feature-known",
            }
        ],
        briefs=[
            {
                "name": "known-feature",
                "title": "Known Feature",
                "status": "draft",
                "notion_id": "b1",
            }
        ],
    )

    result = ArchitectReviewAutomationService(store, dispatcher=dispatcher).scan(
        now=datetime(2026, 3, 18, 10, 0, tzinfo=timezone.utc)
    )
    assert result["dispatches"][0]["brief_name_resolved"] is True


def test_brief_name_resolved_flag_when_brief_not_found():
    store = FakeStore(
        rows=[
            {
                "title": "Unknown Feature",
                "type": "Feature",
                "status": "architect-review",
                "priority": "High",
                "notes": "",
                "brief_link": "",
                "parent_ids": [],
                "notion_id": "feature-unknown",
            }
        ],
        briefs=[],
    )

    result = ArchitectReviewAutomationService(store).scan(
        now=datetime(2026, 3, 18, 10, 0, tzinfo=timezone.utc)
    )
    assert result["dispatched_count"] == 0
    assert result["blocked_count"] == 1
    assert "No matching brief" in result["blocked"][0]["reason"]


def test_blocks_when_brief_is_not_draft():
    store = FakeStore(
        rows=[
            {
                "title": "Known Feature",
                "type": "Feature",
                "status": "architect-review",
                "priority": "High",
                "notes": "",
                "brief_link": "",
                "parent_ids": [],
                "notion_id": "feature-known",
            }
        ],
        briefs=[
            {
                "name": "known-feature",
                "title": "Known Feature",
                "status": "implementation-ready",
                "notion_id": "b1",
            }
        ],
    )

    result = ArchitectReviewAutomationService(store).scan(
        now=datetime(2026, 3, 18, 10, 0, tzinfo=timezone.utc)
    )

    assert result["dispatched_count"] == 0
    assert result["blocked_count"] == 1
    assert "expected brief status 'draft'" in result["blocked"][0]["reason"]
