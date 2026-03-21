"""Idea-close automation service.

Detects Features with status=done whose parent Idea is not yet shipped,
then emits dispatch payloads targeting the delivery manager for the final
Idea close action (mark Idea as shipped with Pacific timestamp).
"""

from __future__ import annotations

from typing import Callable

from src.core.automation.scanner import StatusEntryScanner


def _resolve_parent_idea(row: dict, all_rows: list[dict]) -> dict | None:
    """Find the single parent Idea row for a Feature, or None."""
    parent_ids = row.get("parent_ids") or []
    if len(parent_ids) != 1:
        return None

    parent_id = parent_ids[0]
    for candidate in all_rows:
        cid = candidate.get("notion_id") or candidate.get("id", "")
        if cid == parent_id and (candidate.get("type") or "").lower() == "idea":
            return candidate
    return None


class IdeaCloseAutomationService:
    """Detect done Features and emit dispatch payloads for Idea close."""

    def __init__(
        self,
        store,
        *,
        dispatcher: Callable[[dict], dict] | None = None,
    ) -> None:
        self._store = store
        self._dispatcher = dispatcher
        self._scanner = StatusEntryScanner(
            store,
            target_status="done",
            marker_prefix="[auto-idea-close]",
            token_prefix="ideaclose",
            log_label="Idea-close automation",
            dispatcher=dispatcher,
            gating_check=lambda row, briefs: self._idea_close_gate(row),
        )

    def _idea_close_gate(self, row: dict) -> dict | None:
        """Gate: require single parent Idea (not shipped) + release_note_link."""
        parent_ids = row.get("parent_ids") or []
        if len(parent_ids) == 0:
            return {
                "reason": (
                    f"Feature '{row.get('title', '')}' has no parent Idea; "
                    "cannot auto-close"
                )
            }
        if len(parent_ids) > 1:
            return {
                "reason": (
                    f"Feature '{row.get('title', '')}' has {len(parent_ids)} parents; "
                    "expected exactly one parent Idea"
                )
            }

        all_rows = self._store.read_backlog()
        parent = _resolve_parent_idea(row, all_rows)
        if parent is None:
            return {
                "reason": (
                    f"Feature '{row.get('title', '')}' parent ID "
                    f"'{parent_ids[0]}' does not resolve to an Idea row"
                )
            }

        parent_status = (parent.get("status") or "").strip().lower()
        if parent_status == "shipped":
            return {
                "reason": (
                    f"Parent Idea '{parent.get('title', '')}' is already shipped"
                )
            }

        release_link = (row.get("release_note_link") or "").strip()
        if not release_link:
            return {
                "reason": (
                    f"Feature '{row.get('title', '')}' has no release_note_link; "
                    "cannot confirm shipped evidence"
                )
            }

        return None

    def scan(self, **kwargs) -> dict:
        result = self._scanner.scan(**kwargs)

        # Enrich dispatches with parent Idea context and release_note_link
        all_rows = self._store.read_backlog()
        for dispatch in result.get("dispatches", []):
            # Look up the Feature row to get release_note_link
            feature_id = dispatch.get("feature_id", "")
            release_link = ""
            for r in all_rows:
                rid = r.get("notion_id") or r.get("id", "")
                if rid == feature_id:
                    release_link = (r.get("release_note_link") or "").strip()
                    break
            dispatch["release_note_link"] = release_link

            parent = _resolve_parent_idea(
                {"parent_ids": dispatch.get("parent_ids", [])}, all_rows
            )
            if parent:
                dispatch["parent_idea_id"] = parent.get("notion_id") or parent.get("id", "")
                dispatch["parent_idea_title"] = parent.get("title", "")
                idea_title = parent.get("title", "")
                dispatch["command_hint"] = (
                    f"briefcase backlog upsert --title \"{idea_title}\" "
                    f"--type Idea --status shipped "
                    f"--release-note-link \"{release_link}\" "
                    f"--notes \"Shipped via idea-close automation\""
                )

        return result
