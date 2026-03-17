"""CLI commands: agent brief list, agent brief read, agent brief write."""

from __future__ import annotations

import click

from src.cli.helpers import get_store_from_dir, output_json, output_error, project_dir_option


@click.group()
def brief():
    """Manage feature briefs."""
    pass


@brief.command(name="list")
@project_dir_option
def brief_list(project_dir: str) -> None:
    """List all briefs as JSON."""
    try:
        store = get_store_from_dir(project_dir)
        data = store.list_briefs()
        output_json(data)
    except Exception as e:
        output_error(str(e))


@brief.command(name="read")
@click.argument("name")
@project_dir_option
def brief_read(name: str, project_dir: str) -> None:
    """Read a brief by name. Returns structured JSON."""
    try:
        store = get_store_from_dir(project_dir)
        data = store.read_brief(name)
        output_json(data)
    except KeyError:
        output_error(f"Brief not found: {name}")
    except Exception as e:
        output_error(str(e))


@brief.command(name="write")
@click.argument("name")
@click.option("--title", default=None, help="Brief title.")
@click.option("--status", default="draft", help="Brief status (default: draft).")
@click.option("--problem", default="", help="Problem statement.")
@click.option("--goal", default="", help="Goal statement.")
@click.option("--acceptance-criteria", "ac", default="", help="Acceptance criteria.")
@click.option("--out-of-scope", "oos", default="", help="Out of scope.")
@click.option("--open-questions", "oq", default="", help="Open questions.")
@click.option("--file", "file_path", default=None, type=click.Path(exists=True), help="Read brief from a markdown file instead of inline options.")
@project_dir_option
def brief_write(
    name: str,
    title: str | None,
    status: str,
    problem: str,
    goal: str,
    ac: str,
    oos: str,
    oq: str,
    file_path: str | None,
    project_dir: str,
) -> None:
    """Create or update a brief. Use --file to import from markdown, or inline options."""
    try:
        store = get_store_from_dir(project_dir)

        if file_path:
            # Parse brief from markdown file
            import re
            content = open(file_path).read()
            data = {"title": title or name, "status": status}
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
            # Extract status from file if present
            status_match = re.search(r"\*\*Status:\s*(\S+)\*\*", content)
            if status_match:
                data["status"] = status_match.group(1)
            # Extract title from heading if not provided
            if not title:
                title_match = re.match(r"^#\s+(.+)", content)
                if title_match:
                    data["title"] = title_match.group(1).strip()
        else:
            data = {
                "title": title or name,
                "status": status,
                "problem": problem,
                "goal": goal,
                "acceptance_criteria": ac,
                "out_of_scope": oos,
                "open_questions": oq,
            }

        store.write_brief(name, data)
        output_json({"written": name, "status": data.get("status", status)})
    except Exception as e:
        output_error(str(e))
