# 0-to-1 Agent Skills

Five agent skills for the full lifecycle of building a feature — from idea to shipped code.

| Skill | What it does |
|---|---|
| **ideation** | Turns rough ideas into scoped briefs |
| **architect** | Resolves technical questions, signs off briefs as implementation-ready |
| **implementation** | Breaks briefs into tasks, writes code and tests, ships with release notes |
| **review** | Validates implementation against the brief and acceptance criteria |
| **delivery-manager** | Coordinates handoffs between roles with readiness checks and escalation |

## Setup

Copy into your project:

```bash
# Skills + PLAYBOOK (workflow rules)
cp -r skills/ /path/to/your-project/.skills/

# Document templates
cp -r template/ /path/to/your-project/template/
```

Create two files at your project root:

**AGENTS.md:**
```markdown
Read `.skills/PLAYBOOK.md` fully before taking any action.
Follow all routing, ownership, and handoff rules defined there.
```

**CLAUDE.md:**
```
Read AGENTS.md before taking any action.
```

Your project ends up looking like:
```
your-project/
├── AGENTS.md
├── CLAUDE.md
├── .skills/
│   ├── PLAYBOOK.md
│   └── skills/
│       ├── ideation/SKILL.md
│       ├── architect/SKILL.md
│       ├── implementation/SKILL.md
│       └── review/SKILL.md
└── template/
    ├── brief.md
    ├── tasks.md
    ├── backlog.md
    └── ...
```

## Use Skills + CLI with Notion (Consumer Projects)

For projects that want both agent skills and Notion as the planning database:

### 1. Install the briefcase

One folder, everything the framework needs:

```bash
mkdir -p /path/to/your-project/.briefcase
cp -r skills/   /path/to/your-project/.briefcase/skills/
cp -r template/  /path/to/your-project/.briefcase/template/
cp -r src/       /path/to/your-project/.briefcase/src/

# Patch skill paths for consumer project layout
find /path/to/your-project/.briefcase/skills/ -name '*.md' \
  -exec sed -i '' 's|\.skills/|.briefcase/skills/|g' {} +
```

### 2. Add the `agent` entry point

Create an executable `agent` script at your project root:

```bash
cat > /path/to/your-project/agent << 'EOF'
#!/usr/bin/env python3
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".briefcase"))
from src.cli.main import cli
if __name__ == "__main__":
    cli()
EOF
chmod +x /path/to/your-project/agent
```

### 3. Add to `.gitignore`

```gitignore
# Agent framework (not project code)
.briefcase/
_project/storage.yaml
docs/plan/.sync-manifest.json
```

### 4. Update AGENTS.md

Point to the briefcase:

```markdown
Read `.briefcase/skills/PLAYBOOK.md` fully before taking any action.
```

### 4. Provision Notion workspace

```bash
./agent setup --backend notion
```

This will prompt for your Notion API token and parent page ID, provision databases, and save config.

### Project structure after install

```
your-project/
├── agent                  ← entry point (executable, committed to git)
├── .briefcase/            ← THE FRAMEWORK (gitignored)
│   ├── skills/            ← agent behavior rules (PLAYBOOK + 5 SKILL.md)
│   ├── template/          ← document templates (brief, tasks, backlog, etc.)
│   └── src/               ← CLI + storage + sync code
├── _project/
│   ├── storage.yaml       ← backend config (gitignored)
│   ├── tech-stack.md
│   └── decisions.md
├── AGENTS.md              ← points to .briefcase/skills/PLAYBOOK.md
├── CLAUDE.md              ← points to AGENTS.md
└── src/                   ← YOUR app code (untouched)
```

### Agent Artifact CLI

Agents call `./agent` from the project root. Commands route transparently to the active backend (local files or Notion):

```bash
# Inbox
./agent inbox list                                    # List all ideas
./agent inbox add --type idea --text "Build auth"     # Add an idea

# Briefs
./agent brief list                                    # List all briefs
./agent brief read my-feature                         # Read a brief as JSON
./agent brief write my-feature --problem "..." --goal "..."  # Create/update inline
./agent brief write my-feature --file brief.md        # Import from markdown file

# Backlog
./agent backlog list                                  # List all items
./agent backlog list --type Feature                   # Filter by type
./agent backlog upsert --title "Build login" --type Task --status to-do --priority High

# Decisions
./agent decision list                                 # List all decisions
./agent decision add --id D-001 --title "Use Next.js" --date 2026-03-16 --why "SSR"

# Sync (optional — for git snapshots or bulk import)
./agent sync local                                    # Pull Notion → local
./agent sync notion                                   # Push local → Notion
```

All commands output JSON (`{"success": true, "data": ...}`) to stdout, errors to stderr.

Ownership boundaries:
- Keep your application code in your own `src/` and `tests/`.
- Keep your project-specific skills in your own `.skills/`.
- The CLI manages planning/storage artifacts (`_project/`, `docs/plan/`, `template/`) and Notion sync.

## Usage

### Claude Code

Skills activate based on what you say. Examples:

- *"I want to build a notification system"* → **ideation** activates
- *"How should we architect this?"* → **architect** activates
- *"Build this"* / *"Let's ship this"* → **implementation** activates
- *"Review this"* / *"Is this done?"* → **review** activates

You can also be explicit: `Use the ideation skill to scope this feature.`

### Codex

Codex reads `AGENTS.md` but does not auto-activate skills. Tell it which skill to follow at the start of each session:

```
Read .skills/skills/ideation/SKILL.md and follow it for this task.
```

| Task | Tell Codex to read |
|---|---|
| Brainstorming / scoping | `.skills/skills/ideation/SKILL.md` |
| Technical decisions | `.skills/skills/architect/SKILL.md` |
| Coding / shipping | `.skills/skills/implementation/SKILL.md` |
| QA / acceptance | `.skills/skills/review/SKILL.md` |

## How it works

- **Skills** define how each agent behaves — what it produces, what it must not touch.
- **PLAYBOOK.md** defines who owns what, when to hand off, and where files live.
- **AGENTS.md** is the project entrypoint that points to `PLAYBOOK.md`. Add project-specific overrides here.
