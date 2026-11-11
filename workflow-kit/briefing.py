"""Read-only, fully paginated GitHub evidence for a PO status briefing."""

from __future__ import annotations

import argparse
import json
import subprocess
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from runtime import load_yaml, validate_contract, validate_manifest

Runner = Callable[[list[str]], subprocess.CompletedProcess[str]]

PAGE_INFO = "pageInfo { hasNextPage endCursor }"
FIELDS = """
nodes {
  ... on ProjectV2Field { name }
  ... on ProjectV2SingleSelectField { name }
  ... on ProjectV2IterationField { name }
}
"""
VALUES = """
nodes {
  ... on ProjectV2ItemFieldTextValue {
    text field { ... on ProjectV2FieldCommon { name } }
  }
  ... on ProjectV2ItemFieldSingleSelectValue {
    name field { ... on ProjectV2FieldCommon { name } }
  }
}
"""
COMMENTS = """
nodes { body url createdAt updatedAt author { login } }
"""
SOURCE = """
id title body url updatedAt
comments(first:100) { %s %s }
""" % (COMMENTS, PAGE_INFO)
METADATA = """
query BriefingProject($owner:String!,$number:Int!) {
  repositoryOwner(login:$owner) {
    ... on User { projectV2(number:$number) { %s } }
    ... on Organization { projectV2(number:$number) { %s } }
  }
}
""" % ((f"id title url fields(first:100) {{ {FIELDS} {PAGE_INFO} }}",) * 2)
SCHEMA_PAGE = """
query BriefingSchema($id:ID!,$cursor:String) {
  node(id:$id) { ... on ProjectV2 {
    fields(first:100,after:$cursor) { %s %s }
  } }
}
""" % (FIELDS, PAGE_INFO)
ITEM_PAGE = """
query BriefingItems($id:ID!,$cursor:String) {
  node(id:$id) { ... on ProjectV2 {
    items(first:100,after:$cursor) {
      totalCount
      nodes {
        id databaseId isArchived
        fieldValues(first:100) { %s %s }
        content {
          __typename
          ... on Issue { %s }
          ... on PullRequest { %s }
          ... on DraftIssue { id title body updatedAt }
        }
      }
      %s
    }
  } }
}
""" % (VALUES, PAGE_INFO, SOURCE, SOURCE, PAGE_INFO)


class ReadError(Exception):
    """A read failed or its coverage cannot be established."""


def _object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ReadError(f"{label}: expected an object")
    return value


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ReadError(f"{label}: expected nonempty text")
    return value


def _connection(value: Any, label: str) -> tuple[list[dict[str, Any]], str | None]:
    connection = _object(value, label)
    nodes = connection.get("nodes")
    info = _object(connection.get("pageInfo"), f"{label} pageInfo")
    if not isinstance(nodes, list) or not isinstance(info.get("hasNextPage"), bool):
        raise ReadError(f"{label}: missing nodes or pagination metadata")
    result = [_object(node, f"{label} node") for node in nodes]
    cursor = (
        _text(info.get("endCursor"), f"{label} endCursor")
        if info["hasNextPage"]
        else None
    )
    return result, cursor


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, check=False)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Snapshot:
    observed_from: str = field(default_factory=_now)
    observed_until: str = ""
    complete: bool = False
    project: dict[str, Any] = field(default_factory=dict)
    coverage: dict[str, int] = field(
        default_factory=lambda: {
            "expected_items": 0,
            "items_read": 0,
            "item_pages": 0,
            "schema_pages": 0,
            "field_value_pages": 0,
            "comment_pages": 0,
        }
    )
    items: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    operations: list[str] = field(default_factory=list)


class Reader:
    def __init__(self, snapshot: Snapshot, runner: Runner):
        self.snapshot = snapshot
        self.runner = runner

    def query(
        self, document: str, operation: str, **variables: str | int | None
    ) -> dict[str, Any]:
        if not document.lstrip().startswith("query Briefing"):
            raise ReadError(f"{operation}: only built-in read queries are allowed")
        args = ["gh", "api", "graphql", "-f", f"query={document}"]
        for key, value in variables.items():
            if value is not None:
                args.extend(
                    ["-F" if isinstance(value, int) else "-f", f"{key}={value}"]
                )
        self.snapshot.operations.append(operation)
        try:
            response = self.runner(args)
        except OSError as error:
            raise ReadError(
                f"{operation}: could not run gh ({error.strerror})"
            ) from error
        if response.returncode:
            raise ReadError(
                f"{operation}: gh exited {response.returncode}; "
                "check authentication and source read access locally"
            )
        try:
            payload = _object(json.loads(response.stdout), operation)
        except json.JSONDecodeError as error:
            raise ReadError(f"{operation}: invalid JSON response") from error
        if payload.get("errors"):
            raise ReadError(
                f"{operation}: GitHub returned GraphQL errors; evidence is incomplete"
            )
        return _object(payload.get("data"), f"{operation} data")


@dataclass
class Continuation:
    node_id: str
    kind: str
    cursor: str
    target: list[dict[str, Any]]
    seen: set[str] = field(default_factory=set)


def _drain(reader: Reader, pending: list[Continuation]) -> None:
    while pending:
        batch, pending = pending[:20], pending[20:]
        declarations = []
        selections = []
        variables: dict[str, str | int | None] = {}
        for index, part in enumerate(batch):
            if part.cursor in part.seen:
                raise ReadError(
                    f"{part.node_id} {part.kind}: repeated pagination cursor"
                )
            part.seen.add(part.cursor)
            declarations.extend([f"$id{index}:ID!", f"$cursor{index}:String!"])
            variables[f"id{index}"] = part.node_id
            variables[f"cursor{index}"] = part.cursor
            if part.kind == "fieldValues":
                fragment = (
                    "... on ProjectV2Item { fieldValues(first:100,"
                    f"after:$cursor{index}) {{ {VALUES} {PAGE_INFO} }} }}"
                )
            else:
                fragment = " ".join(
                    f"... on {kind} {{ comments(first:100,after:$cursor{index}) "
                    f"{{ {COMMENTS} {PAGE_INFO} }} }}"
                    for kind in ("Issue", "PullRequest")
                )
            selections.append(f"p{index}:node(id:$id{index}) {{ {fragment} }}")
        document = (
            f"query BriefingContinuation({','.join(declarations)}) "
            f"{{ {' '.join(selections)} }}"
        )
        sources = ", ".join(f"{part.node_id} {part.kind}" for part in batch)
        data = reader.query(
            document, f"Read nested evidence pages ({sources})", **variables
        )
        for index, part in enumerate(batch):
            label = f"{part.node_id} {part.kind}"
            node = _object(data.get(f"p{index}"), label)
            nodes, cursor = _connection(node.get(part.kind), label)
            part.target.extend(nodes)
            key = "field_value_pages" if part.kind == "fieldValues" else "comment_pages"
            reader.snapshot.coverage[key] += 1
            if cursor:
                part.cursor = cursor
                pending.append(part)


def _normalize(
    raw: dict[str, Any],
    manifest: dict[str, Any],
    contract: dict[str, Any],
    snapshot: Snapshot,
) -> dict[str, Any]:
    item_id = _text(raw.get("id"), "Project item id")
    fields: dict[str, str] = {}
    for value in raw["values"]:
        # Other field types intentionally have no projection in the query.
        if not value:
            continue
        name = _text(_object(value.get("field"), item_id).get("name"), "field name")
        text = value.get("text", value.get("name"))
        if not isinstance(text, str) or name in fields:
            raise ReadError(f"{item_id}: invalid or duplicate field {name}")
        fields[name] = text
    content = _object(raw.get("content"), f"{item_id} content (inaccessible source)")
    kind = content.get("__typename")
    if kind not in {"Issue", "PullRequest", "DraftIssue"}:
        raise ReadError(f"{item_id}: unsupported or inaccessible source type")
    title = _text(content.get("title"), f"{item_id} title")
    body = content.get("body")
    if not isinstance(body, str):
        raise ReadError(f"{item_id}: source body unavailable")
    if kind == "DraftIssue":
        database_id = raw.get("databaseId")
        if type(database_id) is not int or database_id <= 0:
            raise ReadError(f"{item_id}: draft Project link identity unavailable")
        url = f"{snapshot.project['url']}?pane=issue&itemId={database_id}"
    else:
        url = _text(content.get("url"), f"{item_id} source URL")
    names = manifest["project"]["fields"]
    status = fields.get(names["status"])
    owner = fields.get(names["action_owner"])
    warnings = []
    if status not in manifest["project"]["options"]["status"]:
        warnings.append("Status missing or unrecognized; do not infer lifecycle")
    if owner not in manifest["project"]["options"]["action_owner"]:
        warnings.append("Action Owner missing or unrecognized; do not infer owner")
    default_owners = {
        state["label"]: state["owner"]
        for state in contract["statuses"].values()
        if state["owner"] != "explicit"
    }
    if status in default_owners and owner != default_owners[status]:
        warnings.append("Status and Action Owner conflict; no repair attempted")
    if status == "Blocked":
        if owner in (None, "None"):
            warnings.append("Blocked work has no responsible Action Owner")
        if not fields.get("Blocking reason"):
            warnings.append("Blocking reason missing; unblock condition unknown")
        if not fields.get(names["resume_status"]):
            warnings.append("Resume Status missing")
        elif (
            fields[names["resume_status"]]
            not in manifest["project"]["options"]["resume_status"]
        ):
            warnings.append("Resume Status unrecognized; do not infer resume condition")
    archived = raw.get("isArchived")
    if not isinstance(archived, bool):
        raise ReadError(f"{item_id}: archive visibility unavailable")
    for comment in raw["comments"]:
        if not isinstance(comment.get("body"), str):
            raise ReadError(f"{item_id}: discussion body unavailable")
        for key in ("url", "createdAt", "updatedAt"):
            _text(comment.get(key), f"{item_id} discussion {key}")
    return {
        "id": item_id,
        "url": url,
        "title": title,
        "type": kind,
        "archived": archived,
        "status": status,
        "action_owner": owner,
        "blocking_reason": fields.get("Blocking reason"),
        "resume_status": fields.get(names["resume_status"]),
        "fields": fields,
        "body": body,
        "comments": raw["comments"],
        "warnings": warnings,
    }


def collect(manifest_path: Path, *, runner: Runner = _run) -> Snapshot:
    snapshot = Snapshot()
    reader = Reader(snapshot, runner)
    try:
        manifest = load_yaml(manifest_path)
        contract = load_yaml(manifest_path.parent / manifest["contract"])
        errors = validate_contract(contract) + validate_manifest(manifest, contract)
        if errors:
            raise ReadError("Local configuration: " + "; ".join(errors))
        project = manifest["project"]
        data = reader.query(
            METADATA,
            "Resolve Project and schema",
            owner=project["owner"],
            number=project["number"],
        )
        owner = _object(data.get("repositoryOwner"), "Project owner (inaccessible)")
        meta = _object(owner.get("projectV2"), "Project (inaccessible)")
        snapshot.project = {
            "id": _text(meta.get("id"), "Project id"),
            "url": _text(meta.get("url"), "Project URL"),
            "title": _text(meta.get("title"), "Project title"),
            "profile": manifest["mode"],
        }
        fields, cursor = _connection(meta.get("fields"), "Project schema")
        snapshot.coverage["schema_pages"] = 1
        seen: set[str] = set()
        while cursor:
            if cursor in seen:
                raise ReadError("Project schema: repeated pagination cursor")
            seen.add(cursor)
            data = reader.query(
                SCHEMA_PAGE, "Read schema page", id=meta["id"], cursor=cursor
            )
            page, cursor = _connection(
                _object(data.get("node"), "Project schema node").get("fields"),
                "Project schema",
            )
            fields.extend(page)
            snapshot.coverage["schema_pages"] += 1
        required = {
            project["fields"]["status"],
            project["fields"]["action_owner"],
            project["fields"]["resume_status"],
            "Blocking reason",
        }
        field_names = [f.get("name") for f in fields]
        ambiguous = {name for name in required if field_names.count(name) > 1}
        if ambiguous:
            raise ReadError(
                f"Project schema has ambiguous fields: {', '.join(sorted(ambiguous))}"
            )
        missing = required - set(field_names)
        if missing:
            raise ReadError(
                f"Project schema missing fields: {', '.join(sorted(missing))}"
            )
        cursor = None
        seen = set()
        item_ids: set[str] = set()
        while True:
            data = reader.query(
                ITEM_PAGE,
                f"Read Project items page {snapshot.coverage['item_pages'] + 1}",
                id=meta["id"],
                cursor=cursor,
            )
            connection = _object(
                _object(data.get("node"), "Project node").get("items"), "Project items"
            )
            total = connection.get("totalCount")
            if type(total) is not int or total < 0:
                raise ReadError("Project items: expected totalCount")
            if (
                snapshot.coverage["item_pages"]
                and total != snapshot.coverage["expected_items"]
            ):
                raise ReadError("Project item count changed during observation; rerun")
            snapshot.coverage["expected_items"] = total
            nodes, cursor = _connection(connection, "Project items")
            snapshot.coverage["item_pages"] += 1
            pending = []
            raw_items = []
            for raw in nodes:
                item_id = _text(raw.get("id"), "Project item id")
                if item_id in item_ids:
                    raise ReadError(
                        f"{item_id}: repeated item during pagination; rerun"
                    )
                item_ids.add(item_id)
                values, after = _connection(raw.get("fieldValues"), f"{item_id} fields")
                raw["values"] = values
                raw["comments"] = []
                raw_items.append(raw)
                snapshot.coverage["field_value_pages"] += 1
                if after:
                    pending.append(Continuation(item_id, "fieldValues", after, values))
                content = raw.get("content")
                if isinstance(content, dict) and content.get("__typename") in {
                    "Issue",
                    "PullRequest",
                }:
                    comments, after = _connection(
                        content.get("comments"), f"{item_id} comments"
                    )
                    raw["comments"] = comments
                    snapshot.coverage["comment_pages"] += 1
                    if after:
                        pending.append(
                            Continuation(
                                _text(content.get("id"), "Source id"),
                                "comments",
                                after,
                                comments,
                            )
                        )
            _drain(reader, pending)
            for raw in raw_items:
                try:
                    snapshot.items.append(_normalize(raw, manifest, contract, snapshot))
                except ReadError as error:
                    snapshot.errors.append(str(error))
                snapshot.coverage["items_read"] += 1
            if not cursor:
                break
            if cursor in seen:
                raise ReadError("Project items: repeated pagination cursor")
            seen.add(cursor)
        if snapshot.coverage["items_read"] != snapshot.coverage["expected_items"]:
            raise ReadError("Project item coverage differs from totalCount; rerun")
        snapshot.complete = not snapshot.errors
    except yaml.YAMLError:
        snapshot.errors.append(
            "Briefing read failed: invalid local YAML; inspect configuration locally"
        )
    except (ReadError, OSError, ValueError, TypeError, KeyError) as error:
        snapshot.errors.append(f"Briefing read failed: {error}")
    snapshot.observed_until = _now()
    return snapshot


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest", type=Path, default=Path(__file__).with_name("workflow.yaml")
    )
    args = parser.parse_args(argv)
    snapshot = collect(args.manifest)
    print(json.dumps(asdict(snapshot), indent=2))
    return 0 if snapshot.complete else 2


if __name__ == "__main__":
    raise SystemExit(main())
