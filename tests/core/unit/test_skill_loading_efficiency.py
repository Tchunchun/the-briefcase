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
    """install.sh must set up .briefcase/skills/ for framework skill access."""

    def test_install_copies_skills_to_briefcase(self):
        content = (ROOT_DIR / "install.sh").read_text()
        assert ".briefcase" in content
        assert "skills" in content


class TestRepositoryReviewLoop:
    """Keep repository closeout discoverable without changing consumer ownership."""

    def test_entrypoint_links_to_closeout_policy(self):
        content = (ROOT_DIR / "AGENTS.md").read_text()
        assert '"Run the review loop"' in content
        assert "_project/backlog-policy.md#repository-review-loop" in content

    def test_review_checks_override_before_legacy_workflow(self):
        content = (SKILLS_DIR / "review" / "SKILL.md").read_text()
        assert content.index("## Repository Review and Closeout Overrides") < content.index(
            "## Lane Awareness"
        )
        assert "Without such an override, retain the consumer workflow below" in content

    @pytest.mark.parametrize(
        ("evidence", "status", "verdict"),
        [
            ("Current revision passes review", "In review", "Accepted"),
            ("Accepted work landed", "In review", "Accepted"),
            ("Fixable implementation findings", "In progress if", "Changes requested"),
            ("Missing scope approval", "Blocked", "Blocked"),
            ("Only part of the item landed", "In progress if", "Pending"),
            ("Full approved scope independently accepted", "Done", "Accepted"),
        ],
    )
    def test_evidence_has_explicit_outcome(self, evidence, status, verdict):
        content = (ROOT_DIR / "_project" / "backlog-policy.md").read_text()
        row = next(line for line in content.splitlines() if line.startswith(f"| {evidence}"))
        columns = [column.strip() for column in row.strip("|").split("|")]
        assert columns[1].startswith(status)
        assert columns[3] == verdict

    def test_closeout_requires_evidence_and_verified_writes(self):
        content = (ROOT_DIR / "_project" / "backlog-policy.md").read_text()
        for requirement in [
            "Read every result page",
            "session separate from implementation",
            "criterion-by-criterion evidence",
            "squash/rebase merges",
            "without a PR",
            "required dependencies",
            "release/version records",
            "Before any mutation, reread",
            "setting Done last",
            "Read back the saved packet",
            "which writes succeeded and which remain",
            "without duplicating",
            "Draft cards have no",
            "public-safe implementation facts",
            "closed as not planned",
        ]:
            assert requirement in content

    def test_passing_review_merges_before_closing(self):
        content = (ROOT_DIR / "_project" / "backlog-policy.md").read_text()
        merge = content.split("### Merge a passing PR\n", 1)[1].split(
            "### Outcomes and completion gates\n", 1
        )[0]
        for requirement in [
            "full approved item coverage",
            "independent acceptance of the exact PR",
            "required",
            "eligible approvals",
            "branch",
            "automatic issue-closing",
            "approved scope revision and PR head immediately before merge",
            "gh pr merge --match-head-commit",
            "changed",
            "Never use `--admin`",
            "without another",
            "queued merge or enabled auto-merge is not a completed merge",
            "post-merge release evidence",
            "every required landing before closing",
        ]:
            assert requirement in merge
        completion = content.split("For eligible completion,", 1)[1].split(
            "Draft cards have no", 1
        )[0]
        assert completion.index("merge any eligible open PR") < completion.index(
            "then close an open linked issue"
        ) < completion.index("setting Done last")
        assert "do not attempt to merge again or roll back the merge" in content

    def test_merge_authority_is_repository_scoped_and_read_only_is_respected(self):
        policy = (ROOT_DIR / "_project" / "backlog-policy.md").read_text()
        assert "A normal review-loop run is action-enabled" in policy
        assert "An explicitly read-only review reports the proposed actions without writes" in (
            policy
        )
        for path in [ROOT_DIR / "AGENTS.md", ROOT_DIR / "README.md"]:
            content = path.read_text()
            assert "merges" in content
            assert "read-only review" in content.lower()
        skill = (SKILLS_DIR / "review" / "SKILL.md").read_text()
        assert "When the repository policy authorizes reviewer merges" in skill
        assert "Without such an override, retain the consumer workflow below" in skill


class TestRepositoryRequirementsLoop:
    """Keep Standard shaping gated without changing installed workflows."""

    def test_requirements_loop_is_discoverable(self):
        for path in [ROOT_DIR / "AGENTS.md", ROOT_DIR / "README.md"]:
            content = path.read_text()
            assert "_project/backlog-policy.md#repository-technical-shaping-loop" in content

    @pytest.mark.parametrize(
        ("role", "legacy_heading"),
        [("ideation", "## Lane Triage"), ("architect", "## Lane Awareness")],
    )
    def test_override_precedes_legacy_workflow(self, role, legacy_heading):
        content = (SKILLS_DIR / role / "SKILL.md").read_text()
        override = content.index("Requirements-loop")
        assert content.index(legacy_heading) < override < content.index(
            "## Required Workflow"
        )
        assert "Without an override" in content
        assert "stop-at-handoff rule" in content

    @pytest.mark.parametrize(
        ("evidence", "status", "stage"),
        [
            ("Missing approval or a material scope gap", "Blocked", "Requirements"),
            ("Added feature has approved scope", "Technical shaping", "Architecture"),
            ("Approval/sign-off complete", "Technical shaping", "Build"),
            ("An unresolved decision", "Blocked", "Stage where blocked"),
            ("Approved revision, applicable sign-off", "Ready", "Build"),
        ],
    )
    def test_requirements_outcomes_are_explicit(self, evidence, status, stage):
        content = (ROOT_DIR / "_project" / "backlog-policy.md").read_text()
        row = next(line for line in content.splitlines() if line.startswith(f"| {evidence}"))
        columns = [column.strip() for column in row.strip("|").split("|")]
        assert columns[1:3] == [status, stage]

    def test_requirements_gates_and_safe_handoff(self):
        content = (ROOT_DIR / "_project" / "backlog-policy.md").read_text()
        loop = content.split("## Repository Technical Shaping Loop\n", 1)[1].split(
            "## Repository Review Loop\n", 1
        )[0]
        for requirement in [
            "read all pages of Inbox",
            "capture that queue once",
            "authoritative requirement reference",
            "approved immutable revision",
            "A later material scope change needs renewed",
            "separate Review session",
            "its accepted assignment",
            "Before any mutation, reread",
            "Set Ready last",
            "set Review Verdict to Accepted",
            "which writes succeeded and which remain",
            "there is no legacy inbox/backlog fallback",
            "than duplicating records",
            "Stop at this handoff",
        ]:
            assert requirement in " ".join(loop.split())

    def test_standard_reuses_scope_and_preserves_old_prompt(self):
        policy = (ROOT_DIR / "_project" / "backlog-policy.md").read_text()
        assert '<a id="repository-requirements-loop"></a>' in policy
        loop = policy.split("## Repository Technical Shaping Loop\n", 1)[1].split(
            "## Repository Review Loop\n", 1
        )[0]
        for requirement in [
            '"Run the technical shaping loop for <topic>"',
            '"Run the architecture loop"',
            '"Run the requirements loop"** is a compatibility alias',
            "must not restart product shaping",
            "read all pages of Inbox and Technical shaping",
            "do not\n   redraft them",
            "exact gap, owner, and unblock condition",
            "Stop at this handoff",
        ]:
            assert requirement in loop


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
