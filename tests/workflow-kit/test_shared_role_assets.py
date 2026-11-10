import re
import shutil
from pathlib import Path
from urllib.parse import unquote, urlsplit

import pytest

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "workflow-kit"


def normalized(text):
    return " ".join(text.split())


def stage_workflow_kit(tmp_path):
    staged = tmp_path / "consumer with spaces" / "workflow-kit"
    shutil.copytree(SOURCE, staged)
    return staged


def markdown_links(path):
    return re.findall(r"\[[^]]+\]\(([^)]+)\)", path.read_text())


def markdown_anchors(path):
    anchors = set()
    duplicates = {}
    for heading in re.findall(r"^#{1,6}\s+(.+?)\s*$", path.read_text(), re.MULTILINE):
        slug = re.sub(r"[^\w\s-]", "", heading.casefold())
        slug = re.sub(r"[\s-]+", "-", slug).strip("-")
        count = duplicates.get(slug, 0)
        duplicates[slug] = count + 1
        anchors.add(slug if count == 0 else f"{slug}-{count}")
    return anchors


def validate_staged_links(staged):
    root = staged.resolve()
    errors = []
    for markdown in staged.rglob("*.md"):
        for target in markdown_links(markdown):
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc:
                continue

            target_path = unquote(parsed.path)
            resolved = (
                (markdown.parent / target_path).resolve()
                if target_path
                else markdown.resolve()
            )
            try:
                resolved.relative_to(root)
            except ValueError:
                errors.append(f"boundary escape: {markdown.name} -> {target}")
                continue

            if not resolved.exists():
                errors.append(f"missing target: {markdown.name} -> {target}")
                continue
            if parsed.fragment and resolved.suffix == ".md":
                fragment = unquote(parsed.fragment).casefold()
                if fragment not in markdown_anchors(resolved):
                    errors.append(f"missing anchor: {markdown.name} -> {target}")
    return errors


def validate_profile_composition(staged):
    errors = []
    shared_skills = {
        role: (staged / "skills" / role / "SKILL.md").resolve()
        for role in ("requirements", "build", "review")
    }
    for profile in ("lite", "standard"):
        profile_path = staged / "profiles" / profile / "PROFILE.md"
        resolved_links = {
            (profile_path.parent / urlsplit(link).path).resolve()
            for link in markdown_links(profile_path)
            if not urlsplit(link).scheme and urlsplit(link).path
        }
        for role, shared_path in shared_skills.items():
            if shared_path not in resolved_links:
                errors.append(f"{profile} does not use shared {role}")

            copied = staged / "profiles" / profile / "skills" / role / "SKILL.md"
            if copied.exists():
                errors.append(f"{profile} duplicates shared {role}")
    return errors


GATE_CONTRACTS = {
    "profiles/standard/skills/architect/SKILL.md": [
        "exact approved requirement revision",
        "verified Done dependencies",
        "accepted Build assignment",
        "absence of competing claims",
        "set Ready last",
    ],
    "skills/build/SKILL.md": [
        "current session is explicitly assigned",
        "No other active session, branch, worktree, or implementation PR",
        "Re-read both the claim and status",
    ],
    "skills/review/SKILL.md": [
        "exact PR head",
        "Any new commit invalidates the prior acceptance",
        "never fall back to Markdown status",
    ],
    "PLAYBOOK.md": [
        "GitHub read or write failure pauses affected work",
        "Never create or consult a competing Markdown status queue",
    ],
}


def validate_gate_contracts(staged):
    errors = []
    for relative, phrases in GATE_CONTRACTS.items():
        text = normalized((staged / relative).read_text())
        for phrase in phrases:
            if phrase not in text:
                errors.append(f"{relative} missing: {phrase}")
    return errors


def remove_normalized_phrase(text, phrase):
    pattern = r"\s+".join(re.escape(part) for part in phrase.split())
    updated, count = re.subn(pattern, "", text)
    assert count >= 1
    return updated


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
    ]

    for relative in expected:
        assert (staged / relative).is_file()

    assert validate_staged_links(staged) == []


def test_staged_links_handle_fragments_queries_and_refuse_unsafe_targets(tmp_path):
    staged = stage_workflow_kit(tmp_path)
    probe = staged / "link-probe.md"
    probe.write_text(
        "# Probe\n\n"
        "[local section](PLAYBOOK.md#product-contract)\n"
        "[query and fragment](PLAYBOOK.md?view=1#product-contract)\n"
        "[encoded path](profiles/standard/skills/architect/SKILL.md)\n"
    )
    assert validate_staged_links(staged) == []

    probe.write_text("# Probe\n\n[missing](missing.md)\n")
    assert validate_staged_links(staged) == [
        "missing target: link-probe.md -> missing.md"
    ]

    probe.write_text("# Probe\n\n[missing anchor](PLAYBOOK.md#not-an-anchor)\n")
    assert validate_staged_links(staged) == [
        "missing anchor: link-probe.md -> PLAYBOOK.md#not-an-anchor"
    ]

    outside = staged.parent / "outside.md"
    outside.write_text("# Outside\n")
    probe.write_text("# Probe\n\n[escape](../outside.md)\n")
    assert validate_staged_links(staged) == [
        "boundary escape: link-probe.md -> ../outside.md"
    ]


def test_profiles_use_one_shared_role_source_and_refuse_profile_copies(tmp_path):
    staged = stage_workflow_kit(tmp_path)
    assert validate_profile_composition(staged) == []

    copied = staged / "profiles" / "standard" / "skills" / "review" / "SKILL.md"
    copied.parent.mkdir(parents=True, exist_ok=True)
    copied.write_text((staged / "skills" / "review" / "SKILL.md").read_text())
    assert validate_profile_composition(staged) == ["standard duplicates shared review"]


@pytest.mark.parametrize(
    ("relative", "phrase"),
    [
        (relative, phrase)
        for relative, phrases in GATE_CONTRACTS.items()
        for phrase in phrases
    ],
)
def test_staged_gate_contract_detects_missing_safeguards(tmp_path, relative, phrase):
    staged = stage_workflow_kit(tmp_path)
    assert validate_gate_contracts(staged) == []

    target = staged / relative
    text = target.read_text()
    assert phrase in normalized(text)
    target.write_text(remove_normalized_phrase(text, phrase))

    assert f"{relative} missing: {phrase}" in validate_gate_contracts(staged)


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


def test_standard_technical_loop_reuses_scope_and_checks_every_ready_gate():
    architect = normalized(
        (SOURCE / "profiles/standard/skills/architect/SKILL.md").read_text()
    )
    for phrase in [
        "applies only to Standard profile work",
        '"Run the technical shaping loop"',
        '"Run the architecture loop"',
        '"Run the requirements loop"** is a compatibility alias',
        "read every page of `Inbox` and `Technical shaping`",
        "Do not redraft approved scope",
        "never infer approval or restart all shaping",
        "exact approved requirement revision",
        "verified Done dependencies",
        "accepted Build assignment",
        "absence of competing claims",
        "Before any mutation, reread",
        "set Ready last",
        "GitHub read or write failure pauses",
        "Stop at handoff",
        "Never automatically dispatch Build",
    ]:
        assert phrase in architect


def test_standard_alias_does_not_change_lite_or_delivery():
    requirements = normalized((SOURCE / "skills/requirements/SKILL.md").read_text())
    profile = normalized((SOURCE / "profiles/standard/PROFILE.md").read_text())
    assert (
        "shaping procedure below applies to Lite and explicit product-gap"
        in requirements
    )
    assert "delivery verification procedure below in both profiles" in requirements
    assert "Lite returns to `Shaping`; Standard records `Blocked`" in requirements
    assert "Added features move directly to Technical shaping" in profile
    assert "Lite is unchanged" in profile
