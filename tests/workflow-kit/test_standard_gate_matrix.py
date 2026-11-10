"""Contract evidence for Standard gates.

These tests validate the shipped workflow assets and staged example records. They
do not claim that prose is a runtime gate engine or that live GitHub mutations
were exercised.
"""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
KIT = ROOT / "workflow-kit"

ASSETS = {
    "playbook": (KIT / "PLAYBOOK.md").read_text(),
    "requirements": (KIT / "skills/requirements/SKILL.md").read_text(),
    "architect": (KIT / "profiles/standard/skills/architect/SKILL.md").read_text(),
    "build": (KIT / "skills/build/SKILL.md").read_text(),
    "review": (KIT / "skills/review/SKILL.md").read_text(),
    "lite": (KIT / "profiles/lite/PROFILE.md").read_text(),
    "standard": (KIT / "profiles/standard/PROFILE.md").read_text(),
    "release": (KIT / "templates/standard/release.md").read_text(),
}
STANDARD_EXAMPLE = (KIT / "examples/standard-example.md").read_text()


def normalized(text):
    return " ".join(text.split())


CONTRACT_MATRIX = {
    "valid-standard-ready": {
        "architect": [
            "verified Done dependencies",
            "accepted Build assignment",
            "absence of competing claims",
            "set Ready last",
        ],
        "build": [
            "Project status is still `Ready`",
            "Move the Project status from `Ready` to `In progress`",
        ],
    },
    "missing-or-mismatched-signoff": {
        "standard": [
            "refuse a Standard claim when sign-off is missing",
            "names a different revision",
            "stopping technical question unresolved",
        ],
    },
    "material-requirement-change": {
        "architect": [
            "sign-off is stale",
            "approved revision changes after the sign-off",
            "Constraints, NFRs, approach assumptions, or release obligations",
            "Requirements returns the item to Architecture",
        ],
    },
    "unfinished-blocker-or-competing-owner": {
        "build": [
            "Every native blocker is `Done`",
            "current session is explicitly assigned",
            "No other active session, branch, worktree, or implementation PR",
            "Do not move skipped work to `In progress`",
        ],
    },
    "lite-technical-question": {
        "lite": [
            "Requirements-owned blocker",
            "Revalidate all shared Ready gates after resolution",
            "do not jump directly from Blocked to Ready",
            "invent an Architect prerequisite",
        ],
    },
    "accepted-but-unmerged": {
        "playbook": ["Accepted work remains `In review` until delivery gates pass"],
        "requirements": ["Accepted, landed, released, and deployed remain distinct"],
    },
    "changed-review-head": {
        "review": [
            "recorded implementation head equals the live PR head",
            "Any new commit invalidates the prior acceptance",
            "exact PR head",
        ],
    },
    "wrong-base-missing-checks-or-partial-scope": {
        "review": [
            "targets the intended base",
            "required checks pass",
            "complete issue coverage",
        ],
        "standard": [
            "complete scope coverage",
            "required checks",
        ],
    },
    "missing-standard-release-evidence": {
        "standard": [
            "applicable version evidence",
            "linked release record",
            "Accepted work remains `In review`",
        ],
    },
    "release-note-exemption-is-bounded": {
        "release": [
            "Version applicability is independent",
            "exemption never waives version impact, checks, coverage, or readiness",
            "Version approval",
            "Readiness evidence",
        ],
    },
    "github-or-readback-failure": {
        "playbook": [
            "GitHub read or write failure pauses affected work",
            "do not claim a transition succeeded",
        ],
        "architect": [
            "Before any mutation, reread",
            "Read back the packet and sign-off",
            "Report partial-write failures",
        ],
        "build": [
            "Re-read both the claim and status",
            "Do not fall back to Markdown status",
        ],
        "review": ["never fall back to Markdown status"],
    },
}


@pytest.mark.parametrize(
    ("case", "asset", "phrases"),
    [
        (case, asset, phrases)
        for case, asset_contracts in CONTRACT_MATRIX.items()
        for asset, phrases in asset_contracts.items()
    ],
)
def test_instruction_contract_matrix(case, asset, phrases):
    text = normalized(ASSETS[asset])
    missing = [phrase for phrase in phrases if phrase not in text]
    assert missing == [], f"{case} missing from {asset}: {missing}"


def section(text, start, end=None):
    selected = text.split(start, 1)[1]
    return selected.split(end, 1)[0] if end else selected


def field(text, name):
    match = re.search(
        rf"^- {re.escape(name)}: (?:`([^`]*)`|(.+))$",
        text,
        re.MULTILINE,
    )
    if not match:
        return None
    return match.group(1) if match.group(1) is not None else match.group(2)


def validate_standard_example(text):
    errors = []
    feature = section(
        text,
        "## Requirement packet (Feature)",
        "## Feature PRD (Architect sign-off)",
    )
    signoff = section(
        text,
        "## Feature PRD (Architect sign-off)",
        "## Requirement packet (child Task — API endpoint)",
    )
    api_task = section(
        text,
        "## Requirement packet (child Task — API endpoint)",
        "## Requirement packet (child Task - date picker)",
    )
    ui_task = section(
        text,
        "## Requirement packet (child Task - date picker)",
        "## Standard release record",
    )
    release = section(text, "## Standard release record")

    approved_revisions = {
        field(feature, "Canonical requirement"),
        field(signoff, "Canonical requirement"),
        field(signoff, "Approved requirement revision"),
        field(api_task, "Approved parent revision"),
        field(ui_task, "Approved parent revision"),
        field(release, "Approved requirement revision"),
    }
    if None in approved_revisions or len(approved_revisions) != 1:
        errors.append("stale or missing requirement/sign-off revision")

    task_items = {
        field(api_task, "Work item").rsplit("/", 1)[-1],
        field(ui_task, "Work item").rsplit("/", 1)[-1],
    }
    coverage = field(release, "Child Tasks covered") or ""
    missing_tasks = sorted(task for task in task_items if f"#{task}" not in coverage)
    if missing_tasks:
        errors.append(f"partial child coverage: {', '.join(missing_tasks)}")
    if field(release, "Coverage complete") != "yes":
        errors.append("coverage is not complete")

    required_release_fields = [
        "Accepted head",
        "Landing evidence",
        "Version impact",
        "Version",
        "Version approval",
        "Required environments",
        "Readiness evidence",
        "Remaining obligations",
    ]
    for name in required_release_fields:
        if not field(release, name):
            errors.append(f"missing release evidence: {name}")

    if (
        field(release, "Remaining obligations")
        != "none in this illustrative completed record."
    ):
        errors.append("release obligations remain")
    if field(release, "Deployment") != "not claimed.":
        errors.append("deployment is inferred or ambiguous")
    return errors


def replace_field_in_section(text, section_heading, name, value):
    before, selected = text.split(section_heading, 1)
    pattern = rf"(^- {re.escape(name)}: )(?:`[^`]*`|[^\n]*)"
    updated, count = re.subn(
        pattern,
        rf"\g<1>`{value}`",
        selected,
        count=1,
        flags=re.MULTILINE,
    )
    assert count == 1
    return before + section_heading + updated


def test_completed_standard_record_is_internally_consistent():
    assert validate_standard_example(STANDARD_EXAMPLE) == []


@pytest.mark.parametrize(
    ("heading", "field_name", "value", "expected_error"),
    [
        (
            "## Feature PRD (Architect sign-off)",
            "Approved requirement revision",
            "docs/requirements/feat-42.md @ sha:stale999",
            "stale or missing requirement/sign-off revision",
        ),
        (
            "## Standard release record",
            "Child Tasks covered",
            "#43 (API)",
            "partial child coverage: 44",
        ),
        (
            "## Standard release record",
            "Version approval",
            "",
            "missing release evidence: Version approval",
        ),
        (
            "## Standard release record",
            "Readiness evidence",
            "",
            "missing release evidence: Readiness evidence",
        ),
        (
            "## Standard release record",
            "Deployment",
            "production complete",
            "deployment is inferred or ambiguous",
        ),
    ],
)
def test_standard_record_mutations_are_refused(
    heading, field_name, value, expected_error
):
    mutated = replace_field_in_section(STANDARD_EXAMPLE, heading, field_name, value)
    assert expected_error in validate_standard_example(mutated)


def test_lite_resolution_does_not_acquire_standard_gates():
    lite = normalized(ASSETS["lite"])
    assert "There is no Architect role" in lite
    assert "Standard release record requirement" in lite
    assert "Requirements-owned blocker" in lite
    assert "Revalidate all shared Ready gates after resolution" in lite


def test_matrix_is_explicitly_contract_evidence_not_runtime_proof():
    module_text = Path(__file__).read_text()
    assert "do not claim that prose is a runtime gate engine" in normalized(module_text)
    assert "live GitHub mutations were exercised" in normalized(module_text)
