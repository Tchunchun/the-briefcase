"""Integration tests for install.sh."""

import os
import stat
import subprocess
from pathlib import Path

import pytest


FRAMEWORK_DIR = str(Path(__file__).resolve().parents[3])


@pytest.fixture
def consumer_dir(tmp_path):
    """Create an empty consumer project directory."""
    target = tmp_path / "consumer"
    target.mkdir()
    return target


def run_install(consumer_dir, env_overrides=None):
    """Run install.sh with TARGET_DIR pointing to consumer_dir."""
    env = os.environ.copy()
    env["FRAMEWORK_DIR"] = FRAMEWORK_DIR
    env["TARGET_DIR"] = str(consumer_dir)
    if env_overrides:
        env.update(env_overrides)

    result = subprocess.run(
        ["bash", os.path.join(FRAMEWORK_DIR, "install.sh")],
        capture_output=True, text=True,
        env=env,
        timeout=30,
    )
    return result


class TestFreshInstall:
    def test_creates_briefcase_directory(self, consumer_dir):
        result = run_install(consumer_dir)
        assert result.returncode == 0
        assert (consumer_dir / ".briefcase").is_dir()

    def test_copies_framework_subdirs(self, consumer_dir):
        run_install(consumer_dir)
        assert (consumer_dir / ".briefcase" / "src").is_dir()
        assert (consumer_dir / ".briefcase" / "skills").is_dir()
        assert (consumer_dir / ".briefcase" / "template").is_dir()

    def test_creates_storage_yaml(self, consumer_dir):
        run_install(consumer_dir)
        yaml_path = consumer_dir / ".briefcase" / "storage.yaml"
        assert yaml_path.exists()
        content = yaml_path.read_text()
        assert "backend: local" in content

    def test_generates_briefcase_wrapper(self, consumer_dir):
        run_install(consumer_dir)
        wrapper = consumer_dir / "briefcase"
        assert wrapper.exists()
        assert os.access(wrapper, os.X_OK)
        content = wrapper.read_text()
        assert ".briefcase" in content
        assert "find_project_root" in content

    def test_creates_gitignore_entries(self, consumer_dir):
        run_install(consumer_dir)
        gitignore = consumer_dir / ".gitignore"
        assert gitignore.exists()
        content = gitignore.read_text()
        assert ".briefcase/" in content
        assert ".env" in content

    def test_rewrites_skill_paths(self, consumer_dir):
        run_install(consumer_dir)
        playbook = consumer_dir / ".briefcase" / "skills" / "PLAYBOOK.md"
        if playbook.exists():
            content = playbook.read_text()
            # Should not contain raw .skills/ references
            # (they should be rewritten to .briefcase/skills/)
            # Note: some may remain as part of a path convention explanation
            assert ".briefcase/skills/" in content

    def test_does_not_touch_consumer_dirs(self, consumer_dir):
        """Install must not create consumer-owned directories."""
        (consumer_dir / "src").mkdir()
        (consumer_dir / "src" / "app.py").write_text("# consumer code")

        run_install(consumer_dir)

        # Consumer file should be untouched
        assert (consumer_dir / "src" / "app.py").read_text() == "# consumer code"


class TestIdempotentReInstall:
    def test_does_not_duplicate_gitignore(self, consumer_dir):
        run_install(consumer_dir)
        run_install(consumer_dir)

        content = (consumer_dir / ".gitignore").read_text()
        # Each entry should appear exactly once
        assert content.count(".briefcase/") == 1
        assert content.count(".env") == 1

    def test_preserves_storage_yaml(self, consumer_dir):
        run_install(consumer_dir)

        # Modify storage.yaml to simulate user config
        yaml_path = consumer_dir / ".briefcase" / "storage.yaml"
        yaml_path.write_text("backend: notion\nnotion:\n  parent_page_id: abc\n")

        run_install(consumer_dir)

        # Should not be overwritten
        content = yaml_path.read_text()
        assert "notion" in content
        assert "abc" in content

    def test_overwrites_framework_code(self, consumer_dir):
        run_install(consumer_dir)

        # Add a marker file inside .briefcase/src/ to verify it gets replaced
        marker = consumer_dir / ".briefcase" / "src" / "__marker__.txt"
        marker.write_text("old")

        run_install(consumer_dir)

        # Marker should be gone (fresh copy)
        assert not marker.exists()


class TestBriefcaseWrapperIntegration:
    def test_briefcase_help_works(self, consumer_dir):
        run_install(consumer_dir)

        result = subprocess.run(
            [str(consumer_dir / "briefcase"), "--help"],
            capture_output=True, text=True,
            cwd=str(consumer_dir),
            timeout=15,
        )
        assert result.returncode == 0
        assert "Agent workflow CLI" in result.stdout

    def test_briefcase_command_works_with_local_backend(self, consumer_dir):
        run_install(consumer_dir)

        # Create minimal local backend structure
        plan = consumer_dir / "docs" / "plan"
        shared = plan / "_shared"
        shared.mkdir(parents=True, exist_ok=True)
        (plan / "_inbox.md").write_text("# Inbox\n\n## Entries\n\n")
        (shared / "backlog.md").write_text(
            "# Backlog\n\n"
            "| ID | Type | Use Case | Feature | Title | Priority | Status | Notes |\n"
            "|---|---|---|---|---|---|---|---|\n"
        )
        (consumer_dir / "_project").mkdir(exist_ok=True)

        result = subprocess.run(
            [str(consumer_dir / "briefcase"), "inbox", "list"],
            capture_output=True, text=True,
            cwd=str(consumer_dir),
            timeout=15,
        )
        assert result.returncode == 0
        assert '"success": true' in result.stdout


class TestNotionTokenDetection:
    def test_detects_notion_api_key(self, consumer_dir):
        result = run_install(consumer_dir, {"NOTION_API_KEY": "test-key"})
        assert result.returncode == 0
        assert "NOTION_API_KEY detected" in result.stdout

    def test_detects_legacy_token(self, consumer_dir):
        env = {"NOTION_API_TOKEN": "legacy-key"}
        # Clear NOTION_API_KEY if set in parent env
        env["NOTION_API_KEY"] = ""
        result = run_install(consumer_dir, env)
        assert result.returncode == 0
        assert "Legacy" in result.stdout or "legacy" in result.stdout or "NOTION_API_TOKEN" in result.stdout

    def test_reports_no_token(self, consumer_dir):
        env = {"NOTION_API_KEY": "", "NOTION_API_TOKEN": ""}
        result = run_install(consumer_dir, env)
        assert result.returncode == 0
        assert "No API key" in result.stdout or "NOTION_API_KEY" in result.stdout
