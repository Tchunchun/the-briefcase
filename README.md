# 0-to-1 Agent Skills

Four agent skills for the full lifecycle of building a feature — from idea to shipped code.

| Skill | What it does |
|---|---|
| **ideation** | Turns rough ideas into scoped briefs |
| **architect** | Resolves technical questions, signs off briefs as implementation-ready |
| **implementation** | Breaks briefs into tasks, writes code and tests, ships with release notes |
| **review** | Validates implementation against the brief and acceptance criteria |

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

1. Install skills and templates into your project (same as Setup above).
2. Install the **agent CLI** as a tool/dependency (do not copy this repo's `src/` into your project source tree).
3. In your project root, run:

```bash
agent setup --backend notion --project-dir .
```

During setup, the CLI will:
- write `_project/storage.yaml`
- prompt for `NOTION_API_TOKEN` and parent page ID
- provision Notion databases/pages
- add `docs/plan/` to `.gitignore` (Notion becomes source of truth for planning artifacts)

Daily workflow:

```bash
# Pull Notion -> local before working
agent sync local --project-dir .

# Push local -> Notion after updating planning artifacts
agent sync notion --project-dir .

# Optional: sync template updates from backend
agent sync templates --project-dir .
```

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
