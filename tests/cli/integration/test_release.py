"""Tests for the agent release CLI command (local backend)."""

import json
import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner

from src.cli.main import cli
from src.core.storage.config import StorageConfig, save_config


@pytest.fixture
def project(tmp_path):
    root = tmp_path / "project"
    root.mkdir()

    # Copy templates from upstream
    upstream_templates = Path(__file__).resolve().parents[3] / "template"
    shutil.copytree(upstream_templates, root / "template")

    # Create directory structure
    (root / "_project").mkdir()
    plan = root / "docs" / "plan"
    (plan / "_shared").mkdir(parents=True)
    (plan / "_releases").mkdir(parents=True)

    # Seed required files
    shutil.copy(root / "template" / "_inbox.md", plan / "_inbox.md")
    shutil.copy(root / "template" / "backlog.md", plan / "_shared" / "backlog.md")
    (root / "_project" / "decisions.md").write_text(
        "# Decisions Log\n\n"
        "| ID | Date | Decision | Why | Alternatives Rejected | ADR |\n"
        "|---|---|---|---|---|---|\n"
    )

    save_config(StorageConfig(backend="local"), root / "_project")
    return root


@pytest.fixture
def runner():
    return CliRunner()


def test_release_write_and_read(runner, project):
    result = runner.invoke(
        cli,
        ["release", "write", "--version", "v0.5.0", "--notes", "# v0.5.0\n\nNew feature.", "--project-dir", str(project)],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["success"] is True
    assert data["data"]["written"] == "v0.5.0"

    result = runner.invoke(
        cli,
        ["release", "read", "--version", "v0.5.0", "--project-dir", str(project)],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["success"] is True
    assert data["data"]["version"] == "v0.5.0"
    assert "New feature" in data["data"]["content"]


def test_release_list(runner, project):
    # Write two release notes
    for v in ["v0.1.0", "v0.2.0"]:
        runner.invoke(
            cli,
            ["release", "write", "--version", v, "--notes", f"# {v}\n\nRelease.", "--project-dir", str(project)],
        )

    result = runner.invoke(
        cli,
        ["release", "list", "--project-dir", str(project)],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["success"] is True
    versions = [n["version"] for n in data["data"]]
    assert "v0.1.0" in versions
    assert "v0.2.0" in versions


def test_release_read_not_found(runner, project):
    result = runner.invoke(
        cli,
        ["release", "read", "--version", "v99.0.0", "--project-dir", str(project)],
    )
    assert result.exit_code != 0
    assert "not found" in result.output.lower() or "not found" in (result.stderr or "").lower()


def test_release_write_overwrites(runner, project):
    runner.invoke(
        cli,
        ["release", "write", "--version", "v0.5.0", "--notes", "Original.", "--project-dir", str(project)],
    )
    runner.invoke(
        cli,
        ["release", "write", "--version", "v0.5.0", "--notes", "Updated.", "--project-dir", str(project)],
    )
    result = runner.invoke(
        cli,
        ["release", "read", "--version", "v0.5.0", "--project-dir", str(project)],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "Updated" in data["data"]["content"]
    assert "Original" not in data["data"]["content"]


def test_release_list_empty(runner, project):
    result = runner.invoke(
        cli,
        ["release", "list", "--project-dir", str(project)],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["success"] is True
    assert data["data"] == []


# ---------------------------------------------------------------------------
# Version bump tests
# ---------------------------------------------------------------------------

def test_release_write_bumps_pyproject(runner, project):
    """release write auto-bumps pyproject.toml when present."""
    pyproject = project / "pyproject.toml"
    pyproject.write_text('[project]\nname = "my-pkg"\nversion = "0.1.0"\n')

    result = runner.invoke(
        cli,
        ["release", "write", "--version", "v0.5.0", "--notes", "New.", "--project-dir", str(project)],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["data"]["version_bumped"] is True
    assert '0.5.0' in pyproject.read_text()


def test_release_write_no_pyproject(runner, project):
    """release write succeeds and reports version_bumped=False when pyproject.toml absent."""
    result = runner.invoke(
        cli,
        ["release", "write", "--version", "v0.5.0", "--notes", "New.", "--project-dir", str(project)],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["data"]["version_bumped"] is False


def test_release_check_version_in_sync(runner, project):
    """check-version reports in_sync=True when pyproject matches latest release."""
    pyproject = project / "pyproject.toml"
    pyproject.write_text('[project]\nname = "my-pkg"\nversion = "0.5.0"\n')

    runner.invoke(
        cli,
        ["release", "write", "--version", "v0.5.0", "--notes", "New.", "--project-dir", str(project)],
    )
    result = runner.invoke(
        cli,
        ["release", "check-version", "--project-dir", str(project)],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["data"]["in_sync"] is True
    assert data["data"]["latest_release"] == "v0.5.0"


def test_release_check_version_out_of_sync(runner, project):
    """check-version reports in_sync=False when pyproject is behind latest release."""
    pyproject = project / "pyproject.toml"
    pyproject.write_text('[project]\nname = "my-pkg"\nversion = "0.1.0"\n')

    runner.invoke(
        cli,
        ["release", "write", "--version", "v0.5.0", "--notes", "New.", "--project-dir", str(project)],
    )
    # Manually reset pyproject to old version to simulate drift
    pyproject.write_text('[project]\nname = "my-pkg"\nversion = "0.1.0"\n')

    result = runner.invoke(
        cli,
        ["release", "check-version", "--project-dir", str(project)],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["data"]["in_sync"] is False
    assert data["data"]["pyproject_version"] == "0.1.0"
    assert data["data"]["latest_release"] == "v0.5.0"
