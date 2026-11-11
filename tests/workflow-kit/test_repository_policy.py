"""Regression tests for current repository shaping and review policy."""

from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parents[2]


class TestRepositoryReviewLoop:
    """Keep repository closeout discoverable without changing consumer ownership."""

    def test_entrypoint_links_to_closeout_policy(self):
        content = (ROOT_DIR / "AGENTS.md").read_text()
        assert '"Run the review loop"' in content
        assert "_project/backlog-policy.md#repository-review-loop" in content

    @pytest.mark.parametrize(
        ("evidence", "status", "verdict"),
        [
            ("Current revision passes review", "In review", "Accepted"),
            ("Accepted work landed", "In review", "Accepted"),
            ("Fixable implementation findings", "In progress", "Changes requested"),
            ("Missing scope approval", "Blocked", "Blocked"),
            ("Only part of the item landed", "In progress if", "Pending"),
            ("Full scope accepted", "Done", "Accepted"),
        ],
    )
    def test_evidence_has_explicit_outcome(self, evidence, status, verdict):
        content = (ROOT_DIR / "_project" / "backlog-policy.md").read_text()
        row = next(
            line for line in content.splitlines() if line.startswith(f"| {evidence}")
        )
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
        assert (
            completion.index("merge any eligible open PR")
            < completion.index("then close an open linked issue")
            < completion.index("setting Done last")
        )
        assert "do not attempt to merge again or roll back the merge" in content

    def test_merge_authority_is_repository_scoped_and_read_only_is_respected(self):
        policy = (ROOT_DIR / "_project" / "backlog-policy.md").read_text()
        assert "A normal review-loop run is action-enabled" in policy
        assert (
            "An explicitly read-only review reports the proposed actions without writes"
            in (policy)
        )
        for path in [ROOT_DIR / "AGENTS.md", ROOT_DIR / "README.md"]:
            content = path.read_text()
            assert "merges" in content
            assert "read-only review" in content.lower()


class TestRepositoryRequirementsLoop:
    """Keep Standard shaping gated without changing installed workflows."""

    def test_requirements_loop_is_discoverable(self):
        for path in [ROOT_DIR / "AGENTS.md", ROOT_DIR / "README.md"]:
            content = path.read_text()
            assert (
                "_project/backlog-policy.md#repository-technical-shaping-loop"
                in content
            )

    @pytest.mark.parametrize(
        ("evidence", "status", "owner"),
        [
            ("Missing approval or a material scope gap", "Blocked", "Requirements"),
            (
                "Approved scope awaits technical review",
                "Technical shaping",
                "Architect",
            ),
            ("An unresolved technical decision", "Blocked", "Architect"),
            ("A dependency, access failure", "Blocked", "Explicit responsible role"),
            ("Approved revision, current sign-off", "Ready", "Build"),
        ],
    )
    def test_requirements_outcomes_are_explicit(self, evidence, status, owner):
        content = (ROOT_DIR / "_project" / "backlog-policy.md").read_text()
        row = next(
            line for line in content.splitlines() if line.startswith(f"| {evidence}")
        )
        columns = [column.strip() for column in row.strip("|").split("|")]
        assert columns[1:3] == [status, owner]

    def test_requirements_gates_and_safe_handoff(self):
        content = (ROOT_DIR / "_project" / "backlog-policy.md").read_text()
        loop = content.split("## Repository Technical Shaping Loop\n", 1)[1].split(
            "## Repository Review Loop\n", 1
        )[0]
        for requirement in [
            "read all pages of Technical shaping cards owned by Architect",
            "capture that queue once",
            "authoritative requirement reference",
            "approved immutable revision",
            "A later material scope change needs renewed",
            "separate Review session",
            "Build records assignment when it later claims Ready",
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
            "A Requirements invocation remains owned by Requirements",
            "silently changing roles",
            "read all pages of Technical shaping cards owned by Architect",
            "do not\n   redraft them",
            "exact gap, owner, and unblock condition",
            "Stop at this handoff",
        ]:
            assert requirement in loop
