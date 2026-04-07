**Status: implementation-ready**

---

## Problem
No automated check exists to verify all release prerequisites are met before shipping. Teams risk pushing releases with incomplete feature statuses, missing release notes, blocking review findings, or dirty git state.

## Goal
A CLI command (briefcase release gate --version vX.Y.Z) validates release readiness across feature status, blocking findings, required tests, release-note existence, feature release_note_link, parent idea shipped propagation, and git cleanliness. Supports --dry-run (read-only check) and --apply (safe artifact updates + printed git commands). Emits a release report artifact for auditability.

## Acceptance Criteria
- [ ] briefcase release gate --version vX.Y.Z runs all readiness checks
- [ ] Checks: all linked Features are review-accepted/done, no blocking findings, release note exists, done Features have release_note_link, parent Ideas shipped, git tree clean, tag does not exist
- [ ] --dry-run prints checklist with pass/fail, exits non-zero on failure
- [ ] --apply performs safe artifact updates then prints git commands
- [ ] JSON release report emitted to stdout
- [ ] Clear actionable error messages per failed check
- [ ] Unit and integration tests

## Non-Functional Requirements
Gate completes in under 10s for typical project (<100 backlog rows). No new dependencies.

## Out of Scope
Automatic git tagging/pushing. CI/CD integration. Changelog generation. Multi-version batching.

## Open Questions


## Technical Approach
Files: src/cli/commands/release.py (add gate subcommand), new src/core/release_gate.py (logic)

1. CLI (release.py): Add gate subcommand with --version (required), --dry-run (default), --apply. Delegates to ReleaseGate.

2. Business logic (release_gate.py): ReleaseGate class with check methods per criterion. Each returns CheckResult(passed, message). Gate aggregates results.

3. Apply mode: Set release_note_link on Features missing it, propagate shipped to parent Ideas, print git tag/push commands.

4. Output: JSON with version, timestamp, checks array, overall_passed.

Testing: Unit tests per check, integration test for full gate.
