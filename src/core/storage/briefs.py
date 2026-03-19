"""Helpers for parsing and rendering shared brief markdown content."""

from __future__ import annotations

import re
from datetime import datetime, timezone


_STATUS_PATTERN = re.compile(
    r"^\s*\*{0,2}Status:\s*([^*\n]+?)\*{0,2}\s*$",
    re.MULTILINE,
)

BRIEF_SECTIONS = {
    "Problem": "problem",
    "Goal": "goal",
    "Acceptance Criteria": "acceptance_criteria",
    "Non-Functional Requirements": "non_functional_requirements",
    "Out of Scope": "out_of_scope",
    "Open Questions": "open_questions",
    "Technical Approach": "technical_approach",
}

REVISION_METADATA_FIELDS = {
    "Revision ID": "revision_id",
    "Captured At": "captured_at",
    "Actor": "actor",
    "Change Summary": "change_summary",
}


def extract_brief_status(content: str, default: str = "draft") -> str:
    """Extract a brief status from markdown-like content."""
    match = _STATUS_PATTERN.search(content)
    return match.group(1).strip() if match else default


def parse_brief_sections(content: str) -> dict[str, str]:
    """Extract known brief sections from markdown-like content."""
    data: dict[str, str] = {key: "" for key in BRIEF_SECTIONS.values()}
    current_key: str | None = None
    current_lines: list[str] = []

    def flush_current() -> None:
        nonlocal current_key, current_lines
        if current_key is not None:
            data[current_key] = "\n".join(current_lines).strip()
        current_key = None
        current_lines = []

    for line in content.splitlines():
        if line.startswith("## "):
            flush_current()
            heading = line[3:].strip()
            current_key = BRIEF_SECTIONS.get(heading)
            continue
        if current_key is not None:
            current_lines.append(line)

    flush_current()
    return data


def normalize_inline_brief_value(value: str | None) -> str | None:
    """Convert CLI-escaped newlines back to multiline content."""
    if value is None:
        return None
    return value.replace("\\n", "\n")


def render_brief_markdown(
    brief_name: str,
    data: dict,
    *,
    include_title: bool = True,
) -> str:
    """Render structured brief data to markdown."""
    status = data.get("status", "draft")
    lines: list[str] = []
    if include_title:
        lines.extend([f"# {data.get('title', brief_name)}", ""])
    lines.extend(
        [
            f"**Status: {status}**",
            "",
            "---",
            "",
            "## Problem",
            data.get("problem", ""),
            "",
            "## Goal",
            data.get("goal", ""),
            "",
            "## Acceptance Criteria",
            data.get("acceptance_criteria", ""),
            "",
            "## Non-Functional Requirements",
            data.get("non_functional_requirements", ""),
            "",
            "## Out of Scope",
            data.get("out_of_scope", ""),
            "",
            "## Open Questions",
            data.get("open_questions", ""),
            "",
            "## Technical Approach",
            data.get("technical_approach", "*Owned by architect agent.*"),
            "",
        ]
    )
    return "\n".join(lines) + "\n"


def build_revision_id(now: datetime | None = None) -> str:
    """Return a sortable UTC revision identifier."""
    now = now or datetime.now(timezone.utc)
    return now.strftime("%Y%m%dT%H%M%S%fZ")


def render_revision_markdown(
    brief_name: str,
    snapshot: dict,
    metadata: dict,
) -> str:
    """Render a revision document with metadata and full brief snapshot."""
    lines = [
        f"**Revision ID: {metadata['revision_id']}**",
        f"**Captured At: {metadata['captured_at']}**",
    ]
    if metadata.get("actor"):
        lines.append(f"**Actor: {metadata['actor']}**")
    if metadata.get("change_summary"):
        lines.append(f"**Change Summary: {metadata['change_summary']}**")
    lines.extend(["", "---", ""])
    lines.append(render_brief_markdown(brief_name, snapshot).rstrip())
    return "\n".join(lines) + "\n"


def parse_revision_markdown(content: str) -> dict[str, object]:
    """Parse a revision document into metadata plus brief snapshot data."""
    metadata: dict[str, str] = {}
    brief_start = content.find("# ")
    meta_content = content[:brief_start] if brief_start >= 0 else content
    brief_content = content[brief_start:] if brief_start >= 0 else ""

    for line in meta_content.splitlines():
        stripped = line.strip()
        for label, key in REVISION_METADATA_FIELDS.items():
            prefix = f"**{label}:"
            if stripped.startswith(prefix):
                value = stripped[len(prefix):].strip().rstrip("*").strip()
                metadata[key] = value
                break

    snapshot: dict[str, str] = {"raw": brief_content}
    title_match = re.match(r"^#\s+(.+)", brief_content)
    snapshot["title"] = title_match.group(1).strip() if title_match else ""
    snapshot["status"] = extract_brief_status(brief_content)
    snapshot.update(parse_brief_sections(brief_content))

    return {
        **metadata,
        "snapshot": snapshot,
        "raw": content,
    }
