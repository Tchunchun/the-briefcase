# Notion Setup Feedback — Fresh Install (2026-03-20)

Source: User laptop fresh install test
Logged by: Ideation Agent
Status: Pending Notion sync — capture via `agent inbox add` when NOTION_API_KEY is available

---

## Inbox Items to Capture

### 1. No dependency manifest

```
agent inbox add --type idea --text "Add dependency manifest file" --notes "[tech-debt] No requirements.txt or pyproject.toml. Users must discover click, pyyaml, and notion-client through tracebacks. Add a pyproject.toml with all dependencies."
```

### 2. Installer skips venv and packages

```
agent inbox add --type idea --text "Installer create venv and deps" --notes "[tech-debt] install.sh never creates .briefcase/.venv or installs packages. The ./agent wrapper checks for .briefcase/.venv/bin/python but it doesn't exist. Every new user hits ModuleNotFoundError immediately. Have install.sh create the venv and pip install into it."
```

### 3. Notion import blocks all CLI

```
agent inbox add --type idea --text "Lazy-import Notion modules in CLI" --notes "[tech-debt] upgrade.py unconditionally imports notion_client, so even ./agent --help fails without it installed. This blocks local-only users. Imports should be lazy/conditional so local backend works without notion-client."
```

### 4. docs/plan/ not created on install

```
agent inbox add --type idea --text "Create docs/plan/ during install" --notes "[tech-debt] The local backend reads/writes to docs/plan/, but neither install.sh nor ./agent setup creates it. Every write command fails with FileNotFoundError. Create docs/plan/ during install or setup for the local backend."
```

### 5. AGENTS.md and CLAUDE.md not installed

```
agent inbox add --type idea --text "Install AGENTS.md CLAUDE.md files" --notes "[tech-debt] The README shows AGENTS.md, CLAUDE.md, and _project/ in the post-install structure, but the installer doesn't copy them."
```

### 6. Step counter mismatch in installer

```
agent inbox add --type idea --text "Fix install.sh step counter" --notes "[tech-debt] install.sh prints [1/4], [2/4], [3/4], then switches to [4/5], [5/5]. Step count is inconsistent."
```

### 7. README misleads about default backend

```
agent inbox add --type idea --text "Clarify default backend in README" --notes "[tech-debt] README section ordering and emphasis could mislead users into thinking Notion is the primary path, but install.sh and setup both default to local. Reorder or clarify that local is the default."
```

### 8. Setup --backend flag missing

```
agent inbox add --type idea --text "Add --backend flag to setup" --notes "[tech-debt] README says './agent setup --backend notion', but the actual command prompts interactively for backend choice. There's no --backend flag. Either add the flag or fix the README."
```

---

## What Works Well (for reference)

- Clean CLI design with consistent JSON output
- Idempotent installer with good project-root discovery
- Thoughtful agent role/skill separation
- Pluggable backend architecture

## Recommendations Summary

1. Add a pyproject.toml with dependencies
2. Have install.sh create the venv and pip install into it
3. Lazy-import Notion modules so local-only users aren't blocked
4. Create docs/plan/ during install or setup for the local backend
5. Add a post-install smoke test in the README
