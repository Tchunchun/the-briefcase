# Playbook: 0-to-1 Agent Workflow

This is the single source of truth for agent routing, file ownership, and handoff rules.
Read this file fully before taking any action.

---

## Folder Structure

```
{project-root}/
├── AGENTS.md                          ← project entrypoint; references this file
├── CLAUDE.md                          ← Claude Code entrypoint; points to AGENTS.md
├── _project/                          ← project-level constants; set during setup
│   ├── tech-stack.md                  ← architectural boundaries and technology choices
│   ├── definition-of-done.md         ← shared DoD reference
│   ├── testing-strategy.md           ← test types, coverage priorities, CI gate
│   └── decisions.md                  ← architectural decisions index
├── template/                          ← blank templates; copy when creating new artifacts
├── docs/
│   ├── plan/
│   │   ├── _inbox.md                  ← raw ideas (local backend); managed via `briefcase inbox` CLI
│   │   ├── _shared/
│   │   │   └── backlog.md             ← local backend only; managed via `briefcase backlog` CLI
│   │   ├── _reference/
│   │   │   └── adr/
│   │   └── {feature-name}/
│   │       └── brief.md              ← local backend only; managed via `briefcase brief` CLI
│   └── user/
├── src/
│   ├── core/
│   └── {feature-name}/
└── tests/
    ├── core/
    └── {feature-name}/
```

Feature folder names must be identical across docs/plan/, src/, tests/, and docs/user/.

> **Path convention:** In this repo, skill paths are relative to the project root (e.g. `skills/ideation/SKILL.md`). When installed into a consumer project, `install.sh` rewrites all skill paths to use the `.briefcase/` prefix automatically.

---

## Agent Routing

### 1. Ideation Agent

Use when the request is exploratory, ambiguous, or still shaping scope.
Guideline: skills/ideation/SKILL.md

Do not use for: coding, task breakdown, or setting Status: implementation-ready.

### 2. Architect Agent

Use when a brief has open technical questions, or a new project needs setup.
Guideline: skills/architect/SKILL.md

Do not use for: writing acceptance criteria, coding, or task breakdown.

### 3. Implementation Agent

Use when a brief has Status: implementation-ready and work is ready to build.
Guideline: skills/implementation/SKILL.md

Do not use for: exploration without scope, or final acceptance review of its own work.

### 4. Review Agent

Use when implementation is complete and needs validation against the brief.
Guideline: skills/review/SKILL.md

Do not use for: writing the brief, doing implementation, or expanding scope.

### 5. Delivery Manager Agent

Use when work must transition between role owners and needs readiness checks, packeted context, or escalation.
Guideline: skills/delivery-manager/SKILL.md

Do not use for: writing scope, architecture decisions, coding, or acceptance decisions.

---

## Handoff Sequence

1. Ideation → produces brief (Status: draft)
2. Delivery Manager → validates ideation handoff packet, sets Route State: routed, routes to architect
3. Architect → resolves open questions, sets Feature Status: implementation-ready
4. Delivery Manager → validates architect handoff packet, sets Route State: routed, routes to implementation
5. Implementation → produces Task backlog rows, src/, tests/, sets Feature Status: in-progress
6. Delivery Manager → validates implementation handoff packet, sets Route State: routed, routes to review
7. Review → validates against brief, sets Review Verdict, and moves accepted Features to review-accepted
8. Delivery Manager → reads Review Verdict, routes to implementation (fix cycle) or ship path
9. Implementation → ships accepted work, writes release notes, sets Feature Status: done

---

## Reverse-Flow Escalation Protocol

Normal fix cycles (`changes-requested` → implementation) stay inside the forward model.
**Escalation** is reserved for cases where an upstream owner must revise scope, acceptance criteria, or architecture before forward progress is valid.

### Escalation vs. Fix Cycle

| Situation | Mechanism |
|---|---|
| Review finding that implementation can fix inside the accepted brief | Normal `changes-requested` loop — no escalation |
| Missing scope, contradictory acceptance criteria, or ambiguous requirements | Escalation: Implementation → Ideation (via delivery-manager) |
| Architectural blocker discovered during implementation or review | Escalation: Implementation/Review → Architect (via delivery-manager) |
| Review reveals the brief itself needs revision | Escalation: Review → Ideation (via delivery-manager) |

### Escalation Packet

Record escalation in the Feature's `--notes` field so it is visible in both local and Notion backends:

```
[escalation] <DATE>
Source Role: <role that detected the blocker>
Target Role: <upstream owner who must act>
Trigger: <one sentence — why forward progress is invalid>
Affected Artifact: <brief / tech-stack / acceptance criteria>
Blocking Question: <what the upstream owner must answer or revise>
Required Action: <specific update the upstream owner must make>
Reroute Condition: <what must be true before the feature moves forward again>
```

### Escalation Rules

1. **Any role may detect** an escalation condition. The active role appends the packet to the Feature notes.
2. **Delivery-manager owns routing.** Only delivery-manager sets `Route State: blocked` or `returned` and records the routing note.
3. **No reroute until resolved.** Delivery-manager must not reroute the feature back to the downstream role until the named upstream owner has updated the artifact they own and the escalation note records that resolution.
4. **No infinite loops.** A feature may not be escalated back to the same upstream role for the same question twice. If the upstream owner's update does not resolve the blocker, delivery-manager escalates to the user.
5. **Escalation is append-only.** Escalation notes are never deleted or overwritten — only appended with resolution details.

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
   - Implementation work -> `skills/implementation/SKILL.md`
   - Review validation -> `skills/review/SKILL.md`
4. Record return state (`returned`, `blocked`) and next route.

Delivery-manager must not replace, duplicate, or reinterpret implementation/review responsibilities.

---

## Workflow Phases

| Phase | Trigger | Action |
|---|---|---|
| 0 Capture | New idea | Ideation captures via `briefcase inbox add` |
| 1 Plan | Idea promoted | Ideation creates brief via `briefcase brief write` (`Status: draft`), sets Feature to architect-review |
| 1.25 Orchestrate | Brief drafted | Delivery manager validates packet + routes to architect |
| 1.5 Architect | Brief drafted | Architect resolves open questions, sets Status: implementation-ready |
| 1.75 Orchestrate | Brief implementation-ready | Delivery manager validates packet + routes to implementation |
| 2 Break Down | Brief ready | Implementation creates Task backlog rows via `briefcase backlog upsert` |
| 3 Build | Tasks ready | Implementation builds src/, tests/, updates status |
| 3.5 Orchestrate | Build complete | Delivery manager validates packet + routes to review |
| 4 Review | Work done | Review validates against brief.md, records verdict, and moves accepted Features to `review-accepted` |
| 4.5 Orchestrate | Review verdict recorded | Delivery manager routes fix cycle or ship path |
| 5 Ship | Work accepted | Implementation writes release notes, closes backlog rows, and moves Feature to `done` |

---

## Backlog Schema

Backlog database fields: Title · Type · Status (per-type) · Priority · Review Verdict · Route State · Brief Link · Release Note Link · Notes · Parent

- Type: Idea / Feature / Task
- Priority: High / Medium / Low
- Idea Status: new / exploring / promoted / rejected / shipped
- Feature Status: draft / architect-review / implementation-ready / in-progress / review-ready / review-accepted / done
- Task Status: to-do / in-progress / blocked / done
- Review Verdict (Features only): pending / accepted / changes-requested
- Route State (delivery-manager only): routed / returned / blocked
- Brief Link: URL to the brief page (set on Feature rows)
- Release Note Link: URL to the release note page (set when Feature ships)
- Parent: self-relation for Idea→Feature and Feature→Task hierarchy
- Tech debt items must be logged via `briefcase inbox add --type idea --text "[tech-debt] ..."` before backlog.
- Ship notes on Feature `done` rows and Idea `shipped` rows must include an explicit Pacific timestamp in the form `YYYY-MM-DD HH:MM PST/PDT`.

### Lifecycle Axes

Feature lifecycle is tracked on separate axes — do not collapse into one field:

| Axis | Field | Purpose |
|---|---|---|
| Execution | Feature Status | Tracks work progression from draft to done |
| Acceptance | Review Verdict | Tracks review outcome (pending/accepted/changes-requested) |
| Routing | Route State | Tracks delivery-manager handoff outcome (routed/returned/blocked) |
| Shipment | Release Note Link + Feature Status: done | Marks shipped feature work in the current workflow |

### Artifact Ownership Boundary

- **Notion** owns: briefs, backlog tracking, review/routing state, release notes, and operational docs.
- **Local Git** owns: source code, tests, `_project/` engineering-governance docs (tech-stack, testing-strategy, definition-of-done), and code-adjacent ADRs.

---

## Feedback Forwarding

When `--type feedback` is used with `briefcase inbox add`, entries are:
1. Stored in the local project inbox (same as any other entry type).
2. Forwarded to the upstream framework repo as a GitHub issue, if `upstream.feedback_repo` is configured in `storage.yaml`.

The `install.sh` script auto-detects the framework's GitHub origin and seeds `upstream.feedback_repo` in `.briefcase/storage.yaml`. Forwarding requires the `gh` CLI to be installed and authenticated (`gh auth status`).

If upstream forwarding is not configured or fails, the CLI output includes an `upstream_warning` field explaining the situation.

---

## Backend Protocol

> **Read `_project/storage.yaml` before touching any artifact.**
> When the backend is `notion`, ALL planning artifacts (briefs, backlog, inbox, decisions) exist only in Notion — use `briefcase` CLI commands exclusively.
> Do NOT read from or write to `docs/plan/` files directly when backend is `notion` — they may be stale or absent.
> When the backend is `local`, `docs/plan/` files are the source of truth and direct file access is safe.

## Artifact Access Rules

All planning artifacts are accessed through CLI commands. The CLI routes to the correct backend (local files or Notion) based on `_project/storage.yaml`.

| Action | Command |
|---|---|
| List inbox | `briefcase inbox list` |
| Add idea | `briefcase inbox add --type idea --text "Short title" --notes "Description"` |
| Submit feedback | `briefcase inbox add --type feedback --text "Short title" --notes "Description"` |
| Read brief | `briefcase brief read {feature-name}` |
| Write brief head | `briefcase brief write {feature-name} --status draft --problem "..." --goal "..." --change-summary "..."` |
| List brief revisions | `briefcase brief history {feature-name}` |
| Read one revision | `briefcase brief revision {feature-name} <revision-id>` |
| Restore a revision | `briefcase brief restore {feature-name} <revision-id> --change-summary "..."` |
| List briefs | `briefcase brief list` |
| List backlog | `briefcase backlog list` |
| Upsert backlog item | `briefcase backlog upsert --title "..." --type Task --status to-do --priority High` |
| List decisions | `briefcase decision list` |
| Add decision | `briefcase decision add --id D-NNN --title "..." --date YYYY-MM-DD --why "..."` |
| Write release note | `briefcase release write --version v0.x.0 --notes "..."` |
| Read release note | `briefcase release read --version v0.x.0` |
| List release notes | `briefcase release list` |

**Direct file access** is allowed only for project constants (`_project/tech-stack.md`, `_project/testing-strategy.md`, `_project/definition-of-done.md`), source code (`src/`, `tests/`), and ADR templates.

---

## Session Protocol

### On Session Start
1. Read this file fully.
2. **Resolve the project root.** If `./briefcase` or `_project/storage.yaml` is not in the current directory, you may be in a git worktree or subdirectory. Run `git rev-parse --show-toplevel` and `cd` to the result before proceeding. A missing `./briefcase` script means you need to resolve the root — it does **not** mean the CLI is unavailable.
3. Determine the correct agent role for the current request.
4. Read skills/{role}/SKILL.md for that role.
5. If `_project/` does not exist, route to the architect agent for project setup before any implementation work.
6. **Read `_project/storage.yaml` and identify the active backend (`local` or `notion`).** This determines where ALL planning artifacts live — do not read or write `docs/plan/` files directly if the backend is `notion`. When backend is `notion`, every artifact read and write MUST go through `briefcase` CLI commands.
7. Read _project/tech-stack.md before touching any code.
8. Read _project/testing-strategy.md before writing any test.
9. Run `briefcase brief read {feature-name}` and `briefcase backlog list --type Task` before making changes.
10. Do not start new work until you understand current state and artifact ownership.

### On Session End
1. Update all artifacts owned by your active agent role via CLI commands.
2. Keep backlog rows aligned with actual progress via `briefcase backlog upsert`.
3. If a new idea surfaced, capture it via `briefcase inbox add`.

---

## Collaboration Protocol

| Artifact | Owner | Others |
|---|---|---|
| Inbox (via `briefcase inbox`) | Any agent may add | Never overwrite |
| Brief (via `briefcase brief`) | Ideation (scope) + Architect (technical approach + status) | Implementation and review: read-only |
| Backlog - Tasks (via `briefcase backlog`) | Implementation | Review may add findings to `--notes` only; delivery-manager may add coordination notes only |
| Backlog - Features (via `briefcase backlog`) | Implementation owns status | Review and delivery-manager may add notes only |
| Decisions (via `briefcase decision`) | Architect | All other agents: read-only |
| src/ | Implementation | Other agents: read-only |
| tests/ | Implementation | Other agents: read-only |
| _project/ | Architect | All other agents: read-only |
| _releases/ | Implementation | Other agents: read-only |
| docs/user/ | Implementation (after ship) | Other agents: read-only |

Rules:
- Before writing any artifact, read its current state first (via CLI or direct file read for project constants).
- The brief is the source of truth for scope. Do not modify during implementation.
- Brief status and Feature backlog status are related but not interchangeable. During ideation, the valid handoff pair is: brief `draft` + Feature `architect-review`.
- Agents must not force brief status and Feature status to match unless the workflow explicitly defines that mapping for the active phase.
- Decisions are append-only. Log via `briefcase decision add`, never delete.
- Delivery manager may only append coordination notes and route decisions; it must not edit scope, code, tests, or review findings.

### Delivery Manager Optionality

To preserve backward compatibility, projects may run:
- **Five-role orchestrated mode (recommended for single-entrypoint UX):** Ideation -> Delivery Manager -> Architect -> Delivery Manager -> Implementation -> Delivery Manager -> Review -> Delivery Manager -> Implementation (ship)
- **Legacy four-role/manual mode:** Ideation -> Architect -> Implementation -> Review -> Implementation (ship)

In manual mode, the same handoff checks still apply, but the active role owner performs them directly.

---

## Definition of Done

A task is Done only when ALL are true:
- Acceptance criteria in the brief are met (verify via `briefcase brief read`)
- Task backlog row status is `done` (via `briefcase backlog upsert`)
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
- Capture, don't lose. Any new idea or out-of-scope request → `briefcase inbox add` immediately.
- Read _project/tech-stack.md before writing code. Never introduce unlisted technology without logging a decision.
