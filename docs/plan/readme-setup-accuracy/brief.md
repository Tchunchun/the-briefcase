**Status: implementation-ready**
---
## Problem
README claims ./agent setup --backend notion works but no --backend flag exists (it prompts interactively). README emphasis suggests Notion is the primary path but local is the actual default.
## Goal
README accurately documents the default backend (local) and the setup command matches the documented interface.
## Acceptance Criteria
- [ ] README clearly states local is the default backend before mentioning Notion
- [ ] setup command accepts --backend flag for non-interactive use
- [ ] Interactive prompt remains as fallback when --backend is not provided
- [ ] Post-install quick-start section shows local-first workflow
- [ ] No misleading Notion-first ordering in the getting started guide
## Non-Functional Requirements
README remains concise. No breaking changes to existing interactive setup behavior.
## Out of Scope
Redesigning the setup command entirely. Adding new backends.
## Open Questions
Resolved: both fixes -- add the --backend flag AND reorder the README. The flag enables scripted installs and matches what the README already claims.
## Technical Approach
1. In src/cli/commands/setup.py: add a --backend option (click.option) with choices=['local','notion'] and default=None. When provided, skip the interactive prompt. When None, fall back to existing interactive prompt.
2. In README.md: reorder the Quick Start section to lead with local backend (the default). Move Notion setup into a clearly labeled subsection after the local path.
3. Update the example commands in README to show: ./agent setup (local, default) and ./agent setup --backend notion (explicit Notion).
4. No changes to the underlying setup logic -- just the entry point and docs.
