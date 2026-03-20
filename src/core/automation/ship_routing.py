"""Ship-routing automation service.

Detects Features with status=review-accepted AND review_verdict=accepted,
then emits dispatch payloads for the delivery-manager ship phase.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable

from src.core.automation.scanner import StatusEntryScanner, resolve_brief_context


def _ship_routing_gate(row: dict, briefs: list[dict]) -> dict | None:
    """Reject rows that are not in the accepted verdict state.

    Both status=review-accepted AND review_verdict=accepted must be true.
    Also validates that a matching brief exists.
    """
    verdict = (row.get("review_verdict") or "").strip().lower()
    if verdict != "accepted":
        return {
            "reason": (
                f"Feature '{row.get('title', '')}' has review_verdict='{verdict}'; "
                "expected 'accepted'"
            )
        }

    ctx = resolve_brief_context(row, briefs)
    if not ctx.get("brief_name_resolved"):
        return {
            "reason": f"No matching brief found for feature '{row.get('title', '')}'"
        }

    return None


class ShipRoutingAutomationService:
    """Detect review-accepted features and emit dispatch payloads for the ship phase."""

    def __init__(
        self,
        store,
        *,
        dispatcher: Callable[[dict], dict] | None = None,
    ) -> None:
        self._store = store
        self._scanner = StatusEntryScanner(
            store,
            target_status="review-accepted",
            marker_prefix="[auto-ship-routing]",
            token_prefix="shiproute",
            log_label="Ship-routing automation",
            dispatcher=dispatcher,
            gating_check=_ship_routing_gate,
        )

    def scan(self, **kwargs) -> dict:
        return self._scanner.scan(**kwargs)

    def _feature_children(self, parent_id: str) -> list[dict]:
        list_children = getattr(self._store, "list_children", None)
        if callable(list_children):
            return list_children(parent_id)
        return [
            row
            for row in self._store.read_backlog()
            if row.get("type", "").lower() == "feature"
            and parent_id in (row.get("parent_ids") or [])
        ]

    def _append_partial_ship_note(self, parent: dict, *, done: int, total: int) -> bool:
        date_value = datetime.now(timezone.utc).date().isoformat()
        note = f"[partial-ship] {done}/{total} Features done as of {date_value}"
        existing_notes = (parent.get("notes") or "").strip()
        if note in existing_notes:
            return False
        updated_parent = dict(parent)
        updated_parent["notes"] = f"{existing_notes}\n{note}".strip()
        self._store.write_backlog_row(updated_parent)
        return True

    def propagate_release_links(self) -> dict:
        """Copy release_note_link from done Features to their parent Ideas.

        Scans all Feature rows with status=done and a non-empty
        release_note_link.  For each parent Idea (looked up via parent_ids),
        if the Idea has no release_note_link, the Feature's link is copied
        over.  When multiple Features share a parent Idea, the last one
        encountered wins (most recent done Feature).

        Returns a summary dict with counts and details.
        """
        rows = self._store.read_backlog()
        rows_by_id: dict[str, dict] = {}
        for row in rows:
            rid = row.get("notion_id") or row.get("id", "")
            if rid:
                rows_by_id[rid] = row

        propagated: list[dict] = []
        blocked_partial: list[dict] = []
        skipped = 0

        for row in rows:
            if row.get("type", "").lower() != "feature":
                continue
            if row.get("status", "").lower() != "done":
                continue
            link = (row.get("release_note_link") or "").strip()
            if not link:
                continue
            for parent_id in row.get("parent_ids", []):
                parent = rows_by_id.get(parent_id)
                if parent is None:
                    continue
                if parent.get("type", "").lower() != "idea":
                    continue
                sibling_features = self._feature_children(parent_id)
                total = len(sibling_features)
                done = sum(
                    1
                    for sibling in sibling_features
                    if sibling.get("status", "").lower() == "done"
                )
                if total > 0 and done < total:
                    self._append_partial_ship_note(parent, done=done, total=total)
                    blocked_partial.append({
                        "idea_title": parent.get("title", ""),
                        "idea_id": parent_id,
                        "done": done,
                        "total": total,
                    })
                    continue
                existing_link = (parent.get("release_note_link") or "").strip()
                if existing_link:
                    skipped += 1
                    continue
                updated_parent = dict(parent)
                updated_parent["release_note_link"] = link
                self._store.write_backlog_row(updated_parent)
                rows_by_id[parent_id] = updated_parent
                propagated.append({
                    "idea_title": parent.get("title", ""),
                    "idea_id": parent_id,
                    "feature_title": row.get("title", ""),
                    "release_note_link": link,
                })

        return {
            "propagated_count": len(propagated),
            "blocked_partial_count": len(blocked_partial),
            "skipped_count": skipped,
            "propagated": propagated,
            "blocked_partial": blocked_partial,
        }
