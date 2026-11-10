"""Executable workflow contract and read-only GitHub preflight."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable

import yaml


SUPPORTED_CLOSEOUT_OWNER = "Review"
REQUIRED_FIELD_KEYS = {
    "status",
    "action_owner",
    "assignees",
    "claim_session",
    "resume_status",
    "review_verdict",
    "work_type",
}
REQUIRED_OPTION_KEYS = {
    "status",
    "action_owner",
    "resume_status",
    "review_verdict",
    "work_type",
}
FORBIDDEN_MANIFEST_KEYS = {
    "token",
    "password",
    "secret",
    "credential",
    "current_status",
    "assignment",
    "claim",
    "verdict",
    "evidence",
}


def load_yaml(path: Path) -> dict[str, Any]:
    """Load one YAML mapping."""
    with path.open(encoding="utf-8") as stream:
        value = yaml.safe_load(stream)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a YAML mapping")
    return value


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else [value]


def _walk_keys(value: Any) -> list[str]:
    keys: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            keys.append(str(key))
            keys.extend(_walk_keys(child))
    elif isinstance(value, list):
        for child in value:
            keys.extend(_walk_keys(child))
    return keys


def validate_contract(contract: dict[str, Any]) -> list[str]:
    """Validate lifecycle references and required reachability."""
    errors: list[str] = []
    for key in (
        "version",
        "roles",
        "statuses",
        "profiles",
        "work-types",
        "review-verdicts",
        "evidence",
        "transitions",
    ):
        if key not in contract:
            errors.append(f"contract missing {key}")
    if errors:
        return errors
    if contract["version"] != 1:
        errors.append("contract version must be 1")

    roles = set(contract["roles"].values())
    statuses = contract["statuses"]
    profiles = set(contract["profiles"])
    work_types = set(contract["work-types"])
    evidence = set(contract["evidence"])
    labels: set[str] = set()

    for status_key, status in statuses.items():
        label = status.get("label")
        owner = status.get("owner")
        if not label:
            errors.append(f"status {status_key} has no label")
        elif label in labels:
            errors.append(f"duplicate status label {label}")
        labels.add(label)
        if owner not in roles | {"explicit"}:
            errors.append(f"status {status_key} has unknown owner {owner}")
        unknown_profiles = set(status.get("profiles", [])) - profiles
        if unknown_profiles:
            errors.append(
                f"status {status_key} has unknown profiles {sorted(unknown_profiles)}"
            )

    transition_ids: set[str] = set()
    static_edges: list[tuple[str, str, set[str], set[str]]] = []
    has_block = False
    has_resume = False
    has_fix_cycle = False
    forbidden_claim_gates = {"accepted-assignment", "accepted-claim"}

    for transition in contract["transitions"]:
        transition_id = transition.get("id")
        if not transition_id:
            errors.append("transition missing id")
            continue
        if transition_id in transition_ids:
            errors.append(f"duplicate transition id {transition_id}")
        transition_ids.add(transition_id)

        sources = _as_list(transition.get("from"))
        target = transition.get("to")
        actor = transition.get("actor")
        transition_profiles = set(transition.get("profiles", []))
        transition_work_types = set(transition.get("work-types", []))
        required = set(transition.get("requires", []))

        for source in sources:
            if source not in statuses:
                errors.append(f"transition {transition_id} has unknown source {source}")
        if target not in statuses and target != "$resume-status":
            errors.append(f"transition {transition_id} has unknown target {target}")
        if actor not in roles | {"current-owner", "action-owner"}:
            errors.append(f"transition {transition_id} has unknown actor {actor}")
        if not transition_profiles or transition_profiles - profiles:
            errors.append(f"transition {transition_id} has invalid profiles")
        if transition_work_types - work_types:
            errors.append(f"transition {transition_id} has invalid work types")
        unknown_evidence = required - evidence
        if unknown_evidence:
            errors.append(
                f"transition {transition_id} references unknown evidence "
                f"{sorted(unknown_evidence)}"
            )
        result_owner = transition.get("result-owner")
        if result_owner not in roles | {None, "explicit", "target-default"}:
            errors.append(
                f"transition {transition_id} has unknown result owner {result_owner}"
            )
        if transition_id == "claim-build-work" and required & forbidden_claim_gates:
            errors.append("Build claim must not require an already accepted claim")

        if "blocked" in sources:
            has_resume = target == "$resume-status"
        if target == "blocked":
            has_block = True
        if "in-review" in sources and target == "in-progress":
            has_fix_cycle = True
        if target in statuses:
            for source in sources:
                static_edges.append(
                    (source, target, transition_profiles, transition_work_types)
                )

    if not has_block:
        errors.append("contract has no transition into Blocked")
    if not has_resume:
        errors.append("contract has no Resume Status transition from Blocked")
    if not has_fix_cycle:
        errors.append("contract has no Review-to-Build fix cycle")

    for profile, work_type in (("lite", "Task"), ("standard", "Task"), ("standard", "Feature")):
        reachable = {"inbox"}
        changed = True
        while changed:
            changed = False
            for source, target, edge_profiles, edge_work_types in static_edges:
                if profile not in edge_profiles:
                    continue
                if edge_work_types and work_type not in edge_work_types:
                    continue
                if source in reachable and target not in reachable:
                    reachable.add(target)
                    changed = True
        if "done" not in reachable:
            errors.append(f"Done is unreachable for {profile} {work_type}")

    return errors


def validate_manifest(
    manifest: dict[str, Any], contract: dict[str, Any]
) -> list[str]:
    """Validate repository configuration without contacting GitHub."""
    errors: list[str] = []
    required = {
        "version",
        "contract",
        "mode",
        "repository",
        "project",
        "artifacts",
        "review",
        "closeout_owner",
    }
    missing = required - set(manifest)
    if missing:
        errors.append(f"manifest missing {sorted(missing)}")
        return errors
    if manifest["version"] != 1:
        errors.append("manifest version must be 1")
    if manifest["mode"] not in contract.get("profiles", []):
        errors.append(f"unsupported mode {manifest['mode']}")
    if manifest["closeout_owner"] != SUPPORTED_CLOSEOUT_OWNER:
        errors.append(
            f"closeout_owner must be {SUPPORTED_CLOSEOUT_OWNER}; "
            "repository configuration cannot redefine product role semantics"
        )

    project = manifest.get("project", {})
    fields = project.get("fields", {})
    options = project.get("options", {})
    missing_fields = REQUIRED_FIELD_KEYS - set(fields)
    missing_options = REQUIRED_OPTION_KEYS - set(options)
    if missing_fields:
        errors.append(f"manifest missing Project fields {sorted(missing_fields)}")
    if missing_options:
        errors.append(f"manifest missing Project options {sorted(missing_options)}")

    mode = manifest.get("mode")
    expected_statuses = {
        status["label"]
        for status in contract.get("statuses", {}).values()
        if not status.get("profiles") or mode in status["profiles"]
    }
    configured_statuses = set(options.get("status", []))
    missing_statuses = expected_statuses - configured_statuses
    if missing_statuses:
        errors.append(f"manifest missing Status options {sorted(missing_statuses)}")

    configured_owners = set(options.get("action_owner", []))
    expected_owners = set(contract.get("roles", {}).values())
    if expected_owners - configured_owners:
        errors.append(
            f"manifest missing Action Owner options "
            f"{sorted(expected_owners - configured_owners)}"
        )

    forbidden = {
        key
        for key in _walk_keys(manifest)
        if key.casefold() in FORBIDDEN_MANIFEST_KEYS or key.casefold().endswith("_id")
    }
    if forbidden:
        errors.append(f"manifest contains mutable or secret keys {sorted(forbidden)}")

    repository_name = manifest.get("repository", {}).get("name", "")
    artifact_repository = manifest.get("artifacts", {}).get("repository", "")
    for label, value in (
        ("repository.name", repository_name),
        ("artifacts.repository", artifact_repository),
    ):
        if value.count("/") != 1:
            errors.append(f"{label} must use owner/name")
    if not isinstance(project.get("number"), int) or project.get("number", 0) < 1:
        errors.append("project.number must be a positive integer")
    if manifest.get("review", {}).get("merge_strategy") not in {
        "squash",
        "merge",
        "rebase",
    }:
        errors.append("review.merge_strategy is invalid")
    return errors


@dataclass(frozen=True)
class TransitionDecision:
    allowed: bool
    transition_id: str
    from_status: str
    to_status: str | None
    result_owner: str | None
    missing_evidence: tuple[str, ...] = ()
    reason: str = ""
    idempotent: bool = False


def evaluate_transition(
    contract: dict[str, Any], transition_id: str, context: dict[str, Any]
) -> TransitionDecision:
    """Evaluate one transition against supplied, already-read evidence."""
    transition = next(
        (
            candidate
            for candidate in contract["transitions"]
            if candidate["id"] == transition_id
        ),
        None,
    )
    current_status = context.get("status")
    if transition is None:
        return TransitionDecision(
            False, transition_id, current_status, None, None, reason="unknown transition"
        )

    target = transition["to"]
    if target == "$resume-status":
        target = context.get("resume_status")
    if target not in contract["statuses"]:
        return TransitionDecision(
            False,
            transition_id,
            current_status,
            target,
            None,
            reason="missing or invalid Resume Status",
        )

    sources = _as_list(transition["from"])
    idempotent = current_status == target
    if current_status not in sources and not idempotent:
        return TransitionDecision(
            False,
            transition_id,
            current_status,
            target,
            None,
            reason=f"transition requires status {sources}",
        )

    profile = context.get("profile")
    work_type = context.get("work_type")
    if profile not in transition.get("profiles", []):
        return TransitionDecision(
            False, transition_id, current_status, target, None, reason="profile not allowed"
        )
    allowed_work_types = transition.get("work-types", [])
    if allowed_work_types and work_type not in allowed_work_types:
        return TransitionDecision(
            False,
            transition_id,
            current_status,
            target,
            None,
            reason="work type not allowed",
        )

    actor = transition["actor"]
    expected_actor = actor
    if actor in {"current-owner", "action-owner"}:
        expected_actor = context.get("action_owner")
    if context.get("actor") != expected_actor:
        return TransitionDecision(
            False,
            transition_id,
            current_status,
            target,
            None,
            reason=f"transition actor must be {expected_actor}",
        )

    supplied_evidence = context.get("evidence", {})
    missing = tuple(
        gate
        for gate in transition.get("requires", [])
        if not supplied_evidence.get(gate, False)
    )
    if missing:
        return TransitionDecision(
            False,
            transition_id,
            current_status,
            target,
            None,
            missing_evidence=missing,
            reason="required evidence is missing",
            idempotent=idempotent,
        )

    result_owner = transition.get("result-owner")
    if result_owner == "explicit":
        result_owner = context.get("result_owner")
        if result_owner not in set(contract["roles"].values()) - {"None"}:
            return TransitionDecision(
                False,
                transition_id,
                current_status,
                target,
                None,
                reason="blocked transition requires an explicit Action Owner",
            )
    elif result_owner == "target-default" or result_owner is None:
        result_owner = contract["statuses"][target]["owner"]

    if idempotent and context.get("action_owner") != result_owner:
        return TransitionDecision(
            False,
            transition_id,
            current_status,
            target,
            result_owner,
            reason="partial write detected: target owner does not match",
            idempotent=True,
        )

    return TransitionDecision(
        True,
        transition_id,
        current_status,
        target,
        result_owner,
        reason="transition is legal" if not idempotent else "transition already applied",
        idempotent=idempotent,
    )


@dataclass
class PreflightReport:
    passed: bool = True
    checks: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def fail(self, message: str) -> None:
        self.passed = False
        self.errors.append(message)


Runner = Callable[[list[str]], subprocess.CompletedProcess[str]]


def _default_runner(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, check=False, capture_output=True, text=True)


def _run_json(runner: Runner, args: list[str]) -> Any:
    completed = runner(args)
    if completed.returncode:
        message = completed.stderr.strip() or completed.stdout.strip()
        raise RuntimeError(message or f"command failed: {' '.join(args)}")
    return json.loads(completed.stdout)


def run_preflight(
    manifest: dict[str, Any],
    contract: dict[str, Any],
    *,
    offline: bool = False,
    runner: Runner = _default_runner,
) -> PreflightReport:
    """Validate local configuration and optionally read live GitHub schema."""
    report = PreflightReport()
    for error in validate_contract(contract):
        report.fail(f"Contract: {error}")
    for error in validate_manifest(manifest, contract):
        report.fail(f"Manifest: {error}")
    if report.errors or offline:
        if not report.errors:
            report.checks.append("Local contract and manifest are valid")
        return report

    auth = runner(["gh", "auth", "status"])
    if auth.returncode:
        report.fail("GitHub authentication is unavailable")
        return report
    report.checks.append("GitHub authentication is available")

    repository = manifest["repository"]["name"]
    base_branch = manifest["repository"]["base_branch"]
    merge_strategy = manifest["review"]["merge_strategy"]
    try:
        repo = _run_json(
            runner,
            [
                "gh",
                "repo",
                "view",
                repository,
                "--json",
                "nameWithOwner,viewerPermission,mergeCommitAllowed,rebaseMergeAllowed,squashMergeAllowed",
            ],
        )
        if repo.get("nameWithOwner") != repository:
            report.fail(f"Repository resolved as {repo.get('nameWithOwner')}")
        if repo.get("viewerPermission") not in {"ADMIN", "MAINTAIN", "WRITE"}:
            report.fail("Repository write permission is required for workflow operation")
        strategy_key = {
            "squash": "squashMergeAllowed",
            "merge": "mergeCommitAllowed",
            "rebase": "rebaseMergeAllowed",
        }[merge_strategy]
        if not repo.get(strategy_key):
            report.fail(f"Configured merge strategy {merge_strategy} is disabled")
        _run_json(
            runner,
            ["gh", "api", "--method", "GET", f"repos/{repository}/branches/{base_branch}"],
        )
        report.checks.append(f"Repository and base branch are accessible: {repository}@{base_branch}")
    except RuntimeError as error:
        report.fail(f"Repository preflight failed: {error}")

    artifact_repository = manifest["artifacts"]["repository"]
    try:
        artifact = _run_json(
            runner,
            [
                "gh",
                "repo",
                "view",
                artifact_repository,
                "--json",
                "nameWithOwner,viewerPermission",
            ],
        )
        if artifact.get("nameWithOwner") != artifact_repository:
            report.fail(f"Artifact repository resolved as {artifact.get('nameWithOwner')}")
        if artifact.get("viewerPermission") not in {"ADMIN", "MAINTAIN", "WRITE"}:
            report.fail("Artifact repository write permission is required")
        report.checks.append(f"Artifact repository is accessible: {artifact_repository}")
    except RuntimeError as error:
        report.fail(f"Artifact repository preflight failed: {error}")

    project_owner = manifest["project"]["owner"]
    project_number = str(manifest["project"]["number"])
    try:
        project = _run_json(
            runner,
            [
                "gh",
                "project",
                "view",
                project_number,
                "--owner",
                project_owner,
                "--format",
                "json",
            ],
        )
        project_id = project["id"]
        permission = _run_json(
            runner,
            [
                "gh",
                "api",
                "graphql",
                "-f",
                "query=query($id:ID!){node(id:$id){... on ProjectV2{viewerCanUpdate}}}",
                "-f",
                f"id={project_id}",
            ],
        )
        if not permission["data"]["node"]["viewerCanUpdate"]:
            report.fail("Project update permission is required for workflow operation")
        field_payload = _run_json(
            runner,
            [
                "gh",
                "project",
                "field-list",
                project_number,
                "--owner",
                project_owner,
                "--limit",
                "100",
                "--format",
                "json",
            ],
        )
        live_fields = {item["name"]: item for item in field_payload["fields"]}
        for logical_name, configured_name in manifest["project"]["fields"].items():
            live = live_fields.get(configured_name)
            if live is None:
                report.fail(
                    f"Project field missing: {logical_name} configured as {configured_name}"
                )
                continue
            expected_options = manifest["project"]["options"].get(logical_name)
            if expected_options is None:
                continue
            live_options = {option["name"] for option in live.get("options", [])}
            missing_options = set(expected_options) - live_options
            if missing_options:
                report.fail(
                    f"{configured_name} option mismatch; missing "
                    f"{sorted(missing_options)}; live {sorted(live_options)}"
                )
        report.checks.append(
            f"Project schema is readable: {project_owner}/{project_number}"
        )
    except (KeyError, RuntimeError) as error:
        report.fail(f"Project preflight failed: {error}")

    return report


def format_report(report: PreflightReport) -> str:
    lines = [f"Workflow preflight: {'PASSED' if report.passed else 'FAILED'}"]
    if report.checks:
        lines.append("")
        lines.extend(f"OK: {check}" for check in report.checks)
    if report.errors:
        lines.append("")
        lines.extend(f"ERROR: {error}" for error in report.errors)
    lines.extend(["", "No changes were made."])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    default_manifest = Path(__file__).with_name("workflow.yaml")
    parser.add_argument("--manifest", type=Path, default=default_manifest)
    parser.add_argument("--contract", type=Path)
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)

    try:
        manifest = load_yaml(args.manifest)
        contract_path = args.contract or args.manifest.parent / manifest["contract"]
        contract = load_yaml(contract_path)
        report = run_preflight(manifest, contract, offline=args.offline)
    except (KeyError, OSError, ValueError, yaml.YAMLError) as error:
        report = PreflightReport(False, errors=[f"Configuration: {error}"])

    if args.as_json:
        print(json.dumps(asdict(report), indent=2, sort_keys=True))
    else:
        print(format_report(report))
    return 0 if report.passed else 2


if __name__ == "__main__":
    sys.exit(main())
