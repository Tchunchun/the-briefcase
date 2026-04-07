**Status: implementation-ready**
**Created: 2026-03-21**

---

## Problem
pyproject.toml version drifts from actual release versions. The package showed 0.8.0 while release notes were at 0.9.3. No gate prevents this.

## Goal
Ensure pyproject.toml version stays in sync with release notes automatically or with a hard gate.

## Acceptance Criteria
- [ ] When a release note is written or a feature ships, pyproject.toml version is bumped to match
- [ ] Version mismatch between pyproject.toml and latest release note is detectable via a check command or CI gate
- [ ] The version bump is committed as part of the ship flow

## Non-Functional Requirements


## Out of Scope


## Open Questions


## Technical Approach
