"""CLI commands: agent brief list, agent brief read, agent brief write."""

from __future__ import annotations

import os
import click

from src.cli.helpers import get_store_from_dir, output_json, output_error, project_dir_option
from src.core.storage.briefs import (
    extract_brief_status,
    normalize_inline_brief_value,
    parse_brief_sections,
)


@click.group()
def brief():
    """Manage feature briefs."""
    pass


def _default_actor() -> str:
    return os.environ.get("USER", "")


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
@click.option("--status", default=None, help="Brief status.")
@click.option("--problem", default=None, help="Problem statement.")
@click.option("--goal", default=None, help="Goal statement.")
@click.option("--acceptance-criteria", "ac", default=None, help="Acceptance criteria.")
@click.option(
    "--non-functional-requirements",
    "nfr",
    default=None,
    help="Non-functional requirements.",
)
@click.option("--out-of-scope", "oos", default=None, help="Out of scope.")
@click.option("--open-questions", "oq", default=None, help="Open questions.")
@click.option("--technical-approach", "ta", default=None, help="Technical approach.")
@click.option("--change-summary", default="", help="Optional human summary for the new revision.")
@click.option("--file", "file_path", default=None, type=click.Path(exists=True), help="Read brief from a markdown file instead of inline options.")
@project_dir_option
def brief_write(
    name: str,
    title: str | None,
    status: str | None,
    problem: str | None,
    goal: str | None,
    ac: str | None,
    nfr: str | None,
    oos: str | None,
    oq: str | None,
    ta: str | None,
    change_summary: str,
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
            data = {"title": title or name, "status": status or "draft"}
            data.update(parse_brief_sections(content))
            # Extract status from file if present
            data["status"] = extract_brief_status(content, data["status"])
            # Extract title from heading if not provided
            if not title:
                title_match = re.match(r"^#\s+(.+)", content)
                if title_match:
                    data["title"] = title_match.group(1).strip()
        else:
            try:
                existing = store.read_brief(name)
            except KeyError:
                existing = {}

            data = {
                "title": title if title is not None else existing.get("title", name),
                "status": status if status is not None else existing.get("status", "draft"),
                "problem": (
                    normalize_inline_brief_value(problem)
                    if problem is not None
                    else existing.get("problem", "")
                ),
                "goal": (
                    normalize_inline_brief_value(goal)
                    if goal is not None
                    else existing.get("goal", "")
                ),
                "acceptance_criteria": (
                    normalize_inline_brief_value(ac)
                    if ac is not None
                    else existing.get("acceptance_criteria", "")
                ),
                "non_functional_requirements": (
                    normalize_inline_brief_value(nfr)
                    if nfr is not None
                    else existing.get("non_functional_requirements", "")
                ),
                "out_of_scope": (
                    normalize_inline_brief_value(oos)
                    if oos is not None
                    else existing.get("out_of_scope", "")
                ),
                "open_questions": (
                    normalize_inline_brief_value(oq)
                    if oq is not None
                    else existing.get("open_questions", "")
                ),
                "technical_approach": (
                    normalize_inline_brief_value(ta)
                    if ta is not None
                    else existing.get("technical_approach", "")
                ),
            }

        data["_actor"] = _default_actor()
        data["_change_summary"] = change_summary
        store.write_brief(name, data)
        output_json({"written": name, "status": data.get("status", status or "draft")})
    except Exception as e:
        output_error(str(e))


@brief.command(name="history")
@click.argument("name")
@project_dir_option
def brief_history(name: str, project_dir: str) -> None:
    """List stored revisions for a brief."""
    try:
        store = get_store_from_dir(project_dir)
        data = store.list_brief_revisions(name)
        output_json(data)
    except Exception as e:
        output_error(str(e))


@brief.command(name="revision")
@click.argument("name")
@click.argument("revision_id")
@project_dir_option
def brief_revision(name: str, revision_id: str, project_dir: str) -> None:
    """Read a stored revision for a brief."""
    try:
        store = get_store_from_dir(project_dir)
        data = store.read_brief_revision(name, revision_id)
        output_json(data)
    except KeyError:
        output_error(f"Brief revision not found: {name}@{revision_id}")
    except Exception as e:
        output_error(str(e))


@brief.command(name="restore")
@click.argument("name")
@click.argument("revision_id")
@click.option("--change-summary", default="", help="Optional summary for the restore revision.")
@project_dir_option
def brief_restore(
    name: str,
    revision_id: str,
    change_summary: str,
    project_dir: str,
) -> None:
    """Restore a stored revision into the brief head."""
    try:
        store = get_store_from_dir(project_dir)
        data = store.restore_brief_revision(
            name,
            revision_id,
            actor=_default_actor(),
            change_summary=change_summary,
        )
        output_json(
            {
                "restored": name,
                "revision_id": revision_id,
                "status": data.get("status", ""),
            }
        )
    except KeyError:
        output_error(f"Brief revision not found: {name}@{revision_id}")
    except Exception as e:
        output_error(str(e))
