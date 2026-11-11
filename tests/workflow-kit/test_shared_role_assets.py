import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "workflow-kit"


def normalized(text):
    return " ".join(text.split())


def stage_workflow_kit(tmp_path):
    staged = tmp_path / "workflow-kit"
    shutil.copytree(SOURCE, staged)
    return staged


def markdown_links(path):
    return re.findall(r"\[[^]]+\]\(([^)]+)\)", path.read_text())


def test_staged_shared_assets_and_relative_links_resolve(tmp_path):
    staged = stage_workflow_kit(tmp_path)
    expected = [
        "skills/requirements/SKILL.md",
        "profiles/standard/skills/architect/SKILL.md",
        "skills/build/SKILL.md",
        "skills/review/SKILL.md",
        "templates/shared/requirement.md",
        "templates/shared/blocker.md",
        "templates/shared/review.md",
        "templates/shared/delivery.md",
        "examples/handoffs.md",
        "templates/workflow.yaml",
    ]

    for relative in expected:
        assert (staged / relative).is_file()

    for markdown in staged.rglob("*.md"):
        for target in markdown_links(markdown):
            if "://" not in target and not target.startswith("#"):
                assert (markdown.parent / target).resolve().exists(), (
                    markdown,
                    target,
                )


def test_requirements_is_direct_revision_bound_and_failure_safe():
    requirements = (SOURCE / "skills/requirements/SKILL.md").read_text()
    required = [
        "user explicitly asks to run the Requirements loop",
        "not a continuous scanner or automatic orchestrator",
        "exact approved revision",
        "material scope change invalidates the approval",
        "Standard moves approved scope to `Technical shaping`",
        "GitHub read or write failure pauses",
        "Never fall back to a Markdown status queue",
    ]

    for phrase in required:
        assert phrase in normalized(requirements)


def test_review_refuses_self_review_and_binds_current_head():
    review = (SOURCE / "skills/review/SKILL.md").read_text()
    required = [
        "Review session must be separate from the session that produced the code",
        "bugs, tech debt, documentation, and workflow assets",
        "refuse self-review",
        "exact PR head",
        "Any new commit invalidates the prior acceptance",
        "never fall back to Markdown status",
    ]

    for phrase in required:
        assert phrase in normalized(review)


def test_delivery_template_preserves_completion_distinctions():
    review = (SOURCE / "skills/review/SKILL.md").read_text()
    delivery = (SOURCE / "templates/shared/delivery.md").read_text()

    assert "Never treat `Accepted` as landed, released, deployed, or `Done`" in review
    assert "Standard release evidence" in delivery
    assert "Deployment" in delivery
    assert "Project `Done` verified" in delivery


def test_examples_cover_success_and_required_refusals():
    examples = (SOURCE / "examples/handoffs.md").read_text()
    required = [
        "## Happy path",
        "## Refused self-review",
        "## Refused missing approval",
        "## Refused competing ownership",
        "dedicated worktree",
        "separate Review session",
    ]

    for phrase in required:
        assert phrase in normalized(examples)


def test_templates_capture_revision_commit_evidence_and_verdict():
    templates = SOURCE / "templates/shared"
    requirement = (templates / "requirement.md").read_text()
    blocker = (templates / "blocker.md").read_text()
    review = (templates / "review.md").read_text()

    assert "immutable revision" in requirement
    assert "Resume condition" in blocker
    assert "Reviewed head" in review
    assert "Criterion evidence" in review
    assert "## Verdict" in review


def test_standard_technical_loop_reuses_scope_and_checks_every_ready_gate():
    architect = normalized(
        (SOURCE / "profiles/standard/skills/architect/SKILL.md").read_text()
    )
    for phrase in [
        "applies only to Standard profile work",
        '"Run the technical shaping loop"',
        '"Run the architecture loop"',
        "A Requirements invocation remains owned by Requirements",
        "read every page of `Technical shaping`",
        "Do not redraft approved scope",
        "never infer approval or restart all shaping",
        "exact approved requirement revision",
        "verified Done dependencies",
        "Build assignment is recorded atomically",
        "absence of competing implementation claims",
        "Before any mutation, reread",
        "set Ready last",
        "GitHub read or write failure pauses",
        "Stop at handoff",
        "Never automatically dispatch Build",
    ]:
        assert phrase in architect


def test_standard_roles_remain_distinct_and_lite_is_unchanged():
    requirements = normalized((SOURCE / "skills/requirements/SKILL.md").read_text())
    profile = normalized((SOURCE / "profiles/standard/PROFILE.md").read_text())
    assert "never silently execute the Architecture loop" in requirements
    assert "Requirements and Architect remain distinct roles" in profile
    assert "Build assignment is recorded atomically" in profile


def test_active_roles_follow_repository_document_organization():
    roles = [
        "skills/requirements/SKILL.md",
        "skills/build/SKILL.md",
        "skills/review/SKILL.md",
        "profiles/standard/skills/architect/SKILL.md",
    ]
    for relative in roles:
        skill = normalized((SOURCE / relative).read_text())
        for phrase in [
            "document organization",
            "repository policy",
            "issue-centered repositories",
            "snapshot",
            "issue comment",
        ]:
            assert phrase in skill, (relative, phrase)

    playbook = normalized((SOURCE / "PLAYBOOK.md").read_text())
    for phrase in [
        "four entries",
        "Do not invent approval",
        "compare the live issue requirements block with its approved snapshot",
        "private planning is not published to a public issue without explicit approval",
        "does not migrate Lite or legacy installed consumers",
    ]:
        assert phrase in playbook


def test_product_signoff_template_has_only_four_approval_entries():
    requirement = (SOURCE / "templates/shared/requirement.md").read_text()
    signoff = requirement.split("## Product sign-off\n", 1)[1]
    fields = re.findall(r"^- ([^:]+):", signoff, flags=re.MULTILINE)
    assert fields == ["Approved by", "Approved on", "Approved scope", "Evidence"]
    assert "pinned approved snapshot link" in signoff
    assert "Keep hashes and migration history in linked Git evidence" in signoff
    assert "Never record approval on the user's behalf" in signoff
    assert "Status / Action Owner:" not in requirement


def test_po_status_feedback_is_captured_in_active_guidance():
    agents = normalized((ROOT / "AGENTS.md").read_text())
    playbook = normalized((SOURCE / "PLAYBOOK.md").read_text())
    assert "## Read-only PO status guidance" in agents
    for phrase in [
        "A request for status is not permission",
        "design guidance from implementation acceptance",
    ]:
        assert phrase in agents
    for phrase in [
        "Decision-first presentation",
        "observation time and coverage",
        "then explicit pending product decisions, blockers, and moving work",
        "Project/schema metadata once per invocation",
        "batch necessary source reads",
        "do not filter evidence solely by Status, Action Owner, or keywords",
        "Current approval evidence",
        "canonical issue's current product sign-off",
        "Lean delivery",
        "all approved verification and release obligations",
        "zero attempted writes on success, failure, and repeat invocation",
    ]:
        assert phrase in playbook
    for relative in [
        "skills/requirements/SKILL.md",
        "skills/build/SKILL.md",
        "skills/review/SKILL.md",
        "profiles/standard/skills/architect/SKILL.md",
    ]:
        skill = normalized((SOURCE / relative).read_text())
        assert "shared playbook's read-only PO status guidance" in skill
