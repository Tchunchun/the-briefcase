"""Local filesystem backend for artifact storage.

Reads and writes markdown files at canonical paths:
- docs/plan/_inbox.md
- docs/plan/{brief_name}/brief.md
- _project/decisions.md
- docs/plan/_shared/backlog.md
- template/{name}.md
"""

from __future__ import annotations

import re
from pathlib import Path


class LocalBackend:
    """ArtifactStore implementation backed by local markdown files."""

    def __init__(self, project_root: str | Path) -> None:
        self.root = Path(project_root)
        self.plan_dir = self.root / "docs" / "plan"
        self.project_dir = self.root / "_project"
        self.template_dir = self.root / "template"

    # -- Inbox --

    def read_inbox(self) -> list[dict]:
        path = self.plan_dir / "_inbox.md"
        if not path.exists():
            return []
        content = path.read_text()
        entries = []
        for line in content.splitlines():
            match = re.match(
                r"^- \[(?P<type>[^\]]+)\]\s*(?P<text>.+?)(?:\s+\[-> (?P<status>[^\]]+)\])?(?:\s+\u2192\s.+)?$",
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
                    "text": title.strip(),
                    "status": match.group("status") or "new",
                    "notes": notes.strip(),
                }
                entries.append(entry)
        return entries

    def append_inbox(self, entry: dict) -> None:
        path = self.plan_dir / "_inbox.md"
        entry_type = entry.get("type", "idea")
        text = entry["text"]
        notes = entry.get("notes", "")
        if notes:
            line = f"- [{entry_type}] {text} \u2014 {notes}\n"
        else:
            line = f"- [{entry_type}] {text}\n"
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
        content = self._render_brief(brief_name, data)
        path.write_text(content)

    def list_briefs(self) -> list[dict]:
        briefs = []
        if not self.plan_dir.exists():
            return briefs
        for child in sorted(self.plan_dir.iterdir()):
            brief_file = child / "brief.md"
            if child.is_dir() and not child.name.startswith("_") and brief_file.exists():
                content = brief_file.read_text()
                status = "draft"
                status_match = re.search(
                    r"\*\*Status:\s*(\S+)\*\*", content
                )
                if status_match:
                    status = status_match.group(1)
                title_match = re.match(r"^#\s+(.+)", content)
                title = title_match.group(1) if title_match else child.name
                briefs.append(
                    {"name": child.name, "status": status, "title": title}
                )
        return briefs

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

    def read_backlog(self) -> list[dict]:
        path = self.plan_dir / "_shared" / "backlog.md"
        if not path.exists():
            return []
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
                if len(cols) >= 8:
                    rows.append(
                        {
                            "id": cols[0],
                            "type": cols[1],
                            "use_case": cols[2],
                            "feature": cols[3],
                            "title": cols[4],
                            "priority": cols[5],
                            "status": cols[6],
                            "notes": cols[7],
                        }
                    )
            elif in_table and not line.startswith("|"):
                break
        return rows

    def write_backlog_row(self, row: dict) -> None:
        path = self.plan_dir / "_shared" / "backlog.md"
        content = path.read_text()
        row_id = row["id"]
        new_line = (
            f"| {row['id']} | {row['type']} | {row.get('use_case', '—')} "
            f"| {row['feature']} | {row['title']} | {row['priority']} "
            f"| {row['status']} | {row.get('notes', '—')} |"
        )
        lines = content.splitlines()
        updated = False
        for i, line in enumerate(lines):
            if line.startswith("|") and f"| {row_id} |" in line:
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

        status_match = re.search(r"\*\*Status:\s*(\S+)\*\*", content)
        data["status"] = status_match.group(1) if status_match else "draft"

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

        return data

    @staticmethod
    def _render_brief(brief_name: str, data: dict) -> str:
        """Render structured brief data to markdown."""
        status = data.get("status", "draft")
        lines = [
            f"# {data.get('title', brief_name)}",
            "",
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
        return "\n".join(lines) + "\n"
