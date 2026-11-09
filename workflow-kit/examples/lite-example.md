# Lite profile example

This example shows the concise artifact set for one Lite task. There is no
Architect role, no Feature/Task hierarchy, and no release record beyond the
application's normal policy.

---

## Requirement packet

- Work item: `https://github.com/owner/repo/issues/55`
- Profile: `Lite`
- Parent: none
- Canonical requirement: `docs/tasks/fix-55.md @ sha:c3d4e5f`
- Approval: `@user, 2026-11-05T08:00Z, https://github.com/owner/repo/issues/55#issuecomment-500`

### Context and outcome

The login button is unresponsive when the form has a validation error. Users are
unable to submit after correcting a typo.

### Scope

- Fix the disabled state on the login button to clear when all validation errors
  are resolved.

### Exclusions

- No change to validation logic or error messages.

### Acceptance and verification

| Criterion | Observable result | Check | Owner |
|---|---|---|---|
| AC-01 | Button is enabled after all errors are resolved | Manual smoke test | Build |
| AC-02 | Existing login tests pass | `pytest tests/ui/test_login.py` | Build |

### Dependencies and questions

- Blockers: none
- Open questions: none
- Privacy/visibility: public-facing UI, no PII

---

## Review record (excerpt)

- Work item: `https://github.com/owner/repo/issues/55`
- Pull request: `https://github.com/owner/repo/pull/61`
- Approved requirement: `docs/tasks/fix-55.md @ sha:c3d4e5f`
- Reviewed head: `jkl345mno678`
- Reviewer session: review-session-8 (separate from Build session)

### Criterion evidence

| Criterion | Evidence at reviewed head | Result |
|---|---|---|
| AC-01 | Manual smoke test: button re-enables on error clear | pass |
| AC-02 | `pytest tests/ui/test_login.py` output: 12/12 pass | pass |

### Verdict

Accepted

Reason: Both criteria met at the reviewed head. No scope drift or regressions
observed in the adjacent login flow.

---

## Notes

Lite does not use:
- An Architect role or sign-off record.
- A Standard release record with version and coverage fields.
- A Feature/Task hierarchy.

A stopping technical question moves the item to `Blocked` with a
Requirements-owned question and resume condition.
