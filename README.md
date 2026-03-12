# The Briefcase v1

A lightweight, AI-agent-friendly workflow system for solo builders who use multiple agents to go from idea to shipped product.

Designed for two-agent setups — one agent for ideation, one for implementation — collaborating on the same project without stepping on each other.

---

## What's in the Briefcase

The Briefcase gives your agents a shared operating system: clear roles, clean handoffs, and a single source of truth at every phase of development.

- **Ideation agent** shapes raw ideas into scoped, implementation-ready briefs
- **Implementation agent** picks up those briefs and builds, tests, and ships
- **Review agent** validates that what got built matches what was planned

No duplicate information. No guessing about who owns what. No scope drift.

---

## Folder Structure

```
{project-root}/
│
├── AGENTS.md                        ← start here (Codex / all agents)
├── CLAUDE.md                        ← start here (Claude Code)
│
├── _agent_guideline/                ← how each agent behaves
│   ├── ideation-agent-guideline.md
│   ├── implementation-agent-guideline.md
│   └── review-agent-guideline.md
│
├── _doc_template/                   ← copy these when creating new artifacts
│   ├── brief.md
│   ├── tasks.md
│   ├── backlog.md
│   ├── release-notes.md
│   ├── tech-stack.md
│   ├── definition-of-done.md
│   └── _inbox.md
│
├── _project/                        ← project-level constants (set during setup)
│   ├── tech-stack.md
│   ├── definition-of-done.md
│   └── decisions.md
│
├── docs/plan/
│   ├── _inbox.md                    ← raw ideas; append-only
│   ├── _shared/
│   │   └── backlog.md
│   ├── _releases/
│   │   └── v{version}/
│   │       └── release-notes.md
│   └── {feature-name}/
│       ├── brief.md
│       └── tasks.md
│
├── src/                             ← all application code
│   ├── core/                        ← shared infrastructure
│   └── {feature-name}/
│
└── tests/                           ← mirrors src/
    ├── core/
    └── {feature-name}/
```

Feature names must be identical across `docs/plan/`, `src/`, and `tests/`.

---

## How It Works

### The 6-Phase Workflow

| Phase | Goal | Who |
|---|---|---|
| **0 — Capture** | Log ideas with zero friction | Ideation |
| **1 — Plan** | Turn an idea into an implementation-ready brief | Ideation |
| **2 — Break Down** | Convert the brief into atomic tasks | Implementation |
| **3 — Build** | Write code, write tests, ship incrementally | Implementation |
| **4 — Review** | Validate against the brief before closing | Review |
| **5 — Ship** | Deploy and document the release | Implementation |

### The Handoff

The critical moment is Phase 1 → 2. The ideation agent sets `Status: implementation-ready` in `brief.md` when the scope is locked. The implementation agent checks for this before starting. Nothing moves forward without it.

---

## Agent Setup

### If you're using Claude Code
Claude Code auto-reads `CLAUDE.md` at session start, which points to `AGENTS.md`.

Open with:
> *"You are the ideation agent. Read AGENTS.md."*

### If you're using Codex
Codex auto-reads `AGENTS.md` at session start.

Open with:
> *"You are the implementation agent. Read AGENTS.md."*

### If you're using both
- Claude → ideation agent
- Codex → implementation agent
- One role per session. State it explicitly at the start.

---

## File Ownership

| File | Owner | Others |
|---|---|---|
| `docs/plan/_inbox.md` | Any agent (append only) | Never overwrite |
| `docs/plan/{feature}/brief.md` | Ideation | Read-only for all others |
| `docs/plan/{feature}/tasks.md` | Implementation | Review may append findings |
| `docs/plan/_shared/backlog.md` | Implementation | Review may add notes |
| `src/` | Implementation | Read-only for all others |
| `tests/` | Implementation | Read-only for all others |
| `_project/` | Set during setup | Read-only during active work |

---

## Designed For

- Solo builders working with AI agents across multiple tools (Claude, Codex, VS Code)
- Projects that need a clear boundary between thinking and building
- Anyone tired of agents that drift out of scope or rewrite each other's work

---

## Version History

| Version | Date | Notes |
|---|---|---|
| v1 | 2026-03-12 | Initial release — two-agent workflow, 6-phase lifecycle, split guideline files |
