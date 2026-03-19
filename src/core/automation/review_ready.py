"""Review-ready automation service.

Detects Features newly entering review-ready and emits dispatch payloads.
Validates that all child Task rows are done before dispatch.
"""

from __future__ import annotations

from typing import Callable

from src.core.automation.scanner import StatusEntryScanner, resolve_brief_context


def _review_ready_gate(row: dict, briefs: list[dict]) -> dict | None:
    """Validate brief exists before dispatch.

    Task-done validation is deferred to delivery-manager at dispatch time,
    since the scanner only sees Features (not their child Tasks).
    """
    ctx = resolve_brief_context(row, briefs)
    if not ctx.get("brief_name_resolved"):
        return {"reason": f"No matching brief found for feature '{row.get('title', '')}'"}
    return None


def _review_ready_gate_with_store(store, row: dict, briefs: list[dict]) -> dict | None:
    gate_result = _review_ready_gate(row, briefs)
    if gate_result is not None:
        return gate_result

    ctx = resolve_brief_context(row, briefs)
    feature_id = row.get("notion_id") or row.get("id") or ""
    brief_name = str(ctx["brief_name"])
    incomplete_tasks: list[str] = []
    for candidate in store.read_backlog():
        if candidate.get("type") != "Task":
            continue
        linked = False
        if feature_id and feature_id in (candidate.get("parent_ids") or []):
            linked = True
        elif brief_name and candidate.get("feature") == brief_name:
            linked = True
        if linked and candidate.get("status") != "done":
            incomplete_tasks.append(candidate.get("title", "Untitled task"))

    if incomplete_tasks:
        return {
            "reason": (
                f"Feature '{row.get('title', '')}' has incomplete tasks: "
                + ", ".join(incomplete_tasks)
            )
        }

    return None


class ReviewReadyAutomationService:
    """Detect newly entered review-ready features and emit dispatch payloads."""

    def __init__(
        self,
        store,
        *,
        dispatcher: Callable[[dict], dict] | None = None,
    ) -> None:
        self._scanner = StatusEntryScanner(
            store,
            target_status="review-ready",
            marker_prefix="[auto-review-ready]",
            token_prefix="revready",
            log_label="Review-ready automation",
            dispatcher=dispatcher,
            gating_check=lambda row, briefs: _review_ready_gate_with_store(store, row, briefs),
        )

    def scan(self, **kwargs) -> dict:
        return self._scanner.scan(**kwargs)
