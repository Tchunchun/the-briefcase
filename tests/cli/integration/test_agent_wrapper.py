"""Integration tests for the ./briefcase entry point wrapper."""

import os
import stat
import subprocess
from pathlib import Path

import pytest

from src.core.storage.config import save_config, StorageConfig


@pytest.fixture
def consumer_project(tmp_path):
    """Create a simulated consumer project with .briefcase/ layout."""
    root = tmp_path / "myproject"
    root.mkdir()

    # Create .briefcase/ with framework code
    briefcase = root / ".briefcase"
    briefcase.mkdir()

    # Copy src/ into .briefcase/src/
    import shutil
    src_origin = Path(__file__).resolve().parents[3] / "src"
    shutil.copytree(src_origin, briefcase / "src")

    # Create storage.yaml inside .briefcase/
    save_config(StorageConfig(backend="local"), briefcase)

    # Create _project/ for consumer docs (minimal)
    (root / "_project").mkdir()

    # Create local backend structure
    plan = root / "docs" / "plan"
    shared = plan / "_shared"
    shared.mkdir(parents=True)
    (plan / "_inbox.md").write_text("# Inbox\n\n## Entries\n\n")
    (shared / "backlog.md").write_text(
        "# Backlog\n\n"
        "| ID | Type | Use Case | Feature | Title | Priority | Status | Notes |\n"
        "|---|---|---|---|---|---|---|---|\n"
    )

    # Create template/
    (root / "template").mkdir()

    # Generate ./briefcase wrapper from template
    template_path = Path(__file__).resolve().parents[3] / "template" / "briefcase.sh"
    wrapper = root / "briefcase"
    wrapper.write_text(template_path.read_text())
    wrapper.chmod(wrapper.stat().st_mode | stat.S_IEXEC)

    return root


class TestAgentWrapper:
    def test_wrapper_is_executable(self, consumer_project):
        wrapper = consumer_project / "briefcase"
        assert wrapper.exists()
        assert os.access(wrapper, os.X_OK)

    def test_wrapper_shows_help(self, consumer_project):
        result = subprocess.run(
            ["./briefcase", "--help"],
            capture_output=True, text=True,
            cwd=str(consumer_project),
            timeout=15,
        )
        assert result.returncode == 0
        assert "Agent workflow CLI" in result.stdout

    def test_wrapper_runs_inbox_list(self, consumer_project):
        result = subprocess.run(
            ["./briefcase", "inbox", "list"],
            capture_output=True, text=True,
            cwd=str(consumer_project),
            timeout=15,
        )
        assert result.returncode == 0
        assert '"success": true' in result.stdout

    def test_wrapper_works_from_subdirectory(self, consumer_project):
        subdir = consumer_project / "src" / "deep"
        subdir.mkdir(parents=True)

        # Need to use absolute path to wrapper since we're in subdir
        wrapper = consumer_project / "briefcase"
        result = subprocess.run(
            [str(wrapper), "--help"],
            capture_output=True, text=True,
            cwd=str(subdir),
            timeout=15,
        )
        # Should find .briefcase/ by walking up and show help
        assert result.returncode == 0
        assert "Agent workflow CLI" in result.stdout

    def test_wrapper_fails_outside_project(self, tmp_path):
        """Wrapper outside any project should fail with clear error."""
        # Create a wrapper in a directory with no .briefcase/
        empty = tmp_path / "nowhere"
        empty.mkdir()

        template_path = Path(__file__).resolve().parents[3] / "template" / "briefcase.sh"
        wrapper = empty / "briefcase"
        wrapper.write_text(template_path.read_text())
        wrapper.chmod(wrapper.stat().st_mode | stat.S_IEXEC)

        result = subprocess.run(
            ["./briefcase", "--help"],
            capture_output=True, text=True,
            cwd=str(empty),
            timeout=15,
        )
        assert result.returncode != 0
        assert "not inside an initialized project" in result.stderr or ".briefcase" in result.stderr
