"""CLI commands: agent brief list, agent brief read, agent brief write, agent brief migrate."""

from __future__ import annotations

import os
import re
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


def _tokenize(value: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]+", (value or "").lower()) if token}


def _build_notion_url(value: str) -> str:
    compact = "".join(ch for ch in value if ch.isalnum())
    if len(compact) != 32:
        return ""
    return f"https://www.notion.so/{compact.lower()}"


def _idea_match_score(
    idea_title: str, brief_name: str, brief_title: str, *, idea_status: str = ""
) -> float:
    idea_tokens = _tokenize(idea_title)
    if not idea_tokens:
        return 0.0
    target_tokens = _tokenize(brief_name) | _tokenize(brief_title)
    if not target_tokens:
        return 0.0
    overlap = idea_tokens & target_tokens
    if not overlap:
        return 0.0
    # Use the better of both directions to handle asymmetric token counts
    score = max(
        len(overlap) / max(1, len(target_tokens)),
        len(overlap) / max(1, len(idea_tokens)),
    )
    # Boost ideas at exploring status — they're the most likely link target
    if idea_status == "exploring":
        score = min(score * 1.15, 1.0)
    return score


def _resolve_idea_row(
    store,
    *,
    idea_id: str,
    idea_title: str,
    brief_name: str,
    brief_title: str,
) -> tuple[dict | None, str]:
    rows = store.read_backlog()
    ideas = [row for row in rows if row.get("type", "").lower() == "idea"]
    if not ideas:
        return None, "no idea rows found"

    if idea_id:
        for row in ideas:
            candidate_id = row.get("notion_id") or row.get("id") or ""
            if candidate_id == idea_id:
                return row, "matched by idea id"
        raise ValueError(f"Idea not found for --link-idea-id '{idea_id}'.")

    if idea_title:
        for row in ideas:
            if row.get("title", "") == idea_title:
                return row, "matched by idea title"
        raise ValueError(f"Idea not found for --link-idea-title '{idea_title}'.")

    scored: list[tuple[float, dict]] = []
    for row in ideas:
        if row.get("brief_link"):
            continue
        idea_status = row.get("status", "")
        score = _idea_match_score(
            row.get("title", ""), brief_name, brief_title, idea_status=idea_status
        )
        if score > 0:
            scored.append((score, row))
    if not scored:
        return None, "no unlinked idea title matched brief"

    scored.sort(key=lambda item: item[0], reverse=True)
    best_score, best_row = scored[0]
    second_score = scored[1][0] if len(scored) > 1 else 0.0
    if best_score < 0.5 or (best_score - second_score) < 0.2:
        return None, "ambiguous idea match; provide --link-idea-id or --link-idea-title"
    return best_row, "matched by title token overlap"


def _link_brief_to_idea(
    store,
    *,
    brief_name: str,
    brief_title: str,
    brief_url: str,
    idea_id: str,
    idea_title: str,
) -> dict:
    if not brief_url:
        return {"idea_linked": False, "link_reason": "brief has no notion url"}

    idea_row, reason = _resolve_idea_row(
        store,
        idea_id=idea_id,
        idea_title=idea_title,
        brief_name=brief_name,
        brief_title=brief_title,
    )
    if idea_row is None:
        return {"idea_linked": False, "link_reason": reason}

    updated_row = dict(idea_row)
    updated_row["brief_link"] = brief_url
    store.write_backlog_row(updated_row)
    return {
        "idea_linked": True,
        "linked_idea_title": updated_row.get("title", ""),
        "linked_idea_id": updated_row.get("notion_id") or updated_row.get("id", ""),
        "link_reason": reason,
    }


def _group_briefs_by_date(briefs: list[dict]) -> list[dict]:
    grouped: dict[str, list[dict]] = {}
    for brief in briefs:
        date_value = brief.get("date", "") or "unknown"
        grouped.setdefault(date_value, []).append(brief)
    return [
        {"date": date_value, "briefs": grouped[date_value]}
        for date_value in sorted(grouped.keys(), reverse=True)
    ]


def _format_briefs_human(groups: list[dict]) -> str:
    """Format brief groups as human-readable terminal output."""
    lines: list[str] = []
    # Find max name length for alignment
    max_name = 0
    for group in groups:
        for b in group["briefs"]:
            max_name = max(max_name, len(b.get("name", "")))
    col_width = max(max_name + 4, 30)

    for group in groups:
        date_str = group["date"]
        lines.append(f"── {date_str} " + "─" * max(0, 48 - len(date_str)))
        for b in group["briefs"]:
            name = b.get("name", "")
            status = b.get("status", "")
            lines.append(f"  {name:<{col_width}}{status}")
        lines.append("")  # blank line between groups
    return "\n".join(lines).rstrip()


@brief.command(name="list")
@project_dir_option
def brief_list(project_dir: str) -> None:
    """List all briefs grouped by date."""
    try:
        store = get_store_from_dir(project_dir)
        data = store.list_briefs()
        groups = _group_briefs_by_date(data)
        click.echo(_format_briefs_human(groups))
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
@click.option("--link-idea-id", default="", help="Idea notion_id/id to attach this brief URL to.")
@click.option("--link-idea-title", default="", help="Idea title to attach this brief URL to.")
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
    link_idea_id: str,
    link_idea_title: str,
    project_dir: str,
) -> None:
    """Create or update a brief. Use --file to import from markdown, or inline options."""
    try:
        if link_idea_id and link_idea_title:
            raise ValueError("Use only one of --link-idea-id or --link-idea-title.")

        store = get_store_from_dir(project_dir)

        if file_path:
            # Parse brief from markdown file
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
        output_data = {
            "written": name,
            "status": data.get("status", status or "draft"),
        }
        try:
            written_brief = store.read_brief(name)
            brief_title = written_brief.get("title", data.get("title", name))
            brief_url = (
                written_brief.get("notion_url", "")
                or _build_notion_url(written_brief.get("notion_id", ""))
            )
            if brief_url:
                output_data["notion_url"] = brief_url

            link_data = _link_brief_to_idea(
                store,
                brief_name=name,
                brief_title=brief_title,
                brief_url=brief_url,
                idea_id=link_idea_id,
                idea_title=link_idea_title,
            )
            output_data.update(link_data)
        except Exception as exc:  # noqa: BLE001
            if link_idea_id or link_idea_title:
                raise
            output_data["idea_linked"] = False
            output_data["link_reason"] = str(exc)

        output_json(output_data)
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


@brief.command(name="migrate")
@click.option("--dry-run", is_flag=True, default=False, help="Report what would happen without making changes.")
@project_dir_option
def brief_migrate(dry_run: bool, project_dir: str) -> None:
    """Migrate briefs from legacy container page to a Notion database."""
    from pathlib import Path

    from src.core.storage.config import load_config, resolve_config_dir, save_config
    from src.integrations.notion.client import NotionClient
    from src.integrations.notion.schemas import DATABASE_REGISTRY
    from src.migrations.briefs_to_database import migrate_briefs_to_database

    try:
        root = Path(project_dir).resolve()
        config_dir = resolve_config_dir(root)
        config = load_config(config_dir)

        if not config.is_notion() or config.notion is None:
            output_error("Brief migration requires the Notion backend. Current backend: local.")
            return

        dbs = config.notion.databases
        briefs_page_id = dbs.get("briefs", "")
        briefs_db_id = dbs.get("briefs_db", "")

        if not briefs_page_id and not briefs_db_id:
            output_error(
                "No briefs page or briefs_db found in config. "
                "Run `briefcase setup --backend notion` first."
            )
            return

        if briefs_db_id and not briefs_page_id:
            output_error("Already using briefs database — nothing to migrate.")
            return

        client = NotionClient()

        # Provision briefs database if it doesn't exist yet
        if not briefs_db_id:
            if dry_run:
                click.echo("Would create Briefs database and migrate briefs.")
                briefs_db_id = "<dry-run-placeholder>"
            else:
                schema = DATABASE_REGISTRY["briefs_db"]
                new_db = client.create_database(
                    config.notion.parent_page_id,
                    "Briefs",
                    schema["properties"],
                    icon=schema.get("icon", "📋"),
                )
                briefs_db_id = new_db["id"]
                click.echo(f"Created Briefs database: {briefs_db_id}")

        result = migrate_briefs_to_database(
            client, briefs_page_id, briefs_db_id, dry_run=dry_run,
        )

        # Persist briefs_db to config after successful migration
        if not dry_run and result["migrated"] and not dbs.get("briefs_db"):
            config.notion.databases["briefs_db"] = briefs_db_id
            save_config(config, config_dir)
            click.echo(f"Updated storage config with briefs_db: {briefs_db_id}")

        output_json(result)
    except Exception as e:
        output_error(str(e))
