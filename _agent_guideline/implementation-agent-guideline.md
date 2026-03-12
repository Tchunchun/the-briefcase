# Implementation Agent Guideline (v3)

Purpose: implement work from an implementation-ready brief, keep execution artifacts synchronized, and avoid scope drift.

Use this guideline when a feature already has an implementation-ready `docs/plan/{feature-name}/brief.md` and is ready to be broken down, built, or shipped.

## Operating Principle

The implementation agent is responsible for delivery, not exploration. Its job is to execute the implementation-ready brief, keep records current, and avoid inventing work outside scope.

## Primary Responsibilities

- Read the current plan before making changes.
- Break implementation-ready scope into atomic tasks when needed.
- Implement one task at a time.
- Write or update automated tests under `tests/`.
- Run relevant tests after each meaningful implementation step.
- Keep task and backlog artifacts in sync.
- Produce release notes when completed work ships.

## Required Workflow

1. Read `_project/tech-stack.md` before writing any code.
2. Read `docs/plan/_shared/backlog.md`.
3. Read `docs/plan/{feature-name}/brief.md`.
4. Read `docs/plan/{feature-name}/tasks.md` if it exists.
5. If `tasks.md` does not exist, create it from the implementation-ready brief.
6. Add or update matching rows in `docs/plan/_shared/backlog.md`.
7. Pick the highest-priority available task.
8. Write code under `src/{feature-name}/`, tests under `tests/{feature-name}/`.
9. Run tests, then update task and backlog status before moving on.

## Artifact Rules

- `brief.md` defines scope and is the source of truth for what should be built. Read-only during implementation.
- `tasks.md` is the source of truth for feature-level execution. Owned by this agent.
- `docs/plan/_shared/backlog.md` is the source of truth for cross-feature priority and status. Owned by this agent.
- Application code belongs under `src/{feature-name}/`. Shared infrastructure belongs under `src/core/`.
- Automated tests belong under `tests/{feature-name}/`. Mirror the `src/` structure exactly.
- `_releases/v{version}/release-notes.md` is created by the implementation agent when work is shipped.
- `_project/tech-stack.md` is read-only. If a new technology is needed, log the decision in `_project/decisions.md` and escalate to the user before proceeding.
- Do not create extra implementation logs, temporary planning docs, or duplicate status files.
- Put any new idea, follow-up, or out-of-scope request into `docs/plan/_inbox.md`.

## Execution Rules

- Do not implement anything not described in `brief.md`.
- **Escalation Protocol for Scope Flaws & Blockers**: If a task exposes missing scope, architectural ambiguity, or severe technical blockers, STOP. Do not invent solutions. Instead, escalate to the user and log the blocker in `_inbox.md` or the `Notes` field of `backlog.md` before proceeding.
- Add or update relevant tests in `tests/` when behavior changes.
- Run the relevant test scope after each completed task or meaningful implementation step.
- Do not mark a task done until it has been tested in the target environment.
- Update both `tasks.md` and `_shared/backlog.md` whenever task state changes.
- Use the `Notes` field in `_shared/backlog.md` for blockers, context, or meaningful test outcomes.
- When all scoped work is complete and the feature ships, create `_releases/v{version}/release-notes.md`.
- Release notes must summarize what shipped, how to deploy, rollback steps, and known limitations.

## Done Standard

A task is done only when:

- The related acceptance criteria in `brief.md` are satisfied.
- The checkbox in `tasks.md` is updated.
- The matching backlog row reflects the correct status.
- The work functions end-to-end in the target environment.
- Relevant automated tests in `tests/` are added or updated.
- Any non-trivial notes or blockers are recorded.

## Exit Criteria

Implementation is complete only when:

- All tasks in `tasks.md` are done.
- All related backlog items are marked correctly.
- The feature meets the brief acceptance criteria.
- Release notes are created when the feature ships.
