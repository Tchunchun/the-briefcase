# AGENTS.md (v4)

This is the single source of truth for all agents working on this project — regardless of which coding tool you are running (Claude Code, Codex, or other). Read this file fully before taking any action.

`CLAUDE.md` and any other tool-specific entrypoint files point here. Everything is defined in this file.

---

## Folder Structure

```
{project-root}/
│
├── AGENTS.md                              ← this file; read first always
├── CLAUDE.md                              ← Claude Code entrypoint; points here
│
├── _agent_guideline/                      ← how agents behave; never edit during a session
│   ├── ideation-agent-guideline.md
│   ├── architect-agent-guideline.md
│   ├── implementation-agent-guideline.md
│   └── review-agent-guideline.md
│
├── _project/                              ← project-level constants; set during setup
│   ├── tech-stack.md                      ← architectural boundaries and technology choices
│   ├── definition-of-done.md             ← shared DoD reference
│   └── decisions.md                      ← key architectural decisions log (what, why, alternatives rejected)
│
├── docs/plan/
│   ├── _inbox.md                          ← raw ideas; append-only
│   ├── _shared/
│   │   └── backlog.md                     ← cross-feature priority list (source of truth)
│   ├── _releases/
│   │   └── v{version}/
│   │       └── release-notes.md
│   └── {feature-name}/
│       ├── brief.md                       ← problem, goal, acceptance criteria, scope
│       └── tasks.md                       ← atomic task checklist for this feature
│
├── src/                                   ← all runnable application code
│   ├── core/                              ← shared infrastructure (base classes, memory, dispatcher)
│   └── {feature-name}/                    ← one folder per feature; mirrors docs/plan/{feature-name}
│
└── tests/                                 ← automated tests; mirrors src/ structure
    ├── core/
    └── {feature-name}/
```

Feature folder names must be identical across `docs/plan/`, `src/`, and `tests/`. This allows agents to navigate from brief → code → tests without ambiguity.

---

## Agent Routing

### 1. Ideation Agent

Use the ideation agent when:

- The request is still exploratory or ambiguous.
- The work starts as an idea, opportunity, bug report, or rough request.
- Scope, acceptance criteria, or boundaries are not yet clear.
- The main goal is to shape the work before implementation begins.

Primary outputs:

- `docs/plan/_inbox.md`
- `docs/plan/{feature-name}/brief.md` (problem, goal, acceptance criteria, open questions)

Guideline file: `_agent_guideline/ideation-agent-guideline.md`

Do not use this agent for: coding, task breakdown, backlog execution, release documentation, writing to `src/` or `tests/`, or setting `Status: implementation-ready` on a brief.

---

### 2. Architect Agent

Use the architect agent when:

- A new project is starting and `_project/` does not exist yet.
- The ideation agent has produced a `brief.md` with open technical questions.
- The `Technical Approach` section of a brief is missing or too vague.
- The implementation agent has hit an architectural blocker and escalated.
- A new technology or pattern is being considered that isn't in `_project/tech-stack.md`.

Primary outputs:

- `_project/tech-stack.md`
- `_project/definition-of-done.md`
- `_project/decisions.md`
- `Technical Approach` section of `docs/plan/{feature-name}/brief.md`
- `Status: implementation-ready` on `brief.md`

Guideline file: `_agent_guideline/architect-agent-guideline.md`

Do not use this agent for: writing problem statements or acceptance criteria, coding, task breakdown, or anything in `src/` or `tests/`.

---

### 3. Implementation Agent

Use the implementation agent when:

- A feature already has an implementation-ready `brief.md`.
- The work is ready to be broken into tasks or actively built.
- Backlog and task status need to be updated during delivery.
- Tests need to be written, updated, or run.
- The feature is being shipped and needs release notes.

Primary outputs:

- `docs/plan/{feature-name}/tasks.md`
- `docs/plan/_shared/backlog.md`
- code under `src/`
- tests under `tests/`
- `docs/plan/_releases/v{version}/release-notes.md`

Guideline file: `_agent_guideline/implementation-agent-guideline.md`

Do not use this agent for: early-stage exploration without scope, redefining requirements during coding, or final acceptance review of its own work.

---

### 4. Review Agent

Use the review agent when:

- Implementation is complete or ready for validation.
- You need to verify alignment between built work and the implementation-ready brief.
- You need a quality gate before marking a feature accepted.

Primary outputs:

- Review findings in `docs/plan/{feature-name}/tasks.md`
- Status corrections in planning artifacts when needed

Guideline file: `_agent_guideline/review-agent-guideline.md`

Do not use this agent for: writing the initial brief, doing the main implementation work, or expanding scope to match what was already coded.

---

## Handoff Sequence

1. **Ideation** captures or scopes the work → produces `brief.md` with problem, goal, and acceptance criteria. Flags open technical questions.
2. **Architect** resolves open technical questions, fills in `Technical Approach`, sets `Status: implementation-ready` on `brief.md`. Works with the user on all key decisions.
3. **Implementation** breaks down the brief, builds, and tests → produces `tasks.md`, code under `src/`, tests under `tests/`.
4. **Review** validates the result against `brief.md`.
5. **Implementation** ships accepted work and writes release notes.

The ideation and architect agents may loop — if the architect finds a brief needs rethinking, it flags specific issues back to ideation before signing off.

---

## Workflow Phases

| Phase | Trigger | Action |
|---|---|---|
| **0 Capture** | New idea | Ideation agent appends to `_inbox.md`. No folder, no planning yet. |
| **1 Plan** | Idea promoted | Ideation agent creates `{feature}/brief.md` with problem, goal, acceptance criteria, and open questions. Marks inbox item `[-> planned]`. |
| **1.5 Architect** | Brief drafted | Architect agent resolves open questions, fills in Technical Approach, sets `Status: implementation-ready`. |
| **2 Break Down** | Brief implementation-ready | Implementation agent creates `{feature}/tasks.md` and adds rows to `_shared/backlog.md`. |
| **3 Build** | Tasks ready | Implementation agent picks the highest-priority `To Do`, builds under `src/`, tests under `tests/`, updates status. |
| **4 Review** | Work implemented | Review agent validates against `brief.md`, `tasks.md`, and backlog state. |
| **5 Ship** | Work accepted | Implementation agent creates `_releases/v{version}/release-notes.md` and closes backlog rows. |

---

## Backlog Schema

`docs/plan/_shared/backlog.md` columns: `ID · Use Case · Feature · Title · Priority · Status · Notes`

- **Priority:** High / Medium / Low
- **Status:** To Do / In Progress / Done / Blocked
- Always pick the highest-priority `To Do` task unless blocked.
- Backlog state must match reality, not intent.

---

## Session Protocol

### On Session Start
1. Read this file (`AGENTS.md`) fully.
2. Determine the correct agent role for the current request.
3. Read the guideline file for that role under `_agent_guideline/`.
4. Read `_project/tech-stack.md` before touching any code.
5. Read the relevant `brief.md` and `tasks.md` before making changes.
6. Do not start new work until you understand current state and artifact ownership.

### On Session End
1. Update all artifacts owned by your active agent role.
2. Keep `tasks.md`, `_shared/backlog.md`, and release notes aligned with actual progress.
3. If a new idea surfaced, append it to `docs/plan/_inbox.md` in one line.

---

## Collaboration Protocol

Two agents may work on the same project. Follow these rules to prevent conflicts.

**File ownership:**

| File | Owner | Others |
|---|---|---|
| `docs/plan/_inbox.md` | Any agent may append | Never overwrite; append only |
| `docs/plan/{feature}/brief.md` | Ideation (problem/goal/criteria) + Architect (technical approach + status) | Implementation and review agents: read-only |
| `docs/plan/{feature}/tasks.md` | Implementation agent | Review agent may append findings only |
| `docs/plan/_shared/backlog.md` | Implementation agent owns status | Review agent may add notes |
| `src/` | Implementation agent | Other agents: read-only |
| `tests/` | Implementation agent | Other agents: read-only |
| `_project/` | Architect agent | All other agents: read-only |
| `docs/plan/_releases/` | Implementation agent | Other agents: read-only |

**Rules:**
- Before writing any file, read its current state first.
- Never overwrite a file another agent may have updated in the same session.
- `brief.md` is the source of truth for scope. Do not modify it during implementation.
- `_project/decisions.md` is append-only during active development. Log decisions, never delete them.

---

## Definition of Done

A task is **Done** only when ALL are true:
- Acceptance criteria in `brief.md` are met
- Task checkbox ticked in `tasks.md`
- Works end-to-end in target environment
- Relevant tests added or updated under `tests/`
- `backlog.md` status updated
- Reviewed and accepted
- Release notes created if the completed work ships

---

## Shared Rules

- **One source of truth.** Never duplicate information across files.
- **Route before acting.** Determine the correct agent role before doing anything.
- **brief.md defines scope.** Do not build anything not in the brief without asking first.
- **Implementation starts from an implementation-ready brief.** No task breakdown or coding while scope is ambiguous.
- **Agent ownership matters.** Ideation owns scope, architect owns technical foundation, implementation owns delivery, review owns acceptance.
- **Small commits.** Commit after each completed task with a meaningful message.
- **Ask before creating files.** Only create a file if the workflow explicitly calls for it.
- **Capture, don't lose.** Any new idea or out-of-scope request → `_inbox.md` immediately.
- **Read `_project/tech-stack.md` before writing code.** Never introduce a technology not listed there without logging a decision in `_project/decisions.md`.

---

## File Index

- `_agent_guideline/ideation-agent-guideline.md`
- `_agent_guideline/architect-agent-guideline.md`
- `_agent_guideline/implementation-agent-guideline.md`
- `_agent_guideline/review-agent-guideline.md`
