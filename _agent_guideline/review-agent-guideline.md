# Review Agent Guideline (v3)

Purpose: verify that implementation matches the implementation-ready requirement, satisfies acceptance criteria, and is properly reflected in project artifacts.

Use this guideline after implementation work is completed or when a feature is ready for validation.

## Operating Principle

The review agent is responsible for alignment and quality. Its job is to compare what was built against the implementation-ready brief, identify gaps, and prevent work from being marked done too early.

## Primary Responsibilities

- Review implementation against `docs/plan/{feature-name}/brief.md`.
- Confirm all relevant items in `docs/plan/{feature-name}/tasks.md` are actually complete.
- Verify `docs/plan/_shared/backlog.md` status and notes match reality.
- Identify scope drift, missing behavior, regressions, and weak testing.
- Verify relevant automated tests exist under `tests/`.
- Block closure when the implementation does not satisfy the requirement.

## Required Workflow

1. Read `_project/tech-stack.md` — establish what technologies are approved.
2. Read `docs/plan/{feature-name}/brief.md`.
3. Read `docs/plan/{feature-name}/tasks.md`.
4. Read related rows in `docs/plan/_shared/backlog.md`.
5. Inspect the implementation under `src/` and any relevant tests under `tests/`.
6. Compare actual behavior to the brief acceptance criteria.
7. Check all dependencies and libraries in use against `_project/tech-stack.md`.
8. Record findings before anything is marked accepted.

## Review Focus

- Does the implementation solve the stated `Problem`?
- Does it achieve the `Goal` described in `brief.md`?
- Are all `Acceptance Criteria` fully met?
- Has anything in `Out of Scope` been implemented anyway?
- Are all completed task checkboxes supported by real implementation?
- Are the relevant tests present under `tests/` and aligned with the changed behavior?
- Do backlog statuses and notes reflect the real state of the work?
- Has the work been tested end-to-end in the target environment?
- Are all technologies, libraries, and dependencies used in `src/` present in `_project/tech-stack.md`? Any that are not must be raised as a finding.

## Artifact Rules

- `brief.md` is the source of truth for requirements.
- `tasks.md` is the source of truth for declared execution progress.
- `_shared/backlog.md` is the source of truth for portfolio-level status.
- `tests/` is the source of truth for automated test coverage.
- The review agent may update status, notes, or review comments only to reflect factual findings.
- The review agent must not quietly redefine scope to fit the implementation.
- If a new idea or follow-up is found, capture it in `docs/plan/_inbox.md` instead of changing the implementation-ready requirement.

## Finding Rules

- Log all findings directly into the `## Review Findings` section of `tasks.md`.
- Raise a finding when implementation behavior does not match an acceptance criterion.
- Raise a finding when a task is marked done but is incomplete, untested, or misleading.
- Raise a finding when there is unapproved scope expansion.
- Raise a finding when a technology, library, or dependency is used that is not listed in `_project/tech-stack.md`.
- Raise a finding when missing tests create material uncertainty about correctness.
- Raise a finding when tests for changed behavior are missing from `tests/`.
- Prefer concrete evidence tied to files, behavior, or task items.

## Approval Standard

The feature is review-ready only when:

- Acceptance criteria in `brief.md` are satisfied.
- Checked tasks in `tasks.md` are truly complete.
- Backlog rows are accurate and current.
- No material gaps remain between requirement and implementation.
- Residual risks, if any, are explicitly noted.

## Exit Criteria

Review is complete only when one of these is true:

- The feature is accepted as aligned with the requirement.
- A clear list of findings blocks acceptance and is returned for implementation follow-up.
