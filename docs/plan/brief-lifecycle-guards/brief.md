**Status: implementation-ready**
**Created: 2026-03-30**

---

## Problem
Briefcase allows briefs to advance through lifecycle states (draft -> architect-review -> implementation-ready) without validating that required structured sections are populated. Combined with the lossy Notion round-trip (addressed separately in brief-write-corruption), this means briefs can reach implementation-ready with blank Problem, Goal, or Acceptance Criteria sections. ~30 briefs in the current workspace are stuck at implementation-ready with missing sections. Even after the round-trip fix ships, agents can still explicitly pass empty values or omit fields when the existing read is stale, and there is no guardrail to catch this before the brief advances.

## Goal
Prevent briefs from advancing to protected lifecycle states when required sections are blank, and surface field-completeness issues immediately after every write so that agents and users can catch data loss before it propagates.

## Acceptance Criteria
- [ ] `briefcase brief write` rejects status transitions to `architect-review` or `implementation-ready` when any of Problem, Goal, or Acceptance Criteria are blank or missing in the final merged data — returns a structured JSON error naming the blank sections.
- [ ] `briefcase brief write` succeeds for draft status even when required sections are blank (drafts are expected to be incomplete).
- [ ] `briefcase brief write` output includes a `field_validation` key that lists each required section and whether it is populated or blank — present on every successful write.
- [ ] When `--force` flag is passed, promotion proceeds even with blank required sections — the output includes a `field_validation_bypassed: true` warning instead of blocking.
- [ ] Existing briefs that are already at implementation-ready with blank sections are not retroactively broken — validation only triggers on new writes.
- [ ] Required sections for promotion are configurable via a constant (default: Problem, Goal, Acceptance Criteria) so future sections can be added without code changes across multiple files.
- [ ] All validation logic is tested: unit tests for the guard function, CLI integration tests for block/allow/force scenarios.

## Expected Experience
**Before (current behavior):**
```
$ briefcase brief write my-feature --status implementation-ready --change-summary 'Sign-off'
{"written": "my-feature", "status": "implementation-ready"}
```
Brief silently advances with blank Problem, Goal, and AC. No indication of missing fields.

**After (with guards):**
```
$ briefcase brief write my-feature --status implementation-ready --change-summary 'Sign-off'
{"success": false, "error": "Cannot promote to implementation-ready: required sections are blank: problem, goal, acceptance_criteria"}
```

With force flag:
```
$ briefcase brief write my-feature --status implementation-ready --change-summary 'Sign-off' --force
{"written": "my-feature", "status": "implementation-ready", "field_validation": {"problem": "blank", "goal": "blank", "acceptance_criteria": "blank"}, "field_validation_bypassed": true}
```

Successful write with all fields:
```
$ briefcase brief write my-feature --status implementation-ready --problem '...' --goal '...' --acceptance-criteria '...' --change-summary 'Sign-off'
{"written": "my-feature", "status": "implementation-ready", "field_validation": {"problem": "populated", "goal": "populated", "acceptance_criteria": "populated"}}
```

## Non-Functional Requirements
- No new dependencies.
- Must work on both local and Notion backends (validation happens in CLI/service layer, above the backend).
- Must not break existing brief revision history.
- Guard logic must be a pure function (no I/O) for easy unit testing.
- Performance: no additional API calls beyond the existing read-before-write in the CLI.

## Out of Scope
- Retroactive repair of already-corrupted briefs (separate concern).
- Notion round-trip lossiness fix (covered by brief-write-corruption).
- Diff preview before writes (future enhancement — too much scope for this brief).
- Replace-vs-patch CLI semantics documentation (can be a separate doc task after both fixes ship).
- Validation of non-required sections (Expected Experience, NFRs, etc.) — these remain optional.

## Open Questions
1. ~~Should the guard also apply to architect-review status, or only implementation-ready?~~ Resolved: Apply to both. architect-review requires Problem and Goal; implementation-ready requires Problem, Goal, and Acceptance Criteria.
2. ~~Should --force be available to all agents, or restricted?~~ Resolved: Available to all agents. The --force write is recorded in revision history (change_summary includes force-promoted) so the audit trail captures it.

## Technical Approach
### Architecture Decision
Validation lives in the CLI command layer (brief_write in src/cli/commands/brief.py), invoked after the merge step builds the final data dict and before the store.write_brief() call. This keeps the pure guard logic separate from I/O, works identically on both local and Notion backends, and avoids adding backend-specific validation.

### New Constants (src/core/storage/briefs.py)
Add PROMOTION_REQUIRED_SECTIONS dict mapping protected statuses to required section tuples: architect-review requires (problem, goal); implementation-ready requires (problem, goal, acceptance_criteria). Single source of truth for future additions.

### New Pure Function (src/core/storage/briefs.py)
Add validate_promotion_sections(data, target_status) returning a dict mapping each required section key to populated or blank. Returns empty dict for unprotected statuses.

### CLI Changes (src/cli/commands/brief.py)
1. New --force flag on brief_write.
2. Validation call after merge, before store.write_brief(). If blank sections and no --force, output_error with structured message. If --force, proceed and add field_validation_bypassed: true to output. Append [force-promoted] to change_summary.
3. Add field_validation key to output JSON on every successful write to a protected status.

### File Change Map
src/core/storage/briefs.py - Add PROMOTION_REQUIRED_SECTIONS and validate_promotion_sections()
src/cli/commands/brief.py - Add --force flag, validation call, enrich output JSON
tests/core/unit/test_briefs_validation.py (new) - Unit tests for guard function
tests/cli/unit/test_brief_write_guards.py (new) - CLI integration tests for block/allow/force

### Risk Assessment
Low risk. Validation is additive. Existing workflows passing populated fields are unaffected. draft writes are unguarded. --force escape hatch is always available and auditable via revision history.
