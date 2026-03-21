"""Unit tests for the framework self-updater."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from src.core.updater import Updater, _parse_version, _version_gte
from src.core.manifest import write_version, build_manifest, write_manifest


# --- Version parsing ---


class TestVersionParsing:
    def test_parse_simple(self):
        assert _parse_version("0.8.0") == (0, 8, 0)

    def test_parse_with_v_prefix(self):
        assert _parse_version("v0.8.0") == (0, 8, 0)

    def test_version_gte_equal(self):
        assert _version_gte("0.8.0", "0.8.0") is True

    def test_version_gte_greater(self):
        assert _version_gte("0.9.0", "0.8.0") is True

    def test_version_gte_less(self):
        assert _version_gte("0.7.0", "0.8.0") is False

    def test_version_gte_patch(self):
        assert _version_gte("0.8.1", "0.8.0") is True


# --- Updater with local source ---


@pytest.fixture
def framework_source(tmp_path):
    """Create a mock framework source directory."""
    source = tmp_path / "framework"
    source.mkdir()
    (source / "src").mkdir()
    (source / "src" / "main.py").write_text("print('v2')")
    (source / "skills").mkdir()
    (source / "skills" / "SKILL.md").write_text("# Skill v2")
    (source / "template").mkdir()
    (source / "template" / "brief.md").write_text("# Brief v2")
    (source / "pyproject.toml").write_text('version = "0.9.0"\n')
    return source


@pytest.fixture
def consumer_project(tmp_path, framework_source):
    """Create a consumer project with .briefcase/ installed at v0.8.0."""
    project = tmp_path / "consumer"
    project.mkdir()
    bc = project / ".briefcase"
    bc.mkdir()
    (bc / "src").mkdir()
    (bc / "src" / "main.py").write_text("print('v1')")
    (bc / "skills").mkdir()
    (bc / "skills" / "SKILL.md").write_text("# Skill v1")
    (bc / "template").mkdir()
    (bc / "template" / "brief.md").write_text("# Brief v1")
    (bc / "pyproject.toml").write_text('version = "0.8.0"\n')

    write_version(bc, "0.8.0")
    manifest = build_manifest(bc, "0.8.0")
    write_manifest(bc, manifest)

    # Consumer-owned files that must not be touched
    (project / "AGENTS.md").write_text("# Consumer AGENTS")
    (project / "CLAUDE.md").write_text("# Consumer CLAUDE")
    (project / "_project").mkdir()
    (project / "_project" / "storage.yaml").write_text("backend: local\n")

    return project


class TestUpdaterCheck:
    def test_check_detects_update_available(self, consumer_project, framework_source):
        updater = Updater(consumer_project, source_dir=str(framework_source))
        info = updater.check()
        assert info.current_version == "0.8.0"
        assert info.latest_version == "0.9.0"
        assert info.is_up_to_date is False

    def test_check_up_to_date(self, consumer_project, framework_source):
        # Set current version to match source
        write_version(consumer_project / ".briefcase", "0.9.0")
        updater = Updater(consumer_project, source_dir=str(framework_source))
        info = updater.check()
        assert info.is_up_to_date is True

    def test_check_detects_customizations(self, consumer_project, framework_source):
        # Modify a framework file in the consumer
        (consumer_project / ".briefcase" / "src" / "main.py").write_text("custom!")
        updater = Updater(consumer_project, source_dir=str(framework_source))
        info = updater.check()
        assert "src/main.py" in info.customized_files

    def test_check_no_version_file(self, consumer_project, framework_source):
        (consumer_project / ".briefcase" / "VERSION").unlink()
        updater = Updater(consumer_project, source_dir=str(framework_source))
        info = updater.check()
        assert info.current_version is None
        assert info.is_up_to_date is False


class TestUpdaterApply:
    def test_apply_updates_files(self, consumer_project, framework_source):
        updater = Updater(consumer_project, source_dir=str(framework_source))
        result = updater.apply()
        assert result.success is True
        assert result.version == "0.9.0"
        assert result.files_updated > 0

        # Verify files were updated
        bc = consumer_project / ".briefcase"
        assert bc.joinpath("src", "main.py").read_text() == "print('v2')"
        assert bc.joinpath("skills", "SKILL.md").read_text() != "# Skill v1"

    def test_apply_writes_new_version(self, consumer_project, framework_source):
        updater = Updater(consumer_project, source_dir=str(framework_source))
        updater.apply()
        from src.core.manifest import read_version
        assert read_version(consumer_project / ".briefcase") == "0.9.0"

    def test_apply_writes_new_manifest(self, consumer_project, framework_source):
        updater = Updater(consumer_project, source_dir=str(framework_source))
        updater.apply()
        from src.core.manifest import read_manifest
        manifest = read_manifest(consumer_project / ".briefcase")
        assert manifest is not None
        assert manifest["version"] == "0.9.0"

    def test_apply_preserves_consumer_files(self, consumer_project, framework_source):
        updater = Updater(consumer_project, source_dir=str(framework_source))
        updater.apply()
        assert (consumer_project / "AGENTS.md").read_text() == "# Consumer AGENTS"
        assert (consumer_project / "CLAUDE.md").read_text() == "# Consumer CLAUDE"
        assert (consumer_project / "_project" / "storage.yaml").exists()

    def test_apply_rejects_customizations_without_force(
        self, consumer_project, framework_source
    ):
        (consumer_project / ".briefcase" / "src" / "main.py").write_text("custom!")
        updater = Updater(consumer_project, source_dir=str(framework_source))
        result = updater.apply(force=False)
        assert result.success is False
        assert "customized" in result.message.lower()

    def test_apply_force_overwrites_customizations(
        self, consumer_project, framework_source
    ):
        (consumer_project / ".briefcase" / "src" / "main.py").write_text("custom!")
        updater = Updater(consumer_project, source_dir=str(framework_source))
        result = updater.apply(force=True)
        assert result.success is True
        assert (consumer_project / ".briefcase" / "src" / "main.py").read_text() == "print('v2')"

    def test_apply_up_to_date_returns_success(self, consumer_project, framework_source):
        write_version(consumer_project / ".briefcase", "0.9.0")
        updater = Updater(consumer_project, source_dir=str(framework_source))
        result = updater.apply()
        assert result.success is True
        assert "up to date" in result.message.lower()

    def test_apply_rewrites_skill_paths(self, consumer_project, framework_source):
        # Add a skill file with bare skills/ reference
        (framework_source / "skills" / "SKILL.md").write_text(
            "See skills/ideation/SKILL.md for details"
        )
        updater = Updater(consumer_project, source_dir=str(framework_source))
        updater.apply()
        content = (consumer_project / ".briefcase" / "skills" / "SKILL.md").read_text()
        assert ".briefcase/skills/" in content

    def test_apply_detects_notion_backend_for_schema_check(
        self, consumer_project, framework_source
    ):
        (consumer_project / "_project" / "storage.yaml").write_text("backend: notion\n")
        updater = Updater(consumer_project, source_dir=str(framework_source))
        result = updater.apply()
        assert result.schema_check_needed is True


class TestUpdaterInstallShIntegration:
    def test_install_writes_version_file(self, tmp_path):
        """After install.sh runs, .briefcase/VERSION should exist."""
        import os
        import subprocess

        framework_dir = str(Path(__file__).resolve().parents[3])
        consumer = tmp_path / "consumer"
        consumer.mkdir()

        env = os.environ.copy()
        env["FRAMEWORK_DIR"] = framework_dir
        env["TARGET_DIR"] = str(consumer)

        result = subprocess.run(
            ["bash", os.path.join(framework_dir, "install.sh")],
            capture_output=True, text=True, env=env, timeout=30,
        )
        assert result.returncode == 0

        version_file = consumer / ".briefcase" / "VERSION"
        assert version_file.exists()
        version = version_file.read_text().strip()
        assert version  # non-empty
        # Version should match pyproject.toml
        import re
        pyproject = Path(framework_dir) / "pyproject.toml"
        match = re.search(r'version\s*=\s*"([^"]+)"', pyproject.read_text())
        assert match
        assert version == match.group(1)

    def test_install_writes_manifest(self, tmp_path):
        """After install.sh runs, .briefcase/manifest.json should exist."""
        import os
        import subprocess

        framework_dir = str(Path(__file__).resolve().parents[3])
        consumer = tmp_path / "consumer"
        consumer.mkdir()

        env = os.environ.copy()
        env["FRAMEWORK_DIR"] = framework_dir
        env["TARGET_DIR"] = str(consumer)

        subprocess.run(
            ["bash", os.path.join(framework_dir, "install.sh")],
            capture_output=True, text=True, env=env, timeout=30,
        )

        manifest_file = consumer / ".briefcase" / "manifest.json"
        assert manifest_file.exists()
        manifest = json.loads(manifest_file.read_text())
        assert "version" in manifest
        assert "files" in manifest
        assert len(manifest["files"]) > 0
