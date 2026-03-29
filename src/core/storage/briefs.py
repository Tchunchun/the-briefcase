"""Helpers for parsing and rendering shared brief markdown content."""

from __future__ import annotations

import re
from datetime import datetime, timezone


_STATUS_PATTERN = re.compile(
    r"^\s*\*{0,2}Status:\s*([^*\n]+?)\*{0,2}\s*$",
    re.MULTILINE,
)

_CREATED_PATTERN = re.compile(
    r"^\s*\*{0,2}Created:\s*([^*\n]+?)\*{0,2}\s*$",
    re.MULTILINE,
)

_PROJECT_PATTERN = re.compile(
    r"^\s*\*{0,2}Project:\s*([^*\n]+?)\*{0,2}\s*$",
    re.MULTILINE,
)

BRIEF_SECTIONS = {
    "Problem": "problem",
    "Goal": "goal",
    "Acceptance Criteria": "acceptance_criteria",
    "Expected Experience": "expected_experience",
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


def extract_brief_created(content: str, default: str = "") -> str:
    """Extract a brief creation date from markdown-like content."""
    match = _CREATED_PATTERN.search(content)
    return match.group(1).strip() if match else default


def extract_brief_project(content: str, default: str = "") -> str:
    """Extract a brief project name from markdown-like content."""
    match = _PROJECT_PATTERN.search(content)
    return match.group(1).strip() if match else default


def parse_brief_sections(content: str) -> dict[str, str]:
    """Extract known brief sections from markdown-like content.

    Only sections that are actually present in *content* appear in the
    returned dict.  Sections not found are **omitted** (not set to ""),
    so callers can distinguish "absent" from "explicitly empty".
    """
    data: dict[str, str] = {}
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


def render_history_section(history: list[dict]) -> str:
    """Render a ``## History`` section from a list of revision summaries."""
    if not history:
        return ""
    lines = ["## History", ""]
    for entry in history:
        rid = entry.get("revision_id", "")
        summary = entry.get("change_summary", "no summary")
        actor = entry.get("actor", "unknown")
        ts = entry.get("captured_at", "")
        lines.append(f"- **{rid}** — {summary} (by {actor}, {ts})")
    lines.append("")
    return "\n".join(lines)


def render_brief_markdown(
    brief_name: str,
    data: dict,
    *,
    include_title: bool = True,
    history: list[dict] | None = None,
) -> str:
    """Render structured brief data to markdown.

    If *history* is provided the entries are appended as a ``## History``
    section at the end of the document.
    """
    status = data.get("status", "draft")
    created = data.get("created", "")
    lines: list[str] = []
    if include_title:
        lines.extend([f"# {data.get('title', brief_name)}", ""])
    lines.append(f"**Status: {status}**")
    if created:
        lines.append(f"**Created: {created}**")
    if data.get("project"):
        lines.append(f"**Project: {data['project']}**")
    lines.extend(
        [
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
            "## Expected Experience",
            data.get("expected_experience", ""),
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
    if history:
        lines.append(render_history_section(history))
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
    snapshot["project"] = extract_brief_project(brief_content)
    snapshot.update(parse_brief_sections(brief_content))

    return {
        **metadata,
        "snapshot": snapshot,
        "raw": content,
    }
