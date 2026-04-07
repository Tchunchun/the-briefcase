## Problem
The current AGENTS.md is 164 lines — well past the research-backed 100-line hard maximum. It mixes agent instructions with human documentation (repo tree, consumer install scripts, changelog), duplicates content already in PLAYBOOK.md, and omits critical agent-facing sections (runnable commands, file-scoped test/lint, commit attribution). Instruction-following quality degrades as document length increases.
## Goal
AGENTS.md is under 60 lines and contains only what agents need to act: entrypoint pointer, runnable commands, key conventions, and commit attribution. Human-facing content (repo structure, consumer setup, changelog) lives in README.md where it already has a natural home.
## Acceptance Criteria
- [ ] AGENTS.md is ≤ 60 lines (hard ceiling: 80)
- [ ] Contains **Entrypoint** section pointing to `skills/PLAYBOOK.md`
- [ ] Contains **Package Manager & Commands** section with runnable commands (`python3 -m pytest`, `ruff check`, `python3 -m src.cli.main`)
- [ ] Contains **File-Scoped Commands** table mapping task → per-file command (test one file, lint one file)
- [ ] Contains **Key Conventions** section (kebab-case, skill paths upstream vs consumer, 3–7 word title rule)
- [ ] Contains **Commit Attribution** section with Co-Authored-By format
- [ ] Does NOT contain the full repository tree (covered by PLAYBOOK.md)
- [ ] Does NOT contain the consumer setup instructions (covered by README.md)
- [ ] Does NOT contain the changelog (tracked in git history)
- [ ] Repo tree and consumer setup sections from AGENTS.md are preserved in README.md (no content lost)
- [ ] CLAUDE.md continues to point to AGENTS.md
- [ ] All existing tests still pass (53/53)
## Out of Scope
- Rewriting PLAYBOOK.md or any SKILL.md files
- Changing the consumer project AGENTS.md template
- Adding new skills or modifying agent routing
- Restructuring README.md beyond absorbing the moved content
## Open Questions
- Should the upstream AGENTS.md include a one-line project scope sentence, or is that redundant with README.md? (Leaning yes — one sentence is cheap and orients the agent.)
- Should we add a `testing-strategy.md` pointer in the commands section, or is the file-scoped commands table sufficient?
## Technical Approach
*Owned by architect agent.*
---
