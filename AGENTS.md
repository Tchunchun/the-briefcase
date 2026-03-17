# AGENTS.md (v9)

This is the project-level entrypoint for all agents working on this repository.

**Read `.briefcase/skills/PLAYBOOK.md` before taking any action.** That file defines all workflow rules, agent routing, file ownership, and handoff sequences. This file adds project-specific scope and conventions.

Note: In this upstream repository, skills live at `skills/` (source). In consumer projects after install, they live at `.briefcase/skills/`. The PLAYBOOK uses `.skills/` paths — the canonical consumer path.

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
├── skills/                        ← distributable skills (source; consumers get .briefcase/skills/)
│   ├── PLAYBOOK.md                ← shared workflow rules; source of truth for all agents
│   ├── ideation/SKILL.md
│   ├── architect/SKILL.md
│   ├── implementation/SKILL.md
│   ├── review/SKILL.md
│   └── delivery-manager/SKILL.md
│
├── template/                      ← blank document templates (source; consumers get .briefcase/template/)
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
├── src/                           ← CLI + storage + sync code (source; consumers get .briefcase/src/)
│   ├── cli/                       ← CLI commands (inbox, brief, backlog, decision, setup, sync)
│   ├── core/                      ← storage protocol, config, factory, local backend
│   ├── integrations/              ← Notion API client, schemas, provisioner, backend
│   └── sync/                      ← sync logic, manifest, snapshots
│
├── _project/                      ← project-level constants (architect-owned)
│   ├── tech-stack.md
│   ├── definition-of-done.md
│   ├── testing-strategy.md
│   ├── decisions.md
│   └── storage.yaml               ← backend config (local or notion)
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

Consumer projects install skills, templates, and CLI tooling into a single `.briefcase/` folder. The install patches skill paths from `.skills/` to `.briefcase/skills/`.

```
consumer-project/
├── agent                          ← entry point script (executable, committed)
├── AGENTS.md                      ← points to .briefcase/skills/PLAYBOOK.md
├── CLAUDE.md                      ← points to AGENTS.md
├── .briefcase/                    ← THE FRAMEWORK (gitignored)
│   ├── skills/                    ← PLAYBOOK + 5 SKILL.md files
│   ├── template/                  ← document templates
│   └── src/                       ← CLI + storage + sync code
├── _project/                      ← project-level constants
│   ├── tech-stack.md              ← committed
│   ├── decisions.md               ← committed
│   └── storage.yaml               ← gitignored (contains Notion DB IDs)
└── src/                           ← consumer's own app code (untouched)
```

Install into a consumer project:

```bash
# 1. Copy framework into .briefcase/
mkdir -p /path/to/your-project/.briefcase
cp -r skills/   /path/to/your-project/.briefcase/skills/
cp -r template/  /path/to/your-project/.briefcase/template/
cp -r src/       /path/to/your-project/.briefcase/src/

# 2. Patch skill paths for consumer layout
find /path/to/your-project/.briefcase/skills/ -name '*.md' \
  -exec sed -i '' 's|\.skills/|.briefcase/skills/|g' {} +

# 3. Create entry point, add to .gitignore, set up AGENTS.md
# See README.md for full instructions.
```

The consumer's `AGENTS.md` points to `.briefcase/skills/PLAYBOOK.md` and adds project-specific scope.

---

## Changelog

| Version | Date | Summary |
|---|---|---|
| v9 | 2026-03-16 | Updated for `.briefcase/` consumer convention. Consumer project structure documented. Skill paths note clarified (upstream `skills/` → consumer `.briefcase/skills/`). Added delivery-manager to skill list. Added `storage.yaml` to `_project/`. Added `src/` module descriptions. |
| v8 | 2026-03-16 | Restructured: AGENTS.md is now project-scoped; `skills/PLAYBOOK.md` is the shared workflow source of truth. Fixed template path (`template/`), skill paths, inbox tags. Added domain/module-based code organization, consumer setup guidance, folder naming conventions, changelog. |
| v7 | — | Monolithic version containing all workflow rules inline. |
