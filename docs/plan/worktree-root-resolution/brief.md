**Status: implementation-ready**
**Created: 2026-03-24**

---

## Problem
Agent in git worktree cannot find briefcase script, silently fails, assumes wrong backend, corrupts artifact reads/writes.

## Goal
Agents resolve true project root before invoking briefcase. Missing script triggers root resolution, not CLI unavailable.

## Acceptance Criteria
- [ ] PLAYBOOK instructs root resolution via git rev-parse
- [ ] Missing briefcase documented as worktree scenario
- [ ] briefcase.sh handles worktree paths
- [ ] Consumer projects using worktrees work correctly

## Non-Functional Requirements
No new deps. Docs and shell only. No breakage for non-worktree usage.

## Out of Scope
Rewriting CLI in Python. Non-git worktree dirs.

## Open Questions
- [RESOLVED] Should briefcase.sh try git rev-parse as fallback? No — the walk-up logic in briefcase.sh already handles worktrees. The fix belongs in agent instructions (AGENTS.md/PLAYBOOK.md), not the shell script.
- [RESOLVED] Should PLAYBOOK define root resolution algorithm? Yes — add a Project Root Resolution step to Session Protocol.

## Technical Approach
Documentation-only fix. No code changes, no new dependencies.

1. **AGENTS.md** — Add a Project Root Resolution callout in the Commands section. Instruct agents to run `git rev-parse --show-toplevel` to find the true project root before running any `briefcase` command. Explicitly state: a missing `./briefcase` in CWD means you are in a subdirectory or worktree, not that the CLI is unavailable.

2. **PLAYBOOK.md Session Protocol** — Add step 0: Resolve the project root. If CWD is inside a git worktree (e.g. `.claude/worktrees/<name>/`), run `git rev-parse --show-toplevel` and `cd` to the project root or pass `--project-dir` before running `briefcase` commands.

3. **template/briefcase.sh** — No change needed. The existing walk-up logic (`find_project_root`) already resolves the root correctly from any subdirectory.

4. **install.sh** — No change needed. Briefcase is already installed at the project root. Optionally add a worktree usage note to install output.

Cost: Zero. No new dependencies. No cloud services. No licensing.
