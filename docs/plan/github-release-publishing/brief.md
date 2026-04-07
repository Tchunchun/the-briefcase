**Status: implementation-ready**
**Created: 2026-03-21**

---

## Problem
briefcase update fails with HTTP 404 because no GitHub releases exist. Consumers cannot use the default update path without --source workaround.

## Goal
Ensure consumers can run ./briefcase update and get the latest version without manual flags.

## Acceptance Criteria
- [ ] A GitHub release exists for the current version after ship
- [ ] ./briefcase update --check returns the correct latest version from the published release
- [ ] Ship checklist or automation includes a release publishing step

## Non-Functional Requirements


## Out of Scope


## Open Questions


## Technical Approach
