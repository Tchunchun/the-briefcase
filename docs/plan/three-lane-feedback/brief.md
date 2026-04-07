**Status: implementation-ready**

---

## Problem
All user feedback (bugs, small fixes, feature requests) flows through the same heavyweight pipeline: inbox → ideation (full brief) → architect review → implementation → review → ship. A one-line bug fix requires the same ceremony as a multi-week feature, creating unnecessary friction and slowing delivery of simple changes.

## Goal
Introduce three processing lanes so that the workflow ceremony matches the complexity of the work. Quick fixes skip the brief entirely, small changes use a lightweight brief without architect review, and features use the current full pipeline.

## Acceptance Criteria
- [ ] Ideation agent assigns a lane (quick-fix, small, or feature) during triage based on a decision tree
- [ ] User can override the lane via --lane flag on inbox add
- [ ] Quick-fix lane: creates a Task backlog row directly (no brief), routes straight to implementation with self-review
- [ ] Small lane: creates a lite brief (Problem + Goal + AC only, no NFRs/open questions/architect review), routes to implementation then review
- [ ] Feature lane: uses the current full pipeline (brief → architect → implementation → review)
- [ ] Lane assignment is recorded on the backlog row and visible in backlog list output
- [ ] Implementation agent can escalate a quick-fix or small item to a higher lane if complexity is discovered
- [ ] PLAYBOOK.md documents all three lanes, their handoff rules, and escalation between lanes
- [ ] Ideation SKILL.md includes the triage decision tree for lane assignment
- [ ] Existing feature pipeline is unchanged — no regressions for current full-brief workflow

## Non-Functional Requirements
- **Expected load / scale:** Same as current — single user, ~50 operations/day
- **Latency / response time:** CLI response < 2s for lane assignment and routing
- **Availability / reliability:** Best-effort, same as current CLI
- **Cost constraints:** No new paid services; Notion API usage stays within current patterns
- **Compliance / data residency:** No change — internal use only
- **Other constraints:** Must not break existing briefcase CLI commands or Notion backlog structure; existing briefs and backlog rows must continue to work without migration

## Out of Scope
- Automated lane detection via AI/heuristics (ideation agent decides manually using decision tree)
- Changes to the review agent or delivery manager agent workflows
- New Notion database fields beyond lane tracking
- Dashboard or analytics for lane throughput
- Safety guards or freeze-list functionality (separate initiative)

## Open Questions
All resolved by architect:

1. Lane field: New select property "Lane" on the Backlog database with options: quick-fix, small, feature. Added to BACKLOG_SCHEMA in schemas.py, patched on existing databases via upgrade command.

2. Lite brief template: Reuse existing brief.md template. The small lane simply omits NFRs, open questions, and technical approach sections — the brief write CLI already supports optional sections. No new template needed.

3. --lane override behavior: --lane flag is a hard override. If passed, ideation agent does not re-triage. If omitted, ideation agent assigns lane during triage using the decision tree.

4. Quick-fix Idea row: No. Quick-fix items go from inbox directly to Task backlog row, skipping Idea and brief entirely. The inbox entry is the audit trail.

## Technical Approach
### Architecture

This is primarily a workflow/documentation change with minimal code changes. The three lanes modify agent behavior rules, not core infrastructure.

#### 1. Notion Schema Change

Add a "Lane" select property to BACKLOG_SCHEMA in `src/integrations/notion/schemas.py`:
- Options: `quick-fix`, `small`, `feature`
- Default: `feature` (backward compatible — all existing rows treated as feature lane)
- The upgrade command (`src/integrations/notion/upgrade.py`) will detect and patch this field on existing databases.

#### 2. CLI Changes

**`src/cli/commands/inbox.py`** — add `--lane` option to `inbox add`:
- Accepts: `quick-fix`, `small`, `feature`
- Optional — if omitted, ideation agent assigns during triage
- Stored in the inbox item notes for the ideation agent to read

**`src/cli/commands/backlog.py`** — surface Lane field in `backlog upsert` and `backlog list`:
- `--lane` option on upsert
- Lane column in list output

#### 3. Skill Documentation Changes (primary deliverable)

**`skills/PLAYBOOK.md`** — add a "Processing Lanes" section after "Handoff Sequence":
- Lane definitions with entry criteria, required artifacts, and handoff rules
- Lane-specific handoff sequences (quick-fix skips phases 1-1.75, small skips 1.5-1.75)
- Escalation rules: how to move an item to a higher lane

**`skills/ideation/SKILL.md`** — add triage decision tree:
```
Is the root cause known AND the fix is a single-file change? → quick-fix
Is the scope clear AND touches ≤2 files AND no architectural questions? → small  
Everything else → feature
```

**`skills/implementation/SKILL.md`** — add lane-aware entry:
- Quick-fix: skip brief read, work from Task notes, self-review
- Small: read lite brief, implement, route to review
- Feature: unchanged current flow

#### 4. No Migration Required

Existing backlog rows without a Lane value default to `feature` behavior. No data migration needed.

#### Dependencies
- Tech stack: Python 3.11+, Click, Notion API — all within current stack
- No new libraries required
