"""Unit tests for idea-close automation."""

from __future__ import annotations

from datetime import datetime, timezone

from src.core.automation.idea_close import IdeaCloseAutomationService


class FakeStore:
    def __init__(self, rows: list[dict], briefs: list[dict] | None = None) -> None:
        self.rows = rows
        self.briefs = briefs or []
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
        return {"command": "fake-idea-close", "returncode": 0, "stdout": "ok"}


NOW = datetime(2026, 3, 21, 12, 0, tzinfo=timezone.utc)


def _done_feature(
    title="Login UI",
    notion_id="feat-1",
    parent_ids=None,
    release_note_link="https://www.notion.so/release-1",
):
    return {
        "title": title,
        "type": "Feature",
        "status": "done",
        "notes": "",
        "brief_link": "",
        "parent_ids": ["idea-1"] if parent_ids is None else parent_ids,
        "notion_id": notion_id,
        "release_note_link": release_note_link,
        "automation_trace": "",
    }


def _idea(title="Login idea", notion_id="idea-1", status="exploring"):
    return {
        "title": title,
        "type": "Idea",
        "status": status,
        "notes": "",
        "parent_ids": [],
        "notion_id": notion_id,
        "release_note_link": "",
        "automation_trace": "",
    }


def _brief(name="login-ui"):
    return {"name": name, "title": "Login UI", "notion_id": "b1"}


def test_dispatches_done_feature_with_valid_parent():
    idea = _idea()
    feature = _done_feature()
    dispatcher = FakeDispatcher()
    store = FakeStore(rows=[feature, idea], briefs=[_brief()])
    result = IdeaCloseAutomationService(store, dispatcher=dispatcher).scan(now=NOW)

    assert result["dispatched_count"] == 1
    d = result["dispatches"][0]
    assert d["parent_idea_id"] == "idea-1"
    assert d["parent_idea_title"] == "Login idea"
    assert d["release_note_link"] == "https://www.notion.so/release-1"
    assert "briefcase backlog upsert" in d["command_hint"]
    assert "[auto-idea-close]" in store.writes[-1].get("automation_trace", "")


def test_blocks_when_no_parent_ids():
    feature = _done_feature(parent_ids=[])
    store = FakeStore(rows=[feature], briefs=[_brief()])
    result = IdeaCloseAutomationService(store).scan(now=NOW)

    assert result["dispatched_count"] == 0
    assert result["blocked_count"] == 1
    assert "no parent Idea" in result["blocked"][0]["reason"]


def test_blocks_when_multiple_parents():
    feature = _done_feature(parent_ids=["idea-1", "idea-2"])
    idea1 = _idea(notion_id="idea-1")
    idea2 = _idea(title="Second idea", notion_id="idea-2")
    store = FakeStore(rows=[feature, idea1, idea2], briefs=[_brief()])
    result = IdeaCloseAutomationService(store).scan(now=NOW)

    assert result["dispatched_count"] == 0
    assert result["blocked_count"] == 1
    assert "2 parents" in result["blocked"][0]["reason"]


def test_blocks_when_parent_already_shipped():
    idea = _idea(status="shipped")
    feature = _done_feature()
    store = FakeStore(rows=[feature, idea], briefs=[_brief()])
    result = IdeaCloseAutomationService(store).scan(now=NOW)

    assert result["dispatched_count"] == 0
    assert result["blocked_count"] == 1
    assert "already shipped" in result["blocked"][0]["reason"]


def test_blocks_when_no_release_note_link():
    idea = _idea()
    feature = _done_feature(release_note_link="")
    store = FakeStore(rows=[feature, idea], briefs=[_brief()])
    result = IdeaCloseAutomationService(store).scan(now=NOW)

    assert result["dispatched_count"] == 0
    assert result["blocked_count"] == 1
    assert "no release_note_link" in result["blocked"][0]["reason"]


def test_blocks_when_parent_id_not_an_idea():
    """Parent ID resolves to a Feature, not an Idea."""
    other_feature = {
        "title": "Other Feature",
        "type": "Feature",
        "status": "in-progress",
        "notion_id": "idea-1",
        "parent_ids": [],
        "release_note_link": "",
        "automation_trace": "",
    }
    feature = _done_feature()
    store = FakeStore(rows=[feature, other_feature], briefs=[_brief()])
    result = IdeaCloseAutomationService(store).scan(now=NOW)

    assert result["dispatched_count"] == 0
    assert result["blocked_count"] == 1
    assert "does not resolve to an Idea" in result["blocked"][0]["reason"]


def test_idempotent_second_run():
    idea = _idea()
    feature = _done_feature()
    dispatcher = FakeDispatcher()
    store = FakeStore(rows=[feature, idea], briefs=[_brief()])
    svc = IdeaCloseAutomationService(store, dispatcher=dispatcher)

    first = svc.scan(now=NOW)
    assert first["dispatched_count"] == 1

    second = svc.scan(now=datetime(2026, 3, 21, 12, 5, tzinfo=timezone.utc))
    assert second["dispatched_count"] == 0


def test_skips_non_done_features():
    idea = _idea()
    feature = {**_done_feature(), "status": "in-progress"}
    store = FakeStore(rows=[feature, idea], briefs=[_brief()])
    result = IdeaCloseAutomationService(store).scan(now=NOW)

    assert result["dispatched_count"] == 0


def test_dry_run_does_not_write():
    idea = _idea()
    feature = _done_feature()
    store = FakeStore(rows=[feature, idea], briefs=[_brief()])
    result = IdeaCloseAutomationService(store).scan(apply=False, now=NOW)

    assert result["dispatched_count"] == 1
    assert result["dry_run"] is True
    assert len(store.writes) == 0


def test_marker_is_auto_idea_close():
    idea = _idea()
    feature = _done_feature()
    dispatcher = FakeDispatcher()
    store = FakeStore(rows=[feature, idea], briefs=[_brief()])
    IdeaCloseAutomationService(store, dispatcher=dispatcher).scan(now=NOW)

    trace = store.writes[-1].get("automation_trace", "")
    assert "[auto-idea-close]" in trace
    assert "[auto-ship-dispatch]" not in trace
