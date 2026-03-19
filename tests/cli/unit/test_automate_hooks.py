"""Unit tests for automation CLI hook behavior."""

from __future__ import annotations

from src.cli.commands import automate as automate_module


class FakeStore:
    def __init__(self, rows: list[dict]) -> None:
        self.rows = [dict(row) for row in rows]
        self.writes: list[dict] = []

    def read_backlog(self) -> list[dict]:
        return [dict(row) for row in self.rows]

    def write_backlog_row(self, row: dict) -> None:
        self.writes.append(dict(row))
        for idx, existing in enumerate(self.rows):
            candidate_id = existing.get("notion_id") or existing.get("id")
            row_id = row.get("notion_id") or row.get("id")
            if row_id and candidate_id == row_id:
                self.rows[idx] = dict(row)
                return
            if (
                existing.get("type") == row.get("type")
                and existing.get("title") == row.get("title")
            ):
                self.rows[idx] = dict(row)
                return
        self.rows.append(dict(row))


def test_review_post_hook_promotes_accepted_review():
    store = FakeStore(
        [
            {
                "title": "Review Accept",
                "type": "Feature",
                "status": "review-ready",
                "review_verdict": "accepted",
                "notion_id": "feat-1",
            }
        ]
    )

    result = automate_module._run_post_dispatch_hooks(
        store,
        "review-ready",
        {"feature_title": "Review Accept", "feature_id": "feat-1"},
        project_dir=".",
        fix_command_template="",
    )

    assert result is None
    assert store.rows[0]["status"] == "review-accepted"
    assert store.rows[0]["review_verdict"] == "accepted"
    assert store.rows[0]["route_state"] == "routed"


def test_review_post_hook_writes_structured_review_verdict():
    store = FakeStore(
        [
            {
                "title": "Review Accept",
                "type": "Feature",
                "status": "review-ready",
                "review_verdict": "pending",
                "notion_id": "feat-1",
            }
        ]
    )

    result = automate_module._run_post_dispatch_hooks(
        store,
        "review-ready",
        {"feature_title": "Review Accept", "feature_id": "feat-1"},
        project_dir=".",
        fix_command_template="",
        dispatch_result={"review_verdict": "accepted", "stdout": '{"review_verdict": "accepted"}'},
    )

    assert result is None
    assert store.rows[0]["review_verdict"] == "accepted"
    assert store.rows[0]["status"] == "review-accepted"
    assert store.rows[0]["route_state"] == "routed"


def test_review_post_hook_requeues_changes_requested(monkeypatch):
    store = FakeStore(
        [
            {
                "title": "Review Reject",
                "type": "Feature",
                "status": "review-ready",
                "review_verdict": "changes-requested",
                "notion_id": "feat-2",
            }
        ]
    )
    calls: list[tuple[str, str, str, dict]] = []

    def fake_run_command_template(
        command_template: str,
        project_dir: str,
        label: str,
        payload: dict,
    ) -> dict:
        calls.append((command_template, project_dir, label, dict(payload)))
        return {"command": command_template, "returncode": 0, "stdout": "impl"}

    monkeypatch.setattr(automate_module, "_run_command_template", fake_run_command_template)

    result = automate_module._run_post_dispatch_hooks(
        store,
        "review-ready",
        {"feature_title": "Review Reject", "feature_id": "feat-2", "brief_name": "review-reject"},
        project_dir="/tmp/project",
        fix_command_template="run-impl {feature_title}",
        dispatch_result={"review_verdict": "changes-requested", "stdout": '{"review_verdict": "changes-requested"}'},
    )

    assert store.rows[0]["status"] == "in-progress"
    assert store.rows[0]["review_verdict"] == "changes-requested"
    assert store.rows[0]["route_state"] == "returned"
    assert result == {"command": "run-impl {feature_title}", "returncode": 0, "stdout": "impl"}
    assert calls == [
        (
            "run-impl {feature_title}",
            "/tmp/project",
            "Implementation",
            {
                "feature_title": "Review Reject",
                "feature_id": "feat-2",
                "brief_name": "review-reject",
            },
        )
    ]


def test_review_post_hook_requires_implementation_dispatch_command():
    store = FakeStore(
        [
            {
                "title": "Review Reject",
                "type": "Feature",
                "status": "review-ready",
                "review_verdict": "changes-requested",
                "notion_id": "feat-2",
            }
        ]
    )

    try:
        automate_module._run_post_dispatch_hooks(
            store,
            "review-ready",
            {"feature_title": "Review Reject", "feature_id": "feat-2"},
            project_dir=".",
            fix_command_template="",
            dispatch_result={"review_verdict": "changes-requested", "stdout": '{"review_verdict": "changes-requested"}'},
        )
    except RuntimeError as exc:
        assert "no implementation dispatch command" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError when fix dispatch command is missing")


def test_fix_cycle_pre_hook_moves_review_ready_feature_to_in_progress():
    store = FakeStore(
        [
            {
                "title": "Fix Cycle Feature",
                "type": "Feature",
                "status": "review-ready",
                "review_verdict": "changes-requested",
                "notion_id": "feat-fix-1",
            }
        ]
    )

    automate_module._run_pre_dispatch_hooks(
        store,
        "fix-cycle",
        {"feature_title": "Fix Cycle Feature", "feature_id": "feat-fix-1"},
    )

    assert store.rows[0]["status"] == "in-progress"
    assert store.rows[0]["review_verdict"] == "changes-requested"
    assert store.rows[0]["route_state"] == "returned"


def test_ship_dispatch_post_hook_writes_release_note_link_and_route_state():
    store = FakeStore(
        [
            {
                "title": "Ship Feature",
                "type": "Feature",
                "status": "review-accepted",
                "review_verdict": "accepted",
                "notion_id": "feat-ship-1",
            }
        ]
    )

    result = automate_module._run_post_dispatch_hooks(
        store,
        "ship-dispatch",
        {"feature_title": "Ship Feature", "feature_id": "feat-ship-1"},
        project_dir=".",
        fix_command_template="",
        dispatch_result={
            "release_note_link": "https://example.com/releases/v0.9.0",
            "stdout": '{"release_note_link": "https://example.com/releases/v0.9.0"}',
        },
    )

    assert result is None
    assert store.rows[0]["route_state"] == "routed"
    assert store.rows[0]["release_note_link"] == "https://example.com/releases/v0.9.0"
