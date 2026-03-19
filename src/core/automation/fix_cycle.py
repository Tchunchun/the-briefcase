"""Fix-cycle dispatch automation service.

Detects Features with status=review-ready AND review_verdict=changes-requested,
then emits dispatch payloads for the implementation agent fix cycle.
"""

from __future__ import annotations

from typing import Callable

from src.core.automation.scanner import StatusEntryScanner, resolve_brief_context


def _fix_cycle_gate(row: dict, briefs: list[dict]) -> dict | None:
    """Reject rows that are not in the changes-requested verdict state.

    Both status=review-ready AND review_verdict=changes-requested must be true.
    Also validates that a matching brief exists.
    """
    verdict = (row.get("review_verdict") or "").strip().lower()
    if verdict != "changes-requested":
        return {
            "reason": (
                f"Feature '{row.get('title', '')}' has review_verdict='{verdict}'; "
                "expected 'changes-requested'"
            )
        }

    ctx = resolve_brief_context(row, briefs)
    if not ctx.get("brief_name_resolved"):
        return {
            "reason": f"No matching brief found for feature '{row.get('title', '')}'"
        }

    return None


class FixCycleAutomationService:
    """Detect features needing a fix cycle and emit dispatch payloads."""

    def __init__(
        self,
        store,
        *,
        dispatcher: Callable[[dict], dict] | None = None,
    ) -> None:
        self._scanner = StatusEntryScanner(
            store,
            target_status="review-ready",
            marker_prefix="[auto-fix-cycle]",
            token_prefix="fixcycle",
            log_label="Fix-cycle automation",
            dispatcher=dispatcher,
            gating_check=_fix_cycle_gate,
        )

    def scan(self, **kwargs) -> dict:
        return self._scanner.scan(**kwargs)
