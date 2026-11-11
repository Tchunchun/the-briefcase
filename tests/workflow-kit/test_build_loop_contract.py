from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_KIT = ROOT / "workflow-kit"
PLAYBOOK = (WORKFLOW_KIT / "PLAYBOOK.md").read_text()
BUILD_SKILL = (WORKFLOW_KIT / "skills" / "build" / "SKILL.md").read_text()
STANDARD_PROFILE = (
    WORKFLOW_KIT / "profiles" / "standard" / "PROFILE.md"
).read_text()
WORKFLOW_CONFIG = (WORKFLOW_KIT / "workflow.yaml").read_text()


def normalized(text):
    return " ".join(text.split())


def test_new_build_assets_are_additive_and_links_resolve():
    assert "not an installed workflow by itself" in PLAYBOOK
    assert "legacy and must remain behaviorally unchanged" in normalized(PLAYBOOK)
    assert (WORKFLOW_KIT / "skills" / "build" / "SKILL.md").is_file()
    assert (WORKFLOW_KIT / "profiles" / "standard" / "PROFILE.md").is_file()
    assert not (WORKFLOW_KIT / "src").exists()


def test_repository_entrypoint_selects_current_roles_before_legacy_workflow():
    agents = (ROOT / "AGENTS.md").read_text()
    legacy = (ROOT / "skills" / "PLAYBOOK.md").read_text()
    readme = (ROOT / "README.md").read_text()

    assert agents.index("workflow-kit/PLAYBOOK.md") < agents.index("skills/PLAYBOOK.md")
    assert "repository policy takes precedence" in normalized(agents)
    assert "Legacy Playbook" in legacy
    assert legacy.index("## Workflow Selection") < legacy.index("## Agent Routing")
    assert "current workflow playbook" in legacy
    assert "Existing consumer behavior is unchanged" in legacy
    assert "## Legacy Installed Workflow" in readme
    assert "workflow-kit/PLAYBOOK.md" in readme


def test_current_role_roster_resolves_skills_and_preserves_closeout_override():
    role_rows = [
        line for line in PLAYBOOK.splitlines()
        if line.startswith("| ") and "skills/" in line
    ]
    assert len(role_rows) == 4
    skill_paths = [
        "skills/requirements/SKILL.md",
        "profiles/standard/skills/architect/SKILL.md",
        "skills/build/SKILL.md",
        "skills/review/SKILL.md",
    ]
    for path in skill_paths:
        assert f"({path})" in PLAYBOOK
        assert (WORKFLOW_KIT / path).is_file()
    assert "Lite uses three roles: Requirements, Build, and Review" in PLAYBOOK
    assert "There is no Delivery Manager role" in normalized(PLAYBOOK)
    assert "self-review exception" in PLAYBOOK
    assert "configured Review role owns merge and verified closeout" in normalized(PLAYBOOK)
    assert "Action Owner" in PLAYBOOK


def test_closeout_owner_has_one_configuration_point():
    assert WORKFLOW_CONFIG.count("closeout_owner:") == 1
    assert "closeout_owner: Review" in WORKFLOW_CONFIG
    assert "single configuration point" in normalized(PLAYBOOK)

    for path in [
        WORKFLOW_KIT / "profiles" / "standard" / "PROFILE.md",
        WORKFLOW_KIT / "skills" / "requirements" / "SKILL.md",
        WORKFLOW_KIT / "skills" / "build" / "SKILL.md",
        WORKFLOW_KIT / "skills" / "review" / "SKILL.md",
    ]:
        assert "workflow.yaml" in path.read_text()


def test_every_role_requires_the_executable_transition_gate():
    required_transitions = {
        "requirements": ["begin-requirement-shaping", "ready-lite-work"],
        "build": ["claim-build-work", "handoff-for-review"],
        "review": ["accept-review", "complete-task", "complete-feature"],
    }
    for role, transitions in required_transitions.items():
        skill = (WORKFLOW_KIT / "skills" / role / "SKILL.md").read_text()
        assert "mandatory live preflight" in skill
        assert "denied decision" in skill.casefold()
        for transition in transitions:
            assert transition in skill

    architect = (
        WORKFLOW_KIT / "profiles" / "standard" / "skills" / "architect" / "SKILL.md"
    ).read_text()
    assert "mandatory live preflight" in architect
    assert "ready-standard-feature" in architect
    assert "ready-standard-task" in architect
    assert "--offline` is insufficient" in PLAYBOOK


def test_current_guidance_uses_requirements_terminology():
    agents = (ROOT / "AGENTS.md").read_text()
    assert "brief" not in agents.lower().replace("briefcase", "")
    assert "canonical planning issue description holds user\nrequirements" in agents
    assert "Short handoffs are issue comments" in agents
    assert "Git holds technical design, technical sign-off" in agents
    assert "## Legacy CLI Project Root Resolution" in agents
    assert "Use GitHub directly for this repository's backlog" in agents

    template = WORKFLOW_KIT / "templates" / "standard" / "brief.md"
    assert template.read_text().startswith("# Standard Feature PRD\n")
    for path in WORKFLOW_KIT.rglob("*.md"):
        prose = path.read_text().replace("brief.md", "").replace("Briefcase", "")
        assert "brief" not in prose.lower(), path


def test_repository_issue_centered_documents_preserve_evidence_and_privacy():
    policy = (ROOT / "_project" / "backlog-policy.md").read_text()
    required = [
        "## Document organization",
        "Planning issue description",
        "Git design document",
        "Planning issue comments",
        "private planning issue",
        "do not add a second Project card",
        "immutable Git snapshot of the exact approved block",
        "SHA-256",
        "four readable entries",
        "migration history in linked Git records",
        "material changes require renewed product approval",
        "do not invent a\nnew approval",
        "New handoffs go in issue comments",
        "must not change status, owner, claim, review verdict, or scope",
    ]
    for phrase in required:
        assert phrase.casefold() in policy.casefold()


def test_implementation_pr_uses_native_github_navigation():
    policy = normalized((ROOT / "_project" / "backlog-policy.md").read_text())
    board = normalized((WORKFLOW_KIT / "board-setup.md").read_text())
    review = normalized((WORKFLOW_KIT / "skills/review/SKILL.md").read_text())
    build = normalized(BUILD_SKILL)
    assert "pull_request: Linked pull requests" in WORKFLOW_CONFIG
    assert "not a custom text field or Notes" in policy
    assert "different repositories" in board
    assert "do not create a duplicate" in board
    assert "native Development relationship" in build
    assert "`Linked pull requests` field before handoff" in build
    assert "not Notes or a custom text field" in review
    assert "missing, inaccessible, or conflicting link blocks" in review
    assert "must not automatically set Project Done" in review


def test_explicit_invocation_scans_every_ready_item_sequentially():
    required = [
        "user explicitly asks to run the Build loop",
        "every item whose live `Status` is `Ready`",
        "Process eligible items one at a time",
        "until no eligible Ready work remains",
        "not a continuous scanner or background scheduler",
    ]

    for phrase in required:
        assert phrase in normalized(BUILD_SKILL)


def test_ready_gate_refuses_unapproved_or_competing_work():
    required = [
        "canonical requirements revision is linked and approved",
        "Standard Feature work requires its own",
        "Every native blocker is `Done`",
        "Action Owner` is `Build`",
        "No other active session, branch, worktree, or implementation PR",
        "do not start coding",
    ]

    for phrase in required:
        assert phrase in BUILD_SKILL


def test_standard_signoff_is_revision_bound():
    required = [
        "exact approved Feature PRD revision",
        "material requirements change makes that sign-off stale",
        "refuse a Standard claim when the applicable evidence is missing",
    ]

    for phrase in required:
        assert phrase in normalized(STANDARD_PROFILE)


def test_claim_happens_before_code_and_requires_readback():
    claim = BUILD_SKILL.index("## Claim and readback")
    build = BUILD_SKILL.index("## Build and verify")

    assert claim < build
    assert "Move the Project status from `Ready` to `In progress`" in BUILD_SKILL
    assert "re-read assignment, claim, owner, and status" in BUILD_SKILL
    assert "reconcile the concurrent change" in normalized(BUILD_SKILL)


def test_github_failure_never_falls_back_to_markdown():
    assert "GitHub read or write failure pauses affected work" in PLAYBOOK
    assert "Do not fall back to\nMarkdown status" in BUILD_SKILL
    assert "report a transition as successful" in BUILD_SKILL


def test_pull_request_is_required_before_in_review():
    push = BUILD_SKILL.index("Commit the verified change and push")
    open_pr = BUILD_SKILL.index("Open an implementation PR")
    link_pr = BUILD_SKILL.index("Link the intended PR")
    verify_pr = BUILD_SKILL.index("Verify through GitHub readback")
    handoff = BUILD_SKILL.index("Save and read back a short issue-comment handoff")
    in_review = BUILD_SKILL.index("move `In progress` to `In review`")

    assert push < open_pr < link_pr < verify_pr < handoff < in_review
    assert "mandatory for both Standard and Lite" in normalized(BUILD_SKILL)
    assert "Never assert `native-pr-link` without live readback" in BUILD_SKILL
    assert "failed PR write is not a review handoff" in BUILD_SKILL


def test_review_uses_issue_requirements_and_applicable_git_design():
    review = normalized((WORKFLOW_KIT / "skills/review/SKILL.md").read_text())
    template = (WORKFLOW_KIT / "templates/shared/review.md").read_text()
    assert "canonical issue's approved requirements and acceptance criteria" in review
    assert "verified against its immutable snapshot" in review
    assert "Git technical-design revision linked from that issue" in review
    assert "technical decisions, interfaces, constraints, and NFR verification" in review
    assert "record that the section is empty" in review
    assert "requiring a not-applicable rationale" in review
    assert "Missing or stale Standard design evidence blocks review" in review
    assert "match the current Build handoff and tested head" in review
    assert "## Criterion evidence" in template
    assert "## Design conformance" in template
    assert "Native PR relationship:" in template
    assert "Technical design:" in template


def test_issue_template_has_mode_specific_technical_design():
    template = (WORKFLOW_KIT / "templates/shared/requirement.md").read_text()
    requirements = (
        WORKFLOW_KIT / "skills/requirements/SKILL.md"
    ).read_text()
    lite = normalized(
        (WORKFLOW_KIT / "profiles/lite/PROFILE.md").read_text()
    )
    standard = normalized(STANDARD_PROFILE)

    assert "## User requirements\n" in template
    assert "## Technical design\n" in template
    scope = template.split("<!-- approved-requirements:start -->", 1)[1].split(
        "<!-- approved-requirements:end -->", 1
    )[0]
    assert "### Acceptance and verification" in scope
    assert "## Technical design" not in scope
    assert template.index("<!-- approved-requirements:end -->") < template.index(
        "## Technical design\n"
    )
    assert "either leaves the section empty or writes simple technical details" in (
        normalized(template)
    )
    assert "Requirements decides whether to leave the section empty" in (
        normalized(requirements)
    )
    assert "No separate Git design document or technical sign-off is required" in lite
    assert "empty Technical design section does not block review" in lite
    assert "Technical design links to the Git architecture/design document" in standard
    assert "Do not replace that document with inline technical notes" in standard


def test_build_and_review_allow_empty_lite_design_without_a_git_document():
    build = normalized(BUILD_SKILL)
    review = normalized((WORKFLOW_KIT / "skills/review/SKILL.md").read_text())
    record = normalized(
        (WORKFLOW_KIT / "templates/shared/review.md").read_text()
    )
    assert "Lite uses any simple inline details and permits an empty section" in build
    assert "an empty Technical design section is valid" in build
    assert "reviewed inline design content (or empty section)" in review
    assert "Do not require a Git design snapshot for Lite" in review
    assert "Lite technical questions go to Requirements" in review
    assert "an empty section needs no rationale or conformance rows" in record


def test_review_fixes_reuse_the_same_branch_and_pr():
    assert "resumes the\nsame item, branch, and PR" in BUILD_SKILL
    assert "return it to `In review`" in BUILD_SKILL
    assert "new head requires a fresh Review verdict" in BUILD_SKILL
    fixes = BUILD_SKILL.split("## Review fixes", 1)[1]
    assert fixes.index("Recheck the native issue/PR relationship") < fixes.index(
        "return it to `In review`"
    )


def test_build_cannot_merge_close_or_mark_done():
    required = [
        "Never review your own implementation",
        "Never merge or enable auto-merge",
        "Never move an item to `Done` or close its issue",
        "closeout_owner",
    ]

    for phrase in required:
        assert phrase in BUILD_SKILL


def test_accepted_work_is_not_prematurely_done():
    assert "Accepted work remains `In review`" in STANDARD_PROFILE
    assert "completed child Task does not make its Feature Done" in STANDARD_PROFILE
    assert "Deployment is separate" in normalized(STANDARD_PROFILE)


def test_feature_and_task_have_distinct_architecture_and_done_gates():
    profile = normalized(STANDARD_PROFILE)
    assert "parent sign-off applies" in profile
    assert "Task-specific Architect sign-off" in profile
    assert "Task can become Done after its own approved slice" in profile
    assert "Feature Done requires every required child slice" in profile


def test_statuses_have_one_dispatch_owner_and_no_deliver_stage():
    expected = {
        "Inbox": "Requirements",
        "Requirement shaping": "Requirements",
        "Technical shaping": "Architect",
        "Ready": "Build",
        "In progress": "Build",
        "In review": "Review",
        "Done": "None",
    }
    for status, owner in expected.items():
        assert f"| {status} | {owner} |" in PLAYBOOK
    assert "There is no separate Deliver status, stage, or agent" in normalized(PLAYBOOK)


def test_ready_does_not_require_preassignment():
    architect = (
        WORKFLOW_KIT / "profiles" / "standard" / "skills" / "architect" / "SKILL.md"
    ).read_text()
    assert "assignment is recorded atomically when Build claims `Ready`" in normalized(architect)
    assert "not a prerequisite for Architect to set `Ready`" in normalized(architect)
    assert "current session is explicitly assigned" not in BUILD_SKILL


def test_repository_policy_defines_dispatch_fields():
    policy = (ROOT / "_project" / "backlog-policy.md").read_text()
    for field in [
        "| Status | single select |",
        "| Action Owner | single select |",
        "| Assignees | native people field |",
        "| Claim Session | text |",
        "| Resume Status | single select |",
    ]:
        assert field in policy
    assert "automation must never dispatch from it" in normalized(policy)
