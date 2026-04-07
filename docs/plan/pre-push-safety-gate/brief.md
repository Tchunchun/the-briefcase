**Status: draft**
**Created: 2026-03-21**

---

## Problem
Pushing to main after rebase is error-prone. Conflict resolution can silently drop imports or introduce semantic breaks. Tests are run manually and reactively — broken code can reach main if the developer forgets.

## Goal
A briefcase ship command that automates the safe merge-to-main sequence: pull --rebase, run tests, push. Fails fast on test failure so broken code never reaches main.

## Acceptance Criteria
- [ ] briefcase ship command exists with usage: briefcase ship [branch] (defaults to main)
- [ ] Runs git pull --rebase origin <branch> before pushing
- [ ] Runs pytest tests/ --ignore=tests/e2e -x -q after rebase
- [ ] Aborts push and prints failure summary if tests fail
- [ ] Pushes to origin on success
- [ ] Warns if working directory has uncommitted changes (does not block)

## Non-Functional Requirements


## Out of Scope


## Open Questions


## Technical Approach
