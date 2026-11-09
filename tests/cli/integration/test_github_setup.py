"""Exercise GitHub-first onboarding without network calls or real credentials."""

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "setup-github.sh"
STATUSES = [
    "Inbox", "Shaping", "Ready", "In progress", "In review", "Blocked", "Done",
]
FAKE_GH = r'''
import json
import os
from pathlib import Path
import sys

args = sys.argv[1:]
state_file = Path(os.environ["GH_TEST_STATE"])
state = json.loads(state_file.read_text())
with Path(os.environ["GH_TEST_LOG"]).open("a") as log:
    log.write(json.dumps(args) + "\n")

def flag(name):
    return args[args.index(name) + 1]

def save():
    state_file.write_text(json.dumps(state))

def emit(value):
    if isinstance(value, bool):
        print(str(value).lower())
    else:
        print(value)

def error(message):
    print(message, file=sys.stderr)
    raise SystemExit(1)

def new_field(name, options=None):
    prefix = "PVTSSF_" if options is not None else "PVTF_"
    return {"id": prefix + name.replace(" ", "_"),
            "options": options, "type": "SINGLE_SELECT" if options else "TEXT"}

if args[:2] == ["auth", "status"]:
    if state.get("auth_error"):
        error("Authentication failed")
elif args[:2] == ["api", "repos/demo/app"]:
    emit("\t".join(str(state.get(k, True)).lower()
                   for k in ["issues", "repo_write", "repo_private"]))
elif args[:2] == ["project", "list"]:
    if flag("--jq") == ".totalCount":
        emit(len(state["projects"]))
    else:
        for project in state["projects"]:
            emit(str(project["number"]) + "\t" + project["title"])
elif args[:2] == ["project", "create"]:
    error("GraphQL: Variable $query is used by anonymous mutation but not declared")
elif args[:2] == ["project", "view"]:
    if flag("--jq") == ".items.totalCount":
        emit(state.get("items", 0))
    else:
        emit("\t".join(["PVT_demo", "https://github.com/users/demo/projects/7",
                       str(state.get("closed", False)).lower(),
                       str(state.get("public", False)).lower()]))
elif args[:2] == ["project", "field-list"]:
    expression = flag("--jq")
    if state.get("field_read_error"):
        error("Cannot read Project fields")
    if expression == ".totalCount":
        emit(len(state["fields"]))
    else:
        name = expression.split('select(.name == "')[1].split('"')[0]
        previous_calls = Path(os.environ["GH_TEST_LOG"]).read_text().splitlines()
        lookups = sum(json.loads(line) == args for line in previous_calls)
        if state.get("late_field_error") and name == "Work Type" and lookups >= 2:
            error("Late field lookup failure")
        field = state["fields"].get(name)
        if field:
            if expression.endswith(".id"):
                emit(field["id"])
            else:
                for option in field["options"] or []:
                    emit(option)
elif args[:2] == ["project", "field-create"]:
    if state.get("create_field_error"):
        error("Field creation denied")
    name = flag("--name")
    if name in state["fields"]:
        error("Duplicate field")
    options = flag("--single-select-options").split(",") if "--single-select-options" in args else None
    state["fields"][name] = new_field(name, options)
    save()
elif args[:2] == ["project", "link"]:
    if state.get("link_error"):
        error("Linking denied")
    state["linked"] = True
    save()
elif args[:2] == ["api", "graphql"]:
    if "--input" in args:
        payload = json.load(sys.stdin)
        if state.get("status_write_error"):
            error("Status mutation denied")
        state["fields"]["Status"]["options"] = [
            option["name"] for option in payload["variables"]["options"]]
        save()
        emit("{}")
    else:
        query = flag("query") if "query" in args else ""
        if not query:
            query = next(a[6:] for a in args if a.startswith("query="))
        if "repositoryOwner" in query:
            if state.get("owner_read_error"):
                error("Cannot resolve Project owner")
            emit(state.get("owner_id", "MDQ6VXNlcjE="))
        elif "createProjectV2" in query:
            if state.get("project_create_error"):
                error("Project creation denied")
            title = next(a[6:] for a in args if a.startswith("title="))
            state["projects"].append({"number": 7, "title": title})
            state["fields"] = {"Status": new_field("Status", ["Todo", "In Progress", "Done"])}
            save()
            emit(state.get("creation_number", 7))
        elif "viewerCanUpdate" in query:
            emit(state.get("project_write", True))
        elif "dataType" in query:
            field_id = next(a[3:] for a in args if a.startswith("id="))
            emit(next(f["type"] for f in state["fields"].values()
                      if f["id"] == field_id))
        elif "repositories" in query:
            emit(state.get("linked", False) and not state.get("link_readback_error"))
        else:
            error("Unexpected GraphQL query")
else:
    error("Unexpected gh invocation: " + repr(args))
'''


@pytest.fixture
def github(tmp_path):
    binary = tmp_path / "bin"
    binary.mkdir()
    gh = binary / "gh"
    gh.write_text(f"#!{sys.executable}\n" + FAKE_GH)
    gh.chmod(0o755)
    state = tmp_path / "state.json"
    log = tmp_path / "calls.jsonl"
    initial = {
        "projects": [{"number": 7, "title": "Briefcase Standard"}],
        "fields": {
            "Status": {
                "id": "PVTSSF_Status", "options": STATUSES, "type": "SINGLE_SELECT",
            },
        },
    }
    state.write_text(json.dumps(initial))
    env = {
        **os.environ,
        "PATH": str(binary) + os.pathsep + os.environ["PATH"],
        "GH_TEST_STATE": str(state),
        "GH_TEST_LOG": str(log),
    }

    def run(*extra, create=False, mode="standard", update=None):
        if update:
            current = json.loads(state.read_text())
            current.update(update)
            state.write_text(json.dumps(current))
        target = ["--create-project", "--title", "Briefcase Standard"] if create else ["--project", "7"]
        return subprocess.run(
            ["bash", str(SCRIPT), "--mode", mode, "--repo", "demo/app",
             "--owner", "demo", *target, *extra],
            env=env, cwd=tmp_path, text=True, capture_output=True,
        )

    return run, state, log


def mutations(log):
    calls = [json.loads(line) for line in log.read_text().splitlines()]
    return [
        call for call in calls
        if call[:2] in [
            ["project", "create"], ["project", "field-create"], ["project", "link"],
        ] or call[:2] == ["api", "graphql"] and (
            "--input" in call or any("createProjectV2" in arg for arg in call)
        )
    ]


def test_preview_does_not_mutate(github):
    run, state, log = github
    before = state.read_text()
    result = run("--dry-run")
    assert result.returncode == 0, result.stderr
    assert state.read_text() == before
    assert mutations(log) == []
    assert "Preview only" in result.stdout
    assert "No local or remote changes" in result.stdout


def test_standard_apply_creates_fields_and_links_idempotently(github):
    run, state, log = github
    for _ in range(2):
        result = run("--apply")
        assert result.returncode == 0, result.stderr
        assert "GitHub backlog verified" in result.stdout
        assert "No workflow files installed" in result.stdout
    data = json.loads(state.read_text())
    assert data["linked"]
    assert set(data["fields"]) == {
        "Status", "Work Type", "Priority", "Stage", "Review Verdict",
        "Brief Link", "Release Note Link",
    }
    creates = [call for call in mutations(log) if call[:2] == ["project", "field-create"]]
    assert len(creates) == 6
    assert data["fields"]["Status"]["options"] == STATUSES


def test_lite_uses_only_common_fields(github):
    run, state, _ = github
    result = run("--apply", mode="lite")
    assert result.returncode == 0, result.stderr
    assert set(json.loads(state.read_text())["fields"]) == {"Status", "Work Type", "Priority"}


def test_create_private_project_and_initialize_status(github):
    run, state, log = github
    result = run("--apply", create=True, update={"projects": []})
    assert result.returncode == 0, result.stderr
    assert "Created Project #7" in result.stdout
    assert json.loads(state.read_text())["fields"]["Status"]["options"] == STATUSES
    calls = [json.loads(line) for line in log.read_text().splitlines()]
    assert not any(c[:2] == ["project", "create"] for c in calls)
    creation = next(c for c in calls if any("createProjectV2" in a for a in c))
    assert "ownerId=MDQ6VXNlcjE=" in creation
    assert "title=Briefcase Standard" in creation


@pytest.mark.parametrize(
    ("update", "message"),
    [
        ({"owner_read_error": True}, "Cannot resolve Project owner"),
        ({"owner_id": "null"}, "Could not resolve Project owner"),
        ({"owner_id": ""}, "Could not resolve Project owner"),
    ],
)
def test_new_project_owner_failure_prevents_creation(github, update, message):
    run, _, log = github
    result = run("--apply", create=True, update={"projects": [], **update})
    assert result.returncode != 0
    assert message in result.stderr
    assert mutations(log) == []


def test_project_creation_failure_stops_without_fallback(github):
    run, state, log = github
    result = run(
        "--apply", create=True,
        update={"projects": [], "project_create_error": True},
    )
    assert result.returncode != 0
    assert "Project creation denied" in result.stderr
    assert "GitHub backlog verified" not in result.stdout
    assert json.loads(state.read_text())["projects"] == []
    assert len(mutations(log)) == 1


@pytest.mark.parametrize("number", ["null", "", "0", "not-a-number"])
def test_invalid_creation_response_stops_before_schema_changes(github, number):
    run, _, log = github
    result = run(
        "--apply", create=True,
        update={"projects": [], "creation_number": number},
    )
    assert result.returncode != 0
    assert "inspect GitHub before retrying" in result.stderr
    assert "GitHub backlog verified" not in result.stdout
    assert len(mutations(log)) == 1


def test_create_preview_is_read_only(github):
    run, state, log = github
    result = run(create=True, update={"projects": []})
    assert result.returncode == 0, result.stderr
    assert json.loads(state.read_text())["projects"] == []
    assert mutations(log) == []
    for name in ["Inbox", "Architecture", "Review Verdict", "Brief Link", "Release Note Link"]:
        assert name in result.stdout


def test_existing_title_is_reused(github):
    run, _, log = github
    result = run("--apply", create=True)
    assert result.returncode == 0, result.stderr
    assert not any(c[:2] == ["project", "create"] for c in mutations(log))


def test_populated_legacy_project_is_never_reset(github):
    run, state, log = github
    data = json.loads(state.read_text())
    data["fields"]["Status"]["options"] = ["draft", "review-accepted", "done"]
    state.write_text(json.dumps(data))
    result = run("--apply", "--initialize-empty", update={"items": 5})
    assert result.returncode != 0
    assert "populated Project" in result.stderr
    assert mutations(log) == []


def test_empty_status_reset_requires_explicit_consent(github):
    run, state, log = github
    data = json.loads(state.read_text())
    data["fields"]["Status"]["options"] = ["Todo", "Done"]
    state.write_text(json.dumps(data))
    result = run("--apply")
    assert result.returncode != 0
    assert "--initialize-empty" in result.stderr
    assert mutations(log) == []
    result = run("--apply", "--initialize-empty")
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    ("update", "message"),
    [
        ({"auth_error": True}, "Authentication failed"),
        ({"repo_write": False}, "Repository write access"),
        ({"issues": False}, "Enable repository Issues"),
        ({"project_write": False}, "Project update access"),
        ({"closed": True}, "is closed"),
        ({"public": True}, "Project is public"),
        ({"field_read_error": True}, "Cannot read Project fields"),
    ],
)
def test_preflight_failure_prevents_all_mutation(github, update, message):
    run, _, log = github
    result = run("--apply", update=update)
    assert result.returncode != 0
    assert message in result.stderr
    assert mutations(log) == []
    assert "GitHub backlog verified" not in result.stdout


@pytest.mark.parametrize("failure", ["create_field_error", "link_error", "link_readback_error"])
def test_mutation_or_readback_failure_never_reports_success(github, failure):
    run, _, _ = github
    result = run("--apply", update={failure: True})
    assert result.returncode != 0
    assert "GitHub backlog verified" not in result.stdout


def test_incompatible_supporting_field_is_not_overwritten(github):
    run, state, log = github
    data = json.loads(state.read_text())
    data["fields"]["Review Verdict"] = {
        "id": "PVTSSF_Review", "options": ["accepted"], "type": "SINGLE_SELECT",
    }
    state.write_text(json.dumps(data))
    result = run("--apply")
    assert result.returncode != 0
    assert "Review Verdict options differ" in result.stderr
    assert mutations(log) == []


def test_failed_field_lookup_is_not_treated_as_missing(github):
    run, _, log = github
    result = run("--apply", update={"late_field_error": True})
    assert result.returncode != 0
    assert "Late field lookup failure" in result.stderr
    assert mutations(log) == []
    assert "GitHub backlog verified" not in result.stdout


def test_no_local_workflow_files_are_written(github):
    run, state, _ = github
    result = run("--apply")
    assert result.returncode == 0, result.stderr
    assert not (state.parent / ".briefcase").exists()
    assert not (state.parent / "AGENTS.md").exists()
    assert not (state.parent / "PRODUCT.md").exists()


def test_missing_gh_has_actionable_error(tmp_path):
    result = subprocess.run(
        ["/bin/bash", str(SCRIPT), "--mode", "standard", "--repo", "demo/app",
         "--owner", "demo", "--project", "7"],
        env={**os.environ, "PATH": str(tmp_path)},
        text=True, capture_output=True,
    )
    assert result.returncode != 0
    assert "Install gh and authenticate" in result.stderr


def test_explicit_public_project_consent(github):
    run, _, _ = github
    result = run("--apply", "--allow-public-project", update={"public": True})
    assert result.returncode == 0, result.stderr


def test_duplicate_project_title_requires_explicit_number(github):
    run, _, log = github
    result = run(
        "--apply", create=True,
        update={"projects": [
            {"number": 7, "title": "Briefcase Standard"},
            {"number": 8, "title": "Briefcase Standard"},
        ]},
    )
    assert result.returncode != 0
    assert "Multiple Projects" in result.stderr
    assert mutations(log) == []


def test_failed_new_project_initialization_can_be_resumed(github):
    run, state, log = github
    result = run(
        "--apply", create=True,
        update={"projects": [], "status_write_error": True},
    )
    assert result.returncode != 0
    assert "Created Project #7" in result.stdout
    assert "GitHub backlog verified" not in result.stdout
    result = run(
        "--apply", "--initialize-empty", create=True,
        update={"status_write_error": False},
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(state.read_text())["fields"]["Status"]["options"] == STATUSES
    assert len([
        c for c in mutations(log) if any("createProjectV2" in arg for arg in c)
    ]) == 1


def test_nontext_link_field_is_rejected_before_mutation(github):
    run, state, log = github
    data = json.loads(state.read_text())
    data["fields"]["Brief Link"] = {
        "id": "PVTF_Brief", "options": None, "type": "NUMBER",
    }
    state.write_text(json.dumps(data))
    result = run("--apply")
    assert result.returncode != 0
    assert "Brief Link must be text" in result.stderr
    assert mutations(log) == []


@pytest.mark.parametrize("extra", [("--apply", "--dry-run"), ("--unknown",)])
def test_invalid_arguments_fail_before_github(github, extra):
    run, _, log = github
    result = run(*extra)
    assert result.returncode != 0
    assert not log.exists()
