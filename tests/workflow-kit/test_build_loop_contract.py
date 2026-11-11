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
    verify_pr = BUILD_SKILL.index("Verify through GitHub readback")
    in_review = BUILD_SKILL.index("move `In progress` to `In review`")

    assert push < open_pr < verify_pr < in_review
    assert "failed PR write is not a review handoff" in BUILD_SKILL


def test_review_fixes_reuse_the_same_branch_and_pr():
    assert "resumes the\nsame item, branch, and PR" in BUILD_SKILL
    assert "return it to `In review`" in BUILD_SKILL
    assert "new head requires a fresh Review verdict" in BUILD_SKILL


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
