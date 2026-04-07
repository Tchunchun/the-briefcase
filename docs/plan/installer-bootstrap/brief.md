**Status: implementation-ready**
---
## Problem
install.sh does not create a venv, install dependencies, create docs/plan/, copy AGENTS.md/CLAUDE.md, or fix its step counter. Every new user hits ModuleNotFoundError or FileNotFoundError on first command.
## Goal
A fresh install produces a working CLI on the first try: venv with all deps, docs/plan/ for local backend, AGENTS.md and CLAUDE.md copied, step counter consistent.
## Acceptance Criteria
- [ ] install.sh creates a pyproject.toml in .briefcase/ listing click, pyyaml, and notion-client
- [ ] install.sh creates .briefcase/.venv and pip-installs deps into it
- [ ] install.sh creates docs/plan/ with _inbox.md and _shared/backlog.md from template/
- [ ] install.sh copies AGENTS.md, CLAUDE.md, and _project/ to consumer root
- [ ] install.sh step counter uses consistent [N/M] numbering
- [ ] ./agent --help succeeds after clean install with only Python 3.11+
## Non-Functional Requirements
Idempotent: re-running does not duplicate or corrupt consumer files. Portable: macOS and Linux (bash 4+).
## Out of Scope
Notion provisioning (./agent setup). Windows. Upgrading existing installs (./agent upgrade).
## Open Questions
Resolved: notion-client installs with all deps for now (lazy-import-notion brief handles the conditional loading). install.sh should NOT auto-run setup -- that is a separate interactive step.
## Technical Approach
1. Add a pyproject.toml to the framework repo root with [project] dependencies: click, pyyaml, notion-client. install.sh copies it to .briefcase/pyproject.toml.
2. After copying framework code, install.sh runs: python3 -m venv .briefcase/.venv && .briefcase/.venv/bin/pip install -q -e .briefcase/ (or pip install from the copied pyproject.toml).
3. Add a new step to install.sh that creates docs/plan/_inbox.md, docs/plan/_shared/backlog.md, and docs/plan/_reference/adr/ by copying from .briefcase/template/.
4. Add a step that copies AGENTS.md and CLAUDE.md from .briefcase/ (rewritten versions) plus _project/ templates (tech-stack.md, definition-of-done.md, testing-strategy.md) to the consumer root -- skip if already present (idempotent).
5. Fix step counter: count total steps at script top (N=7), use [step/N] consistently.
6. The ./agent wrapper already prefers .briefcase/.venv/bin/python, so no wrapper changes needed.
7. All file copies use cp -n or conditional checks to avoid overwriting consumer-owned files.
