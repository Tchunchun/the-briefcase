**Status: implementation-ready**
---
## Problem
When an Idea row is marked shipped, the Release Note Link field is never set. The PLAYBOOK requires ship notes on Idea shipped rows and the backlog schema has a Release Note Link field, but no workflow step propagates the release note URL from the shipped Feature back to its parent Idea. The implementation agent sets Release Note Link on Feature done rows, but the delivery-manager (which marks Ideas as shipped) does not copy or set the link on the Idea row.
## Goal
When a Feature ships and its parent Idea is marked shipped, the Release Note Link from the Feature row must be propagated to the Idea row. This ensures every shipped Idea has a direct link to its release notes.
## Acceptance Criteria
- [ ] When delivery-manager sets an Idea to shipped, it copies the Release Note Link from the child Feature's done row to the Idea row
- [ ] If multiple Features share a parent Idea, the most recent release note link is used
- [ ] The ship-routing or ship-dispatch automation includes this propagation step
- [ ] Existing shipped Ideas without links are not retroactively fixed (out of scope)
- [ ] Both local and Notion backends handle the link propagation
## Non-Functional Requirements
No new dependencies. Must work within existing automation dispatch flow.
## Out of Scope
Retroactive backfill of release note links on already-shipped Ideas. Changes to the implementation agent's ship flow. UI for viewing linked release notes.
## Open Questions
Resolved: Both. The delivery-manager skill instructions should document the responsibility (copy Release Note Link from Feature to parent Idea when marking shipped). The ship-routing automation should include the propagation as a post-dispatch step so it happens automatically when orchestrated mode is on. This covers both manual and orchestrated flows.
## Technical Approach
Two changes:
**1. Delivery-manager skill update (skills/delivery-manager/SKILL.md):**
Add to the ship path instructions: when marking an Idea as shipped, the delivery-manager must read the child Feature's Release Note Link and set it on the Idea row via backlog upsert --release-note-link. This covers manual mode.
**2. Ship-routing automation (src/core/automation/ship_routing.py):**
After the ship-routing scanner detects a Feature at done with a Release Note Link, look up its parent Idea (via parent_id). If the parent Idea exists and has no Release Note Link, propagate the link via store.write_backlog_row(). This covers orchestrated mode.
The backlog upsert CLI already supports --release-note-link (used by implementation agent). No new CLI options needed. Both Notion and local backends handle the field through existing write_backlog_row paths.
