"""Ship-routing automation service.

Detects Features with status=review-accepted AND review_verdict=accepted,
then emits dispatch payloads for the delivery-manager ship phase.
"""

from __future__ import annotations

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
