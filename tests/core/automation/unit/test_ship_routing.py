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

    def list_children(self, parent_id: str) -> list[dict]:
        return [
            dict(row)
            for row in self.rows
            if row.get("type", "").lower() == "feature"
            and parent_id in (row.get("parent_ids") or [])
        ]


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


# --- propagate_release_links tests ---


def test_propagate_release_link_to_parent_idea():
    store = FakeStore(
        rows=[
            {
                "title": "Parent Idea",
                "type": "Idea",
                "status": "exploring",
                "release_note_link": "",
                "parent_ids": [],
                "notion_id": "idea-1",
            },
            {
                "title": "Child Feature",
                "type": "Feature",
                "status": "done",
                "release_note_link": "https://notion.so/release-v1",
                "parent_ids": ["idea-1"],
                "notion_id": "feat-1",
            },
        ],
        briefs=[],
    )
    result = ShipRoutingAutomationService(store).propagate_release_links()
    assert result["propagated_count"] == 1
    assert result["propagated"][0]["idea_title"] == "Parent Idea"
    assert result["propagated"][0]["release_note_link"] == "https://notion.so/release-v1"
    # Verify the Idea row was updated in the store
    assert any(
        w.get("title") == "Parent Idea" and w.get("release_note_link") == "https://notion.so/release-v1"
        for w in store.writes
    )


def test_propagate_skips_idea_with_existing_link():
    store = FakeStore(
        rows=[
            {
                "title": "Parent Idea",
                "type": "Idea",
                "status": "shipped",
                "release_note_link": "https://notion.so/old-link",
                "parent_ids": [],
                "notion_id": "idea-1",
            },
            {
                "title": "Child Feature",
                "type": "Feature",
                "status": "done",
                "release_note_link": "https://notion.so/release-v2",
                "parent_ids": ["idea-1"],
                "notion_id": "feat-1",
            },
        ],
        briefs=[],
    )
    result = ShipRoutingAutomationService(store).propagate_release_links()
    assert result["propagated_count"] == 0
    assert result["skipped_count"] == 1
    assert len(store.writes) == 0


def test_propagate_skips_feature_without_release_link():
    store = FakeStore(
        rows=[
            {
                "title": "Parent Idea",
                "type": "Idea",
                "status": "exploring",
                "release_note_link": "",
                "parent_ids": [],
                "notion_id": "idea-1",
            },
            {
                "title": "Child Feature",
                "type": "Feature",
                "status": "done",
                "release_note_link": "",
                "parent_ids": ["idea-1"],
                "notion_id": "feat-1",
            },
        ],
        briefs=[],
    )
    result = ShipRoutingAutomationService(store).propagate_release_links()
    assert result["propagated_count"] == 0
    assert result["skipped_count"] == 0


def test_propagate_skips_non_done_features():
    store = FakeStore(
        rows=[
            {
                "title": "Parent Idea",
                "type": "Idea",
                "status": "exploring",
                "release_note_link": "",
                "parent_ids": [],
                "notion_id": "idea-1",
            },
            {
                "title": "Child Feature",
                "type": "Feature",
                "status": "in-progress",
                "release_note_link": "https://notion.so/release-v1",
                "parent_ids": ["idea-1"],
                "notion_id": "feat-1",
            },
        ],
        briefs=[],
    )
    result = ShipRoutingAutomationService(store).propagate_release_links()
    assert result["propagated_count"] == 0


def test_propagate_multiple_features_last_wins():
    """When multiple done Features share a parent Idea, the last one wins."""
    store = FakeStore(
        rows=[
            {
                "title": "Parent Idea",
                "type": "Idea",
                "status": "exploring",
                "release_note_link": "",
                "parent_ids": [],
                "notion_id": "idea-1",
            },
            {
                "title": "Feature Phase 1",
                "type": "Feature",
                "status": "done",
                "release_note_link": "https://notion.so/release-v1",
                "parent_ids": ["idea-1"],
                "notion_id": "feat-1",
            },
            {
                "title": "Feature Phase 2",
                "type": "Feature",
                "status": "done",
                "release_note_link": "https://notion.so/release-v2",
                "parent_ids": ["idea-1"],
                "notion_id": "feat-2",
            },
        ],
        briefs=[],
    )
    result = ShipRoutingAutomationService(store).propagate_release_links()
    # First feature propagates; second is skipped because idea already has link
    assert result["propagated_count"] == 1
    assert result["skipped_count"] == 1


def test_propagate_ignores_non_idea_parents():
    store = FakeStore(
        rows=[
            {
                "title": "Parent Feature",
                "type": "Feature",
                "status": "done",
                "release_note_link": "",
                "parent_ids": [],
                "notion_id": "feat-parent",
            },
            {
                "title": "Child Feature",
                "type": "Feature",
                "status": "done",
                "release_note_link": "https://notion.so/release-v1",
                "parent_ids": ["feat-parent"],
                "notion_id": "feat-child",
            },
        ],
        briefs=[],
    )
    result = ShipRoutingAutomationService(store).propagate_release_links()
    assert result["propagated_count"] == 0


def test_propagate_blocks_when_sibling_features_not_done_and_notes_partial_ship():
    store = FakeStore(
        rows=[
            {
                "title": "Parent Idea",
                "type": "Idea",
                "status": "exploring",
                "release_note_link": "",
                "notes": "",
                "parent_ids": [],
                "notion_id": "idea-1",
            },
            {
                "title": "Feature Phase 1",
                "type": "Feature",
                "status": "done",
                "release_note_link": "https://notion.so/release-v1",
                "parent_ids": ["idea-1"],
                "notion_id": "feat-1",
            },
            {
                "title": "Feature Phase 2",
                "type": "Feature",
                "status": "in-progress",
                "release_note_link": "",
                "parent_ids": ["idea-1"],
                "notion_id": "feat-2",
            },
        ],
        briefs=[],
    )

    result = ShipRoutingAutomationService(store).propagate_release_links()

    assert result["propagated_count"] == 0
    assert result["blocked_partial_count"] == 1
    assert result["blocked_partial"][0]["done"] == 1
    assert result["blocked_partial"][0]["total"] == 2
    assert any(
        w.get("title") == "Parent Idea" and "[partial-ship] 1/2 Features done as of" in w.get("notes", "")
        for w in store.writes
    )
