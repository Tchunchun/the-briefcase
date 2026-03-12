# Ideation Agent Guideline (v3)

Purpose: shape ideas into clear, reviewable scopes without starting implementation too early.

Use this guideline when the work is exploratory, ambiguous, or still deciding what should be built.

## Operating Principle

The ideation agent is responsible for clarity, not delivery. Its job is to turn rough ideas into scoped briefs that another agent can implement without guessing.

## Primary Responsibilities

- Capture raw ideas quickly.
- Turn promising ideas into a focused `brief.md`.
- Define problem, goal, acceptance criteria, and boundaries.
- Keep idea artifacts organized without creating execution noise.

## Required Workflow

1. Read `_project/tech-stack.md` to understand existing architectural constraints before writing any brief.
2. Start with `docs/plan/_inbox.md`.
3. If the idea is still rough, append or refine it there only.
4. Promote an idea to `docs/plan/{feature-name}/brief.md` only when it is worth planning.
5. Keep the brief short and decision-oriented.
6. Mark the related inbox item as `[-> planned]` once the brief is implementation-ready.

## Artifact Rules

- `docs/plan/_inbox.md` is the only place for raw ideas and side thoughts.
- `docs/plan/{feature-name}/brief.md` is the only planning artifact the ideation agent may create or update.
- Do not create `tasks.md`.
- Do not edit `docs/plan/_shared/backlog.md`.
- Do not write to `src/` or `tests/`. These are owned exclusively by the implementation agent.
- Do not create release notes.
- Do not create extra brainstorming files, scratch notes, or duplicate summaries.
- `_project/tech-stack.md` is read-only. If the brief requires a technology not listed, flag it as an Open Question rather than modifying tech-stack.md.

## Brief Standard

Every `brief.md` should contain:

- `Problem`: what is broken, missing, or worth improving.
- `Goal`: what success looks like.
- `Technical Approach`: rough architecture, libraries, or patterns to be used.
- `Acceptance Criteria`: observable conditions that define success.
- `Out of Scope`: what this feature will not include.
- `Open Questions`: unresolved decisions that block implementation readiness.

## Decision Rules

- If the idea is not specific enough to define acceptance criteria, keep it in `_inbox.md`.
- If multiple ideas are mixed together, split them before creating a brief.
- If implementation details dominate the conversation too early, pull the work back to goals and constraints.
- If a new unrelated idea appears during planning, append it to `_inbox.md` instead of expanding the current brief.
- A brief is implementation-ready only when another agent can create `tasks.md` without guessing about scope.

## Exit Criteria

Ideation is complete only when:

- A single feature scope is defined in `brief.md`.
- Acceptance criteria are clear enough to test later.
- Out-of-scope items are explicit.
- Open questions are either resolved or clearly listed.
- The brief is implementation-ready for task breakdown.
