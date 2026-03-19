"""Unit tests for shared brief parsing helpers."""

from src.core.storage.briefs import parse_brief_sections


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
