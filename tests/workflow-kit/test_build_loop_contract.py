from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_KIT = ROOT / "workflow-kit"
PLAYBOOK = (WORKFLOW_KIT / "PLAYBOOK.md").read_text()
BUILD_SKILL = (WORKFLOW_KIT / "skills" / "build" / "SKILL.md").read_text()
STANDARD_PROFILE = (
    WORKFLOW_KIT / "profiles" / "standard" / "PROFILE.md"
).read_text()


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
    assert "Review session to merge passing PRs" in normalized(PLAYBOOK)
    assert "Requirements closeout invocation is not required" in normalized(PLAYBOOK)
    assert "backlog policy linked from the root `AGENTS.md`" in PLAYBOOK


def test_current_guidance_uses_requirements_terminology():
    agents = (ROOT / "AGENTS.md").read_text()
    assert "brief" not in agents.lower().replace("briefcase", "")
    assert "Feature\nPRD" in agents
    assert "task document for Lite" in agents
    assert "## Legacy CLI Project Root Resolution" in agents
    assert "Use GitHub directly for this repository's backlog" in agents

    template = WORKFLOW_KIT / "templates" / "standard" / "brief.md"
    assert template.read_text().startswith("# Standard Feature PRD\n")
    for path in WORKFLOW_KIT.rglob("*.md"):
        prose = path.read_text().replace("brief.md", "").replace("Briefcase", "")
        assert "brief" not in prose.lower(), path


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
        "Standard requires Architect sign-off",
        "Every native blocker is `Done`",
        "current session is explicitly assigned",
        "No other active session, branch, worktree, or implementation PR",
        "do not start coding",
    ]

    for phrase in required:
        assert phrase in BUILD_SKILL


def test_standard_signoff_is_revision_bound():
    required = [
        "exact approved Feature PRD revision",
        "material requirements change makes that sign-off stale",
        "refuse a Standard claim when sign-off is missing",
    ]

    for phrase in required:
        assert phrase in normalized(STANDARD_PROFILE)


def test_claim_happens_before_code_and_requires_readback():
    claim = BUILD_SKILL.index("## Claim and readback")
    build = BUILD_SKILL.index("## Build and verify")

    assert claim < build
    assert "Move the Project status from `Ready` to `In progress`" in BUILD_SKILL
    assert "Re-read both the claim and status" in BUILD_SKILL
    assert "reconcile the concurrent change" in BUILD_SKILL


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
        "Requirements verifies closeout",
    ]

    for phrase in required:
        assert phrase in BUILD_SKILL


def test_accepted_work_is_not_prematurely_done():
    assert "Accepted work remains `In review`" in PLAYBOOK
    assert "completed child Task does not make its Feature Done" in STANDARD_PROFILE
    assert "Deployment is separate" in STANDARD_PROFILE
