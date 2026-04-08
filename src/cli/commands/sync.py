"""CLI commands: sync local/notion (Notion backend) and sync push/pull (git backend)."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import click
import yaml

from src.sync.to_local import sync_to_local, sync_templates_to_local


@click.group()
def sync():
    """Sync artifacts between cloud backend and local files."""
    pass


@sync.command(name="local")
@click.option("--dry-run", is_flag=True, help="Preview changes without writing.")
@click.option(
    "--project-dir",
    type=click.Path(exists=True, file_okay=False, resolve_path=True),
    default=".",
    help="Project root directory.",
)
def sync_local(dry_run: bool, project_dir: str) -> None:
    """Pull from cloud backend to local markdown files (Notion → local)."""
    try:
        result = sync_to_local(project_dir, dry_run=dry_run)
    except ValueError as e:
        raise click.ClickException(str(e))

    if dry_run:
        click.echo("[dry-run] No files were written.\n")

    # Warn about conflicts
    conflicts = result.get("conflicts", [])
    if conflicts:
        click.echo(
            click.style(
                f"\n⚠ {len(conflicts)} file(s) changed locally since last sync:",
                fg="yellow",
            )
        )
        for c in conflicts:
            click.echo(f"  - {c}")
        click.echo(
            "  These files were overwritten by the pull. "
            "Check the snapshot branch for previous versions.\n"
        )

    click.echo(f"Sync complete:")
    click.echo(f"  Fetched:  {result['fetched']}")
    click.echo(f"  Created:  {result['created']}")
    click.echo(f"  Skipped:  {result['skipped']}")
    click.echo(f"  Failed:   {result['failed']}")

    snapshot = result.get("snapshot_hash")
    if snapshot:
        click.echo(f"  Snapshot: {snapshot[:12]}")

    if result["failed"] > 0:
        raise click.ClickException(
            f"{result['failed']} item(s) failed to sync. Check logs."
        )


@sync.command(name="notion")
@click.option("--dry-run", is_flag=True, help="Preview changes without writing.")
@click.option(
    "--project-dir",
    type=click.Path(exists=True, file_okay=False, resolve_path=True),
    default=".",
    help="Project root directory.",
)
def sync_notion(dry_run: bool, project_dir: str) -> None:
    """Push local markdown files to cloud backend (local → Notion)."""
    from src.sync.to_notion import sync_to_notion

    try:
        result = sync_to_notion(project_dir, dry_run=dry_run)
    except ValueError as e:
        raise click.ClickException(str(e))

    if dry_run:
        click.echo("[dry-run] No changes were pushed.\n")

    click.echo(f"Push complete:")
    click.echo(f"  Pushed:   {result['pushed']}")
    click.echo(f"  Skipped:  {result['skipped']}")
    click.echo(f"  Failed:   {result['failed']}")

    if result["failed"] > 0:
        raise click.ClickException(
            f"{result['failed']} item(s) failed to push. Check logs."
        )


@sync.command(name="templates")
@click.option("--dry-run", is_flag=True, help="Preview changes without writing.")
@click.option(
    "--project-dir",
    type=click.Path(exists=True, file_okay=False, resolve_path=True),
    default=".",
    help="Project root directory.",
)
def sync_templates(dry_run: bool, project_dir: str) -> None:
    """Pull updated templates from the cloud backend to local template/ files."""
    try:
        result = sync_templates_to_local(project_dir, dry_run=dry_run)
    except ValueError as e:
        raise click.ClickException(str(e))

    if dry_run:
        click.echo("[dry-run] No files were written.\n")

    click.echo(f"Template sync complete:")
    click.echo(f"  Fetched:  {result['fetched']}")
    click.echo(f"  Updated:  {result['updated']}")
    click.echo(f"  Skipped:  {result['skipped']}")
    click.echo(f"  Failed:   {result['failed']}")


@sync.command(name="push")
@click.option("--dry-run", is_flag=True, help="Preview changes without committing or pushing.")
@click.option(
    "--project-dir",
    type=click.Path(exists=True, file_okay=False, resolve_path=True),
    default=".",
    help="Project root directory.",
)
def sync_push(dry_run: bool, project_dir: str) -> None:
    """Stage and push artifacts to git remote (git backend only)."""
    from pathlib import Path

    from src.core.storage.config import load_config, resolve_config_dir
    from src.sync.git_sync import GitSyncError, git_sync_from_config

    config = load_config(resolve_config_dir(Path(project_dir)))
    if not config.is_git():
        raise click.ClickException(
            "sync push is only available for the git backend. "
            f"Current backend: '{config.backend}'."
        )

    syncer = git_sync_from_config(project_dir, config)

    try:
        result = syncer.push(dry_run=dry_run)
    except GitSyncError as e:
        raise click.ClickException(str(e))

    if dry_run:
        click.echo(f"[dry-run] {result['message']}")
        if result.get("files"):
            for f in result["files"]:
                click.echo(f"  {f}")
    else:
        click.echo(result["message"])


@sync.command(name="pull")
@click.option("--dry-run", is_flag=True, help="Preview incoming changes without applying them.")
@click.option(
    "--project-dir",
    type=click.Path(exists=True, file_okay=False, resolve_path=True),
    default=".",
    help="Project root directory.",
)
def sync_pull(dry_run: bool, project_dir: str) -> None:
    """Fetch and merge artifacts from git remote (git backend only)."""
    from pathlib import Path

    from src.core.storage.config import load_config, resolve_config_dir
    from src.sync.git_sync import GitSyncError, git_sync_from_config

    config = load_config(resolve_config_dir(Path(project_dir)))
    if not config.is_git():
        raise click.ClickException(
            "sync pull is only available for the git backend. "
            f"Current backend: '{config.backend}'."
        )

    syncer = git_sync_from_config(project_dir, config)

    try:
        result = syncer.pull(dry_run=dry_run)
    except GitSyncError as e:
        raise click.ClickException(str(e))

    if result["conflicts"]:
        click.echo(f"⚠️  {result['message']}", err=True)
        for f in result["conflicts"]:
            click.echo(f"  conflict: {f}", err=True)
        raise click.ClickException("Pull aborted due to conflicts.")

    if dry_run:
        click.echo(f"[dry-run] {result['message']}")
        for f in result["incoming"]:
            click.echo(f"  {f}")
    else:
        click.echo(result["message"])


@sync.command(name="shakedown-git")
@click.option("--brief-name", default="", help="Brief slug to verify in the clean consumer.")
@click.option("--feature-title", default="", help="Feature title to verify in the clean consumer backlog.")
@click.option("--expected-status", default="", help="Expected feature status after pull.")
@click.option(
    "--expected-review-verdict",
    default="",
    type=click.Choice(["", "pending", "accepted", "changes-requested"], case_sensitive=False),
    help="Expected review verdict after pull.",
)
@click.option(
    "--expected-route-state",
    default="",
    type=click.Choice(["", "routed", "returned", "blocked"], case_sensitive=False),
    help="Expected route state after pull.",
)
@click.option(
    "--expected-lane",
    default="",
    type=click.Choice(["", "quick-fix", "small", "feature"], case_sensitive=False),
    help="Expected lane after pull.",
)
@click.option(
    "--expected-release-note-link",
    default="",
    help="Expected release note link after pull.",
)
@click.option(
    "--expected-automation-trace-contains",
    default="",
    help="Substring that must appear in automation_trace after pull.",
)
@click.option(
    "--keep-consumer",
    is_flag=True,
    help="Keep the temporary clean consumer workspace for inspection.",
)
@click.option(
    "--project-dir",
    type=click.Path(exists=True, file_okay=False, resolve_path=True),
    default=".",
    help="Project root directory.",
)
def sync_shakedown_git(
    brief_name: str,
    feature_title: str,
    expected_status: str,
    expected_review_verdict: str,
    expected_route_state: str,
    expected_lane: str,
    expected_release_note_link: str,
    expected_automation_trace_contains: str,
    keep_consumer: bool,
    project_dir: str,
) -> None:
    """Push current git artifacts, pull into a clean consumer, and verify roundtrip reads."""
    from src.cli.helpers import get_store_from_dir
    from src.core.storage.config import load_config, resolve_config_dir
    from src.sync.git_sync import GitSyncError, git_sync_from_config

    project_root = Path(project_dir).resolve()
    config = load_config(resolve_config_dir(project_root))
    if not config.is_git() or config.git is None:
        raise click.ClickException(
            "sync shakedown-git is only available for the git backend. "
            f"Current backend: '{config.backend}'."
        )

    syncer = git_sync_from_config(project_root, config)
    consumer_dir = Path(tempfile.mkdtemp(prefix="briefcase-git-shakedown."))
    summary: dict[str, object] = {
        "consumer_dir": str(consumer_dir),
        "push": None,
        "pull": None,
        "brief": None,
        "feature_row": None,
        "checks": [],
    }

    try:
        push_result = syncer.push(dry_run=False)
        summary["push"] = push_result

        consumer_project = consumer_dir / "_project"
        consumer_project.mkdir(parents=True, exist_ok=True)
        shakedown_config = {
            "backend": "git",
            "git": {
                "remote": config.git.remote,
                "remote_url": config.git.remote_url,
                "branch": config.git.branch,
                "project_slug": config.git.project_slug,
                "paths": list(config.git.paths),
            },
        }
        (consumer_project / "storage.yaml").write_text(yaml.safe_dump(shakedown_config, sort_keys=False))

        consumer_syncer = git_sync_from_config(consumer_dir, config)
        pull_result = consumer_syncer.pull(dry_run=False)
        summary["pull"] = pull_result

        consumer_store = get_store_from_dir(str(consumer_dir))

        if brief_name:
            summary["brief"] = consumer_store.read_brief(brief_name)

        feature_row = None
        if feature_title:
            backlog_rows = consumer_store.read_backlog()
            feature_row = next(
                (row for row in backlog_rows if row.get("title") == feature_title),
                None,
            )
            if feature_row is None:
                raise click.ClickException(
                    f"Feature not found in clean consumer backlog: {feature_title}"
                )
            summary["feature_row"] = feature_row

        checks: list[str] = []
        if feature_row is not None and expected_status:
            _assert_expected(feature_row.get("status", ""), expected_status, "status")
            checks.append("status")
        if feature_row is not None and expected_review_verdict:
            _assert_expected(
                feature_row.get("review_verdict", ""),
                expected_review_verdict,
                "review_verdict",
            )
            checks.append("review_verdict")
        if feature_row is not None and expected_route_state:
            _assert_expected(
                feature_row.get("route_state", ""),
                expected_route_state,
                "route_state",
            )
            checks.append("route_state")
        if feature_row is not None and expected_lane:
            _assert_expected(feature_row.get("lane", ""), expected_lane, "lane")
            checks.append("lane")
        if feature_row is not None and expected_release_note_link:
            _assert_expected(
                feature_row.get("release_note_link", ""),
                expected_release_note_link,
                "release_note_link",
            )
            checks.append("release_note_link")
        if feature_row is not None and expected_automation_trace_contains:
            trace_value = feature_row.get("automation_trace", "") or ""
            if expected_automation_trace_contains not in trace_value:
                raise click.ClickException(
                    "automation_trace mismatch: expected substring "
                    f"{expected_automation_trace_contains!r}, got {trace_value!r}"
                )
            checks.append("automation_trace")

        summary["checks"] = checks
        summary["success"] = True
        if not keep_consumer:
            summary["consumer_dir_cleaned"] = True
        click.echo(yaml.safe_dump(summary, sort_keys=False))
    except GitSyncError as e:
        raise click.ClickException(str(e))
    finally:
        if not keep_consumer:
            shutil.rmtree(consumer_dir, ignore_errors=True)


def _assert_expected(actual: str, expected: str, field_name: str) -> None:
    if actual != expected:
        raise click.ClickException(
            f"{field_name} mismatch: expected {expected!r}, got {actual!r}"
        )

