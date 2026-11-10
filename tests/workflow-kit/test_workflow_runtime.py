import importlib.util
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
KIT = ROOT / "workflow-kit"

SPEC = importlib.util.spec_from_file_location(
    "workflow_runtime", KIT / "runtime.py"
)
RUNTIME = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = RUNTIME
SPEC.loader.exec_module(RUNTIME)

CONTRACT = RUNTIME.load_yaml(KIT / "contract.yaml")
MANIFEST = RUNTIME.load_yaml(KIT / "workflow.yaml")


def evidence_for(transition_id):
    transition = next(
        item for item in CONTRACT["transitions"] if item["id"] == transition_id
    )
    return {gate: True for gate in transition.get("requires", [])}


def decide(transition_id, **overrides):
    transition = next(
        item for item in CONTRACT["transitions"] if item["id"] == transition_id
    )
    source = transition["from"]
    if isinstance(source, list):
        source = source[0]
    context = {
        "status": source,
        "profile": "standard",
        "work_type": "Task",
        "actor": transition["actor"],
        "action_owner": transition["actor"],
        "evidence": evidence_for(transition_id),
    }
    context.update(overrides)
    return RUNTIME.evaluate_transition(CONTRACT, transition_id, context)


def completed(args, payload=None, returncode=0, stderr=""):
    stdout = "" if payload is None else json.dumps(payload)
    return subprocess.CompletedProcess(args, returncode, stdout, stderr)


def live_fields(manifest=MANIFEST):
    fields = []
    for logical_name, field_name in manifest["project"]["fields"].items():
        fields.append(
            {
                "name": field_name,
                "type": "ProjectV2Field",
                "options": [
                    {"id": f"option-{index}", "name": name}
                    for index, name in enumerate(
                        manifest["project"]["options"].get(logical_name, [])
                    )
                ],
            }
        )
    return fields


def make_runner(fields=None):
    calls = []
    configured_fields = fields if fields is not None else live_fields()

    def runner(args):
        calls.append(args)
        if args[:3] == ["gh", "auth", "status"]:
            return completed(args)
        if args[:3] == ["gh", "repo", "view"]:
            repository = args[3]
            payload = {
                "nameWithOwner": repository,
                "viewerPermission": "ADMIN",
            }
            if repository == MANIFEST["repository"]["name"]:
                payload.update(
                    {
                        "mergeCommitAllowed": True,
                        "rebaseMergeAllowed": True,
                        "squashMergeAllowed": True,
                    }
                )
            return completed(args, payload)
        if args[:4] == ["gh", "api", "--method", "GET"]:
            return completed(args, {"name": MANIFEST["repository"]["base_branch"]})
        if args[:3] == ["gh", "project", "view"]:
            return completed(args, {"id": "PVT_project", "number": 5})
        if args[:3] == ["gh", "api", "graphql"]:
            return completed(
                args, {"data": {"node": {"viewerCanUpdate": True}}}
            )
        if args[:3] == ["gh", "project", "field-list"]:
            return completed(args, {"fields": configured_fields})
        return completed(args, returncode=1, stderr=f"unexpected command: {args}")

    return runner, calls


def test_contract_and_manifest_are_valid():
    assert RUNTIME.validate_contract(CONTRACT) == []
    assert RUNTIME.validate_manifest(MANIFEST, CONTRACT) == []
    assert MANIFEST["closeout_owner"] == "Review"


def test_manifest_contains_names_not_live_ids_or_mutable_state():
    text = (KIT / "workflow.yaml").read_text()
    assert "PVT_" not in text
    assert "option_id" not in text
    assert "current_status" not in text
    assert "token:" not in text


def test_standard_happy_path_is_executable():
    steps = [
        ("standard-approved-at-creation", "inbox", "technical-shaping", "Requirements"),
        ("ready-standard-task", "technical-shaping", "ready", "Architect"),
        ("claim-build-work", "ready", "in-progress", "Build"),
        ("handoff-for-review", "in-progress", "in-review", "Build"),
        ("complete-task", "in-review", "done", "Review"),
    ]
    for transition_id, source, target, actor in steps:
        decision = decide(
            transition_id,
            status=source,
            actor=actor,
            action_owner=actor,
        )
        assert decision.allowed, decision
        assert decision.to_status == target


def test_ready_rejects_missing_approval_stale_signoff_and_dependency():
    for missing_gate in (
        "approved-requirement",
        "current-feature-signoff",
        "current-task-architecture",
        "completed-dependencies",
    ):
        evidence = evidence_for("ready-standard-task")
        evidence[missing_gate] = False
        decision = decide(
            "ready-standard-task",
            actor="Architect",
            action_owner="Architect",
            evidence=evidence,
        )
        assert not decision.allowed
        assert missing_gate in decision.missing_evidence


def test_build_claim_has_no_ready_assignment_cycle():
    transition = next(
        item for item in CONTRACT["transitions"] if item["id"] == "claim-build-work"
    )
    assert "accepted-claim" not in transition["requires"]
    assert "accepted-assignment" not in transition["requires"]
    assert set(transition["effects"]) == {"record-assignee", "record-claim-session"}

    evidence = evidence_for("claim-build-work")
    evidence["no-competing-work"] = False
    decision = decide(
        "claim-build-work",
        actor="Build",
        action_owner="Build",
        evidence=evidence,
    )
    assert not decision.allowed
    assert decision.missing_evidence == ("no-competing-work",)


def test_changed_head_or_unmerged_acceptance_cannot_complete():
    evidence = evidence_for("complete-task")
    evidence["reviewed-head-current"] = False
    changed_head = decide(
        "complete-task",
        actor="Review",
        action_owner="Review",
        evidence=evidence,
    )
    assert not changed_head.allowed
    assert changed_head.missing_evidence == ("reviewed-head-current",)

    evidence = evidence_for("complete-task")
    evidence["landing-verified"] = False
    unmerged = decide(
        "complete-task",
        actor="Review",
        action_owner="Review",
        evidence=evidence,
    )
    assert not unmerged.allowed


def test_task_and_feature_completion_have_distinct_gates():
    task = decide(
        "complete-task",
        actor="Review",
        action_owner="Review",
        work_type="Task",
    )
    assert task.allowed

    wrong_transition = decide(
        "complete-feature",
        actor="Review",
        action_owner="Review",
        work_type="Task",
    )
    assert not wrong_transition.allowed

    feature_evidence = evidence_for("complete-feature")
    feature_evidence["feature-release-evidence"] = False
    feature = decide(
        "complete-feature",
        actor="Review",
        action_owner="Review",
        work_type="Feature",
        evidence=feature_evidence,
    )
    assert not feature.allowed


def test_blocked_work_requires_owner_resume_path_and_revalidation():
    block = decide(
        "block-work",
        actor="Requirements",
        action_owner="Requirements",
        result_owner="Architect",
    )
    assert block.allowed
    assert block.to_status == "blocked"
    assert block.result_owner == "Architect"

    resume_evidence = evidence_for("resume-blocked-work")
    resume_evidence["target-gates-revalidated"] = False
    resume = decide(
        "resume-blocked-work",
        status="blocked",
        resume_status="technical-shaping",
        actor="Architect",
        action_owner="Architect",
        evidence=resume_evidence,
    )
    assert not resume.allowed


def test_partial_write_rerun_is_idempotent_only_when_owner_matches():
    good = decide(
        "claim-build-work",
        status="in-progress",
        actor="Build",
        action_owner="Build",
    )
    assert good.allowed
    assert good.idempotent

    bad = decide(
        "claim-build-work",
        status="in-progress",
        actor="Build",
        action_owner="Review",
    )
    assert not bad.allowed
    assert bad.idempotent
    assert "partial write" in bad.reason


def test_live_preflight_passes_without_mutating_github():
    runner, calls = make_runner()
    report = RUNTIME.run_preflight(MANIFEST, CONTRACT, runner=runner)
    assert report.passed, report.errors
    assert all(
        command not in call
        for call in calls
        for command in ("edit", "create", "delete", "add", "remove")
    )


def test_live_preflight_reports_option_mismatch_without_repair():
    fields = live_fields()
    status_name = MANIFEST["project"]["fields"]["status"]
    status = next(field for field in fields if field["name"] == status_name)
    status["options"] = [
        option for option in status["options"] if option["name"] != "Technical shaping"
    ]
    runner, calls = make_runner(fields)
    report = RUNTIME.run_preflight(MANIFEST, CONTRACT, runner=runner)
    assert not report.passed
    assert any("Technical shaping" in error for error in report.errors)
    assert "No changes were made." in RUNTIME.format_report(report)
    assert all("edit" not in call for call in calls)


def test_offline_preflight_validates_without_calling_github():
    def forbidden_runner(args):
        raise AssertionError(f"runner called in offline mode: {args}")

    report = RUNTIME.run_preflight(
        MANIFEST, CONTRACT, offline=True, runner=forbidden_runner
    )
    assert report.passed
