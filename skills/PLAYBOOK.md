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
├── template/                              ← blank templates; copy when creating new artifacts
├── docs/
│   ├── plan/
│   │   ├── _inbox.md                      ← raw ideas (local backend); managed via `agent inbox` CLI
│   │   ├── _shared/
│   │   │   └── backlog.md                 ← local backend only; managed via `agent backlog` CLI
│   │   ├── _reference/
│   │   │   └── adr/
│   │   └── {feature-name}/
│   │       └── brief.md                   ← local backend only; managed via `agent brief` CLI
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

### 5. Delivery Manager Agent

Use when work must transition between role owners and needs readiness checks, packeted context, or escalation.
Guideline: .skills/delivery-manager/SKILL.md

Do not use for: writing scope, architecture decisions, coding, or acceptance decisions.

---

## Handoff Sequence

1. Ideation → produces brief.md (Status: draft)
2. Delivery Manager → validates ideation handoff packet and routes to architect
3. Architect → resolves open questions, sets Status: implementation-ready
4. Delivery Manager → validates architect handoff packet and routes to implementation
5. Implementation → produces Task backlog rows, src/, tests/
6. Delivery Manager → validates implementation handoff packet and routes to review
7. Review → validates against brief.md and returns verdict (`accepted` or `changes-requested`)
8. Delivery Manager → routes to implementation (fix cycle) or ship path based on review verdict
9. Implementation → ships accepted work, writes release notes

---

## Execution Modes

Projects may run one of two supported modes:

- **Orchestrated mode (`orchestrated-mode: true`)**: user interacts only with delivery-manager for implementation, review, and ship flow. Delivery-manager delegates to existing role skills.
- **Manual mode (`orchestrated-mode: false`)**: user may directly invoke implementation/review roles while following the same handoff checks.

Default: `orchestrated-mode: false` for backward compatibility.

### Orchestrated Delegation Contract

When `orchestrated-mode: true`, delivery-manager must:
1. Run readiness checklist for current transition.
2. Append handoff packet and route decision.
3. Dispatch to existing role skills only:
   - Implementation work -> `.skills/implementation/SKILL.md`
   - Review validation -> `.skills/review/SKILL.md`
4. Record return state (`returned`, `blocked`) and next route.

Delivery-manager must not replace, duplicate, or reinterpret implementation/review responsibilities.

---

## Workflow Phases

| Phase | Trigger | Action |
|---|---|---|
| 0 Capture | New idea | Ideation captures via `agent inbox add` |
| 1 Plan | Idea promoted | Ideation creates brief via `agent brief write`, sets Feature to architect-review |
| 1.25 Orchestrate | Brief drafted | Delivery manager validates packet + routes to architect |
| 1.5 Architect | Brief drafted | Architect resolves open questions, sets Status: implementation-ready |
| 1.75 Orchestrate | Brief implementation-ready | Delivery manager validates packet + routes to implementation |
| 2 Break Down | Brief ready | Implementation creates Task backlog rows via `agent backlog upsert` |
| 3 Build | Tasks ready | Implementation builds src/, tests/, updates status |
| 3.5 Orchestrate | Build complete | Delivery manager validates packet + routes to review |
| 4 Review | Work done | Review validates against brief.md, records verdict |
| 4.5 Orchestrate | Review verdict recorded | Delivery manager routes fix cycle or ship path |
| 5 Ship | Work accepted | Implementation writes release notes, closes backlog rows |

---

## Backlog Schema

Backlog database fields: ID · Type · Use Case · Feature · Title · Priority · Status · Notes

- Type: Feature / Tech Debt / Bug / Idea / Task
- Priority: High / Medium / Low
- Status: per-type (Idea Status, Feature Status, Task Status)
- Tech debt items must be logged via `agent inbox add --type idea --text "[tech-debt] ..."` before backlog.

---

## Session Protocol

### On Session Start
1. Read this file fully.
2. Determine the correct agent role for the current request.
3. Read .skills/{role}/SKILL.md for that role.
4. If `_project/` does not exist, route to the architect agent for project setup before any implementation work.
5. Read _project/tech-stack.md before touching any code.
6. Read _project/testing-strategy.md before writing any test.
7. Run `agent brief read {feature-name}` and `agent backlog list --type Task` before making changes.
8. Do not start new work until you understand current state and artifact ownership.

### On Session End
1. Update all artifacts owned by your active agent role via CLI commands.
2. Keep backlog rows aligned with actual progress via `agent backlog upsert`.
3. If a new idea surfaced, capture it via `agent inbox add`.

---

## Collaboration Protocol

| Artifact | Owner | Others |
|---|---|---|
| Inbox (via `agent inbox`) | Any agent may add | Never overwrite |
| Brief (via `agent brief`) | Ideation (scope) + Architect (technical approach + status) | Implementation and review: read-only |
| Backlog - Tasks (via `agent backlog`) | Implementation | Review may add findings to `--notes` only; delivery-manager may add coordination notes only |
| Backlog - Features (via `agent backlog`) | Implementation owns status | Review and delivery-manager may add notes only |
| Decisions (via `agent decision`) | Architect | All other agents: read-only |
| src/ | Implementation | Other agents: read-only |
| tests/ | Implementation | Other agents: read-only |
| _project/ | Architect | All other agents: read-only |
| _releases/ | Implementation | Other agents: read-only |
| docs/user/ | Implementation (after ship) | Other agents: read-only |

Rules:
- Before writing any artifact, read its current state first (via CLI or direct file read for project constants).
- The brief is the source of truth for scope. Do not modify during implementation.
- Decisions are append-only. Log via `agent decision add`, never delete.
- Delivery manager may only append coordination notes and route decisions; it must not edit scope, code, tests, or review findings.

### Delivery Manager Optionality

To preserve backward compatibility, projects may run:
- **Five-role orchestrated mode (recommended for single-entrypoint UX):** Ideation -> Delivery Manager -> Architect -> Delivery Manager -> Implementation -> Delivery Manager -> Review -> Delivery Manager -> Implementation (ship)
- **Legacy four-role/manual mode:** Ideation -> Architect -> Implementation -> Review -> Implementation (ship)

In manual mode, the same handoff checks still apply, but the active role owner performs them directly.

---

## Definition of Done

A task is Done only when ALL are true:
- Acceptance criteria in the brief are met (verify via `agent brief read`)
- Task backlog row status is `done` (via `agent backlog upsert`)
- Works end-to-end in target environment
- Relevant tests added or updated under tests/
- Backlog rows updated via CLI
- Reviewed and accepted (see review requirements below)
- Release notes created if the work ships

### Review Requirements by Type

- **Feature:** Full review by the review agent required before acceptance.
- **Tech Debt / Bug:** Self-review by the implementation agent is sufficient. Note the self-review in backlog `--notes`.

Delivery manager orchestration never replaces review acceptance requirements.

---

## Shared Rules

- One source of truth. Never duplicate information across files.
- Route before acting. Determine the correct agent role before doing anything.
- brief.md defines scope. Do not build anything not in the brief without asking first.
- Implementation starts from an implementation-ready brief. No coding while scope is ambiguous.
- Agent ownership matters. Ideation owns scope, architect owns technical foundation, implementation owns delivery, review owns acceptance.
- Delivery manager owns handoff orchestration only. It cannot redefine scope, architecture, or acceptance outcomes.
- Small commits. Commit after each completed task with a meaningful message.
- Ask before creating files. Only create a file if the workflow explicitly calls for it.
- Capture, don't lose. Any new idea or out-of-scope request → `agent inbox add` immediately.
- Read _project/tech-stack.md before writing code. Never introduce unlisted technology without logging a decision.
