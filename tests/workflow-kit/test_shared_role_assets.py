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
        "skills/build/SKILL.md",
        "skills/review/SKILL.md",
        "templates/shared/requirement.md",
        "templates/shared/blocker.md",
        "templates/shared/review.md",
        "templates/shared/delivery.md",
        "examples/handoffs.md",
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
        "Standard routes approved scope to Architecture",
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
    requirements = (SOURCE / "skills/requirements/SKILL.md").read_text()
    delivery = (SOURCE / "templates/shared/delivery.md").read_text()

    assert "Accepted, landed, released, and deployed remain distinct" in requirements
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
