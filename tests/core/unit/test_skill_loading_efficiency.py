"""Regression tests for the two-layer skill-loading architecture.

Validates that:
- Shared cross-role rules live only in PLAYBOOK.md (always-on layer).
- Role SKILL.md files reference PLAYBOOK.md instead of duplicating shared content.
- install.sh supports native skill discovery via the .skills symlink step.
"""

from pathlib import Path

import pytest

SKILLS_DIR = Path(__file__).resolve().parents[3] / "skills"
ROOT_DIR = SKILLS_DIR.parent

ROLE_SKILLS = ["ideation", "architect", "implementation", "review", "delivery-manager"]


class TestAlwaysOnLayer:
    """PLAYBOOK.md must contain the shared cross-role guidance."""

    def test_playbook_has_backend_protocol(self):
        content = (SKILLS_DIR / "PLAYBOOK.md").read_text()
        assert "## Backend Protocol" in content

    def test_playbook_has_artifact_access_rules(self):
        content = (SKILLS_DIR / "PLAYBOOK.md").read_text()
        assert "## Artifact Access Rules" in content

    def test_playbook_has_session_protocol(self):
        content = (SKILLS_DIR / "PLAYBOOK.md").read_text()
        assert "## Session Protocol" in content

    def test_playbook_has_collaboration_protocol(self):
        content = (SKILLS_DIR / "PLAYBOOK.md").read_text()
        assert "## Collaboration Protocol" in content

    def test_playbook_has_shared_rules(self):
        content = (SKILLS_DIR / "PLAYBOOK.md").read_text()
        assert "## Shared Rules" in content


class TestRoleSkillsReferencePlaybook:
    """Each role skill must use the one-liner reference rather than duplicating."""

    @pytest.mark.parametrize("role", ROLE_SKILLS)
    def test_skill_references_playbook(self, role):
        content = (SKILLS_DIR / role / "SKILL.md").read_text()
        assert "see PLAYBOOK.md" in content, (
            f"{role}/SKILL.md must reference PLAYBOOK.md for backend/artifact rules"
        )

    @pytest.mark.parametrize("role", ROLE_SKILLS)
    def test_skill_does_not_duplicate_artifact_table(self, role):
        """Role skills should not contain the full artifact access command table."""
        content = (SKILLS_DIR / role / "SKILL.md").read_text()
        # The full table in PLAYBOOK starts with "| Action | Command |"
        # Role skills should not duplicate this; they may have role-specific commands
        assert "| Action | Command |" not in content, (
            f"{role}/SKILL.md still contains the shared Artifact Access command table "
            "which should only be in PLAYBOOK.md"
        )

    @pytest.mark.parametrize("role", ROLE_SKILLS)
    def test_skill_does_not_duplicate_backend_check_block(self, role):
        """No role skill should contain the full 4-line backend check block."""
        content = (SKILLS_DIR / role / "SKILL.md").read_text()
        # The characteristic duplicated block pattern
        assert 'Read `_project/storage.yaml` before touching any artifact.' not in content, (
            f"{role}/SKILL.md still contains the duplicated Backend Check block "
            "which should only be in PLAYBOOK.md"
        )


class TestInstallSkillDiscovery:
    """install.sh must create the .skills symlink for native discovery."""

    def test_install_has_skills_symlink_step(self):
        content = (ROOT_DIR / "install.sh").read_text()
        assert ".skills" in content
        assert "ln -s" in content


class TestTokenFootprintBaseline:
    """Measure total role-skill line count to prevent bloat regression."""

    def test_total_skill_lines_under_threshold(self):
        """Combined role SKILL.md files should stay reasonably slim.
        Baseline after dedup: ~820 lines across 5 roles. Allow headroom up to 1000."""
        total = 0
        for role in ROLE_SKILLS:
            total += len((SKILLS_DIR / role / "SKILL.md").read_text().splitlines())
        assert total < 1000, (
            f"Combined role skill files are {total} lines — expected < 1000. "
            "Check for duplicated cross-role content that should be in PLAYBOOK.md."
        )
