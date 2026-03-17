"""E2E test: Local backend consumer project workflow.

Simulates a consumer project using the local (default) storage backend.
Creates a temporary project directory, runs setup, and exercises every
ArtifactStore operation through the factory.

Run:
    python3 -m pytest tests/e2e/test_local_workflow.py -v
"""

import shutil
from pathlib import Path

import pytest
import yaml

from src.core.storage.config import load_config
from src.core.storage.factory import get_store
from src.core.storage.protocol import ArtifactStore


@pytest.fixture
def consumer_project(tmp_path):
    """Bootstrap a consumer project with templates and directory structure."""
    root = tmp_path / "my-project"
    root.mkdir()

    # Copy templates from upstream
    upstream_templates = Path(__file__).resolve().parents[2] / "template"
    shutil.copytree(upstream_templates, root / "template")

    # Create directory structure
    (root / "_project").mkdir()
    plan = root / "docs" / "plan"
    (plan / "_shared").mkdir(parents=True)

    # Seed initial files from templates
    shutil.copy(root / "template" / "_inbox.md", plan / "_inbox.md")
    shutil.copy(root / "template" / "backlog.md", plan / "_shared" / "backlog.md")

    # Create decisions.md
    (root / "_project" / "decisions.md").write_text(
        "# Decisions Log\n\n"
        "| ID | Date | Decision | Why | Alternatives Rejected | ADR |\n"
        "|---|---|---|---|---|---|\n"
    )

    # Run setup via config save (simulates `agent setup --backend local`)
    from src.core.storage.config import StorageConfig, save_config
    save_config(StorageConfig(backend="local"), root / "_project")

    return root


class TestLocalWorkflowE2E:
    """End-to-end local backend workflow: setup → CRUD → verify on disk."""

    def test_step1_config_loads_and_factory_returns_local_backend(self, consumer_project):
        config = load_config(consumer_project / "_project")
        store = get_store(config, str(consumer_project))
        assert config.backend == "local"
        assert isinstance(store, ArtifactStore)
        assert type(store).__name__ == "LocalBackend"

    def test_step2_inbox_append_and_read(self, consumer_project):
        store = get_store(load_config(consumer_project / "_project"), str(consumer_project))

        store.append_inbox({"type": "idea", "text": "Add dark mode support"})
        store.append_inbox({"type": "bug", "text": "Login fails on Safari"})
        store.append_inbox({"type": "tech-debt", "text": "Refactor auth module"})

        entries = store.read_inbox()
        types = [e["type"] for e in entries]
        assert "idea" in types
        assert "bug" in types
        assert "tech-debt" in types
        assert any("dark mode" in e["text"] for e in entries)

    def test_step3_brief_write_read_list(self, consumer_project):
        store = get_store(load_config(consumer_project / "_project"), str(consumer_project))

        store.write_brief("dark-mode", {
            "title": "Dark Mode Support",
            "status": "draft",
            "problem": "Users strain their eyes at night.",
            "goal": "Provide a toggle-able dark mode.",
            "acceptance_criteria": "- [ ] Dark mode toggle\n- [ ] Respects OS setting",
            "out_of_scope": "- Custom theme editor",
            "open_questions": "- CSS variables or Tailwind dark:?",
        })

        brief = store.read_brief("dark-mode")
        assert brief["name"] == "dark-mode"
        assert brief["status"] == "draft"
        assert "eyes" in brief["problem"]

        briefs = store.list_briefs()
        assert any(b["name"] == "dark-mode" for b in briefs)

    def test_step4_decisions_append_and_read(self, consumer_project):
        store = get_store(load_config(consumer_project / "_project"), str(consumer_project))

        store.append_decision({
            "id": "D-001",
            "date": "2026-03-16",
            "title": "Use Tailwind dark: prefix",
            "why": "Works with existing setup",
            "alternatives_rejected": "CSS variables",
            "adr_link": "—",
        })

        decisions = store.read_decisions()
        assert len(decisions) >= 1
        assert decisions[-1]["id"] == "D-001"

    def test_step5_backlog_write_and_update(self, consumer_project):
        store = get_store(load_config(consumer_project / "_project"), str(consumer_project))

        store.write_backlog_row({
            "id": "T-001", "type": "Feature", "use_case": "Dark mode",
            "feature": "dark-mode", "title": "Add toggle",
            "priority": "High", "status": "To Do", "notes": "—",
        })
        store.write_backlog_row({
            "id": "T-002", "type": "Feature", "use_case": "OS sync",
            "feature": "dark-mode", "title": "Detect OS preference",
            "priority": "Medium", "status": "To Do", "notes": "—",
        })

        rows = store.read_backlog()
        assert len(rows) >= 2

        # Update T-001 status
        store.write_backlog_row({
            "id": "T-001", "type": "Feature", "use_case": "Dark mode",
            "feature": "dark-mode", "title": "Add toggle",
            "priority": "High", "status": "In Progress", "notes": "Started",
        })
        rows = store.read_backlog()
        t001 = next(r for r in rows if r["id"] == "T-001")
        assert t001["status"] == "In Progress"

    def test_step6_templates_read(self, consumer_project):
        store = get_store(load_config(consumer_project / "_project"), str(consumer_project))

        templates = store.read_templates()
        names = [t["name"] for t in templates]
        assert "brief" in names
        assert "tasks" in names
        assert len(templates) >= 9

    def test_step7_files_exist_on_disk(self, consumer_project):
        store = get_store(load_config(consumer_project / "_project"), str(consumer_project))

        # Write artifacts so files are created
        store.append_inbox({"type": "idea", "text": "Disk check"})
        store.write_brief("disk-check", {
            "title": "Disk Check", "status": "draft",
            "problem": "Test", "goal": "Test",
            "acceptance_criteria": "- [ ] Test",
        })

        assert (consumer_project / "_project" / "storage.yaml").exists()
        assert (consumer_project / "docs" / "plan" / "_inbox.md").exists()
        assert (consumer_project / "docs" / "plan" / "disk-check" / "brief.md").exists()

    def test_step8_release_notes_write_read_list(self, consumer_project):
        store = get_store(load_config(consumer_project / "_project"), str(consumer_project))

        store.write_release_note("v0.1.0", "# v0.1.0\n\nInitial release.\n")
        store.write_release_note("v0.2.0", "# v0.2.0\n\nBug fixes.\n")

        note = store.read_release_note("v0.1.0")
        assert note["version"] == "v0.1.0"
        assert "Initial release" in note["content"]

        notes = store.list_release_notes()
        versions = [n["version"] for n in notes]
        assert "v0.1.0" in versions
        assert "v0.2.0" in versions

        # Overwrite and verify
        store.write_release_note("v0.1.0", "# v0.1.0\n\nUpdated.\n")
        note = store.read_release_note("v0.1.0")
        assert "Updated" in note["content"]

        # Verify on disk
        path = consumer_project / "docs" / "plan" / "_releases" / "v0.1.0" / "release-notes.md"
        assert path.exists()

    def test_step9_config_roundtrip(self, consumer_project):
        config = load_config(consumer_project / "_project")
        assert config.backend == "local"
        assert config.notion is None

        config_path = consumer_project / "_project" / "storage.yaml"
        data = yaml.safe_load(config_path.read_text())
        assert data["backend"] == "local"
