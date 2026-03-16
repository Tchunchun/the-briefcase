# AGENTS.md (v8)

This is the project-level entrypoint for all agents working on this repository.

**Read `skills/PLAYBOOK.md` before taking any action.** That file defines all workflow rules, agent routing, file ownership, and handoff sequences. This file adds project-specific scope and conventions.

---

## Project Scope

This repository is the upstream source of the **0-to-1 Agent Skills** — a system of four agent roles (ideation, architect, implementation, review) that guide software projects from idea capture through implementation and shipping.

### What This Project Builds

1. **Agent Skills** — Role-specific `SKILL.md` files defining how each agent behaves.
2. **Workflow Playbook** — `skills/PLAYBOOK.md`, the shared workflow rules imported by consumer projects.
3. **Document Templates** — Reusable templates (`template/`) for briefs, tasks, backlogs, ADRs, and planning artifacts.
4. **CLI Tooling** — Commands for project setup, artifact sync, and status management *(planned)*.
5. **Notion Integration** — Automated Notion workspace provisioning and on-demand sync between Notion databases and local planning artifacts *(planned)*.

### End-to-End Workflow

The system enables a repeatable workflow across any consumer project:

```
Idea → Inbox → Brief → Architect Review → Tasks → Build → Review → Ship
```

Each phase is owned by a specific agent role with clear handoff points, artifact ownership, and escalation paths. See `skills/PLAYBOOK.md` for the full workflow definition.

---

## Repository Structure

```
{project-root}/
│
├── AGENTS.md                      ← this file; project-specific scope and conventions
├── CLAUDE.md                      ← Claude Code entrypoint; points here
├── README.md                      ← public-facing project overview
│
├── skills/                        ← distributable output (imported by consumer projects)
│   ├── PLAYBOOK.md                ← shared workflow rules; source of truth for all agents
│   ├── ideation/SKILL.md
│   ├── architect/SKILL.md
│   ├── implementation/SKILL.md
│   └── review/SKILL.md
│
├── template/                      ← blank document templates; copy when creating artifacts
│   ├── brief.md
│   ├── tasks.md
│   ├── backlog.md
│   ├── release-notes.md
│   ├── tech-stack.md
│   ├── testing-strategy.md
│   ├── definition-of-done.md
│   ├── adr.md
│   └── _inbox.md
│
├── _project/                      ← project-level constants (architect-owned)
│   ├── tech-stack.md
│   ├── definition-of-done.md
│   ├── testing-strategy.md
│   └── decisions.md
│
├── docs/
│   ├── plan/                      ← agent working space
│   │   ├── _inbox.md              ← raw ideas; append-only
│   │   ├── _shared/
│   │   │   └── backlog.md
│   │   ├── _releases/
│   │   │   └── v{version}/
│   │   │       └── release-notes.md
│   │   ├── _reference/
│   │   │   └── adr/
│   │   │       └── ADR-{NNN}.md
│   │   └── {brief-name}/          ← one folder per scoped brief (kebab-case)
│   │       ├── brief.md
│   │       └── tasks.md
│   │
│   └── user/                      ← human-readable documentation
│       ├── getting-started.md
│       ├── how-it-works.md
│       └── {topic}.md
│
├── src/                           ← application code (organized by module)
│   ├── core/                      ← shared infrastructure
│   ├── cli/                       ← CLI commands and entry points
│   ├── integrations/              ← external API clients (Notion, etc.)
│   └── sync/                      ← skill distribution and artifact sync
│
└── tests/                         ← automated tests; mirrors src/ modules
    ├── core/
    ├── cli/
    ├── integrations/
    └── sync/
```

### Folder Naming Conventions

- **All folders use `kebab-case`**: lowercase, hyphens, no spaces. Example: `notion-sync`, not `Notion Sync` or `notion_sync`.
- **Planning folders** (`docs/plan/{brief-name}/`): named after the scoped brief. A single brief may touch multiple code modules.
- **Source folders** (`src/`): organized by domain/module — what the code does, not which brief requested it. A module may serve multiple briefs.
- **Test folders** (`tests/`): mirror `src/` module structure.
- **User docs** (`docs/user/`): organized by topic for the reader.

### Skill Paths (This Repo vs. Consumer Projects)

In this upstream repository, skill files live at `skills/{role}/SKILL.md` (no dot prefix). The playbook references `.skills/{role}/SKILL.md`, which is the path after installation in consumer projects. When working in this repo, use `skills/` without the dot prefix.

---

## Consumer Project Setup

Consumer projects import the skills and playbook from this repository. Each consumer project creates its own `AGENTS.md` at the project root:

```markdown
# AGENTS.md

Read `.skills/PLAYBOOK.md` fully before taking any action.
Follow all routing, ownership, and handoff rules defined there.

## Project Scope

[Describe what this project builds — one paragraph.]
```

To install skills into a consumer project:

```bash
cp -r skills/ /path/to/your-project/.skills/
cp -r template/ /path/to/your-project/template/
```

The consumer's `AGENTS.md` is the place for project-specific overrides, scope, and conventions. The playbook handles everything else.

---

## Changelog

| Version | Date | Summary |
|---|---|---|
| v8 | 2026-03-16 | Restructured: AGENTS.md is now project-scoped; `skills/PLAYBOOK.md` is the shared workflow source of truth. Fixed template path (`template/`), skill paths, inbox tags. Added domain/module-based code organization, consumer setup guidance, folder naming conventions, changelog. |
| v7 | — | Monolithic version containing all workflow rules inline. |
