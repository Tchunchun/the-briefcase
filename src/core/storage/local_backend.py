"""Local filesystem backend for artifact storage.

Reads and writes markdown files at canonical paths:
- docs/plan/_inbox.md
- docs/plan/{brief_name}/brief.md
- _project/decisions.md
- docs/plan/_shared/backlog.md
- template/{name}.md
"""

from __future__ import annotations

import os
import re
from datetime import datetime, date, timezone
from pathlib import Path

from src.core.storage.briefs import (
    build_revision_id,
    extract_brief_created,
    extract_brief_project,
    extract_brief_status,
    parse_brief_sections,
    parse_revision_markdown,
    render_brief_markdown,
    render_revision_markdown,
)


class LocalBackend:
    """ArtifactStore implementation backed by local markdown files."""

    def __init__(self, project_root: str | Path) -> None:
        self.root = Path(project_root)
        self.plan_dir = self.root / "docs" / "plan"
        self.project_dir = self.root / "_project"
        self.template_dir = self.root / "template"

    # -- Inbox --

    @staticmethod
    def _iso_from_timestamp(ts: float) -> str:
        return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()

    @staticmethod
    def _parse_since_date(since: str | None) -> date | None:
        if not since:
            return None
        return date.fromisoformat(since)

    @staticmethod
    def _extract_frontmatter_created_at(path: Path) -> str | None:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            return None
        match = re.match(r"^---\n(?P<body>.*?)\n---\n", text, flags=re.DOTALL)
        if not match:
            return None
        for line in match.group("body").splitlines():
            if line.startswith("created_at:"):
                value = line.split(":", 1)[1].strip().strip("\"'")
                if value:
                    return value
        return None

    @staticmethod
    def _iso_on_or_after(iso_value: str, since_date: date | None) -> bool:
        if since_date is None:
            return True
        if not iso_value:
            return False
        normalized = iso_value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized).date() >= since_date

    def read_inbox(self, since: str | None = None) -> list[dict]:
        path = self.plan_dir / "_inbox.md"
        if not path.exists():
            return []
        created_at = self._extract_frontmatter_created_at(path)
        stat = path.stat()
        created_at = created_at or self._iso_from_timestamp(stat.st_ctime)
        updated_at = self._iso_from_timestamp(stat.st_mtime)
        since_date = self._parse_since_date(since)
        content = path.read_text()
        entries = []
        for line in content.splitlines():
            match = re.match(
                r"^- \[(?P<type>[^\]/]+)(?:/(?P<priority>[^\]]+))?\]\s*(?P<text>.+?)(?:\s+\[-> (?P<status>[^\]]+)\])?(?:\s+\u2192\s.+)?$",
                line,
            )
            if match:
                raw_text = match.group("text").strip()
                # Split title from notes on " \u2014 " (em-dash)
                if " \u2014 " in raw_text:
                    title, notes = raw_text.split(" \u2014 ", 1)
                else:
                    title, notes = raw_text, ""
                entry = {
                    "type": match.group("type"),
                    "priority": match.group("priority") or "Medium",
                    "text": title.strip(),
                    "status": match.group("status") or "new",
                    "notes": notes.strip(),
                    "created_at": created_at,
                    "updated_at": updated_at,
                }
                if self._iso_on_or_after(updated_at, since_date):
                    entries.append(entry)
        return entries

    def append_inbox(self, entry: dict) -> None:
        path = self.plan_dir / "_inbox.md"
        entry_type = entry.get("type", "idea")
        priority = entry.get("priority", "Medium")
        text = entry["text"]
        notes = entry.get("notes", "")
        if notes:
            line = f"- [{entry_type}/{priority}] {text} \u2014 {notes}\n"
        else:
            line = f"- [{entry_type}/{priority}] {text}\n"
        with open(path, "a") as f:
            f.write(line)

    # -- Briefs --

    def read_brief(self, brief_name: str) -> dict:
        path = self.plan_dir / brief_name / "brief.md"
        if not path.exists():
            raise KeyError(f"Brief not found: {brief_name}")
        content = path.read_text()
        return self._parse_brief(brief_name, content)

    def write_brief(self, brief_name: str, data: dict) -> None:
        brief_dir = self.plan_dir / brief_name
        brief_dir.mkdir(parents=True, exist_ok=True)
        path = brief_dir / "brief.md"
        if path.exists():
            current = self.read_brief(brief_name)
            # Merge: start from current, overlay only keys present in data.
            merged = dict(current)
            merged.update({k: v for k, v in data.items() if not k.startswith("_")})
            # Preserve original created date
            if not merged.get("created"):
                merged["created"] = current.get("created", "")
            # Carry internal metadata through for revision storage.
            merged["_actor"] = data.get("_actor", "")
            merged["_change_summary"] = data.get("_change_summary", "")
            self._store_brief_revision(
                brief_name,
                current,
                actor=merged.get("_actor", ""),
                change_summary=merged.get("_change_summary", ""),
            )
            data = merged
        else:
            # Auto-set creation date for new briefs
            if not data.get("created"):
                data["created"] = date.today().isoformat()
        revisions = self.list_brief_revisions(brief_name)
        content = self._render_brief(brief_name, data, history=revisions)
        path.write_text(content)

    def list_briefs(self) -> list[dict]:
        briefs = []
        if not self.plan_dir.exists():
            return briefs
        for child in self.plan_dir.iterdir():
            brief_file = child / "brief.md"
            if child.is_dir() and not child.name.startswith("_") and brief_file.exists():
                content = brief_file.read_text()
                status = extract_brief_status(content)
                created = extract_brief_created(content)
                title_match = re.match(r"^#\s+(.+)", content)
                title = title_match.group(1) if title_match else child.name
                # Prefer explicit created date; fall back to file mtime
                if not created:
                    created = datetime.fromtimestamp(
                        brief_file.stat().st_mtime, tz=timezone.utc
                    ).date().isoformat()
                briefs.append(
                    {"name": child.name, "status": status, "title": title, "date": created}
                )
        briefs.sort(key=lambda item: item.get("date", ""), reverse=True)
        return briefs

    def list_brief_revisions(self, brief_name: str) -> list[dict]:
        history_dir = self._brief_history_dir(brief_name)
        if not history_dir.exists():
            return []

        revisions = []
        for path in sorted(history_dir.glob("*.md"), reverse=True):
            parsed = parse_revision_markdown(path.read_text())
            revisions.append(
                {
                    "revision_id": parsed.get("revision_id", path.stem),
                    "captured_at": parsed.get("captured_at", ""),
                    "actor": parsed.get("actor", ""),
                    "change_summary": parsed.get("change_summary", ""),
                    "title": parsed.get("snapshot", {}).get("title", ""),
                    "status": parsed.get("snapshot", {}).get("status", ""),
                }
            )
        return revisions

    def read_brief_revision(self, brief_name: str, revision_id: str) -> dict:
        path = self._brief_history_dir(brief_name) / f"{revision_id}.md"
        if not path.exists():
            raise KeyError(f"Brief revision not found: {brief_name}@{revision_id}")
        parsed = parse_revision_markdown(path.read_text())
        return {
            "brief_name": brief_name,
            "revision_id": parsed.get("revision_id", revision_id),
            "captured_at": parsed.get("captured_at", ""),
            "actor": parsed.get("actor", ""),
            "change_summary": parsed.get("change_summary", ""),
            "snapshot": parsed["snapshot"],
            "raw": parsed["raw"],
        }

    def restore_brief_revision(
        self,
        brief_name: str,
        revision_id: str,
        *,
        actor: str = "",
        change_summary: str = "",
    ) -> dict:
        revision = self.read_brief_revision(brief_name, revision_id)
        snapshot = dict(revision["snapshot"])
        snapshot["_actor"] = actor
        snapshot["_change_summary"] = (
            change_summary or f"Restored from revision {revision_id}"
        )
        self.write_brief(brief_name, snapshot)
        return self.read_brief(brief_name)

    # -- Decisions --

    def read_decisions(self) -> list[dict]:
        path = self.project_dir / "decisions.md"
        if not path.exists():
            return []
        content = path.read_text()
        decisions = []
        in_table = False
        for line in content.splitlines():
            if line.startswith("| ID"):
                in_table = True
                continue
            if in_table and line.startswith("|---"):
                continue
            if in_table and line.startswith("|"):
                cols = [c.strip() for c in line.split("|")[1:-1]]
                if len(cols) >= 6:
                    decisions.append(
                        {
                            "id": cols[0],
                            "date": cols[1],
                            "title": cols[2],
                            "why": cols[3],
                            "alternatives_rejected": cols[4],
                            "adr_link": cols[5],
                        }
                    )
            elif in_table and not line.startswith("|"):
                break
        return decisions

    def append_decision(self, entry: dict) -> None:
        path = self.project_dir / "decisions.md"
        row = (
            f"| {entry['id']} | {entry['date']} | {entry['title']} "
            f"| {entry['why']} | {entry.get('alternatives_rejected', '—')} "
            f"| {entry.get('adr_link', '—')} |\n"
        )
        with open(path, "a") as f:
            f.write(row)

    # -- Backlog --

    def read_backlog(self, since: str | None = None) -> list[dict]:
        path = self.plan_dir / "_shared" / "backlog.md"
        if not path.exists():
            return []
        created_at = self._extract_frontmatter_created_at(path)
        stat = path.stat()
        created_at = created_at or self._iso_from_timestamp(stat.st_ctime)
        updated_at = self._iso_from_timestamp(stat.st_mtime)
        since_date = self._parse_since_date(since)
        content = path.read_text()
        rows = []
        in_table = False
        for line in content.splitlines():
            if line.startswith("| ID"):
                in_table = True
                continue
            if in_table and line.startswith("|---"):
                continue
            if in_table and line.startswith("|"):
                cols = [c.strip() for c in line.split("|")[1:-1]]
                if len(cols) >= 12:
                    rows.append(
                        {
                            "id": cols[0],
                            "type": cols[1],
                            "use_case": cols[2],
                            "feature": cols[3],
                            "title": cols[4],
                            "priority": cols[5],
                            "status": cols[6],
                            "review_verdict": cols[7],
                            "route_state": cols[8],
                            "release_note_link": cols[9],
                            "project": cols[10] if len(cols) >= 14 else "",
                            "notes": cols[11] if len(cols) >= 14 else cols[10],
                            "automation_trace": cols[12] if len(cols) >= 14 else cols[11],
                            "lane": cols[13] if len(cols) >= 14 else (cols[12] if len(cols) >= 13 else ""),
                            "created_at": created_at,
                            "updated_at": updated_at,
                        }
                    )
                elif len(cols) >= 8:
                    rows.append(
                        {
                            "id": cols[0],
                            "type": cols[1],
                            "use_case": cols[2],
                            "feature": cols[3],
                            "title": cols[4],
                            "priority": cols[5],
                            "status": cols[6],
                            "review_verdict": "",
                            "route_state": "",
                            "release_note_link": "",
                            "project": "",
                            "notes": cols[7],
                            "automation_trace": cols[8] if len(cols) >= 9 else "",
                            "lane": "",
                            "created_at": created_at,
                            "updated_at": updated_at,
                        }
                    )
            elif in_table and not line.startswith("|"):
                break
        return [row for row in rows if self._iso_on_or_after(row["updated_at"], since_date)]

    def write_backlog_row(self, row: dict) -> None:
        path = self.plan_dir / "_shared" / "backlog.md"
        content = path.read_text()

        row_id = row.get("id", "")
        if row_id == "—":
            row_id = ""
        row_type = row.get("type", "Task")
        row_title = row.get("title", "")

        new_line = (
            f"| {row_id or '—'} | {row_type} | {row.get('use_case', '—')} "
            f"| {row.get('feature', '—')} | {row_title} | {row.get('priority', 'Medium')} "
            f"| {row.get('status', 'to-do')} | {row.get('review_verdict', '—') or '—'} "
            f"| {row.get('route_state', '—') or '—'} | {row.get('release_note_link', '—') or '—'} "
            f"| {row.get('project', '—') or '—'} | {row.get('notes', '—')} | {row.get('automation_trace', '')} "
            f"| {row.get('lane', '—') or '—'} |"
        )
        lines = content.splitlines()
        updated = False

        # Primary lookup: by ID if provided
        if row_id:
            for i, line in enumerate(lines):
                if line.startswith("|") and f"| {row_id} |" in line:
                    lines[i] = new_line
                    updated = True
                    break

        # Fallback lookup: by title + type (matches Notion backend behavior)
        if not updated and row_title:
            for i, line in enumerate(lines):
                if not line.startswith("|") or line.startswith("| ID") or line.startswith("|---"):
                    continue
                cols = [c.strip() for c in line.split("|")[1:-1]]
                if len(cols) >= 7 and cols[1] == row_type and cols[4] == row_title:
                    lines[i] = new_line
                    updated = True
                    break

        if not updated:
            # Find end of table and append
            insert_idx = len(lines)
            in_table = False
            for i, line in enumerate(lines):
                if line.startswith("| ID"):
                    in_table = True
                elif in_table and not line.startswith("|"):
                    insert_idx = i
                    break
            lines.insert(insert_idx, new_line)
        path.write_text("\n".join(lines) + "\n")

    def list_children(self, parent_id: str) -> list[dict]:
        """Return direct child Feature rows for parent_id.

        Local backlog markdown does not persist parent links by default, but this
        method supports rows that include parent_ids to keep behavior aligned with
        cloud backends and test doubles.
        """
        rows = self.read_backlog()
        return [
            row
            for row in rows
            if row.get("type", "").lower() == "feature"
            and parent_id in (row.get("parent_ids") or [])
        ]

    # -- Release Notes --

    def write_release_note(self, version: str, content: str) -> None:
        release_dir = self.plan_dir / "_releases" / version
        release_dir.mkdir(parents=True, exist_ok=True)
        path = release_dir / "release-notes.md"
        path.write_text(content)

    def read_release_note(self, version: str) -> dict:
        path = self.plan_dir / "_releases" / version / "release-notes.md"
        if not path.exists():
            raise KeyError(f"Release note not found: {version}")
        content = path.read_text()
        return {
            "version": version,
            "title": f"{version} Release Notes",
            "content": content,
        }

    def list_release_notes(self) -> list[dict]:
        releases_dir = self.plan_dir / "_releases"
        if not releases_dir.exists():
            return []
        notes = []
        for child in sorted(releases_dir.iterdir()):
            if child.is_dir() and (child / "release-notes.md").exists():
                notes.append({
                    "version": child.name,
                    "title": f"{child.name} Release Notes",
                })
        return notes

    # -- Templates --

    def read_templates(self) -> list[dict]:
        if not self.template_dir.exists():
            return []
        templates = []
        for f in sorted(self.template_dir.glob("*.md")):
            content = f.read_text()
            version = "v1"
            version_match = re.search(r"\(v(\d+)\)", content)
            if version_match:
                version = f"v{version_match.group(1)}"
            templates.append(
                {
                    "name": f.stem if not f.stem.startswith("_") else f.stem.lstrip("_"),
                    "version": version,
                    "content": content,
                }
            )
        return templates

    def write_template(self, name: str, content: str, version: str) -> None:
        self.template_dir.mkdir(parents=True, exist_ok=True)
        filename = f"_{name}.md" if name == "inbox" else f"{name}.md"
        path = self.template_dir / filename
        path.write_text(content)

    # -- Internal helpers --

    @staticmethod
    def _parse_brief(brief_name: str, content: str) -> dict:
        """Extract structured data from brief markdown."""
        data: dict = {"name": brief_name, "raw": content}

        title_match = re.match(r"^#\s+(.+)", content)
        data["title"] = title_match.group(1).strip() if title_match else brief_name

        data["status"] = extract_brief_status(content)
        data["created"] = extract_brief_created(content)
        data["project"] = extract_brief_project(content)
        data.update(parse_brief_sections(content))

        return data

    @staticmethod
    def _render_brief(brief_name: str, data: dict, *, history: list[dict] | None = None) -> str:
        """Render structured brief data to markdown."""
        return render_brief_markdown(brief_name, data, history=history)

    def _brief_history_dir(self, brief_name: str) -> Path:
        return self.plan_dir / brief_name / "_history"

    def _store_brief_revision(
        self,
        brief_name: str,
        snapshot: dict,
        *,
        actor: str = "",
        change_summary: str = "",
    ) -> dict:
        history_dir = self._brief_history_dir(brief_name)
        history_dir.mkdir(parents=True, exist_ok=True)

        revision_id = build_revision_id()
        while (history_dir / f"{revision_id}.md").exists():
            revision_id = build_revision_id()

        metadata = {
            "revision_id": revision_id,
            "captured_at": revision_id,
            "actor": actor or os.environ.get("USER", ""),
            "change_summary": change_summary,
        }
        content = render_revision_markdown(brief_name, snapshot, metadata)
        (history_dir / f"{revision_id}.md").write_text(content)
        return metadata
