from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[3]
POLICY = ROOT / "_project" / "backlog-policy.md"


def test_repository_entrypoints_and_consumer_boundary():
    for path in [ROOT / "AGENTS.md", ROOT / "README.md"]:
        content = path.read_text()
        assert "_project/backlog-policy.md#repository-review-loop" in content
        assert "merges" in content
        assert "read-only review" in content.lower()
    skill = (ROOT / "skills" / "review" / "SKILL.md").read_text()
    assert skill.index("## Repository Review and Closeout Overrides") < skill.index(
        "## Lane Awareness"
    )
    assert "When the repository policy authorizes reviewer merges" in skill
    assert "Without such an override, retain the consumer workflow below" in skill


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
def test_evidence_has_explicit_outcome(evidence, status, verdict):
    row = next(
        line for line in POLICY.read_text().splitlines()
        if line.startswith(f"| {evidence}")
    )
    columns = [column.strip() for column in row.strip("|").split("|")]
    assert columns[1].startswith(status)
    assert columns[3] == verdict


def test_closeout_requires_evidence_and_verified_writes():
    content = POLICY.read_text()
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
        "An explicitly read-only review reports the proposed actions without writes",
    ]:
        assert requirement in content


def test_passing_review_merges_before_closing():
    content = POLICY.read_text()
    merge = content.split("### Merge a passing PR\n", 1)[1].split(
        "### Outcomes and completion gates\n", 1
    )[0]
    for requirement in [
        "full approved item coverage",
        "independent acceptance of the exact PR",
        "eligible approvals",
        "automatic issue-closing",
        "approved scope revision and PR head immediately before merge",
        "gh pr merge --match-head-commit",
        "Never use `--admin`",
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


def test_documentation_links_resolve():
    assert POLICY.is_file()
    assert "## Repository Review Loop" in POLICY.read_text()
    assert "Project #5" in (ROOT / "AGENTS.md").read_text()
    assert "Without an override, consumer" in (
        ROOT / "skills" / "PLAYBOOK.md"
    ).read_text()
