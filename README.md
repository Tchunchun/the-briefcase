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
