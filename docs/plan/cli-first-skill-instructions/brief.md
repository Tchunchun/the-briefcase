## Problem
All five skill files (ideation, architect, implementation, review, delivery-manager) instruct agents to directly read/write local file paths in their Required Workflow sections — even when storage.yaml is set to backend: notion. The "How to Access Artifacts" section says CLI is primary, but the actual step-by-step workflows contradict this by referencing docs/plan/_inbox.md, docs/plan/{feature}/brief.md, docs/plan/_shared/backlog.md, and docs/plan/{feature}/tasks.md directly. Agents follow the step-by-step instructions, not the reference section, so all reads and writes go to local disk and the Notion backend is never used.
## Goal
Every planning artifact read/write in every skill file goes through CLI commands (agent inbox, agent brief, agent backlog, agent decision). When backend is Notion, agents never touch local markdown planning files. The only files agents access directly are project constants (_project/tech-stack.md, _project/testing-strategy.md, _project/definition-of-done.md), source code (src/, tests/), and ADR templates — which are legitimately local.
## Acceptance Criteria
- [ ] All 5 skill Required Workflow sections use CLI commands for inbox, briefs, backlog, and decisions — zero local file-path references for these artifacts
- [ ] tasks.md is eliminated as a standalone file; tasks are backlog rows (type=Task) with task-specific statuses managed via `agent backlog upsert --type Task`
- [ ] Review findings are stored on Task backlog rows (via --notes or a dedicated field) instead of a tasks.md Review Findings section
- [ ] The "How to Access Artifacts" section in each skill removes the "File paths (local backend only)" fallback block and presents CLI as THE interface (not primary-with-fallback)
- [ ] Brainstorming Approach (ideation) replaces "scan src/ and docs/plan/" with `agent brief list` + `agent inbox list` + `agent backlog list` for prior-art checks
- [ ] "append to _inbox.md" references become `agent inbox add` everywhere
- [ ] "Mark inbox item [-> architect review]" becomes `agent backlog upsert --status architect-review`
- [ ] _project/ files (tech-stack.md, testing-strategy.md, definition-of-done.md) remain as direct file reads — these are project constants, not planning artifacts
- [ ] src/ and tests/ remain as direct file access — these are code, not planning artifacts
- [ ] ADR creation remains file-based (docs/plan/_reference/adr/) — niche reference artifact
- [ ] PLAYBOOK.md Session Protocol is updated to reference CLI commands for artifact access, keeping direct file reads only for _project/ constants and code
## Out of Scope
- New CLI commands (the existing agent inbox/brief/backlog/decision commands are sufficient)
- Changes to the storage backend code or CLI implementation
- Moving _project/ files to Notion
- Moving ADRs to Notion
- Changing how agents interact with src/ and tests/ (code authoring stays file-based)
- Redesigning the backlog schema or Notion database structure
## Open Questions
- Should review findings use the existing --notes field on Task backlog rows, or do we need a dedicated review-findings field in the backlog schema?
- When implementation agent creates tasks from acceptance criteria, should it create one backlog row per criterion, or group them? Current tasks.md allows freeform grouping.
- The ideation skill says "scan src/ and docs/plan/ for prior-art" — the planning artifact part becomes CLI-only (agent brief list + agent backlog list), but scanning src/ is still valid since it is code. Should the instruction say "scan src/ for code overlap AND run agent brief list + agent inbox list for planning overlap"?
## Technical Approach
*Owned by architect agent.*
