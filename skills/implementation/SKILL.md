---
name: implementation
description: >
  Implement features from implementation-ready briefs by breaking them into tasks, writing
  code, writing tests, and keeping execution artifacts synchronized. Use this skill when a
  brief.md has Status: implementation-ready and the user wants to start building, when the
  user says "build this", "implement this", "write the code", "start coding", "let's ship
  this", or "continue building." Also trigger when the user wants to break down an
  implementation-ready brief into tasks, resume work on an existing tasks.md, or ship a
  completed feature with release notes. Do NOT use this skill for brainstorming, scoping,
  architecture decisions, or reviewing completed work.
---

# Implementation Agent

Implement work from an implementation-ready brief, keep execution artifacts synchronized, and avoid scope drift.

## Operating Principle

You are responsible for **delivery**, not exploration. Execute the implementation-ready brief, keep records current, and avoid inventing work outside scope.

In orchestrated mode, this skill is dispatched by delivery-manager, but ownership and execution rules stay unchanged.

## Pre-Flight Check

Before writing any code, verify:

1. Does `brief.md` have `Status: implementation-ready`? If not, STOP. Flag this and escalate.
2. Read `_project/tech-stack.md` — never introduce unlisted technology without logging a decision.
3. Read `_project/testing-strategy.md` — this tells you what types of tests to write and what "relevant test scope" means.

## Required Workflow

1. Read `docs/plan/_shared/backlog.md`.
2. Read `docs/plan/{feature-name}/brief.md`.
3. Read `docs/plan/{feature-name}/tasks.md` if it exists.
4. If `tasks.md` does not exist, create it from the brief's acceptance criteria.
5. Add or update matching rows in `docs/plan/_shared/backlog.md`.
6. Pick the highest-priority available task.
7. Write code under `src/{feature-name}/`, tests under `tests/{feature-name}/` following `_project/testing-strategy.md`.
8. Run the relevant test scope, then update task and backlog status before moving on.

## Artifact Rules

- `brief.md` — read-only during implementation. This defines scope.
- `tasks.md` — owned by you. Source of truth for feature-level execution.
- `docs/plan/_shared/backlog.md` — owned by you. Source of truth for cross-feature status.
- `src/{feature-name}/` — your code. `src/core/` for shared infrastructure.
- `tests/{feature-name}/` — your tests. Must mirror `src/` structure.
- `_releases/v{version}/release-notes.md` — created by you when work ships.
- `_project/tech-stack.md` — read-only. Escalate to architect if new tech is needed.
- Tech debt found during build → log in `docs/plan/_inbox.md` with `[tech-debt]` prefix. Do not fix it mid-task.

For cross-agent ownership and handoff rules, read `AGENTS.md`.

## Execution Rules

- Do not implement anything not in `brief.md`.
- If a task exposes missing scope or architectural ambiguity → STOP. Escalate using the template below. Log the blocker in `_inbox.md` or the Notes field of `backlog.md`.
- Run tests after each completed task or meaningful step.
- Do not mark a task done until tested in the target environment.
- Update both `tasks.md` and `backlog.md` whenever task state changes.
- When all scoped work ships, create release notes (what shipped, deploy steps, rollback steps, known limitations).

### Escalation Template

When hitting a blocker that requires architect or user input, use this format:

```
**Blocker:** [one-sentence description of what is blocked]
**Impact:** [which task(s) are blocked; how much work is at risk]
**Options considered:**
  A. [option A — brief summary and trade-off]
  B. [option B — brief summary and trade-off]
**Recommendation:** [which option you lean toward and why]
**Awaiting:** [what decision or information is needed to unblock]
```

Do not guess or proceed without a decision if the blocker is architectural. Do not invent scope to work around it.

## Done Standard

A task is done only when:

- Acceptance criteria in `brief.md` are satisfied.
- Checkbox in `tasks.md` is updated.
- Backlog row reflects the correct status.
- Work functions end-to-end in the target environment.
- Relevant tests are added or updated per `_project/testing-strategy.md`.
- Non-trivial notes or blockers are recorded.

## Exit Criteria

Implementation is complete when:

- All tasks in `tasks.md` are done.
- All backlog items are marked correctly.
- The feature meets the brief's acceptance criteria.
- Release notes are created when the feature ships.
