"""Ship-dispatch automation service.

Detects Features with status=review-accepted AND review_verdict=accepted,
then emits dispatch payloads targeting the implementation agent for the
ship wrap-up phase (release notes + Feature → done).

Separate from ship-routing, which routes *to* delivery-manager.  Ship-dispatch
routes *from* delivery-manager to the implementation agent for the actual ship.
"""

from __future__ import annotations

from typing import Callable

from src.core.automation.scanner import StatusEntryScanner, resolve_brief_context


def _ship_dispatch_gate(row: dict, briefs: list[dict]) -> dict | None:
    """Gate: review_verdict must be accepted AND a matching brief must exist."""
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


class ShipDispatchAutomationService:
    """Detect review-accepted features and emit dispatch payloads for ship wrap-up."""

    def __init__(
        self,
        store,
        *,
        dispatcher: Callable[[dict], dict] | None = None,
    ) -> None:
        self._scanner = StatusEntryScanner(
            store,
            target_status="review-accepted",
            marker_prefix="[auto-ship-dispatch]",
            token_prefix="shipdsp",
            log_label="Ship-dispatch automation",
            dispatcher=dispatcher,
            gating_check=_ship_dispatch_gate,
        )

    def scan(self, **kwargs) -> dict:
        return self._scanner.scan(**kwargs)
