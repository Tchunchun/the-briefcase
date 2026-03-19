"""Shared status-entry scanner for workflow automation.

Extracts the common pattern: scan Feature backlog rows for a target status,
detect new entries via marker tokens, build dispatch payloads, write trace
notes, and prevent duplicate dispatches.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable


NOTE_SEPARATOR = " // "


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def parse_notion_id(value: str) -> str:
    """Extract a canonical 8-4-4-4-12 UUID from a Notion URL or ID string.

    Returns empty string if value doesn't contain a valid 32-hex-char ID.
    """
    compact = re.sub(r"[^a-fA-F0-9]", "", value or "")
    if len(compact) < 32:
        return ""
    compact = compact[-32:].lower()
    return (
        f"{compact[:8]}-{compact[8:12]}-{compact[12:16]}-"
        f"{compact[16:20]}-{compact[20:]}"
    )


@dataclass
class MarkerState:
    last_status: str = ""
    active_entry_token: str = ""
    dispatched_token: str = ""
    dispatched_at: str = ""


def parse_marker(notes: str, marker_prefix: str) -> MarkerState:
    segments: list[str] = []
    for line in notes.splitlines():
        segments.extend(part.strip() for part in line.split(NOTE_SEPARATOR))
    for segment in segments:
        stripped = segment.strip()
        if not stripped.startswith(marker_prefix):
            continue
        values: dict[str, str] = {}
        for part in stripped[len(marker_prefix):].strip().split():
            if "=" not in part:
                continue
            key, value = part.split("=", 1)
            values[key] = value
        return MarkerState(
            last_status=values.get("last_status", ""),
            active_entry_token=values.get("active_entry_token", ""),
            dispatched_token=values.get("dispatched_token", ""),
            dispatched_at=values.get("dispatched_at", ""),
        )
    return MarkerState()


def render_marker(marker: MarkerState, marker_prefix: str) -> str:
    return (
        f"{marker_prefix} "
        f"last_status={marker.last_status or '-'} "
        f"active_entry_token={marker.active_entry_token or '-'} "
        f"dispatched_token={marker.dispatched_token or '-'} "
        f"dispatched_at={marker.dispatched_at or '-'}"
    )


def strip_marker(notes: str, marker_prefix: str) -> str:
    kept: list[str] = []
    for line in notes.splitlines():
        for part in line.split(NOTE_SEPARATOR):
            stripped = part.strip()
            if stripped and not stripped.startswith(marker_prefix):
                kept.append(stripped)
    return NOTE_SEPARATOR.join(kept).strip()


def append_dispatch_log(
    notes: str, label: str, dispatch_token: str, timestamp: str, brief_name: str,
) -> str:
    log_line = (
        f"{label} dispatched {dispatch_token} at {timestamp}"
        f" for brief {brief_name or '-'}."
    )
    lines = [" ".join(line.split()) for line in notes.splitlines() if line.strip()]
    if log_line not in lines:
        lines.append(log_line)
    return NOTE_SEPARATOR.join(lines)


def resolve_brief_context(row: dict, briefs: list[dict]) -> dict[str, str | bool]:
    brief_link = row.get("brief_link", "")
    title_slug = slugify(row.get("title", ""))
    brief_id = parse_notion_id(brief_link)

    for brief in briefs:
        if brief_id and parse_notion_id(brief.get("notion_id", "")) == brief_id:
            return {
                "brief_name": brief.get("name", ""),
                "brief_title": brief.get("title", ""),
                "brief_link": brief_link,
                "brief_name_resolved": True,
            }

    for brief in briefs:
        if brief.get("name", "") == title_slug or slugify(brief.get("title", "")) == title_slug:
            return {
                "brief_name": brief.get("name", ""),
                "brief_title": brief.get("title", ""),
                "brief_link": brief_link,
                "brief_name_resolved": True,
            }

    return {
        "brief_name": title_slug,
        "brief_title": row.get("title", ""),
        "brief_link": brief_link,
        "brief_name_resolved": False,
    }


def build_dispatch_token(prefix: str, row: dict, now: datetime) -> str:
    identifier = row.get("notion_id") or row.get("id") or ""
    if identifier in {"", "—"}:
        identifier = slugify(row.get("title", "feature"))
    return f"{prefix}-{identifier}-{now.strftime('%Y%m%dT%H%M%SZ')}"


class StatusEntryScanner:
    """Generic scanner for Features entering a target status.

    Subclass or instantiate with configuration:
      - target_status: the backlog status to detect (e.g., "architect-review")
      - marker_prefix: unique marker tag (e.g., "[auto-architect-review]")
      - token_prefix: prefix for dispatch tokens (e.g., "archrev")
      - log_label: human-readable label for trace notes
    """

    def __init__(
        self,
        store,
        *,
        target_status: str,
        marker_prefix: str,
        token_prefix: str,
        log_label: str,
        dispatcher: Callable[[dict], dict] | None = None,
        gating_check: Callable[[dict, list[dict]], dict | None] | None = None,
    ) -> None:
        self._store = store
        self._target_status = target_status
        self._marker_prefix = marker_prefix
        self._token_prefix = token_prefix
        self._log_label = log_label
        self._dispatcher = dispatcher
        self._gating_check = gating_check

    def scan(self, *, apply: bool = True, now: datetime | None = None) -> dict:
        now = now or utc_now()
        timestamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        rows = self._store.read_backlog()
        briefs = self._store.list_briefs()

        scanned = 0
        dispatched: list[dict] = []
        blocked: list[dict] = []
        updated = 0

        for row in rows:
            if row.get("type", "").lower() != "feature":
                continue
            scanned += 1
            current_status = row.get("status", "")
            trace = row.get("automation_trace", "") or ""
            marker = parse_marker(trace, self._marker_prefix)
            clean_trace = " ".join(strip_marker(trace, self._marker_prefix).split())

            if current_status != self._target_status:
                if marker.last_status or marker.active_entry_token or marker.dispatched_token:
                    marker = MarkerState(last_status=current_status)
                    updated += self._write_trace_if_needed(row, clean_trace, marker, apply)
                continue

            if marker.last_status != self._target_status or not marker.active_entry_token:
                marker.active_entry_token = build_dispatch_token(
                    self._token_prefix, row, now,
                )

            if marker.dispatched_token == marker.active_entry_token:
                marker.last_status = self._target_status
                updated += self._write_trace_if_needed(row, clean_trace, marker, apply)
                continue

            # Gating check (optional per-phase validation)
            if self._gating_check is not None:
                gate_result = self._gating_check(row, briefs)
                if gate_result is not None:
                    marker.last_status = self._target_status
                    latest_row = self._read_latest_row(row) if apply else dict(row)
                    if latest_row.get("route_state") != "blocked" and apply:
                        updated_row = dict(latest_row)
                        updated_row["route_state"] = "blocked"
                        self._store.write_backlog_row(updated_row)
                        updated += 1
                        latest_row = updated_row
                    updated += self._write_trace_if_needed(
                        latest_row,
                        clean_trace,
                        marker,
                        apply,
                    )
                    blocked.append({
                        "feature_title": row.get("title", ""),
                        "feature_id": row.get("notion_id") or row.get("id", ""),
                        "reason": gate_result.get("reason", "gating check failed"),
                    })
                    continue

            brief_context = resolve_brief_context(row, briefs)
            dispatch = {
                "feature_title": row.get("title", ""),
                "feature_id": row.get("notion_id") or row.get("id", ""),
                "feature_url": row.get("notion_url", ""),
                "parent_ids": row.get("parent_ids", []),
                "dispatch_token": marker.active_entry_token,
                "detected_at": timestamp,
                **brief_context,
                "command_hint": (
                    f"agent brief read {brief_context['brief_name']}"
                    if brief_context["brief_name"]
                    else ""
                ),
            }
            if apply and self._dispatcher is not None:
                dispatch_result = self._dispatcher(dispatch)
                dispatch["dispatch_result"] = dispatch_result
            dispatched.append(dispatch)

            marker.last_status = self._target_status
            marker.dispatched_token = marker.active_entry_token
            marker.dispatched_at = timestamp
            clean_trace = append_dispatch_log(
                clean_trace,
                self._log_label,
                marker.active_entry_token,
                timestamp,
                brief_context["brief_name"],
            )
            updated += self._write_trace_if_needed(row, clean_trace, marker, apply)

        result = {
            "scanned_features": scanned,
            "dispatched_count": len(dispatched),
            "blocked_count": len(blocked),
            "updated_rows": updated if apply else 0,
            "dry_run": not apply,
            "dispatches": dispatched,
        }
        if blocked:
            result["blocked"] = blocked
        return result

    def _write_trace_if_needed(
        self,
        row: dict,
        clean_trace: str,
        marker: MarkerState,
        apply: bool,
    ) -> int:
        latest_row = self._read_latest_row(row) if apply else dict(row)
        final_trace = NOTE_SEPARATOR.join(
            part for part in [clean_trace.strip(), render_marker(marker, self._marker_prefix)] if part
        ).strip()
        if final_trace == (latest_row.get("automation_trace", "") or "").strip():
            return 0
        if apply:
            updated_row = dict(latest_row)
            updated_row["automation_trace"] = final_trace
            self._store.write_backlog_row(updated_row)
        return 1

    def _read_latest_row(self, row: dict) -> dict:
        identifier = row.get("notion_id") or row.get("id") or ""
        row_type = row.get("type", "")
        row_title = row.get("title", "")

        for candidate in self._store.read_backlog():
            candidate_identifier = candidate.get("notion_id") or candidate.get("id") or ""
            if identifier and candidate_identifier == identifier:
                return candidate
            if (
                candidate.get("type", "") == row_type
                and candidate.get("title", "") == row_title
            ):
                return candidate
        return row
