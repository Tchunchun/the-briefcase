"""Unit tests for src.core.artifact_service — ArtifactService facade."""

from __future__ import annotations

import pytest

from src.core.artifact_service import (
    ArtifactService,
    ErrorKind,
    Result,
)


# -- Fake store ---------------------------------------------------------------

class FakeStore:
    """Minimal ArtifactStore implementation for testing."""

    def __init__(self) -> None:
        self.inbox: list[dict] = []
        self.briefs: dict[str, dict] = {}
        self.decisions: list[dict] = []
        self.backlog: list[dict] = []
        self.release_notes: dict[str, dict] = {}
        self.last_inbox_since: str | None = None
        self.last_backlog_since: str | None = None

    def read_inbox(self, since: str | None = None) -> list[dict]:
        self.last_inbox_since = since
        return list(self.inbox)

    def append_inbox(self, entry: dict) -> None:
        self.inbox.append(entry)

    def read_brief(self, brief_name: str) -> dict:
        if brief_name not in self.briefs:
            raise KeyError(brief_name)
        return self.briefs[brief_name]

    def write_brief(self, brief_name: str, data: dict) -> None:
        self.briefs[brief_name] = data

    def list_briefs(self) -> list[dict]:
        return [{"name": k, "status": v.get("status")} for k, v in self.briefs.items()]

    def read_decisions(self) -> list[dict]:
        return list(self.decisions)

    def append_decision(self, entry: dict) -> None:
        self.decisions.append(entry)

    def read_backlog(self, since: str | None = None) -> list[dict]:
        self.last_backlog_since = since
        return list(self.backlog)

    def write_backlog_row(self, row: dict) -> None:
        for i, existing in enumerate(self.backlog):
            if existing.get("title") == row.get("title") and existing.get("type") == row.get("type"):
                self.backlog[i] = row
                return
        self.backlog.append(row)

    def write_release_note(self, version: str, content: str) -> None:
        self.release_notes[version] = {"version": version, "content": content}

    def read_release_note(self, version: str) -> dict:
        if version not in self.release_notes:
            raise KeyError(version)
        return self.release_notes[version]

    def list_release_notes(self) -> list[dict]:
        return [{"version": v} for v in self.release_notes]


@pytest.fixture
def store() -> FakeStore:
    return FakeStore()


@pytest.fixture
def svc(store: FakeStore) -> ArtifactService:
    return ArtifactService(store)


# -- Inbox tests --------------------------------------------------------------

class TestInbox:
    def test_list_empty(self, svc: ArtifactService):
        r = svc.list_inbox()
        assert r.success
        assert r.data == []

    def test_add_and_list(self, svc: ArtifactService):
        r = svc.add_inbox(text="Fix login bug", entry_type="idea", notes="Details here")
        assert r.success
        assert r.data["text"] == "Fix login bug"

        r2 = svc.list_inbox()
        assert len(r2.data) == 1

    def test_add_requires_text(self, svc: ArtifactService):
        r = svc.add_inbox(text="")
        assert not r.success
        assert r.error_kind == ErrorKind.VALIDATION

    def test_list_passes_since(self, svc: ArtifactService, store: FakeStore):
        r = svc.list_inbox(since="2026-03-20")
        assert r.success
        assert store.last_inbox_since == "2026-03-20"


# -- Brief tests ---------------------------------------------------------------

class TestBrief:
    def test_read_not_found(self, svc: ArtifactService):
        r = svc.read_brief("nonexistent")
        assert not r.success
        assert r.error_kind == ErrorKind.NOT_FOUND

    def test_write_and_read(self, svc: ArtifactService):
        data = {"status": "draft", "problem": "P", "goal": "G", "acceptance_criteria": "AC"}
        w = svc.write_brief("my-feature", data)
        assert w.success

        r = svc.read_brief("my-feature")
        assert r.success
        assert r.data["problem"] == "P"

    def test_write_requires_status(self, svc: ArtifactService):
        r = svc.write_brief("feat", {"problem": "P"})
        assert not r.success
        assert r.error_kind == ErrorKind.VALIDATION

    def test_write_requires_name(self, svc: ArtifactService):
        r = svc.write_brief("", {"status": "draft"})
        assert not r.success
        assert r.error_kind == ErrorKind.VALIDATION

    def test_list_briefs(self, svc: ArtifactService, store: FakeStore):
        store.briefs["a"] = {"status": "draft"}
        store.briefs["b"] = {"status": "implementation-ready"}
        r = svc.list_briefs()
        assert r.success
        assert len(r.data) == 2


# -- Decision tests ------------------------------------------------------------

class TestDecision:
    def test_list_empty(self, svc: ArtifactService):
        r = svc.list_decisions()
        assert r.success
        assert r.data == []

    def test_add_and_list(self, svc: ArtifactService):
        entry = {"id": "D-001", "title": "Use Python", "date": "2025-01-01", "why": "Team knows it", "status": "accepted"}
        r = svc.add_decision(entry)
        assert r.success
        assert svc.list_decisions().data[0]["id"] == "D-001"

    def test_add_requires_fields(self, svc: ArtifactService):
        r = svc.add_decision({"id": "D-001"})
        assert not r.success
        assert r.error_kind == ErrorKind.VALIDATION


# -- Backlog tests -------------------------------------------------------------

class TestBacklog:
    def test_list_empty(self, svc: ArtifactService):
        r = svc.list_backlog()
        assert r.success
        assert r.data == []

    def test_upsert_and_list(self, svc: ArtifactService):
        row = {"title": "Build API", "type": "Task", "status": "to-do"}
        r = svc.upsert_backlog(row)
        assert r.success

        r2 = svc.list_backlog()
        assert len(r2.data) == 1

    def test_upsert_requires_fields(self, svc: ArtifactService):
        r = svc.upsert_backlog({"title": "X"})
        assert not r.success
        assert r.error_kind == ErrorKind.VALIDATION

    def test_list_passes_since(self, svc: ArtifactService, store: FakeStore):
        r = svc.list_backlog(since="2026-03-20")
        assert r.success
        assert store.last_backlog_since == "2026-03-20"


# -- Release notes tests -------------------------------------------------------

class TestReleaseNotes:
    def test_read_not_found(self, svc: ArtifactService):
        r = svc.read_release_note("v99.0.0")
        assert not r.success
        assert r.error_kind == ErrorKind.NOT_FOUND

    def test_write_and_read(self, svc: ArtifactService):
        w = svc.write_release_note("v0.5.0", "## Changes\n- Added feature")
        assert w.success

        r = svc.read_release_note("v0.5.0")
        assert r.success
        assert r.data["version"] == "v0.5.0"

    def test_write_requires_version(self, svc: ArtifactService):
        r = svc.write_release_note("", "content")
        assert not r.success
        assert r.error_kind == ErrorKind.VALIDATION

    def test_list_release_notes(self, svc: ArtifactService, store: FakeStore):
        store.release_notes["v1"] = {"version": "v1"}
        r = svc.list_release_notes()
        assert r.success
        assert len(r.data) == 1


# -- Backend error normalization -----------------------------------------------

class TestErrorNormalization:
    def test_backend_error_wrapped(self, svc: ArtifactService, store: FakeStore):
        """Raw exceptions from the store become backend_error Results."""
        store.read_inbox = lambda: (_ for _ in ()).throw(RuntimeError("API down"))
        r = svc.list_inbox()
        assert not r.success
        assert r.error_kind == ErrorKind.BACKEND
        assert "API down" in r.error

    def test_result_to_dict(self):
        r = Result(success=True, data={"a": 1})
        d = r.to_dict()
        assert d == {"success": True, "data": {"a": 1}}

    def test_error_result_to_dict(self):
        r = Result(success=False, data=None, error="oops", error_kind=ErrorKind.NOT_FOUND)
        d = r.to_dict()
        assert d["success"] is False
        assert d["error_kind"] == "not_found"
