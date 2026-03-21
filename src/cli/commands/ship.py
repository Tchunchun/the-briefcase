"""CLI command: briefcase ship — safe merge-to-main with rebase + test + push."""

from __future__ import annotations

import subprocess
import sys

import click


@click.command()
@click.argument("branch", default="main")
@click.option("--skip-tests", is_flag=True, default=False, help="Skip test run (not recommended).")
def ship(branch: str, skip_tests: bool) -> None:
    """Safely merge current branch to target branch with rebase, test, and push.

    Sequence: warn on dirty working directory → git pull --rebase → pytest → git push.
    Aborts on test failure so broken code never reaches the target branch.
    """
    # 1. Warn if working directory has uncommitted changes
    status_result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True, text=True,
    )
    if status_result.stdout.strip():
        click.echo("⚠ Working directory has uncommitted changes:")
        for line in status_result.stdout.strip().splitlines()[:10]:
            click.echo(f"  {line}")
        remaining = len(status_result.stdout.strip().splitlines()) - 10
        if remaining > 0:
            click.echo(f"  ... and {remaining} more")
        click.echo()

    # 2. Get current branch
    current_branch = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True, text=True,
    ).stdout.strip()

    # If on a feature branch, checkout target branch and merge
    if current_branch != branch:
        click.echo(f"Switching from {current_branch} to {branch}...")
        result = subprocess.run(["git", "checkout", branch], capture_output=True, text=True)
        if result.returncode != 0:
            click.echo(f"Failed to checkout {branch}: {result.stderr.strip()}", err=True)
            sys.exit(1)

        click.echo(f"Merging {current_branch} into {branch}...")
        result = subprocess.run(
            ["git", "merge", current_branch],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            click.echo(f"Merge failed:\n{result.stderr.strip()}", err=True)
            click.echo(f"Returning to {current_branch}...")
            subprocess.run(["git", "merge", "--abort"], capture_output=True)
            subprocess.run(["git", "checkout", current_branch], capture_output=True)
            sys.exit(1)

    # 3. Rebase on remote
    click.echo(f"Rebasing on origin/{branch}...")
    result = subprocess.run(
        ["git", "pull", "--rebase", "origin", branch],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        click.echo(f"Rebase failed:\n{result.stderr.strip()}", err=True)
        click.echo("Resolve conflicts, then run `briefcase ship` again.")
        sys.exit(1)
    click.echo("Rebase successful.")

    # 4. Run tests
    if skip_tests:
        click.echo("Skipping tests (--skip-tests).")
    else:
        click.echo("Running tests...")
        test_result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "--ignore=tests/e2e", "-x", "-q"],
            capture_output=True, text=True,
        )
        if test_result.returncode != 0:
            click.echo("Tests failed — aborting push.\n", err=True)
            # Show last 20 lines of test output for context
            lines = test_result.stdout.strip().splitlines()
            for line in lines[-20:]:
                click.echo(f"  {line}", err=True)
            if test_result.stderr.strip():
                click.echo(test_result.stderr.strip(), err=True)
            sys.exit(1)
        # Show summary line
        lines = test_result.stdout.strip().splitlines()
        if lines:
            click.echo(f"  {lines[-1]}")

    # 5. Push
    click.echo(f"Pushing to origin/{branch}...")
    result = subprocess.run(
        ["git", "push", "origin", branch],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        click.echo(f"Push failed:\n{result.stderr.strip()}", err=True)
        sys.exit(1)

    click.echo(f"Shipped to {branch}.")
