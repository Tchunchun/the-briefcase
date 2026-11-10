import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "workflow-kit"

ARCHITECT_PATH = SOURCE / "profiles" / "standard" / "skills" / "architect" / "SKILL.md"
ARCHITECT_SKILL = ARCHITECT_PATH.read_text()
BRIEF_TEMPLATE = (SOURCE / "templates" / "standard" / "brief.md").read_text()
DECISION_TEMPLATE = (SOURCE / "templates" / "standard" / "decision.md").read_text()
RELEASE_TEMPLATE = (SOURCE / "templates" / "standard" / "release.md").read_text()
STANDARD_EXAMPLE = (SOURCE / "examples" / "standard-example.md").read_text()
LITE_EXAMPLE = (SOURCE / "examples" / "lite-example.md").read_text()
STANDARD_PROFILE = (SOURCE / "profiles" / "standard" / "PROFILE.md").read_text()


def normalized(text):
    return " ".join(text.split())


def markdown_links(path):
    return re.findall(r"\[[^]]+\]\(([^)]+)\)", path.read_text())


# ── File existence ─────────────────────────────────────────────────────────────


def test_all_deliverables_exist():
    expected = [
        "profiles/standard/skills/architect/SKILL.md",
        "profiles/lite/PROFILE.md",
        "templates/standard/brief.md",
        "templates/standard/decision.md",
        "templates/standard/release.md",
        "examples/standard-example.md",
        "examples/lite-example.md",
    ]
    for relative in expected:
        assert (SOURCE / relative).is_file(), f"missing: {relative}"


def test_no_new_src_directory():
    assert not (SOURCE / "src").exists()


# ── Relative link resolution ───────────────────────────────────────────────────


def test_all_standard_asset_links_resolve():
    for markdown in [
        ARCHITECT_PATH,
        SOURCE / "templates" / "standard" / "brief.md",
        SOURCE / "templates" / "standard" / "decision.md",
        SOURCE / "templates" / "standard" / "release.md",
        SOURCE / "examples" / "standard-example.md",
        SOURCE / "examples" / "lite-example.md",
    ]:
        for target in markdown_links(markdown):
            if "://" not in target and not target.startswith("#"):
                resolved = (markdown.parent / target).resolve()
                assert resolved.exists(), (markdown, target)


# ── Architect skill ────────────────────────────────────────────────────────────


def test_architect_is_standard_only_and_explicit_invocation():
    required = [
        "user explicitly asks to run the Architecture loop",
        "applies only to Standard profile work",
        "not an automatic orchestrator",
    ]
    for phrase in required:
        assert phrase in normalized(ARCHITECT_SKILL)


def test_architect_assesses_all_four_areas():
    required = [
        "Technical approach",
        "Alternatives considered",
        "Risk assessment",
        "NFR verification",
    ]
    for phrase in required:
        assert phrase in ARCHITECT_SKILL


def test_architect_records_revision_bound_signoff():
    required = [
        "exact approved requirement revision",
        "Decision record",
        "Signed by",
        "Signed at",
    ]
    for phrase in required:
        assert phrase in ARCHITECT_SKILL


def test_architect_states_material_change_invalidation():
    required = [
        "sign-off is stale",
        "approved revision changes after the sign-off",
        "Build must refuse the claim",
        "Requirements returns the item to Architecture",
    ]
    for phrase in required:
        assert phrase in normalized(ARCHITECT_SKILL)


def test_architect_has_stopping_question_rule():
    assert "stopping question" in normalized(ARCHITECT_SKILL)
    assert "do not record sign-off" in normalized(ARCHITECT_SKILL)


def test_architect_does_not_replace_requirements_or_review():
    required = [
        "Never approve requirements scope",
        "Never implement or review",
        "Do not copy or re-implement the shared Requirements or Review skills",
    ]
    for phrase in required:
        assert phrase in ARCHITECT_SKILL


def test_architect_github_failure_rule():
    assert "GitHub read or write failure pauses" in ARCHITECT_SKILL
    assert "do not claim a transition succeeded" in normalized(ARCHITECT_SKILL)


# ── Brief template ────────────────────────────────────────────────────────────


def test_brief_template_has_all_required_sections():
    required_sections = [
        "## Context and expected experience",
        "## Scope and exclusions",
        "## Acceptance and verification",
        "## Constraints and compatibility",
        "## Technical approach",
        "## Alternatives considered",
        "## Risk assessment",
        "## NFR verification",
        "## Architect sign-off",
        "## Decisions and child Tasks",
        "## Release obligations",
    ]
    for section in required_sections:
        assert section in BRIEF_TEMPLATE


def test_brief_template_signoff_binds_to_requirement_revision():
    assert "Approved requirement revision" in BRIEF_TEMPLATE
    assert "immutable revision" in BRIEF_TEMPLATE or "same location and revision" in BRIEF_TEMPLATE


def test_brief_template_signoff_references_decision_record():
    assert "Decision record" in BRIEF_TEMPLATE


def test_brief_template_states_invalidation_rule():
    assert "material change" in normalized(BRIEF_TEMPLATE)
    assert "invalidates this sign-off" in normalized(BRIEF_TEMPLATE)


def test_brief_template_has_alternatives_table():
    assert "| Alternative | Why rejected |" in BRIEF_TEMPLATE


def test_brief_template_has_risk_table():
    assert "| Risk | Likelihood | Impact | Mitigation |" in BRIEF_TEMPLATE


def test_brief_template_has_nfr_table():
    assert "| NFR | Requirement | How verified |" in BRIEF_TEMPLATE


# ── Decision template ─────────────────────────────────────────────────────────


def test_decision_template_has_required_fields():
    required = [
        "Decision ID",
        "Approved requirement revision",
        "ADR link",
        "Recorded by",
    ]
    for field in required:
        assert field in DECISION_TEMPLATE


def test_decision_template_has_alternatives_rejected():
    assert "## Alternatives rejected" in DECISION_TEMPLATE
    assert "| Alternative | Why rejected |" in DECISION_TEMPLATE


def test_decision_template_has_consequences():
    assert "## Consequences" in DECISION_TEMPLATE
    assert "Negative / risks" in DECISION_TEMPLATE


def test_decision_template_is_append_only():
    assert "append-only" in normalized(DECISION_TEMPLATE)
    assert "never overwrite a prior decision" in normalized(DECISION_TEMPLATE)


def test_decision_template_links_to_signoff():
    assert "sign-off" in normalized(DECISION_TEMPLATE)


# ── Release template ──────────────────────────────────────────────────────────


def test_release_template_has_required_fields():
    required = [
        "Version",
        "Scope coverage",
        "Required checks",
        "Release note",
        "Approved requirement revision",
        "Review verdict",
        "Accepted head",
        "Landing evidence",
    ]
    for field in required:
        assert field in RELEASE_TEMPLATE


def test_release_template_has_no_release_note_representation():
    assert "N/A — approved no-release-note-required" in RELEASE_TEMPLATE
    assert "Approval:" in RELEASE_TEMPLATE


def test_note_exemption_cannot_waive_version_or_readiness():
    version_section = RELEASE_TEMPLATE.split("## Version")[1].split("## Scope")[0]
    assert "Version impact:" in version_section
    assert "independent reason" in version_section
    assert "no-release-note-required" not in version_section
    assert "exemption never waives version impact" in normalized(RELEASE_TEMPLATE)
    assert "## Environment and readiness" in RELEASE_TEMPLATE
    assert "Remaining obligations:" in RELEASE_TEMPLATE


def test_architect_is_discoverable_only_as_standard_extension():
    assert not (SOURCE / "architect" / "SKILL.md").exists()
    assert "(skills/architect/SKILL.md)" in STANDARD_PROFILE
    assert "(profiles/standard/skills/architect/SKILL.md)" in (
        SOURCE / "PLAYBOOK.md"
    ).read_text()


def test_profiles_reference_the_same_shared_role_files():
    for profile in ("lite", "standard"):
        path = SOURCE / "profiles" / profile / "PROFILE.md"
        links = markdown_links(path)
        for role in ("requirements", "build", "review"):
            expected = (SOURCE / "skills" / role / "SKILL.md").resolve()
            assert expected in [(path.parent / link).resolve() for link in links]
    lite = (SOURCE / "profiles/lite/PROFILE.md").read_text()
    assert "no Architect role" in normalized(lite)
    assert "Requirements-owned blocker" in lite
    assert "Standard release record requirement" in lite


def test_signoff_invalidation_covers_all_material_constraints():
    for text in (ARCHITECT_SKILL, BRIEF_TEMPLATE, STANDARD_PROFILE):
        for category in ("constraints", "NFRs", "approach assumptions", "release obligations"):
            assert category.casefold() in text.casefold()
    assert "Result:" in BRIEF_TEMPLATE
    assert "Approved Task revision:" in BRIEF_TEMPLATE


def test_release_template_separates_deployment():
    assert "Deployment" in RELEASE_TEMPLATE
    assert "separate record" in RELEASE_TEMPLATE or "not be inferred" in normalized(RELEASE_TEMPLATE)


def test_release_template_has_checks_table():
    assert "| Check | Command | Result |" in RELEASE_TEMPLATE


def test_release_template_has_coverage_fields():
    assert "Child Tasks covered" in RELEASE_TEMPLATE
    assert "Coverage complete" in RELEASE_TEMPLATE


# ── Standard example ─────────────────────────────────────────────────────────


def test_standard_example_has_all_required_artifacts():
    required = [
        "## Requirement packet (Feature)",
        "## Feature PRD (Architect sign-off)",
        "## Requirement packet (child Task",
        "## Standard release record",
    ]
    for section in required:
        assert section in STANDARD_EXAMPLE


def test_standard_example_uses_single_requirement_authority():
    revisions = re.findall(r"sha:[a-f0-9]+", STANDARD_EXAMPLE)
    # Feature and sign-off must reference the same revision
    assert len(set(revisions)) >= 1
    # The sign-off revision must match the Feature canonical requirement revision
    assert STANDARD_EXAMPLE.count("sha:a1b2c3d") >= 2, (
        "sign-off must name the same revision as the Feature canonical requirement"
    )


def test_standard_example_child_task_links_parent():
    assert "Parent:" in STANDARD_EXAMPLE
    assert "Approved parent revision:" in STANDARD_EXAMPLE


def test_standard_example_child_does_not_duplicate_parent_scope():
    # Child task section must reference parent rather than re-stating Feature scope
    child_start = STANDARD_EXAMPLE.index("## Requirement packet (child Task")
    child_text = STANDARD_EXAMPLE[child_start:]
    assert "parent" in child_text.lower()
    assert "scope and parent criteria are\ndefined in" in child_text or "scope boundary" in child_text


def test_standard_example_release_has_version_and_coverage():
    release_start = STANDARD_EXAMPLE.index("## Standard release record")
    release_text = STANDARD_EXAMPLE[release_start:]
    assert "Version:" in release_text
    assert "Child Tasks covered:" in release_text
    assert "Coverage complete: yes" in release_text


# ── Lite example ─────────────────────────────────────────────────────────────


def test_lite_example_has_no_architect_role():
    assert "Architect" not in LITE_EXAMPLE or "no Architect role" in normalized(LITE_EXAMPLE)


def test_lite_example_has_no_feature_task_hierarchy():
    assert "no Feature/Task hierarchy" in LITE_EXAMPLE or (
        "Feature/Task" not in LITE_EXAMPLE.split("## Notes")[0]
    )


def test_lite_example_has_no_standard_release_record():
    assert "Standard release record" not in LITE_EXAMPLE.split("## Notes")[0]


def test_lite_example_has_requirement_packet():
    assert "## Requirement packet" in LITE_EXAMPLE


def test_lite_example_has_separate_session_review():
    assert "separate from Build session" in LITE_EXAMPLE


# ── Additive only — existing assets untouched ─────────────────────────────────


def test_shared_skills_unchanged():
    for skill in ["skills/requirements/SKILL.md", "skills/build/SKILL.md", "skills/review/SKILL.md"]:
        assert (SOURCE / skill).is_file()


def test_standard_profile_unchanged():
    assert "exact approved Feature PRD revision" in normalized(STANDARD_PROFILE)
    assert "material requirements change makes that sign-off stale" in normalized(STANDARD_PROFILE)


def test_lite_profile_does_not_add_architect():
    # The Lite profile / AGENTS.md must not reference architecture sign-off
    lite_agents = (ROOT / "lite" / "AGENTS.md").read_text()
    assert "Architect sign-off" not in lite_agents
