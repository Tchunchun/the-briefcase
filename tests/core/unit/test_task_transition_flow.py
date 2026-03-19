"""Regression test: architect-to-implementation inline steps require in-progress before done.

Validates that the architect skill's inlined implementation handoff instructions
require each task to transition through in-progress before being marked done,
as defined in the PLAYBOOK task lifecycle (to-do -> in-progress -> done).
"""

from pathlib import Path

import pytest


SKILLS_DIR = Path(__file__).resolve().parents[3] / "skills"


class TestTaskTransitionInSkills:
    """Ensure skill guidance preserves the to-do -> in-progress -> done lifecycle."""

    def test_architect_inline_steps_require_in_progress(self):
        """The architect skill's inlined implementation steps must explicitly
        mention marking tasks in-progress before done."""
        content = (SKILLS_DIR / "architect" / "SKILL.md").read_text()

        # Find the inlined implementation block (steps after "Continue immediately as the implementation agent")
        assert "Mark it `in-progress`" in content or "mark it `in-progress`" in content.lower(), (
            "Architect SKILL.md inlined implementation steps must require "
            "marking tasks in-progress before done (to-do -> in-progress -> done)"
        )

    def test_implementation_skill_has_in_progress_step(self):
        """The implementation SKILL.md must have an explicit in-progress step for tasks."""
        content = (SKILLS_DIR / "implementation" / "SKILL.md").read_text()
        assert "Mark it in-progress" in content or "mark it in-progress" in content.lower() or "status in-progress" in content, (
            "Implementation SKILL.md must require marking tasks in-progress"
        )

    def test_no_direct_to_done_shortcut(self):
        """No skill should say 'mark tasks done as you go' without in-progress."""
        for skill_dir in SKILLS_DIR.iterdir():
            skill_file = skill_dir / "SKILL.md" if skill_dir.is_dir() else None
            if skill_file and skill_file.exists():
                content = skill_file.read_text()
                # The old buggy pattern was "mark tasks done as you go"
                assert "mark tasks done as you go" not in content.lower(), (
                    f"{skill_file.relative_to(SKILLS_DIR)} contains 'mark tasks done as you go' "
                    "which skips the required in-progress transition"
                )
