"""Unit tests for src.core.gitignore — canonical .gitignore policy."""

from pathlib import Path

import pytest

from src.core.gitignore import (
    BASELINE_ENTRIES,
    NOTION_ENTRIES,
    ensure_gitignore,
    entries_for_backend,
)


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """Empty project directory."""
    return tmp_path


class TestEnsureGitignore:
    def test_creates_file_on_fresh_dir(self, project):
        appended = ensure_gitignore(project, BASELINE_ENTRIES)
        gi = project / ".gitignore"
        assert gi.exists()
        content = gi.read_text()
        assert ".briefcase/" in content
        assert ".env" in content
        assert len(appended) == len(BASELINE_ENTRIES)

    def test_skips_existing_entries(self, project):
        gi = project / ".gitignore"
        gi.write_text(".briefcase/\n.env\n")

        appended = ensure_gitignore(project, BASELINE_ENTRIES)
        assert appended == []
        # File should not grow
        assert gi.read_text().count(".briefcase/") == 1

    def test_appends_only_missing_entries(self, project):
        gi = project / ".gitignore"
        gi.write_text("*.pyc\n.briefcase/\n")

        appended = ensure_gitignore(project, BASELINE_ENTRIES)
        assert appended == [".env"]
        content = gi.read_text()
        assert ".env" in content
        assert content.count(".briefcase/") == 1

    def test_idempotent_double_call(self, project):
        ensure_gitignore(project, BASELINE_ENTRIES)
        ensure_gitignore(project, BASELINE_ENTRIES)

        content = (project / ".gitignore").read_text()
        assert content.count(".briefcase/") == 1
        assert content.count(".env") == 1

    def test_never_removes_user_entries(self, project):
        gi = project / ".gitignore"
        gi.write_text("# my custom rules\nnode_modules/\n*.log\n")

        ensure_gitignore(project, BASELINE_ENTRIES)
        content = gi.read_text()
        assert "node_modules/" in content
        assert "*.log" in content

    def test_adds_comment_before_entry(self, project):
        ensure_gitignore(project, BASELINE_ENTRIES)
        content = (project / ".gitignore").read_text()
        assert "# Framework code" in content
        assert "# Environment secrets" in content


class TestEntriesForBackend:
    def test_local_returns_baseline_only(self):
        entries = entries_for_backend("local")
        patterns = [e[0] for e in entries]
        assert ".briefcase/" in patterns
        assert ".env" in patterns
        assert "docs/plan/" not in patterns

    def test_notion_returns_baseline_plus_docs_plan(self):
        entries = entries_for_backend("notion")
        patterns = [e[0] for e in entries]
        assert ".briefcase/" in patterns
        assert ".env" in patterns
        assert "docs/plan/" in patterns

    def test_notion_entries_not_in_baseline(self):
        """NOTION_ENTRIES must not contain broad ignores like 'docs/'."""
        for pattern, _ in NOTION_ENTRIES:
            assert pattern != "docs/"
