# 0-to-1 Agent Guidelines — Project Overview

> **One-line pitch:** A multi-agent workflow framework that takes a software idea from raw thought to shipped feature — with structured documentation, automated handoffs, and traceable dispatch — backed by Notion (with a pluggable backend layer for future storage targets).

---

## What This Project Is

The **0-to-1 Agent Guidelines** framework is an opinionated, role-based workflow system that automates the journey from idea capture to feature shipment. It defines five specialized AI agent roles, a strict handoff protocol between them, and a CLI toolchain (`agent`) that keeps every planning artifact in sync with the active storage backend.

The framework is designed to be installed into any software project via a `.briefcase/` directory. Once installed, it gives teams (and AI agents working on their behalf) a structured, auditable path from "we should build X" all the way to "X is shipped."

---

## The Five Agent Roles

| Role | Responsibility | Primary Artifact |
|---|---|---|
| **Ideation** | Turns raw ideas into scoped, reviewable feature briefs | `brief.md` (status: `draft`) |
| **Architect** | Resolves open technical questions and signs off on the technical approach | `brief.md` (status: `implementation-ready`) + `_project/` constants |
| **Implementation** | Breaks briefs into tasks, writes code and tests, and ships | `src/`, `tests/`, task backlog rows |
| **Review** | Validates implementation against the brief's acceptance criteria | Review verdict on feature backlog row |
| **Delivery Manager** | Orchestrates handoffs, checks readiness, and escalates blockers | Handoff packets, route state on backlog rows |

Each role has a clearly bounded scope it owns and artifacts it is forbidden from touching. This prevents scope drift, duplicate work, and silent failures.

---

## The Workflow (Ideation to Ship)

```
Idea captured
    ↓
Ideation Agent        → brief.md (draft) + Feature row (architect-review)
    ↓
Delivery Manager      → validates packet, routes to Architect
    ↓
Architect Agent       → technical approach + brief (implementation-ready)
    ↓
Delivery Manager      → validates packet, routes to Implementation
    ↓
Implementation Agent  → Task rows created, src/ + tests/ written
    ↓
Delivery Manager      → validates packet, routes to Review
    ↓
Review Agent          → validates vs brief, sets verdict (accepted / changes-requested)
    ↓
Delivery Manager      → routes: fix cycle or ship path
    ↓
Implementation Agent  → release notes written, Feature marked done
    ↓
Delivery Manager      → Idea marked shipped (with Pacific timestamp)
```

Two execution modes are supported:
- **Orchestrated mode** — user interacts only with the Delivery Manager; all delegation happens automatically.
- **Manual mode** — user can invoke any role agent directly, following the same handoff checks.

---

## Storage Architecture

### Current: Notion Backend

The framework connects to **Notion as its primary planning database**. All planning artifacts — briefs, backlog rows (Ideas, Features, Tasks), inbox entries, decisions, and release notes — live in Notion and are managed exclusively through the `agent` CLI.

The CLI abstracts Notion's API behind simple, role-safe commands:

```bash
agent brief write {feature-name} --status draft --problem "..." --goal "..."
agent backlog upsert --title "Feature title" --type Feature --status in-progress
agent inbox add --type idea --text "Short title" --notes "Context"
agent decision add --id D-001 --title "Use Notion backend" --date 2026-03-19 --why "..."
agent release write --version v0.1.0 --notes "..."
```

**Why Notion:** It provides a visual project management surface for non-technical stakeholders alongside the CLI-driven agent workflow, and supports the relational data model (Idea → Feature → Task hierarchy, multi-axis lifecycle tracking) that the framework requires.

### Future: Pluggable Backend Layer

The storage layer is designed to be swapped without changing agent behavior. The `_project/storage.yaml` file declares the active backend:

```yaml
backend: notion   # or: local
```

- **Local filesystem** (default, no dependencies) — markdown files in `docs/plan/`; suitable for offline or private use.
- **Notion** — cloud backend, currently fully implemented.
- **Future targets** — any backend (Linear, GitHub Projects, Jira, etc.) that can implement the same CLI contract is a valid target. The agent skills read from `storage.yaml` and call the CLI — they have zero direct knowledge of the underlying storage provider.

---

## Key Design Principles

**1. One source of truth per artifact.**
Briefs, backlog, inbox, and decisions live in exactly one place (the active backend). No duplication across files.

**2. Role ownership is enforced, not suggested.**
Every artifact has a named owner. Other roles are read-only. The Delivery Manager cannot edit scope; the Architect cannot write code; the Review agent cannot expand scope to match what was built.

**3. Brief-first, code-second.**
Implementation cannot start until a brief reaches `Status: implementation-ready`. This gate prevents building the wrong thing.

**4. Handoffs are explicit and auditable.**
Every transition produces a structured handoff packet. Route decisions are recorded on backlog rows. Nothing is routed silently.

**5. Lifecycle is tracked on separate axes.**
A Feature's progress is tracked across three independent fields — Execution Status, Review Verdict, and Route State — so no single status field loses information.

**6. Pluggable storage, stable agent behavior.**
Agents interact only through the `agent` CLI. Changing the backend requires updating `storage.yaml`, not rewriting skills.

---

## Technical Foundation

- **Language:** Python 3.11+
- **CLI framework:** Click
- **Storage backends:** Local filesystem (default), Notion API (`notion-client` SDK)
- **Testing:** pytest, pytest-mock, HTTP mocking (responses / respx) for Notion API tests
- **CI/CD:** GitHub Actions (planned)
- **Code style:** PEP 8 via `ruff`; all config in YAML; secrets in `.env`

---

## Artifact Ownership Map

| Artifact | Owner | Others |
|---|---|---|
| Inbox | Any agent may add | Never overwrite |
| Brief scope sections | Ideation | All others: read-only |
| Brief technical approach + status | Architect | All others: read-only |
| Backlog — Tasks | Implementation | Review may add finding notes only |
| Backlog — Features | Implementation (status) | Review/Delivery Manager: notes only |
| Decisions | Architect | All others: read-only |
| `src/` + `tests/` | Implementation | All others: read-only |
| `_project/` constants | Architect | All others: read-only |
| Release notes | Implementation | All others: read-only |

---

## Value Propositions

### 1. Zero context loss between agents
Every handoff carries a structured packet: artifact links, readiness checklist result, blockers, and explicit next-owner actions. No agent ever starts work without knowing exactly where things stand.

### 2. No premature implementation
The `implementation-ready` gate on briefs means code is written only when scope, acceptance criteria, technical approach, and non-functional requirements are all settled. This eliminates the most common source of rework.

### 3. Traceable, auditable lifecycle
Three independent tracking axes (Execution, Acceptance, Routing) give an accurate picture of feature state at any time. Release notes with Pacific timestamps create a permanent ship record.

### 4. Backend-agnostic planning
Agent behavior is decoupled from storage. Teams on Notion today can migrate to another backend without touching a single skill file. The local filesystem backend means the framework works out of the box, with no external dependencies.

### 5. Scope protection by design
The brief is frozen at `implementation-ready`. Review cannot quietly expand scope to match what was built. Out-of-scope work triggers a finding, not a silent acceptance.

### 6. Single entrypoint in orchestrated mode
When `orchestrated-mode: true`, users interact only with the Delivery Manager. All role delegation, dispatch, and return-state tracking happen automatically — the user never has to manually route work.

---

## Fact-Check: Does This Match the Stated Aim?

> **Stated aim:** *"Automated workflow from ideation to ship, with proper documentation; handoff, and dispatch"*

| Claim | Evidence in the project | Verdict |
|---|---|---|
| **Automated workflow from ideation to ship** | Full 9-step handoff sequence (Ideation → Architect → Implementation → Review → Ship) is defined and enforced in PLAYBOOK.md | ✅ Fully realized |
| **Automated handoff** | Delivery Manager role owns all phase transitions with structured readiness checklists and handoff packets; `agent automate` CLI commands trigger dispatch | ✅ Fully realized |
| **Automated dispatch** | `agent automate architect-review --notes-only` and `agent automate review-ready --notes-only` produce dispatch payloads that trigger the next role automatically (in orchestrated mode, without user intervention) | ✅ Fully realized |
| **Proper documentation** | Each feature produces: brief.md (problem, goal, AC, NFRs, technical approach), task backlog rows, decisions log, and a release note. All are versioned/append-only | ✅ Fully realized |
| **Notion as backend DB** | Notion is the active backend; all artifacts are managed through the `agent` CLI backed by the `notion-client` SDK | ✅ Fully realized |
| **Future support for other backends** | `_project/storage.yaml` + CLI abstraction layer means any storage target that implements the CLI contract is a drop-in replacement | ✅ Architected for, not yet built — honest gap to note |

### Gaps / Honest Tensions

- **Orchestrated mode is opt-in** (`orchestrated-mode: false` by default for backward compatibility). Full end-to-end automation requires the user to explicitly enable it. This is a minor friction point between the stated aim and the current default.
- **Future backends are designed for, not built.** Only `local` and `notion` are currently implemented. The pluggable layer exists, but no third backend (e.g. Linear, GitHub Projects) is functional yet.
- **GitHub Actions CI/CD is "planned"** in the tech stack but not yet implemented. The "automated ship" step is currently a manual `agent release write` command rather than a triggered pipeline.

Overall, the project substantially delivers on its stated aim. The core automation loop — idea to brief to implementation to review to ship — is fully specified and backed by a working CLI and Notion integration. The gaps are honest engineering deferrals, not misalignments with the goal.
