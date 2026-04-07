**Status: implementation-ready**

---

## Problem
When the implementation agent moves a feature to Feature Status done, the delivery manager still has a trailing responsibility: mark the parent Idea row as shipped with an explicit Pacific timestamp. This step is defined in the delivery manager skill but has no automated trigger. Features reach done without their parent Ideas ever being closed, leaving the idea lifecycle permanently open and making it impossible to cleanly trace shipped work from idea capture through release.

## Goal
agent automate idea-close detects features newly moved to Feature Status done whose parent Idea is not yet shipped, emits a dispatch payload for the delivery manager, and in live mode dispatches the delivery-manager for the final Idea close action after shipped evidence exists.

## Acceptance Criteria
- [ ] agent automate idea-close detects Feature rows newly moved to status=done whose parent Idea is not yet shipped.
- [ ] Dispatch payload includes feature_title, feature_id, parent idea identifier, command_hint, dispatch_token, and detected_at.
- [ ] --notes-only mode writes trace metadata without executing a shell command.
- [ ] --dry-run mode computes dispatches without writing any trace metadata.
- [ ] Re-running the scan without a relevant status change does not dispatch the same finished Feature twice.
- [ ] Gating requires a single parent Idea relation and release-note-backed Feature completion before dispatch.
- [ ] The automation dispatches delivery-manager for the final write instead of marking the Idea shipped directly.

## Non-Functional Requirements
- **Expected load / scale:** low-frequency workflow scans across a modest backlog of shipped Features and parent Ideas
- **Latency / response time:** detection and any optional close action should remain small relative to existing Notion/API round-trips
- **Availability / reliability:** dispatch and close behavior must be idempotent so repeated scans do not duplicate ship-closing activity
- **Cost constraints:** no new services or persistent workers; stay within the current Python CLI and Notion/local storage model
- **Compliance / data residency:** planning metadata only; the timestamp must use explicit Pacific PST/PDT formatting required by the workflow
- **Other constraints:** must preserve the existing owner boundary where delivery-manager owns the final Idea shipped state

## Out of Scope
- Changing how Features reach done
- Writing release note content
- Redesigning the broader shipment or routing workflow
- Closing unrelated stale Ideas that are not linked to a completed Feature

## Open Questions
none

## Technical Approach
Implement an IdeaCloseAutomationService that scans Feature rows entering status=done using StatusEntryScanner with a dedicated marker/token pair. Gating should require three conditions before dispatch: the Feature has exactly one resolvable parent backlog row of type Idea via parent_ids, that parent Idea is not already shipped, and the Feature already has a release_note_link. Rows missing any of those signals should be blocked and traced rather than auto-closed. Preserve the ownership boundary from skills/PLAYBOOK.md and skills/delivery-manager/SKILL.md by dispatching delivery-manager for the terminal Idea write; the automation command itself should not mark the Idea shipped directly. The CLI should mirror the existing automation pattern with --dry-run, --notes-only, and a configurable dispatch template (defaulting to AGENT_IDEA_CLOSE_COMMAND). Validation should cover parent resolution across local and Notion backends, duplicate-prevention on rescans, blocked rows without release-note evidence or a unique parent Idea, and a live delivery-manager completion path that writes the required Pacific timestamp format.

Implementation reference — mirror these existing patterns exactly:

Service file: src/core/automation/idea_close.py (new). Class: IdeaCloseAutomationService. Follow the constructor pattern from src/core/automation/architect_review.py — StatusEntryScanner with target_status='done', marker_prefix='[auto-idea-close]', token_prefix='ideaclose', and a gating function _idea_close_gate().

Gate function: Unlike existing gates that resolve brief context, idea-close gates must: (1) resolve parent Idea via row['parent_ids'] — require exactly one parent of type Idea, (2) check parent Idea status is not 'shipped', (3) require row['release_note_link'] is present. Use store to look up the parent row.

CLI command: Add 'idea-close' to src/cli/commands/automate.py. Env var: AGENT_IDEA_CLOSE_COMMAND. Follow the existing command pattern with --dry-run, --notes-only, and --dispatch-command options.

Dispatch payload: Include feature_title, feature_id, parent_idea_id, parent_idea_title, release_note_link, command_hint (briefcase backlog upsert --title '<idea-title>' --type Idea --status shipped --release-note-link '<link>' --notes 'Shipped in vX.Y.Z on YYYY-MM-DD HH:MM PDT'), dispatch_token, and detected_at.

Tests: tests/core/automation/unit/test_idea_close.py. Use FakeStore and FakeDispatcher from existing test files. Cover: new done Feature with valid parent triggers dispatch, duplicate prevention on rescan, missing parent blocks, multi-parent blocks, already-shipped parent skips, missing release_note_link blocks.
