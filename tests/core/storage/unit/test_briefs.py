"""Unit tests for shared brief parsing helpers."""

from src.core.storage.briefs import (
    parse_brief_sections,
    render_brief_markdown,
    render_history_section,
)


def test_parse_brief_sections_keeps_blank_nfr_empty():
    content = (
        "**Status: implementation-ready**\n"
        "## Problem\nP\n"
        "## Goal\nG\n"
        "## Acceptance Criteria\n- [ ] A\n"
        "## Non-Functional Requirements\n"
        "## Out of Scope\n- OOS\n"
        "## Open Questions\nResolved\n"
        "## Technical Approach\nDo it\n"
    )

    sections = parse_brief_sections(content)

    assert sections["non_functional_requirements"] == ""
    assert sections["out_of_scope"] == "- OOS"


def test_render_history_section_formats_entries():
    history = [
        {
            "revision_id": "20260319T120000000000Z",
            "change_summary": "Initial draft",
            "actor": "alice",
            "captured_at": "20260319T120000000000Z",
        },
    ]
    result = render_history_section(history)
    assert "## History" in result
    assert "20260319T120000000000Z" in result
    assert "Initial draft" in result
    assert "alice" in result


def test_render_history_section_empty():
    assert render_history_section([]) == ""


def test_render_brief_markdown_includes_history_section():
    data = {"status": "draft", "problem": "P", "goal": "G"}
    history = [
        {
            "revision_id": "rev1",
            "change_summary": "First change",
            "actor": "bob",
            "captured_at": "ts1",
        },
    ]
    md = render_brief_markdown("my-feature", data, history=history)
    assert "## History" in md
    assert "First change" in md


def test_render_brief_markdown_no_history_by_default():
    data = {"status": "draft", "problem": "P", "goal": "G"}
    md = render_brief_markdown("my-feature", data)
    assert "## History" not in md
