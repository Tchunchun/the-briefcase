# Playbook: 0-to-1 Agent Workflow

This is the single source of truth for agent routing, file ownership, and handoff rules.
Read this file fully before taking any action.

---

## Folder Structure

{project-root}/
├── AGENTS.md                              ← project entrypoint; references this file
├── CLAUDE.md                              ← Claude Code entrypoint; points to AGENTS.md
├── _project/                              ← project-level constants; set during setup
│   ├── tech-stack.md                      ← architectural boundaries and technology choices
│   ├── definition-of-done.md             ← shared DoD reference
│   ├── testing-strategy.md               ← test types, coverage priorities, CI gate
│   └── decisions.md                      ← architectural decisions index
├── _doc_template/                         ← blank templates; copy when creating new artifacts
├── docs/
│   ├── plan/
│   │   ├── _inbox.md                      ← raw ideas; append-only
│   │   ├── _shared/
│   │   │   └── backlog.md
│   │   ├── _reference/
│   │   │   └── adr/
│   │   └── {feature-name}/
│   │       ├── brief.md
│   │       └── tasks.md
│   └── user/
├── src/
│   ├── core/
│   └── {feature-name}/
└── tests/
    ├── core/
    └── {feature-name}/

Feature folder names must be identical across docs/plan/, src/, tests/, and docs/user/.

---

## Agent Routing

### 1. Ideation Agent

Use when the request is exploratory, ambiguous, or still shaping scope.
Guideline: .skills/ideation/SKILL.md

Do not use for: coding, task breakdown, or setting Status: implementation-ready.

### 2. Architect Agent

Use when a brief has open technical questions, or a new project needs setup.
Guideline: .skills/architect/SKILL.md

Do not use for: writing acceptance criteria, coding, or task breakdown.

### 3. Implementation Agent

Use when a brief has Status: implementation-ready and work is ready to build.
Guideline: .skills/implementation/SKILL.md

Do not use for: exploration without scope, or final acceptance review of its own work.

### 4. Review Agent

Use when implementation is complete and needs validation against the brief.
Guideline: .skills/review/SKILL.md

Do not use for: writing the brief, doing implementation, or expanding scope.

---

## Handoff Sequence

1. Ideation → produces brief.md (Status: draft)
2. Architect → resolves open questions, sets Status: implementation-ready
3. Implementation → produces tasks.md, src/, tests/
4. Review → validates against brief.md
5. Implementation → ships accepted work, writes release notes

---

## Workflow Phases

| Phase | Trigger | Action |
|---|---|---|
| 0 Capture | New idea | Ideation appends to _inbox.md |
| 1 Plan | Idea promoted | Ideation creates {feature}/brief.md, marks inbox [-> architect review] |
| 1.5 Architect | Brief drafted | Architect resolves open questions, sets Status: implementation-ready |
| 2 Break Down | Brief ready | Implementation creates tasks.md, adds backlog rows |
| 3 Build | Tasks ready | Implementation builds src/, tests/, updates status |
| 4 Review | Work done | Review validates against brief.md |
| 5 Ship | Work accepted | Implementation writes release notes, closes backlog rows |

---

## Backlog Schema

docs/plan/_shared/backlog.md columns: ID · Type · Use Case · Feature · Title · Priority · Status · Notes

- Type: Feature / Tech Debt / Bug
- Priority: High / Medium / Low
- Status: To Do / In Progress / Done / Blocked
- Tech debt items must be logged in _inbox.md first (prefixed [tech-debt]) before backlog.

---

## Session Protocol

### On Session Start
1. Read this file fully.
2. Determine the correct agent role for the current request.
3. Read .skills/{role}/SKILL.md for that role.
4. Read _project/tech-stack.md before touching any code.
5. Read _project/testing-strategy.md before writing any test.
6. Read the relevant brief.md and tasks.md before making changes.
7. Do not start new work until you understand current state and artifact ownership.

### On Session End
1. Update all artifacts owned by your active agent role.
2. Keep tasks.md, backlog.md, and release notes aligned with actual progress.
3. If a new idea surfaced, append it to docs/plan/_inbox.md in one line.

---

## Collaboration Protocol

| File | Owner | Others |
|---|---|---|
| docs/plan/_inbox.md | Any agent may append | Never overwrite |
| docs/plan/{feature}/brief.md | Ideation (scope) + Architect (technical approach + status) | Implementation and review: read-only |
| docs/plan/{feature}/tasks.md | Implementation | Review may append findings only |
| docs/plan/_shared/backlog.md | Implementation owns status | Review may add notes |
| src/ | Implementation | Other agents: read-only |
| tests/ | Implementation | Other agents: read-only |
| _project/ | Architect | All other agents: read-only |
| docs/plan/_releases/ | Implementation | Other agents: read-only |
| docs/user/ | Implementation (after ship) | Other agents: read-only |

Rules:
- Before writing any file, read its current state first.
- brief.md is the source of truth for scope. Do not modify during implementation.
- _project/decisions.md is append-only. Log decisions, never delete them.

---

## Definition of Done

A task is Done only when ALL are true:
- Acceptance criteria in brief.md are met
- Task checkbox ticked in tasks.md
- Works end-to-end in target environment
- Relevant tests added or updated under tests/
- backlog.md status updated
- Reviewed and accepted
- Release notes created if the work ships

---

## Shared Rules

- One source of truth. Never duplicate information across files.
- Route before acting. Determine the correct agent role before doing anything.
- brief.md defines scope. Do not build anything not in the brief without asking first.
- Implementation starts from an implementation-ready brief. No coding while scope is ambiguous.
- Agent ownership matters. Ideation owns scope, architect owns technical foundation, implementation owns delivery, review owns acceptance.
- Small commits. Commit after each completed task with a meaningful message.
- Ask before creating files. Only create a file if the workflow explicitly calls for it.
- Capture, don't lose. Any new idea or out-of-scope request → _inbox.md immediately.
- Read _project/tech-stack.md before writing code. Never introduce unlisted technology without logging a decision.
