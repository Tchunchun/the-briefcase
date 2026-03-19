"""Implementation-ready automation service.

Detects Features newly entering implementation-ready and emits dispatch payloads.
Validates that the linked brief exists and is implementation-ready before dispatch.
"""

from __future__ import annotations

from typing import Callable

from src.core.automation.scanner import StatusEntryScanner, resolve_brief_context


def _implementation_ready_gate(row: dict, briefs: list[dict]) -> dict | None:
    """Validate brief exists and is implementation-ready before dispatch."""
    ctx = resolve_brief_context(row, briefs)
    if not ctx.get("brief_name_resolved"):
        return {"reason": f"No matching brief found for feature '{row.get('title', '')}'"}
    return None


def _implementation_ready_gate_with_store(store, row: dict, briefs: list[dict]) -> dict | None:
    gate_result = _implementation_ready_gate(row, briefs)
    if gate_result is not None:
        return gate_result

    ctx = resolve_brief_context(row, briefs)
    brief = store.read_brief(str(ctx["brief_name"]))
    brief_status = (brief.get("status") or "").strip().lower()
    if brief_status != "implementation-ready":
        return {
            "reason": (
                f"Feature '{row.get('title', '')}' expected brief status 'implementation-ready' "
                f"but found '{brief_status or '-'}'"
            )
        }
    return None


class ImplementationReadyAutomationService:
    """Detect newly entered implementation-ready features and emit dispatch payloads."""

    def __init__(
        self,
        store,
        *,
        dispatcher: Callable[[dict], dict] | None = None,
    ) -> None:
        self._scanner = StatusEntryScanner(
            store,
            target_status="implementation-ready",
            marker_prefix="[auto-impl-ready]",
            token_prefix="implready",
            log_label="Implementation-ready automation",
            dispatcher=dispatcher,
            gating_check=lambda row, briefs: _implementation_ready_gate_with_store(store, row, briefs),
        )

    def scan(self, **kwargs) -> dict:
        return self._scanner.scan(**kwargs)
