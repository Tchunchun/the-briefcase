"""Unit tests for release readiness gate."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.core.release_gate import ReleaseGate, CheckResult, GateReport


@pytest.fixture
def mock_store():
    store = MagicMock()
    store.read_backlog.return_value = []
    store.read_release_note.return_value = {
        "version": "v0.9.0",
        "title": "v0.9.0 Release Notes",
        "content": "Changes...",
    }
    return store


@pytest.fixture
def gate(mock_store):
    return ReleaseGate(mock_store, "v0.9.0", project_root="/tmp")


# --- CheckResult / GateReport ---


def test_gate_report_overall_passed_all_pass():
    report = GateReport(version="v1.0.0", timestamp="2026-01-01T00:00:00Z")
    report.checks = [
        CheckResult("a", True, "ok"),
        CheckResult("b", True, "ok"),
    ]
    assert report.overall_passed is True


def test_gate_report_overall_passed_one_fail():
    report = GateReport(version="v1.0.0", timestamp="2026-01-01T00:00:00Z")
    report.checks = [
        CheckResult("a", True, "ok"),
        CheckResult("b", False, "fail"),
    ]
    assert report.overall_passed is False


def test_gate_report_to_dict():
    report = GateReport(version="v1.0.0", timestamp="2026-01-01T00:00:00Z")
    report.checks = [CheckResult("a", True, "ok")]
    d = report.to_dict()
    assert d["version"] == "v1.0.0"
    assert d["overall_passed"] is True
    assert len(d["checks"]) == 1
    assert d["checks"][0]["name"] == "a"


# --- Release note exists ---


def test_check_release_note_exists_passes(gate, mock_store):
    report = gate.run()
    rn_check = next(c for c in report.checks if c.name == "release_note_exists")
    assert rn_check.passed is True


def test_check_release_note_exists_fails(gate, mock_store):
    mock_store.read_release_note.side_effect = KeyError("not found")
    report = gate.run()
    rn_check = next(c for c in report.checks if c.name == "release_note_exists")
    assert rn_check.passed is False
    assert "missing" in rn_check.message.lower()


# --- Features accepted ---


def test_check_features_accepted_all_done(gate, mock_store):
    mock_store.read_backlog.return_value = [
        {"type": "Feature", "status": "done", "title": "F1"},
        {"type": "Feature", "status": "review-accepted", "title": "F2"},
    ]
    report = gate.run()
    check = next(c for c in report.checks if c.name == "features_accepted")
    assert check.passed is True


def test_check_features_accepted_one_in_progress(gate, mock_store):
    mock_store.read_backlog.return_value = [
        {"type": "Feature", "status": "done", "title": "F1"},
        {"type": "Feature", "status": "in-progress", "title": "F2"},
    ]
    report = gate.run()
    check = next(c for c in report.checks if c.name == "features_accepted")
    assert check.passed is False
    assert "F2" in check.message


# --- Release note links ---


def test_check_release_note_links_all_have_link(gate, mock_store):
    mock_store.read_backlog.return_value = [
        {"type": "Feature", "status": "done", "title": "F1",
         "release_note_link": "https://notion.so/abc"},
    ]
    report = gate.run()
    check = next(c for c in report.checks if c.name == "release_note_links")
    assert check.passed is True


def test_check_release_note_links_missing(gate, mock_store):
    mock_store.read_backlog.return_value = [
        {"type": "Feature", "status": "done", "title": "F1",
         "release_note_link": ""},
    ]
    report = gate.run()
    check = next(c for c in report.checks if c.name == "release_note_links")
    assert check.passed is False
    assert "F1" in check.message


def test_check_release_note_links_apply_sets_link(gate, mock_store):
    mock_store.read_backlog.return_value = [
        {"type": "Feature", "status": "done", "title": "F1",
         "release_note_link": ""},
    ]
    mock_store.read_release_note.return_value = {
        "version": "v0.9.0", "notion_url": "https://notion.so/xyz"
    }
    report = gate.run(apply=True)
    check = next(c for c in report.checks if c.name == "release_note_links")
    assert check.passed is True
    assert "Applied" in check.message
    mock_store.write_backlog_row.assert_called()


# --- Parent ideas shipped ---


def test_check_parent_ideas_shipped_already_shipped(gate, mock_store):
    mock_store.read_backlog.return_value = [
        {"type": "Feature", "status": "done", "title": "F1",
         "parent_ids": ["idea-1"], "release_note_link": "x"},
        {"type": "Idea", "status": "shipped", "title": "I1",
         "notion_id": "idea-1"},
    ]
    report = gate.run()
    check = next(c for c in report.checks if c.name == "parent_ideas_shipped")
    assert check.passed is True


def test_check_parent_ideas_not_shipped(gate, mock_store):
    mock_store.read_backlog.return_value = [
        {"type": "Feature", "status": "done", "title": "F1",
         "parent_ids": ["idea-1"], "release_note_link": "x"},
        {"type": "Idea", "status": "promoted", "title": "I1",
         "notion_id": "idea-1"},
    ]
    report = gate.run()
    check = next(c for c in report.checks if c.name == "parent_ideas_shipped")
    assert check.passed is False


def test_check_parent_ideas_apply_ships_them(gate, mock_store):
    mock_store.read_backlog.return_value = [
        {"type": "Feature", "status": "done", "title": "F1",
         "parent_ids": ["idea-1"], "release_note_link": "x"},
        {"type": "Idea", "status": "promoted", "title": "I1",
         "notion_id": "idea-1", "notes": ""},
    ]
    report = gate.run(apply=True)
    check = next(c for c in report.checks if c.name == "parent_ideas_shipped")
    assert check.passed is True
    mock_store.write_backlog_row.assert_called()


# --- No blocking findings ---


def test_check_no_blocking_findings_clean(gate, mock_store):
    mock_store.read_backlog.return_value = [
        {"type": "Feature", "status": "done", "title": "F1",
         "review_verdict": "accepted", "release_note_link": "x"},
    ]
    report = gate.run()
    check = next(c for c in report.checks if c.name == "no_blocking_findings")
    assert check.passed is True


def test_check_no_blocking_findings_changes_requested(gate, mock_store):
    mock_store.read_backlog.return_value = [
        {"type": "Feature", "status": "in-progress", "title": "F1",
         "review_verdict": "changes-requested"},
    ]
    report = gate.run()
    check = next(c for c in report.checks if c.name == "no_blocking_findings")
    assert check.passed is False
    assert "F1" in check.message


# --- Git clean ---


@patch("src.core.release_gate.subprocess.run")
def test_check_git_clean_passes(mock_run, gate):
    mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
    report = gate.run()
    check = next(c for c in report.checks if c.name == "git_clean")
    assert check.passed is True


@patch("src.core.release_gate.subprocess.run")
def test_check_git_clean_dirty(mock_run, gate):
    mock_run.return_value = MagicMock(
        returncode=0, stdout="M file.py\n?? new.py\n", stderr=""
    )
    report = gate.run()
    check = next(c for c in report.checks if c.name == "git_clean")
    assert check.passed is False
    assert "2 uncommitted" in check.message


# --- Tag not exists ---


@patch("src.core.release_gate.subprocess.run")
def test_check_tag_not_exists_passes(mock_run, gate):
    mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
    report = gate.run()
    check = next(c for c in report.checks if c.name == "tag_not_exists")
    assert check.passed is True


@patch("src.core.release_gate.subprocess.run")
def test_check_tag_exists_fails(mock_run, gate):
    # First call for git status (clean), second for git tag
    mock_run.side_effect = [
        MagicMock(returncode=0, stdout="", stderr=""),  # git status
        MagicMock(returncode=0, stdout="v0.9.0\n", stderr=""),  # git tag
    ]
    report = gate.run()
    check = next(c for c in report.checks if c.name == "tag_not_exists")
    assert check.passed is False
    assert "already exists" in check.message


# --- Full gate integration ---


@patch("src.core.release_gate.subprocess.run")
def test_full_gate_passes(mock_run, gate, mock_store):
    mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
    mock_store.read_backlog.return_value = [
        {"type": "Feature", "status": "done", "title": "F1",
         "review_verdict": "accepted", "release_note_link": "https://x",
         "parent_ids": []},
    ]
    report = gate.run()
    assert report.overall_passed is True
    assert len(report.checks) == 7


@patch("src.core.release_gate.subprocess.run")
def test_full_gate_dry_run_no_writes(mock_run, gate, mock_store):
    mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
    mock_store.read_backlog.return_value = [
        {"type": "Feature", "status": "done", "title": "F1",
         "review_verdict": "accepted", "release_note_link": "",
         "parent_ids": []},
    ]
    report = gate.run(apply=False)
    # Should NOT write anything in dry-run
    mock_store.write_backlog_row.assert_not_called()
    assert report.overall_passed is False  # missing release_note_link
