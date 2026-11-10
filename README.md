# 0-to-1 Agent Skills

A multi-agent workflow framework that takes a software idea from raw thought to shipped feature — with structured documentation, automated handoffs, and traceable dispatch.

Start with [Briefcase Lite](lite/README.md) for the requirements, build, and
review loops using Markdown and Git, with an optional GitHub Projects board.
For the current GitHub-first workflow, see the
[workflow playbook](workflow-kit/PLAYBOOK.md): Requirements, Architect
(Standard only), Build, and Review, invoked directly without a Delivery Manager.
For the legacy workflow with five roles, a CLI, and configurable storage, see
the [installation guide](#quick-start). The installer still installs that
legacy workflow, not the additive workflow kit.

### Technically shape Standard features

For framework development on the Standard board, say **"Run the technical shaping
loop for <topic>"**, **"Run the architecture loop"**, or supply an issue URL or
Project card. Requirements and Architect remain distinct: Requirements shapes
and approves product scope, while Architect owns Technical shaping. An already
approved Feature may enter Technical shaping directly. The session reuses that
approved revision, resolves the technical approach,
dependencies, risks, and verification details, and records technical sign-off. Ready
requires that approval, technical sign-off (or justified non-applicability),
satisfied dependencies, and no competing implementation claim. The loop ends with a
verified handoff and an exact Build prompt; it does not start implementation.

Feature and Task gates are intentionally different. Architect signs the full
Feature architecture. A child Task records either `parent sign-off applies` or
a Task-specific sign-off when it changes a technical decision, interface,
dependency, NFR, approach assumption, or release obligation. A Task may become
Done after its own accepted slice lands and its allocated gates pass; Feature
Done additionally requires complete required child coverage and Feature-level
release evidence. Closeout ownership is configured once in
[`workflow-kit/workflow.yaml`](workflow-kit/workflow.yaml).

The machine-readable lifecycle is
[`workflow-kit/contract.yaml`](workflow-kit/contract.yaml). Validate the local
contract and repository manifest with `python3 workflow-kit/runtime.py
--offline`; run `python3 workflow-kit/runtime.py` for the strictly read-only
GitHub repository and Project preflight. The preflight reports schema or
permission drift and never repairs the board. See the
[workflow-kit installation path](workflow-kit/INSTALLATION.md); the root
installer remains legacy until a named pilot validates the new contract.

Before an invoked role writes Project state, it must run the live preflight and
an allowed `runtime.py --transition ...` decision, preserve that decision, and
verify every resulting field by readback. The
[Workflow Kit CI](.github/workflows/workflow-kit.yml) enforces offline contract
validation, scenario tests, focused lint, and the complete non-live test suite.

After bootstrap is explicitly ended, with no target the loop captures Technical
shaping work owned by Architect. The Requirements loop never silently becomes
Architect. Missing approval or a material scope change returns to Requirements;
approved Standard work moves to Technical shaping with Architect as Action
Owner. **"Run the requirements loop"** remains a compatibility alias; it does
not repeat product shaping for existing features. Lite is unchanged.
See the [repository technical shaping loop](_project/backlog-policy.md#repository-technical-shaping-loop)
for authority, handoff packets, blockers, and safe reruns. This is a
repository-specific Standard entry point, not a new CLI command or a change to
installed consumer/Lite behavior.

### Build the kit before dogfooding

This repository is currently in a bootstrap phase. Requests to build, repair,
document, or test `workflow-kit/` are handled as ordinary repository work; they
do not activate Standard or Lite mode merely because they say "build", "fix",
or "review", or include an issue or Project link. Project #5 remains the only
backlog, and normal tests and PR safeguards still apply.

To dogfood the completed flow, explicitly say **"Use Standard mode for
<target>"**, **"Use Lite mode for <target>"**, or directly invoke a named role or
loop for that target. Activation is prospective and limited to that named pilot
work. Existing kit-development work is not retroactively routed through the
workflow. No-target backlog sweeps remain disabled until bootstrap is explicitly
ended.

### Review this repository's backlog

For framework development, [Project #5](https://github.com/users/Tchunchun/projects/5)
is the authoritative backlog. During bootstrap, invoke the review loop only for
a named, explicitly activated pilot target. After bootstrap is explicitly ended,
in a session separate from implementation say **"Run the review loop"** to
assess its In review column, or supply a specific PR, issue URL, or card. After
a pass, the reviewer merges the eligible PR, verifies intended-base landing and
applicable release evidence, then closes the task and marks it Done without a
separate Deliver stage. Full scope,
independent revision-specific acceptance, required checks, eligible approvals,
and branch protections remain mandatory. Queued or otherwise gated work stays
In review; missing evidence is reported with an owner and unblock condition.
An explicitly read-only review does not merge or update the board.

See the [repository review loop](_project/backlog-policy.md#repository-review-loop)
for closeout permissions, legacy-card reconciliation, and verified GitHub
updates. This is a repository-specific workflow, not a change to Lite or the
legacy installed consumer workflow. It is an agent-invoked
**pass -> merge -> verify -> close** loop, not an unattended background service.

## Legacy Installed Workflow

The legacy installed workflow uses five specialized AI agent roles, a strict handoff protocol between them, and a CLI toolchain (`briefcase`) that manages every planning artifact against a pluggable storage backend (local files or Notion). This is not the current repository agent roster.

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

### Prerequisites

- Python 3.11 or newer
- Git
- A checkout of this framework that is separate from the repository where you
  want to install it

For example:

```bash
git clone https://github.com/Tchunchun/the-briefcase.git /absolute/path/to/the-briefcase
FRAMEWORK_DIR=/absolute/path/to/the-briefcase
```

### Install into your project

The installer copies the framework from `FRAMEWORK_DIR` into another repository.
It intentionally rejects installing the framework into its own checkout.

For a new repository:

```bash
FRAMEWORK_DIR=/absolute/path/to/the-briefcase
TARGET_DIR=/absolute/path/to/new-project

mkdir -p "$TARGET_DIR"
git -C "$TARGET_DIR" init
TARGET_DIR="$TARGET_DIR" "$FRAMEWORK_DIR/install.sh"
```

For an existing repository, review its working tree first and then target it
explicitly:

```bash
FRAMEWORK_DIR=/absolute/path/to/the-briefcase
TARGET_DIR=/absolute/path/to/existing-project

git -C "$TARGET_DIR" status --short
TARGET_DIR="$TARGET_DIR" "$FRAMEWORK_DIR/install.sh"
```

Do not run `./install.sh` with the framework checkout itself as `TARGET_DIR`.

The install script:

1. Copies `src/`, `skills/`, `template/` into `.briefcase/`
2. Creates `.briefcase/storage.yaml` (default: `backend: local`)
3. Generates an executable `./briefcase` entry point
4. Creates a Python venv and installs dependencies (click, pyyaml, notion-client)
5. Creates `docs/plan/` directory structure for local backend
6. Copies `AGENTS.md`, `CLAUDE.md`, and `_project/` templates
7. Updates `.gitignore` (idempotent)

#### Existing-repository preservation rules

The installer replaces framework-managed code under `.briefcase/src/`,
`.briefcase/skills/`, and `.briefcase/template/`, and regenerates the
`./briefcase` wrapper. It does not merge consumer-owned entrypoints or project
policy:

- Existing `AGENTS.md` and `CLAUDE.md` files are preserved and skipped.
- An existing `_project/` directory is preserved and skipped as a whole.
- Existing local planning files under `docs/plan/` are preserved; missing
  scaffold files may be created.
- Consumer `src/`, `tests/`, and other application files are not modified.

If your repository already has `AGENTS.md`, manually integrate the instruction
to read `.briefcase/skills/PLAYBOOK.md` before acting, along with any Briefcase
commands your agents need. If it already has `CLAUDE.md`, make sure it points to
the resulting `AGENTS.md` policy. Review the templates in
`.briefcase/template/` and manually reconcile any desired additions with an
existing `_project/`; the installer will not merge them for you.

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

Run these read-only checks from the target repository root:

```bash
./briefcase --help
./briefcase inbox list
./briefcase backlog list
```

The default configuration is `backend: local`, so these commands require no API
key or external service. Artifact commands emit JSON; successful reads include:

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

### Migrate from Notion to git

If a consumer project already uses the Notion backend and you want to move planning artifacts to a private git backend, use the migration plan in [consumer-notion-to-git-migration-plan.md](/Users/chunchun/Documents/02%20Framework/0%20to%201%20Agent%20Guidelines/consumer-notion-to-git-migration-plan.md).

Core command:

```bash
./briefcase migrate notion-to-git --remote-url <private-artifact-remote>
```

Required acceptance step after migration:

```bash
./briefcase sync shakedown-git --brief-name <brief-slug> --feature-title "<feature-title>" --expected-status <status>
```

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
./briefcase sync push                                     # Push git-backed artifacts to the configured remote
./briefcase sync pull                                     # Pull git-backed artifacts from the configured remote
./briefcase sync shakedown-git --brief-name my-feature --feature-title "My Feature" --expected-status review-accepted
```

### Operator Shakedown Workflow

Use `sync shakedown-git` after migrating a project to the git backend, after changing git sync behavior, or before declaring a git-backed workflow healthy.

For Notion-to-git migrations, this command is the required post-cutover acceptance gate before the migration branch is merged.

Recommended operator sequence:

```bash
# 1. Push current planning artifacts
./briefcase sync push

# 2. Validate a known active feature in a clean consumer workspace
./briefcase sync shakedown-git \
    --brief-name shared-private-artifact-repo \
    --feature-title "Shared private artifact repo" \
    --expected-status review-accepted \
    --expected-review-verdict accepted \
    --expected-route-state routed \
    --expected-lane feature

# 3. Validate a shipped feature with release metadata
./briefcase sync shakedown-git \
    --feature-title "CLI-first skill instructions" \
    --expected-status done \
    --expected-release-note-link docs/plan/_releases/v0.4.0/release-notes.md \
    --expected-automation-trace-contains "[auto-ship-dispatch]"
```

What this command does:

- Pushes current git-backed planning artifacts if needed
- Creates a fresh temporary consumer workspace
- Pulls artifacts from the configured git backend into that clean workspace
- Reads the requested brief and backlog row through the normal storage layer
- Fails if expected workflow fields do not survive the roundtrip

Use `--keep-consumer` if you want to inspect the temporary pulled workspace after the run.

### Automation (Delivery Manager dispatch)

```bash
./briefcase automate architect-review       # Dispatch features needing architect review
./briefcase automate implementation-ready   # Dispatch features ready for implementation
./briefcase automate review-ready           # Dispatch features ready for review
./briefcase automate fix-cycle-dispatch     # Dispatch features back for fix cycle
./briefcase automate ship-routing           # Route accepted features to ship path
./briefcase automate ship-dispatch          # Execute ship dispatch for accepted features
```

### Update an installed framework

Use `update` to check or replace the framework-managed files under
`.briefcase/`. Start with the read-only check:

```bash
./briefcase update --check
```

`update --check` exits `0` when the installed version is current, `2` when an
update is available, and `1` on error. Updates are version-gated: if the
installed `.briefcase/VERSION` is the same as or newer than the source version,
no files are changed.

Apply an available update non-interactively with:

```bash
./briefcase update --yes
```

When testing or updating from a separate local checkout, make the source
explicit:

```bash
./briefcase update --source /absolute/path/to/the-briefcase --check
./briefcase update --source /absolute/path/to/the-briefcase --yes
```

The updater never changes consumer-owned `AGENTS.md`, `CLAUDE.md`, `_project/`,
or `.env`. It also detects local changes inside framework-managed files and
refuses to overwrite them by default. Back up or port those customizations
before retrying. `--force` deliberately overwrites customized framework files;
use it only after reviewing what `--check` reports.

Re-running `install.sh` is also safe for restoring a missing `.briefcase/` or
bootstrapping a fresh clone of a consumer repository. Because `.briefcase/` is
gitignored, a fresh clone does not contain the framework runtime: clone or
locate the framework separately, then run the absolute-`TARGET_DIR` install
command above. Reinstallation replaces framework-managed directories while
preserving the consumer-owned files described earlier.

### Upgrade a Notion workspace schema

`upgrade` does not update framework code. It validates and repairs the schema of
an existing Notion backend:

```bash
./briefcase upgrade --check
./briefcase upgrade --yes
```

Local-backend projects do not need this command. After `briefcase update`, a
Notion-backed project may be prompted to run `briefcase upgrade --check`.

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
