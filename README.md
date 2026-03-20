# 0-to-1 Agent Skills

A multi-agent workflow framework that takes a software idea from raw thought to shipped feature — with structured documentation, automated handoffs, and traceable dispatch.

## What This Does

Five specialized AI agent roles, a strict handoff protocol between them, and a CLI toolchain (`briefcase`) that manages every planning artifact against a pluggable storage backend (local files or Notion).

| Skill | Responsibility |
|---|---|
| **Ideation** | Turns rough ideas into scoped briefs (`Status: draft`) |
| **Architect** | Resolves technical questions, signs off briefs (`Status: implementation-ready`) |
| **Implementation** | Breaks briefs into task backlog rows, writes code and tests, ships with release notes |
| **Review** | Validates implementation against the brief and acceptance criteria |
| **Delivery Manager** | Orchestrates handoffs between roles with readiness checks, dispatch, and escalation |

### The Workflow

```
Idea captured → Ideation → Architect → Implementation → Review → Ship
                    ↓           ↓            ↓             ↓
                brief.md    tech sign-off  src/ + tests/  verdict
```

Each transition is mediated by the Delivery Manager, which validates readiness and produces an auditable handoff packet. Two execution modes:

- **Orchestrated mode** — user interacts only with the Delivery Manager; all delegation is automatic.
- **Manual mode** — user invokes any role agent directly, following the same handoff checks.

---

## Quick Start

### Install into your project

```bash
# From the framework repo root:
./install.sh
```

Or, to install into a specific directory:

```bash
TARGET_DIR=/path/to/your-project ./install.sh
```

The install script:

1. Copies `src/`, `skills/`, `template/` into `.briefcase/`
2. Creates `.briefcase/storage.yaml` (default: `backend: local`)
3. Generates an executable `./briefcase` entry point
4. Creates a Python venv and installs dependencies (click, pyyaml, notion-client)
5. Creates `docs/plan/` directory structure for local backend
6. Copies `AGENTS.md`, `CLAUDE.md`, and `_project/` templates
7. Updates `.gitignore` (idempotent)

### Post-install structure

```
your-project/
├── briefcase               ← CLI entry point (executable, committed to git)
├── .briefcase/            ← THE FRAMEWORK (gitignored)
│   ├── skills/            ← PLAYBOOK.md + 5 SKILL.md agent definitions
│   ├── template/          ← document templates (brief, backlog, etc.)
│   ├── src/               ← CLI + storage + sync code
│   ├── .venv/             ← Python venv with dependencies
│   └── storage.yaml       ← backend config
├── _project/
│   ├── tech-stack.md
│   ├── definition-of-done.md
│   └── testing-strategy.md
├── docs/plan/             ← local planning artifacts (inbox, backlog, briefs)
├── AGENTS.md              ← points to .briefcase/skills/PLAYBOOK.md
├── CLAUDE.md              ← points to AGENTS.md
└── src/                   ← YOUR app code (untouched)
```

### Start using it (local backend — default)

The installer defaults to a **local file backend**. No API keys, no external services — everything works immediately:

```bash
./briefcase --help                    # See all commands
./briefcase inbox add --type idea --text "Build auth flow"
./briefcase inbox list                # See your ideas
```

### Verify your install

Run this quick smoke test right after install:

```bash
./briefcase --help
./briefcase inbox add --type idea --text "Install smoke test" --notes "Safe to keep or delete later"
./briefcase inbox list
```

Expected success indicators:

```json
{"success": true, "data": ...}
```

This works for both local and Notion backends because all commands route through the same CLI contract.

### Enable Notion backend (optional)

To use Notion as your planning surface instead of local files:

```bash
# Set your API key
export NOTION_API_KEY="ntn_..."

# Provision Notion workspace
./briefcase setup --backend notion
```

This prompts for a parent page ID, provisions the Briefs and Backlog databases, and saves config. All `./briefcase` commands then route transparently to Notion.

---

## Agent Artifact CLI

All commands output JSON (`{"success": true, "data": ...}`) to stdout, errors to stderr. Commands route transparently to whichever backend is active.

### Inbox

```bash
./briefcase inbox list                                    # List all ideas
./briefcase inbox add --type idea --text "Build auth" --priority High
```

### Briefs

```bash
./briefcase brief list                                    # List all briefs
./briefcase brief read my-feature                         # Read a brief as JSON
./briefcase brief write my-feature --problem "..." --goal "..." --change-summary "..."
./briefcase brief write my-feature --file brief.md        # Import from markdown file
./briefcase brief history my-feature                      # List stored brief revisions
./briefcase brief revision my-feature <revision-id>       # Read one stored revision
./briefcase brief restore my-feature <revision-id> --change-summary "..."
```

### Backlog

```bash
./briefcase backlog list                                  # List all items
./briefcase backlog list --type Feature                   # Filter by type
./briefcase backlog upsert --title "Build login" --type Task --status to-do --priority High
```

### Decisions

```bash
./briefcase decision list                                 # List all decisions
./briefcase decision add --id D-001 --title "Use Next.js" --date 2026-03-16 --why "SSR"
```

### Releases

```bash
./briefcase release list                                  # List all releases
./briefcase release read v0.4.0                           # Read a release note
./briefcase release write --version v0.5.0 --notes "..."  # Write a release note
```

### Sync (optional — for git snapshots or bulk import)

```bash
./briefcase sync local                                    # Pull Notion → local markdown
./briefcase sync notion                                   # Push local → Notion
```

### Automation (Delivery Manager dispatch)

```bash
./briefcase automate architect-review       # Dispatch features needing architect review
./briefcase automate implementation-ready   # Dispatch features ready for implementation
./briefcase automate review-ready           # Dispatch features ready for review
./briefcase automate fix-cycle-dispatch     # Dispatch features back for fix cycle
./briefcase automate ship-routing           # Route accepted features to ship path
./briefcase automate ship-dispatch          # Execute ship dispatch for accepted features
```

### Upgrade

```bash
./briefcase upgrade                         # Upgrade .briefcase/ from upstream
./briefcase upgrade --check                 # Dry-run: show what would change
```

---

## Namespace Isolation

`.briefcase/` is the single namespace for all framework code — analogous to `node_modules/`.

| Framework repo folder | Consumer `.briefcase/` folder | What it contains |
|---|---|---|
| `skills/` | `.briefcase/skills/` | PLAYBOOK.md + 5 SKILL.md agent definitions |
| `template/` | `.briefcase/template/` | Blank document templates (brief, backlog, etc.) |
| `src/` | `.briefcase/src/` | CLI commands, storage backends, sync logic |

Key rules:

- **Gitignored.** The install script reproduces it; `.briefcase/` is not consumer code.
- **No files outside `.briefcase/`.** Consumer-owned folders (`src/`, `tests/`, `docs/`) are never touched.
- **Path patching.** During install, skill path references are rewritten from `skills/` to `.briefcase/skills/` automatically.
- **`sys.path` isolation.** The `./briefcase` entry point inserts `.briefcase/` into Python's module path, so `from src.cli.main import cli` resolves to `.briefcase/src/cli/main.py` — not the consumer's own `src/`.

---

## Usage

### Claude Code

Skills activate based on what you say:

- *"I want to build a notification system"* → **Ideation** activates
- *"How should we architect this?"* → **Architect** activates
- *"Build this"* / *"Let's ship this"* → **Implementation** activates
- *"Review this"* / *"Is this done?"* → **Review** activates
- *"Route this to the next owner"* → **Delivery Manager** activates

You can also be explicit: `Use the ideation skill to scope this feature.`

### Codex

Codex reads `AGENTS.md` but does not auto-activate skills. Tell it which skill to follow:

```
Read .briefcase/skills/ideation/SKILL.md and follow it for this task.
```

| Task | Tell Codex to read |
|---|---|
| Brainstorming / scoping | `.briefcase/skills/ideation/SKILL.md` |
| Technical decisions | `.briefcase/skills/architect/SKILL.md` |
| Coding / shipping | `.briefcase/skills/implementation/SKILL.md` |
| QA / acceptance | `.briefcase/skills/review/SKILL.md` |
| Handoffs / dispatch | `.briefcase/skills/delivery-manager/SKILL.md` |

---

## Feedback

Found a bug? Have a feature request? Submit it directly through the CLI:

```bash
# Bug report
./briefcase inbox add --type idea --text "Bug: short description" --notes "Steps to reproduce and context"

# Feature request
./briefcase inbox add --type idea --text "Short feature title" --notes "What you need and why"

# Tech debt
./briefcase inbox add --type idea --text "[tech-debt] Short description" --notes "Details"
```

The ideation agent triages incoming feedback, classifies it (bug / feature / tech-debt), and routes it through the standard workflow pipeline.

---

## How It Works

- **Skills** (`SKILL.md`) define how each agent behaves — what it produces, what it must not touch, and what CLI commands it uses.
- **PLAYBOOK.md** defines who owns what, when to hand off, and where files live.
- **AGENTS.md** is the project entrypoint that points to `PLAYBOOK.md`.

All planning artifact operations go through the `briefcase` CLI, which routes to the active backend. Agents never read or write storage directly.

---

## Storage Backends

The active backend is declared in `_project/storage.yaml`:

```yaml
backend: notion   # or: local
```

| Backend | Agent reads/writes via | Source of truth |
|---|---|---|
| `local` | CLI commands or file paths (both work) | Markdown files in `docs/plan/` |
| `notion` | CLI commands only | Notion API |

Future backends (Linear, GitHub Projects, etc.) can be added by implementing the same CLI contract.

---

## Repository Structure (Upstream)

```
{project-root}/
├── AGENTS.md                      ← project entrypoint; agent-facing conventions
├── CLAUDE.md                      ← Claude Code entrypoint; points to AGENTS.md
├── install.sh                     ← installs framework into consumer projects
├── README.md
│
├── skills/                        ← distributable skills (consumers get .briefcase/skills/)
│   ├── PLAYBOOK.md                ← shared workflow rules; source of truth for all agents
│   ├── ideation/SKILL.md
│   ├── architect/SKILL.md
│   ├── implementation/SKILL.md
│   ├── review/SKILL.md
│   └── delivery-manager/SKILL.md
│
├── template/                      ← blank document templates (consumers get .briefcase/template/)
│   ├── brief.md, tasks.md, backlog.md, release-notes.md
│   ├── tech-stack.md, testing-strategy.md, definition-of-done.md
│   └── adr.md, _inbox.md
│
├── src/                           ← CLI + storage + sync code (consumers get .briefcase/src/)
│   ├── cli/                       ← CLI commands (inbox, brief, backlog, decision, release, automate, upgrade, setup, sync)
│   ├── core/                      ← storage protocol, config, factory, local backend, automation
│   ├── integrations/              ← Notion API client, schemas, provisioner, backend
│   └── sync/                      ← sync logic, manifest, snapshots
│
├── _project/                      ← project-level constants (architect-owned)
│   ├── tech-stack.md, definition-of-done.md, testing-strategy.md
│   ├── decisions.md
│   └── storage.yaml               ← backend config (local or notion)
│
├── docs/plan/                     ← briefcase working space
│   ├── _inbox.md                  ← raw ideas; append-only
│   ├── _shared/backlog.md
│   ├── _releases/v{version}/release-notes.md
│   ├── _reference/
│   └── {brief-name}/brief.md     ← one folder per scoped brief (kebab-case)
│
└── tests/                         ← automated tests; mirrors src/ modules
```

---

## Technical Stack

- **Language:** Python 3.11+
- **CLI:** Click
- **Storage:** Local filesystem (default), Notion API (`notion-client` SDK)
- **Testing:** pytest, pytest-mock, HTTP mocking for Notion API tests
- **Code style:** PEP 8 via `ruff`; config in YAML; secrets in `.env`

---

## Development (Framework Contributors)

```bash
# Run all tests
python3 -m pytest tests/

# Run one test file
python3 -m pytest tests/path/to/test_file.py

# Lint
ruff check src/ tests/

# Format
ruff format src/ tests/

# Run CLI from the framework repo
python3 -m src.cli.main <command>
```

Load `.env` before commands that hit Notion:

```bash
export $(grep -v '^#' .env | xargs)
```

### Folder Naming Conventions

- **All folders use `kebab-case`**: lowercase, hyphens, no spaces.
- **Titles** (inbox, backlog, brief): **3–7 words**. Longer context goes in `--notes`.

---

## Releases

| Version | Date | Highlights |
|---|---|---|
| v0.4.0 | 2026-03-16 | CLI-first skill instructions — all 5 skills rewritten for CLI-only artifact access |
| v0.3.0 | 2026-03-16 | Agent Artifact API — `inbox`, `brief`, `decision`, `backlog` CLI commands |
| v0.2.0 | — | Notion backend + sync |
| v0.1.0 | — | Local filesystem backend + skill definitions |

---

## License

See repository for license details.
