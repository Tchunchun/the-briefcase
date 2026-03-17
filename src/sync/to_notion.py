"""Local → Notion sync logic (push).

Reads local markdown artifacts and writes them to Notion via
the NotionBackend methods. Reverse of to_local.py (pull).
"""

from __future__ import annotations

import re
from pathlib import Path

from src.core.storage.config import load_config
from src.core.storage.factory import get_store
from src.core.storage.protocol import ArtifactStore
from src.sync.manifest import compute_checksums, write_manifest


def sync_to_notion(
    project_root: str | Path, *, dry_run: bool = False
) -> dict:
    """Push local markdown artifacts to the Notion backend.

    Reads local files and upserts to Notion via ArtifactStore methods.

    Returns summary dict: {pushed, skipped, failed}.
    """
    root = Path(project_root)
    config = load_config(root / "_project")
    store = get_store(config, str(root))

    if config.is_local():
        raise ValueError(
            "Cannot push to Notion when backend is 'local'. "
            "Set backend to 'notion' in _project/storage.yaml."
        )

    plan_dir = root / "docs" / "plan"
    summary = {"pushed": 0, "skipped": 0, "failed": 0}

    # Push inbox (_inbox.md → Backlog Idea rows)
    _push_inbox(store, plan_dir, summary, dry_run=dry_run)

    # Push briefs (docs/plan/{name}/brief.md → standalone pages)
    _push_briefs(store, plan_dir, summary, dry_run=dry_run)

    # Push decisions (_project/decisions.md → Decisions database)
    _push_decisions(store, root / "_project", summary, dry_run=dry_run)

    # Write manifest after push
    if not dry_run:
        try:
            checksums = compute_checksums(plan_dir)
            artifacts = list(checksums.keys())
            write_manifest(
                plan_dir,
                direction="push",
                backend=config.backend,
                artifacts_synced=artifacts,
                checksums=checksums,
            )
        except Exception:
            pass

    return summary


def _push_inbox(
    store: ArtifactStore,
    plan_dir: Path,
    summary: dict,
    *,
    dry_run: bool = False,
) -> None:
    """Parse _inbox.md and push new ideas to Notion."""
    inbox_path = plan_dir / "_inbox.md"
    if not inbox_path.exists():
        return

    content = inbox_path.read_text()
    # Read existing ideas from Notion to avoid duplicates
    try:
        existing = store.read_inbox()
        existing_texts = {e["text"] for e in existing}
    except Exception:
        existing_texts = set()

    for line in content.splitlines():
        match = re.match(
            r"^- \[(?P<type>[^\]]+)\]\s*(?P<text>.+?)(?:\s*\[-> .+\].*)?$",
            line,
        )
        if not match:
            continue
        raw_text = match.group("text").strip()
        # Split title from notes on " — " (em-dash)
        if " \u2014 " in raw_text:
            title, notes = raw_text.split(" \u2014 ", 1)
        else:
            title, notes = raw_text, ""
        title = title.strip()
        if title in existing_texts:
            summary["skipped"] += 1
            continue
        if dry_run:
            summary["pushed"] += 1
            continue
        try:
            entry = {"text": title, "type": match.group("type")}
            if notes.strip():
                entry["notes"] = notes.strip()
            store.append_inbox(entry)
            summary["pushed"] += 1
        except Exception:
            summary["failed"] += 1


def _push_briefs(
    store: ArtifactStore,
    plan_dir: Path,
    summary: dict,
    *,
    dry_run: bool = False,
) -> None:
    """Push local brief.md files to Notion as standalone pages."""
    if not plan_dir.exists():
        return

    for child in sorted(plan_dir.iterdir()):
        brief_file = child / "brief.md"
        if not (child.is_dir() and not child.name.startswith("_") and brief_file.exists()):
            continue

        brief_name = child.name
        content = brief_file.read_text()

        # Extract title from first heading
        title_match = re.match(r"^#\s+(.+)", content)
        title = title_match.group(1).strip() if title_match else brief_name

        # Extract status
        status_match = re.search(r"\*\*Status:\s*(\S+)\*\*", content)
        status = status_match.group(1) if status_match else "draft"

        # Parse sections
        data = {"title": title, "status": status}
        sections = {
            "problem": r"## Problem\s*\n(.*?)(?=\n## |\Z)",
            "goal": r"## Goal\s*\n(.*?)(?=\n## |\Z)",
            "acceptance_criteria": r"## Acceptance Criteria\s*\n(.*?)(?=\n## |\Z)",
            "out_of_scope": r"## Out of Scope\s*\n(.*?)(?=\n## |\Z)",
            "open_questions": r"## Open Questions[^\n]*\n(.*?)(?=\n## |\Z)",
            "technical_approach": r"## Technical Approach\s*\n(.*?)(?=\n## |\Z)",
        }
        for key, pattern in sections.items():
            match = re.search(pattern, content, re.DOTALL)
            data[key] = match.group(1).strip() if match else ""

        if dry_run:
            summary["pushed"] += 1
            continue
        try:
            store.write_brief(brief_name, data)
            summary["pushed"] += 1
        except Exception:
            summary["failed"] += 1


def _push_decisions(
    store: ArtifactStore,
    project_dir: Path,
    summary: dict,
    *,
    dry_run: bool = False,
) -> None:
    """Parse decisions.md and push new decisions to Notion."""
    decisions_path = project_dir / "decisions.md"
    if not decisions_path.exists():
        return

    content = decisions_path.read_text()

    # Read existing decisions from Notion to avoid duplicates
    try:
        existing = store.read_decisions()
        existing_ids = {d["id"] for d in existing}
    except Exception:
        existing_ids = set()

    # Parse markdown table rows
    for line in content.splitlines():
        if not line.startswith("| D-"):
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if len(cells) < 6:
            continue

        decision_id = cells[0]
        if decision_id in existing_ids:
            summary["skipped"] += 1
            continue

        entry = {
            "id": decision_id,
            "date": cells[1],
            "title": cells[2],
            "why": cells[3],
            "alternatives_rejected": cells[4],
            "adr_link": cells[5] if cells[5] != "—" else "",
        }

        if dry_run:
            summary["pushed"] += 1
            continue
        try:
            store.append_decision(entry)
            summary["pushed"] += 1
        except Exception:
            summary["failed"] += 1
