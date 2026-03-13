# 0-to-1 Agent Skills

Four Claude Code skills that guide an AI agent through the full lifecycle of building a feature from scratch — from raw idea to shipped code.

## Skills

| Skill | What it does | Triggers on |
|---|---|---|
| **ideation** | Turns rough ideas into scoped, reviewable briefs | "I want to build...", "what if we added...", "here's a rough idea..." |
| **architect** | Resolves technical questions and signs off on implementation-ready briefs | "how should we build this?", "what's the right architecture?", "should we use X or Y?" |
| **implementation** | Breaks down briefs into tasks, writes code and tests, ships with release notes | "build this", "implement this", "let's ship this", "continue building" |
| **review** | Validates implementation against the brief and acceptance criteria | "review this", "check the implementation", "QA this", "does this match requirements?" |

## Installation

### For your own projects

Copy the `.skills/` folder into your project root. Claude Code will auto-load skills from this location.

```bash
cp -r .skills/ /path/to/your-project/
```

### For your team (via plugin marketplace)

Add the team marketplace once per machine:

```bash
/plugin marketplace add your-org/agent-skills
```

Then install the plugin in any project:

```bash
/plugin install 0to1-agent-skills@your-org-marketplace
```

## Required setup in each consumer project

**The skills alone are not enough.** Each skill defers to a project-level `AGENTS.md` file for routing rules, file ownership, and the handoff sequence between agents. Without this file, the agent will not know when to hand off, what files it owns, or how to collaborate with other agents.

When setting up a new project, copy the `AGENTS.md` template below into your project root and save it as `AGENTS.md`. Fill in the `_project/` section with your project-specific details once the architect agent has run setup.

---

### AGENTS.md template

```markdown
# AGENTS.md

This is the single source of truth for all agents working on this project.
Read this file fully before taking any action.

---

## Folder Structure

{project-root}/
├── AGENTS.md                              ← this file; read first always
├── CLAUDE.md                              ← Claude Code entrypoint; points here
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
Guideline: .skills/skills/ideation/SKILL.md

Do not use for: coding, task breakdown, or setting Status: implementation-ready.

### 2. Architect Agent

Use when a brief has open technical questions, or a new project needs setup.
Guideline: .skills/skills/architect/SKILL.md

Do not use for: writing acceptance criteria, coding, or task breakdown.

### 3. Implementation Agent

Use when a brief has Status: implementation-ready and work is ready to build.
Guideline: .skills/skills/implementation/SKILL.md

Do not use for: exploration without scope, or final acceptance review of its own work.

### 4. Review Agent

Use when implementation is complete and needs validation against the brief.
Guideline: .skills/skills/review/SKILL.md

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
1. Read this file (AGENTS.md) fully.
2. Determine the correct agent role for the current request.
3. Read .skills/skills/{role}/SKILL.md for that role.
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
```

---

## How the skills and AGENTS.md work together

Each skill handles its own role — brainstorming, architecture, coding, or review. When a skill needs to know about file ownership or what to hand off next, it reads `AGENTS.md`. That means the skills are portable (they travel with the plugin), but the project's workflow conventions live in `AGENTS.md` (which you own and control).

This split is intentional:

- **Skills** = *how* each agent behaves, what it produces, and what it must not touch
- **AGENTS.md** = *who* owns what, *when* to hand off, and *where* files live in this specific project

## Document templates

Each skill references document templates under `_doc_template/`. Copy the `_doc_template/` folder from this repo into your project root when setting up a new project. The architect agent will fill in `_project/` files from these templates during project setup.

---

## Tool compatibility

| Tool | Skills auto-trigger | AGENTS.md routing | Notes |
|---|---|---|---|
| **Claude Code** | ✅ Yes — from `description` field in SKILL.md YAML frontmatter | ✅ Yes | Full support. Install via plugin or copy `.skills/` to project root. |
| **Codex** | ❌ No | ✅ Yes — reads `AGENTS.md` at project root | Skills work but must be referenced manually. At session start, tell Codex: "Read `.skills/skills/{role}/SKILL.md` for this task." |
| **Other tools** | ❌ No | Depends on tool | If the tool reads `AGENTS.md`, routing works. Skills must be pointed to explicitly. |

### Using with Codex

Codex reads `AGENTS.md` and will follow the routing rules, handoff sequence, and file ownership table. It does not auto-trigger skills from the `description` field. To activate a skill in Codex, start your session with an explicit instruction:

```
Read .skills/skills/ideation/SKILL.md and follow it for this task.
```

Or add a note to your project's `AGENTS.md` reminding Codex users to do this:

```markdown
## Note for Codex users
Skills do not auto-trigger in Codex. At the start of each session, read the
relevant skill file directly:
  - Ideation tasks → read `.skills/skills/ideation/SKILL.md`
  - Architecture tasks → read `.skills/skills/architect/SKILL.md`
  - Implementation tasks → read `.skills/skills/implementation/SKILL.md`
  - Review tasks → read `.skills/skills/review/SKILL.md`
```
