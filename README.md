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

Copy two folders from this repo into your project root:

```bash
# Skills — Claude Code auto-loads these from .skills/skills/
cp -r skills/ /path/to/your-project/.skills/skills/

# Document templates — referenced by the skills at runtime
cp -r _doc_template/ /path/to/your-project/_doc_template/
```

Then set up the two project-root files that the skills depend on:

```bash
# Copy the AGENTS.md template (see below) into your project root
# Copy or create CLAUDE.md with one line:
echo 'Read AGENTS.md before taking any action.' > /path/to/your-project/CLAUDE.md
```

### What each piece does

| What you copy | Where it goes in your project | Why |
|---|---|---|
| `skills/` | `.skills/skills/` | The 4 agent skill definitions — Claude Code auto-loads from here |
| `_doc_template/` | `_doc_template/` | Blank templates the skills copy when creating briefs, tasks, etc. |
| AGENTS.md template | `AGENTS.md` (project root) | Routing rules, file ownership, handoff sequence between agents |
| CLAUDE.md | `CLAUDE.md` (project root) | Tells Claude Code to read AGENTS.md first |

## How to call the skills

### In Claude Code (auto-trigger)

Claude Code reads the `description` field in each SKILL.md and **automatically activates the right skill** based on what you say. Just talk naturally:

| What you say | Skill triggered |
|---|---|
| "I have an idea for a notifications feature" | **Ideation** — shapes your idea into a scoped brief |
| "What if we added dark mode?" | **Ideation** |
| "How should we build the auth system?" | **Architect** — resolves technical decisions, signs off the brief |
| "Should we use Postgres or SQLite?" | **Architect** |
| "Build this feature" | **Implementation** — creates tasks, writes code and tests |
| "Continue building" / "Let's ship this" | **Implementation** |
| "Review this" / "Is this feature done?" | **Review** — validates work against the brief |
| "QA this" / "Does this match requirements?" | **Review** |

You can also invoke a skill explicitly:

```
Use the ideation skill to scope this feature: [your idea]
Use the architect skill to review the technical approach for [feature]
```

### In Codex (manual activation)

Codex reads `AGENTS.md` and follows the routing rules, but it does **not** auto-trigger skills from the YAML frontmatter. Start each session by telling Codex which skill to follow:

```
Read .skills/skills/ideation/SKILL.md and follow it for this task.
```

Quick reference:

| Task type | Tell Codex to read |
|---|---|
| Brainstorming / scoping | `.skills/skills/ideation/SKILL.md` |
| Technical decisions / project setup | `.skills/skills/architect/SKILL.md` |
| Coding / building / shipping | `.skills/skills/implementation/SKILL.md` |
| Validating / QA / acceptance | `.skills/skills/review/SKILL.md` |

## Required: AGENTS.md in each project

Each skill defers to a project-level `AGENTS.md` for routing rules, file ownership, and handoff sequence. The full workflow definition lives in `PLAYBOOK.md` (shipped with the skills). Consumers just reference it.

### Consumer setup (2 files)

**AGENTS.md** — create at your project root:

```markdown
# AGENTS.md

Read `.skills/PLAYBOOK.md` fully before taking any action.
Follow all routing, ownership, and handoff rules defined there.

## Project-specific notes

Add any project-specific overrides or context here.
```

**CLAUDE.md** — create at your project root:

```
Read AGENTS.md before taking any action.
```

That's it. The agent reads `AGENTS.md` → follows the reference to `PLAYBOOK.md` → gets all routing rules, file ownership, handoff sequence, session protocol, and shared rules automatically.

---

## How the skills and PLAYBOOK.md work together

Each skill handles its own role — brainstorming, architecture, coding, or review. When a skill needs to know about file ownership or what to hand off next, it reads `PLAYBOOK.md`. That means the skills are portable (they travel with the plugin), but the project's workflow conventions live in `PLAYBOOK.md` (which ships with the skills and works out of the box).

This split is intentional:

- **Skills** = *how* each agent behaves, what it produces, and what it must not touch
- **PLAYBOOK.md** = *who* owns what, *when* to hand off, and *where* files live
- **AGENTS.md** = project-level entrypoint that references `PLAYBOOK.md` (you can add project-specific overrides here)

## Tool compatibility

| Tool | Skills auto-trigger | AGENTS.md routing | Notes |
|---|---|---|---|
| **Claude Code** | ✅ Yes — from `description` field in SKILL.md YAML frontmatter | ✅ Yes | Full support. Copy `skills/` → `.skills/skills/` in your project root. |
| **Codex** | ❌ No — must be invoked manually | ✅ Yes — reads `AGENTS.md` at project root | At session start, tell Codex: "Read `.skills/skills/{role}/SKILL.md` for this task." |
| **Other tools** | ❌ No | Depends on tool | If the tool reads `AGENTS.md`, routing works. Skills must be pointed to explicitly. |
