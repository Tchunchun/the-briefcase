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

> **Backend & artifact rules:** see PLAYBOOK.md — Backend Protocol and Artifact Access Rules.

Before writing any code, verify:

1. Run `briefcase brief read {feature-name}` — does it have `Status: implementation-ready`? If not, STOP. Flag this and escalate.
2. Open `_project/tech-stack.md` (local file, always safe to read directly) — never introduce unlisted technology without logging a decision.
3. Open `_project/testing-strategy.md` (local file, always safe to read directly) — this tells you what types of tests to write and what "relevant test scope" means.

## Required Workflow

1. Run `briefcase backlog list` to see current backlog state.
2. Run `briefcase brief read {feature-name}` to read the brief.
3. Run `briefcase backlog list --type Task` to check for existing tasks for this feature.
4. If no tasks exist, create them from the brief's acceptance criteria: `briefcase backlog upsert --title "Task title" --type Task --status to-do --priority High --parent-id "<feature-notion-id>" --notes "Covers AC ..."`
5. When implementation work begins, move the Feature row from `implementation-ready` to `in-progress`: `briefcase backlog upsert --title "Feature Title" --type Feature --status in-progress --notes "Implementation started on <date>"`
6. Pick the highest-priority available task.
7. Mark it in-progress: `briefcase backlog upsert --title "Task title" --type Task --status in-progress`
8. Write code under `src/{feature-name}/`, tests under `tests/{feature-name}/` following `_project/testing-strategy.md`.
9. Run the relevant test scope, then mark task done: `briefcase backlog upsert --title "Task title" --type Task --status done --notes "Tests: X/X pass"`
10. When all scoped implementation is complete, all feature tasks are `done`, and the work is ready for review, move the Feature row from `in-progress` to `review-ready`: `briefcase backlog upsert --title "Feature Title" --type Feature --status review-ready --notes "Implementation complete; ready for review on <date>"`
11. If the Feature row already has `parent_ids`, preserve them on Feature upserts (do not clear parent links when updating status/notes).
12. Record the handoff: run `briefcase automate review-ready --notes-only` to write trace to the Automation Trace field and get dispatch payloads.
13. **DO NOT STOP. Continue immediately as the review agent.** Tell the user: *"Implementation complete. Switching to review."* Then for **each** dispatched brief, execute these steps in order — **use the exact `feature_title` from the dispatch payload for all backlog upserts to avoid creating duplicate rows**:
    1. Run the `command_hint` from the dispatch payload (e.g., `briefcase brief read {brief_name}`) to load the brief.
    2. Open `_project/tech-stack.md`.
    3. Run `briefcase backlog list --type Task` to review task rows for this feature.
    4. Inspect the implementation under `src/` and tests under `tests/`.
    5. Compare actual behavior to the brief's acceptance criteria.
    6. Run the full test suite to check for regressions.
    7. If accepted: `briefcase backlog upsert --title "<feature_title from payload>" --type Feature --status review-accepted --review-verdict accepted --notes "Review: all AC met"`
    8. If changes needed: `briefcase backlog upsert --title "<feature_title from payload>" --type Feature --status in-progress --review-verdict changes-requested --notes "Review: see findings"` and list the findings, then immediately re-enter the implementation fix cycle.
14. After review accepts the work, complete release notes and ship wrap-up, then move the Feature row from `review-accepted` to `done`: `briefcase backlog upsert --title "Feature Title" --type Feature --status done --release-note-link "<release-note-url>" --notes "Shipped in vX.Y.Z on YYYY-MM-DD HH:MM PST/PDT"`

## Status Updates You Own

You are responsible for updating these statuses in the backlog:

**When implementation starts on a Feature:**
```
agent backlog upsert --title "Feature Title" --type Feature --status in-progress --notes "Implementation started on <date>"
```

Move the Feature row to `in-progress` as soon as active build work begins. Do not leave a Feature at `implementation-ready` once implementation has started.

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

**When implementation is complete and the Feature is ready for review:**
```
agent backlog upsert --title "Feature Title" --type Feature --status review-ready --notes "Implementation complete; ready for review on <date>"
agent automate review-ready --notes-only
```

Use `review-ready` only when all scoped implementation work is finished, the relevant tests have been run, and the Feature is ready for review handoff.

**When review is accepted and ship wrap-up is complete:**
```
agent backlog upsert --title "Feature Title" --type Feature --status done --release-note-link "<release-note-url>" --notes "Shipped in vX.Y.Z on YYYY-MM-DD HH:MM PST/PDT"
```

Always include the ship timestamp in Pacific Time, with the timezone abbreviation explicitly written as `PST` or `PDT`.

## Artifact Rules

- Brief — the head brief is read-only during implementation and remains the source of truth. Inspect history with `briefcase brief history` / `briefcase brief revision` if needed, but do not change scope or restore revisions without the appropriate upstream handoff.
- Backlog — owned by you. Manage via `briefcase backlog upsert`. Source of truth for task and feature status.
- `src/{feature-name}/` — your code. `src/core/` for shared infrastructure.
- `tests/{feature-name}/` — your tests. Must mirror `src/` structure.
- Release notes — written via `briefcase release write --version v0.x.0 --notes "..."` when work ships. **Always use the CLI command** — it routes to the active backend (Notion or local). Never write release note files directly.
- `_project/tech-stack.md` — read-only. Escalate to architect if new tech is needed.
- Tech debt found during build → log via `briefcase inbox add --type idea --text "[tech-debt] ..." --notes "Context"`. Do not fix it mid-task.

For cross-agent ownership and handoff rules, read `AGENTS.md`.

## Execution Rules

- Do not implement anything not in the brief (read via `briefcase brief read`).
- If a task exposes missing scope or architectural ambiguity → STOP. Escalate using the template below. Log the blocker via `briefcase inbox add` or in the `--notes` field of the task's backlog row.
- Run tests after each completed task or meaningful step.
- Do not mark a task done until tested in the target environment.
- Update backlog rows via `briefcase backlog upsert` whenever task state changes.
- When a feature reaches `review-accepted`, finish the release notes and final ship wrap-up before moving it to `done`.

### Escalation

> **Full protocol:** see PLAYBOOK.md — Reverse-Flow Escalation Protocol.

When hitting a blocker that requires scope revision (ideation) or architecture change (architect):
1. STOP implementation on the affected task.
2. Append an escalation packet to the Feature's `--notes` field using the format in the PLAYBOOK.
3. Log the blocker via `briefcase inbox add` or in the task's `--notes`.
4. Do not guess or proceed without a decision if the blocker is architectural. Do not invent scope to work around it.

## Done Standard

A task is done only when:

- Acceptance criteria in the brief (via `briefcase brief read`) are satisfied.
- Task backlog row status is `done` (via `briefcase backlog upsert`).
- Work functions end-to-end in the target environment.
- Relevant tests are added or updated per `_project/testing-strategy.md`.
- Non-trivial notes or blockers are recorded.

## Exit Criteria

Implementation is complete when:

- All Task backlog rows are `done`.
- All backlog items are marked correctly.
- The feature meets the brief's acceptance criteria.
- Release notes are created when the feature moves from `review-accepted` to `done`, and the ship note includes an explicit Pacific timestamp (`PST` or `PDT`).
