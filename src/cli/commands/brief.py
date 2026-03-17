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
    project_dir: str,
) -> None:
    """Create or update a brief."""
    try:
        store = get_store_from_dir(project_dir)
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
        output_json({"written": name, "status": status})
    except Exception as e:
        output_error(str(e))
