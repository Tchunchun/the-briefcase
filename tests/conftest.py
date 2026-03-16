"""Shared pytest fixtures for all tests."""

import pytest
from pathlib import Path


@pytest.fixture
def project_root(tmp_path):
    """Create a minimal project directory structure for testing.

    Returns the root path. Includes:
    - _project/ (empty, for config files)
    - docs/plan/_shared/ (for backlog)
    - docs/plan/_inbox.md (seeded)
    - template/ (with brief.md and tasks.md)
    """
    (tmp_path / "_project").mkdir()
    plan = tmp_path / "docs" / "plan"
    shared = plan / "_shared"
    shared.mkdir(parents=True)

    (plan / "_inbox.md").write_text(
        "# Inbox\n\n## Entries\n\n"
    )
    (shared / "backlog.md").write_text(
        "# Backlog\n\n"
        "| ID | Type | Use Case | Feature | Title | Priority | Status | Notes |\n"
        "|---|---|---|---|---|---|---|---|\n"
    )

    tpl = tmp_path / "template"
    tpl.mkdir()
    (tpl / "brief.md").write_text("# {Feature Name} (v3)\n\n**Status: draft**\n")
    (tpl / "tasks.md").write_text("# Tasks (v2)\n")
    (tpl / "_inbox.md").write_text("# Inbox\n")

    return tmp_path
