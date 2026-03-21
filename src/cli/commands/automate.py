"""CLI commands for workflow automation helpers."""

from __future__ import annotations

import json
import os
import shlex
import subprocess
from typing import Any

import click

from src.cli.helpers import get_store_from_dir, output_json, output_error, project_dir_option
from src.core.automation.architect_review import ArchitectReviewAutomationService
from src.core.automation.fix_cycle import FixCycleAutomationService
from src.core.automation.implementation_ready import ImplementationReadyAutomationService
from src.core.automation.review_ready import ReviewReadyAutomationService
from src.core.automation.ship_routing import ShipRoutingAutomationService
from src.core.automation.ship_dispatch import ShipDispatchAutomationService
from src.core.automation.idea_close import IdeaCloseAutomationService


@click.group()
def automate():
    """Run narrow workflow automation helpers."""
    pass


@automate.command(name="architect-review")
@click.option("--dry-run", is_flag=True, help="Compute dispatches without writing trace notes.")
@click.option(
    "--notes-only",
    is_flag=True,
    help="Write trace notes and return dispatch payloads without executing a shell command.",
)
@click.option(
    "--dispatch-command",
    default="",
    help=(
        "Shell command template used to invoke the architect flow. "
        "Supports placeholders like {brief_name}, {feature_title}, and {dispatch_token}. "
        "Defaults to AGENT_ARCHITECT_COMMAND."
    ),
)
@project_dir_option
def automate_architect_review(
    dry_run: bool,
    notes_only: bool,
    dispatch_command: str,
    project_dir: str,
) -> None:
    """Detect new architect-review entries and dispatch the architect flow."""
    try:
        store = get_store_from_dir(project_dir)
        command_template = dispatch_command or os.environ.get("AGENT_ARCHITECT_COMMAND", "")
        dispatcher = None if notes_only else _build_dispatcher(
            command_template,
            project_dir,
            "Architect",
            store=store,
            phase="architect-review",
        )
        service = ArchitectReviewAutomationService(store, dispatcher=dispatcher)
        output_json(service.scan(apply=not dry_run))
    except Exception as e:
        output_error(str(e))


def _find_backlog_row(store, *, item_type: str, title: str, item_id: str = "") -> dict | None:
    for row in store.read_backlog():
        if item_id:
            candidate_id = row.get("notion_id") or row.get("id") or ""
            if candidate_id == item_id:
                return row
        if row.get("type", "") == item_type and row.get("title", "") == title:
            return row
    return None


def _write_backlog_update(store, row: dict, **changes: Any) -> dict:
    updated = dict(row)
    updated.update(changes)
    store.write_backlog_row(updated)
    return updated


def _build_notion_url(value: str) -> str:
    compact = "".join(ch for ch in value if ch.isalnum())
    if len(compact) != 32:
        return ""
    return f"https://www.notion.so/{compact.lower()}"


def _extract_structured_dispatch_data(dispatch_result: dict | None) -> dict[str, Any]:
    if not dispatch_result:
        return {}

    structured: dict[str, Any] = {}
    for key in (
        "review_verdict",
        "release_note_link",
        "feature_status",
        "release_version",
        "route_state",
    ):
        if key in dispatch_result:
            structured[key] = dispatch_result[key]

    stdout = (dispatch_result.get("stdout") or "").strip()
    if not stdout:
        return structured

    try:
        parsed = json.loads(stdout)
    except json.JSONDecodeError:
        return structured

    if isinstance(parsed, dict) and isinstance(parsed.get("data"), dict):
        parsed = parsed["data"]

    if not isinstance(parsed, dict):
        return structured

    for key in (
        "review_verdict",
        "release_note_link",
        "feature_status",
        "release_version",
        "route_state",
    ):
        if key in parsed and key not in structured:
            structured[key] = parsed[key]
    return structured


def _resolve_release_note_link(store, dispatch_result: dict | None, feature_row: dict) -> str:
    structured = _extract_structured_dispatch_data(dispatch_result)
    if structured.get("release_note_link"):
        return str(structured["release_note_link"])
    if feature_row.get("release_note_link"):
        return str(feature_row["release_note_link"])

    release_version = structured.get("release_version")
    if not release_version:
        return ""

    try:
        note = store.read_release_note(str(release_version))
    except Exception:
        return ""

    if note.get("notion_url"):
        return str(note["notion_url"])
    if note.get("notion_id"):
        return _build_notion_url(str(note["notion_id"]))
    return ""


def _find_feature_row(store, payload: dict) -> dict | None:
    return _find_backlog_row(
        store,
        item_type="Feature",
        title=payload.get("feature_title", ""),
        item_id=payload.get("feature_id", ""),
    )


def _find_child_tasks(store, payload: dict, feature_row: dict) -> list[dict]:
    feature_id = payload.get("feature_id", "") or feature_row.get("notion_id", "")
    brief_name = payload.get("brief_name", "")
    tasks: list[dict] = []
    for row in store.read_backlog():
        if row.get("type", "") != "Task":
            continue
        if feature_id and feature_id in (row.get("parent_ids") or []):
            tasks.append(row)
            continue
        if brief_name and row.get("feature", "") == brief_name:
            tasks.append(row)
    return tasks


def _run_pre_dispatch_hooks(store, phase: str, payload: dict) -> None:
    if phase == "implementation-ready":
        feature_row = _find_feature_row(store, payload)
        if feature_row and feature_row.get("status") == "implementation-ready":
            _write_backlog_update(store, feature_row, status="in-progress")
        return

    if phase == "fix-cycle":
        feature_row = _find_feature_row(store, payload)
        if feature_row and feature_row.get("status") == "review-ready":
            _write_backlog_update(
                store,
                feature_row,
                status="in-progress",
                route_state="returned",
            )
        return


def _run_command_template(
    command_template: str,
    project_dir: str,
    label: str,
    payload: dict,
) -> dict:
    safe_payload = {
        k: shlex.quote(str(v)) if isinstance(v, str) else v
        for k, v in payload.items()
    }
    command = command_template.format(**safe_payload)
    result = subprocess.run(
        shlex.split(command),
        shell=False,
        cwd=project_dir,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"{label} dispatch failed ({result.returncode}): "
            f"{result.stderr.strip() or result.stdout.strip() or command}"
        )
    result_data = {
        "command": command,
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
    }
    result_data.update(_extract_structured_dispatch_data(result_data))
    return result_data


def _run_post_dispatch_hooks(
    store,
    phase: str,
    payload: dict,
    *,
    project_dir: str,
    fix_command_template: str,
    dispatch_result: dict | None = None,
) -> dict | None:
    feature_row = _find_feature_row(store, payload)
    if not feature_row:
        return None

    structured = _extract_structured_dispatch_data(dispatch_result)

    def apply_updates(**changes: Any) -> dict:
        nonlocal feature_row
        filtered = {
            key: value
            for key, value in changes.items()
            if value is not None and feature_row.get(key) != value
        }
        if filtered:
            feature_row = _write_backlog_update(store, feature_row, **filtered)
        return feature_row

    if phase == "architect-review":
        brief_name = payload.get("brief_name", "")
        if not brief_name:
            return None
        try:
            brief = store.read_brief(brief_name)
        except KeyError:
            return None
        if (
            brief.get("status") == "implementation-ready"
            and feature_row.get("status") == "architect-review"
        ):
            apply_updates(status="implementation-ready", route_state="routed")
            return None
        apply_updates(route_state="routed")
        return None

    if phase == "implementation-ready":
        tasks = _find_child_tasks(store, payload, feature_row)
        if (
            tasks
            and all(task.get("status") == "done" for task in tasks)
            and feature_row.get("status") == "in-progress"
        ):
            apply_updates(status="review-ready", route_state="routed")
            return None
        apply_updates(route_state="routed")
        return None

    if phase == "review-ready":
        review_verdict = (structured.get("review_verdict") or feature_row.get("review_verdict") or "").strip()
        if (
            review_verdict == "accepted"
            and feature_row.get("status") == "review-ready"
        ):
            apply_updates(
                status="review-accepted",
                review_verdict="accepted",
                route_state="routed",
            )
            return None
        if review_verdict == "changes-requested":
            if feature_row.get("status") != "in-progress":
                feature_row = apply_updates(
                    status="in-progress",
                    review_verdict="changes-requested",
                    route_state="returned",
                )
            else:
                feature_row = apply_updates(
                    review_verdict="changes-requested",
                    route_state="returned",
                )
            if not fix_command_template:
                raise RuntimeError(
                    "Review requested changes but no implementation dispatch command is configured."
                )
            return _run_command_template(
                fix_command_template,
                project_dir,
                "Implementation",
                payload,
            )
        apply_updates(route_state="routed")
        return None

    if phase == "fix-cycle":
        apply_updates(route_state="returned")
        return None

    if phase == "ship-routing":
        apply_updates(route_state="routed")
        return None

    if phase == "ship-dispatch":
        release_note_link = _resolve_release_note_link(store, dispatch_result, feature_row)
        apply_updates(
            route_state="routed",
            release_note_link=release_note_link or None,
        )
        return None

    return None

def _build_dispatcher(
    command_template: str,
    project_dir: str,
    label: str,
    *,
    store,
    phase: str,
    fix_command_template: str = "",
):
    """Build a safe shell dispatcher from a command template, or return None."""
    if not command_template:
        return None

    def dispatch(payload: dict) -> dict:
        _run_pre_dispatch_hooks(store, phase, payload)
        dispatch_result = _run_command_template(command_template, project_dir, label, payload)
        follow_up_dispatch = _run_post_dispatch_hooks(
            store,
            phase,
            payload,
            project_dir=project_dir,
            fix_command_template=fix_command_template,
            dispatch_result=dispatch_result,
        )
        if follow_up_dispatch is not None:
            dispatch_result["follow_up_dispatch"] = follow_up_dispatch
        return dispatch_result

    return dispatch


@automate.command(name="implementation-ready")
@click.option("--dry-run", is_flag=True, help="Compute dispatches without writing trace notes.")
@click.option("--notes-only", is_flag=True, help="Write trace notes without executing a shell command.")
@click.option("--dispatch-command", default="", help="Shell command template. Defaults to AGENT_IMPLEMENTATION_COMMAND.")
@project_dir_option
def automate_implementation_ready(
    dry_run: bool,
    notes_only: bool,
    dispatch_command: str,
    project_dir: str,
) -> None:
    """Detect new implementation-ready entries and dispatch the implementation flow."""
    try:
        store = get_store_from_dir(project_dir)
        command_template = dispatch_command or os.environ.get("AGENT_IMPLEMENTATION_COMMAND", "")
        dispatcher = None if notes_only else _build_dispatcher(
            command_template,
            project_dir,
            "Implementation",
            store=store,
            phase="implementation-ready",
        )
        service = ImplementationReadyAutomationService(store, dispatcher=dispatcher)
        output_json(service.scan(apply=not dry_run))
    except Exception as e:
        output_error(str(e))


@automate.command(name="review-ready")
@click.option("--dry-run", is_flag=True, help="Compute dispatches without writing trace notes.")
@click.option("--notes-only", is_flag=True, help="Write trace notes without executing a shell command.")
@click.option("--dispatch-command", default="", help="Shell command template. Defaults to AGENT_REVIEW_COMMAND.")
@click.option(
    "--fix-dispatch-command",
    default="",
    help="Shell command template for rejected reviews. Defaults to AGENT_IMPLEMENTATION_COMMAND.",
)
@project_dir_option
def automate_review_ready(
    dry_run: bool,
    notes_only: bool,
    dispatch_command: str,
    fix_dispatch_command: str,
    project_dir: str,
) -> None:
    """Detect new review-ready entries and dispatch the review flow."""
    try:
        store = get_store_from_dir(project_dir)
        command_template = dispatch_command or os.environ.get("AGENT_REVIEW_COMMAND", "")
        fix_command_template = fix_dispatch_command or os.environ.get("AGENT_IMPLEMENTATION_COMMAND", "")
        dispatcher = None if notes_only else _build_dispatcher(
            command_template,
            project_dir,
            "Review",
            store=store,
            phase="review-ready",
            fix_command_template=fix_command_template,
        )
        service = ReviewReadyAutomationService(store, dispatcher=dispatcher)
        output_json(service.scan(apply=not dry_run))
    except Exception as e:
        output_error(str(e))


@automate.command(name="fix-cycle-dispatch")
@click.option("--dry-run", is_flag=True, help="Compute dispatches without writing trace notes.")
@click.option("--notes-only", is_flag=True, help="Write trace notes without executing a shell command.")
@click.option(
    "--dispatch-command",
    default="",
    help=(
        "Shell command template for the fix-cycle implementation run. "
        "Supports placeholders like {brief_name}, {feature_title}, and {dispatch_token}. "
        "Defaults to AGENT_FIX_CYCLE_COMMAND."
    ),
)
@project_dir_option
def automate_fix_cycle_dispatch(
    dry_run: bool,
    notes_only: bool,
    dispatch_command: str,
    project_dir: str,
) -> None:
    """Detect review-ready features with changes-requested verdict and dispatch a fix cycle."""
    try:
        store = get_store_from_dir(project_dir)
        command_template = dispatch_command or os.environ.get("AGENT_FIX_CYCLE_COMMAND", "")
        dispatcher = None if notes_only else _build_dispatcher(
            command_template,
            project_dir,
            "Fix-cycle",
            store=store,
            phase="fix-cycle",
        )
        service = FixCycleAutomationService(store, dispatcher=dispatcher)
        output_json(service.scan(apply=not dry_run))
    except Exception as e:
        output_error(str(e))


@automate.command(name="ship-routing")
@click.option("--dry-run", is_flag=True, help="Compute dispatches without writing trace notes.")
@click.option("--notes-only", is_flag=True, help="Write trace notes without executing a shell command.")
@click.option(
    "--dispatch-command",
    default="",
    help=(
        "Shell command template for the delivery-manager ship phase. "
        "Supports placeholders like {brief_name}, {feature_title}, and {dispatch_token}. "
        "Defaults to AGENT_SHIP_COMMAND."
    ),
)
@project_dir_option
def automate_ship_routing(
    dry_run: bool,
    notes_only: bool,
    dispatch_command: str,
    project_dir: str,
) -> None:
    """Detect review-accepted features and dispatch the delivery-manager ship phase."""
    try:
        store = get_store_from_dir(project_dir)
        command_template = dispatch_command or os.environ.get("AGENT_SHIP_COMMAND", "")
        dispatcher = None if notes_only else _build_dispatcher(
            command_template,
            project_dir,
            "Ship-routing",
            store=store,
            phase="ship-routing",
        )
        service = ShipRoutingAutomationService(store, dispatcher=dispatcher)
        output_json(service.scan(apply=not dry_run))
    except Exception as e:
        output_error(str(e))


@automate.command(name="ship-dispatch")
@click.option("--dry-run", is_flag=True, help="Compute dispatches without writing trace notes.")
@click.option("--notes-only", is_flag=True, help="Write trace notes without executing a shell command.")
@click.option(
    "--dispatch-command",
    default="",
    help=(
        "Shell command template for the implementation ship wrap-up. "
        "Supports placeholders like {brief_name}, {feature_title}, and {dispatch_token}. "
        "Defaults to AGENT_SHIP_COMMAND."
    ),
)
@project_dir_option
def automate_ship_dispatch(
    dry_run: bool,
    notes_only: bool,
    dispatch_command: str,
    project_dir: str,
) -> None:
    """Detect review-accepted features and dispatch the ship wrap-up phase."""
    try:
        store = get_store_from_dir(project_dir)
        command_template = dispatch_command or os.environ.get("AGENT_SHIP_COMMAND", "")
        dispatcher = None if notes_only else _build_dispatcher(
            command_template,
            project_dir,
            "Ship-dispatch",
            store=store,
            phase="ship-dispatch",
        )
        service = ShipDispatchAutomationService(store, dispatcher=dispatcher)
        output_json(service.scan(apply=not dry_run))
    except Exception as e:
        output_error(str(e))


@automate.command(name="idea-close")
@click.option("--dry-run", is_flag=True, help="Compute dispatches without writing trace notes.")
@click.option("--notes-only", is_flag=True, help="Write trace notes without executing a shell command.")
@click.option(
    "--dispatch-command",
    default="",
    help=(
        "Shell command template for the delivery-manager idea close. "
        "Supports placeholders like {parent_idea_title}, {feature_title}, and {dispatch_token}. "
        "Defaults to AGENT_IDEA_CLOSE_COMMAND."
    ),
)
@project_dir_option
def automate_idea_close(
    dry_run: bool,
    notes_only: bool,
    dispatch_command: str,
    project_dir: str,
) -> None:
    """Detect done features and dispatch the delivery-manager idea close."""
    try:
        store = get_store_from_dir(project_dir)
        command_template = dispatch_command or os.environ.get("AGENT_IDEA_CLOSE_COMMAND", "")
        dispatcher = None if notes_only else _build_dispatcher(
            command_template,
            project_dir,
            "Idea-close",
            store=store,
            phase="idea-close",
        )
        service = IdeaCloseAutomationService(store, dispatcher=dispatcher)
        output_json(service.scan(apply=not dry_run))
    except Exception as e:
        output_error(str(e))
