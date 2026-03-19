"""Architect-review automation service.

Thin wrapper around StatusEntryScanner for the architect-review status.
"""

from __future__ import annotations

from typing import Callable

from src.core.automation.scanner import resolve_brief_context
from src.core.automation.scanner import StatusEntryScanner


def _architect_review_gate(store, row: dict, briefs: list[dict]) -> dict | None:
    ctx = resolve_brief_context(row, briefs)
    if not ctx.get("brief_name_resolved"):
        return {"reason": f"No matching brief found for feature '{row.get('title', '')}'"}

    brief = store.read_brief(str(ctx["brief_name"]))
    brief_status = (brief.get("status") or "").strip().lower()
    if brief_status != "draft":
        return {
            "reason": (
                f"Feature '{row.get('title', '')}' expected brief status 'draft' "
                f"but found '{brief_status or '-'}'"
            )
        }

    return None


class ArchitectReviewAutomationService:
    """Detect newly entered architect-review features and emit dispatch payloads."""

    def __init__(
        self,
        store,
        *,
        dispatcher: Callable[[dict], dict] | None = None,
    ) -> None:
        self._scanner = StatusEntryScanner(
            store,
            target_status="architect-review",
            marker_prefix="[auto-architect-review]",
            token_prefix="archrev",
            log_label="Architect-review automation",
            dispatcher=dispatcher,
            gating_check=lambda row, briefs: _architect_review_gate(store, row, briefs),
        )

    def scan(self, **kwargs) -> dict:
        return self._scanner.scan(**kwargs)
