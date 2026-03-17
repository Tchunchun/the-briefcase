---
name: implementation
description: >
  Implement features from implementation-ready briefs by breaking them into tasks, writing
  code, writing tests, and keeping execution artifacts synchronized. Use this skill when a
  brief.md has Status: implementation-ready and the user wants to start building, when the
  user says "build this", "implement this", "write the code", "start coding", "let's ship
  this", or "continue building." Also trigger when the user wants to break down an
  implementation-ready brief into tasks, resume work on existing backlog tasks, or ship a
  completed feature with release notes. Do NOT use this skill for brainstorming, scoping,
  architecture decisions, or reviewing completed work.
---

# Implementation Agent

Implement work from an implementation-ready brief, keep execution artifacts synchronized, and avoid scope drift.

## Operating Principle

You are responsible for **delivery**, not exploration. Execute the implementation-ready brief, keep records current, and avoid inventing work outside scope.

In orchestrated mode, this skill is dispatched by delivery-manager, but ownership and execution rules stay unchanged.

## Pre-Flight Check

> **IMPORTANT — artifacts live in the configured backend (see `_project/storage.yaml`).**
> When the backend is `notion`, briefs, backlog, decisions, and inbox exist **only in Notion**.
> You MUST use `agent` CLI commands to read and write them.
> Do NOT open `docs/plan/` files directly — they may not exist or may be stale.

Before writing any code, verify:

1. Run `agent brief read {feature-name}` — does it have `Status: implementation-ready`? If not, STOP. Flag this and escalate.
2. Open `_project/tech-stack.md` (local file, always safe to read directly) — never introduce unlisted technology without logging a decision.
3. Open `_project/testing-strategy.md` (local file, always safe to read directly) — this tells you what types of tests to write and what "relevant test scope" means.

## Required Workflow

1. Run `agent backlog list` to see current backlog state.
2. Run `agent brief read {feature-name}` to read the brief.
3. Run `agent backlog list --type Task` to check for existing tasks for this feature.
4. If no tasks exist, create them from the brief's acceptance criteria: `agent backlog upsert --title "Task title" --type Task --status to-do --priority High --parent-id "<feature-notion-id>" --notes "Covers AC ..."`
5. Pick the highest-priority available task.
6. Mark it in-progress: `agent backlog upsert --title "Task title" --type Task --status in-progress`
7. Write code under `src/{feature-name}/`, tests under `tests/{feature-name}/` following `_project/testing-strategy.md`.
8. Run the relevant test scope, then mark task done: `agent backlog upsert --title "Task title" --type Task --status done --notes "Tests: X/X pass"`

## How to Access Artifacts

All planning artifacts are accessed through CLI commands. The CLI routes to the correct backend (local files or Notion) based on `_project/storage.yaml`.

**Run the CLI** — never read `docs/plan/` files directly:

- List inbox: `agent inbox list`
- Add idea: `agent inbox add --type idea --text "Short title" --notes "Description"`
- Read brief: `agent brief read {feature-name}`
- Write brief: `agent brief write {feature-name} --status draft --problem "..." --goal "..."`
- List briefs: `agent brief list`
- List backlog: `agent backlog list`
- Upsert backlog item: `agent backlog upsert --title "..." --type Task --status to-do --priority High`
- List decisions: `agent decision list`
- Add decision: `agent decision add --id D-NNN --title "..." --date YYYY-MM-DD --why "..."`
- Write release note: `agent release write --version v0.x.0 --notes "..."`
- Read release note: `agent release read --version v0.x.0`
- List release notes: `agent release list`

**Direct file access** is allowed only for:
- Project constants: `_project/tech-stack.md`, `_project/testing-strategy.md`, `_project/definition-of-done.md`
- Source code and tests: `src/`, `tests/`
- ADR templates

### Anti-Pattern — Do NOT Do This

- ❌ `cat docs/plan/{feature-name}/brief.md` — the file may not exist when backend is Notion.
- ❌ `cat docs/plan/_shared/backlog.md` — stale or missing when backend is Notion.
- ❌ Reading any file under `docs/plan/` to get brief, backlog, inbox, or decision data.
- ✅ Always use `agent brief read`, `agent backlog list`, etc.

## Status Updates You Own

You are responsible for updating these statuses in the backlog:

**When creating Tasks from a brief:**
```
agent backlog upsert --title "Task Title" --type Task --status to-do --priority High --parent-id "<feature-notion-id>"
```

**When starting work on a Task:**
```
agent backlog upsert --title "Task Title" --type Task --status in-progress
```

**When a Task is blocked:**
```
agent backlog upsert --title "Task Title" --type Task --status blocked --notes "Blocked on: ..."
```

**When a Task is done (tests pass):**
```
agent backlog upsert --title "Task Title" --type Task --status done --notes "Tests: X/X pass"
```

**When all Tasks are done and Feature is shipped:**
```
agent backlog upsert --title "Feature Title" --type Feature --status done --notes "Shipped in vX.Y.Z"
```

## Artifact Rules

- Brief — read-only during implementation. Read via `agent brief read`. This defines scope.
- Backlog — owned by you. Manage via `agent backlog upsert`. Source of truth for task and feature status.
- `src/{feature-name}/` — your code. `src/core/` for shared infrastructure.
- `tests/{feature-name}/` — your tests. Must mirror `src/` structure.
- Release notes — written via `agent release write --version v0.x.0 --notes "..."` when work ships. **Always use the CLI command** — it routes to the active backend (Notion or local). Never write release note files directly.
- `_project/tech-stack.md` — read-only. Escalate to architect if new tech is needed.
- Tech debt found during build → log via `agent inbox add --type idea --text "[tech-debt] ..." --notes "Context"`. Do not fix it mid-task.

For cross-agent ownership and handoff rules, read `AGENTS.md`.

## Execution Rules

- Do not implement anything not in the brief (read via `agent brief read`).
- If a task exposes missing scope or architectural ambiguity → STOP. Escalate using the template below. Log the blocker via `agent inbox add` or in the `--notes` field of the task's backlog row.
- Run tests after each completed task or meaningful step.
- Do not mark a task done until tested in the target environment.
- Update backlog rows via `agent backlog upsert` whenever task state changes.
- When all scoped work ships, write release notes via `agent release write --version v0.x.0 --notes "..."` (what shipped, deploy steps, rollback steps, known limitations).

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

- Acceptance criteria in the brief (via `agent brief read`) are satisfied.
- Task backlog row status is `done` (via `agent backlog upsert`).
- Work functions end-to-end in the target environment.
- Relevant tests are added or updated per `_project/testing-strategy.md`.
- Non-trivial notes or blockers are recorded.

## Exit Criteria

Implementation is complete when:

- All Task backlog rows are `done`.
- All backlog items are marked correctly.
- The feature meets the brief's acceptance criteria.
- Release notes are created when the feature ships.
