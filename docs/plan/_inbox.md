# Inbox

Append-only capture for ideas, bugs, requests, and follow-ups.

## Usage

- Add one line per item.
- Keep entries short.
- Do not prioritize or expand here.
- Mark an item `[-> architect review]` when the brief is created and ready for architect assessment.

## Entries

- [idea] Define escalation protocol: reverse-flow triggers for Review→Ideation (ambiguous criteria), Implementation→Architect (mid-build blocker), Review→Architect (unbuildable technical approach)
- [idea] Pluggable artifact storage with Local + Notion backends [-> architect review] → `docs/plan/artifact-storage/brief.md`
- [idea] Delivery-manager orchestrated mode (single user-facing agent delegating to implementation/review via existing framework) [-> architect review] → `docs/plan/delivery-manager-orchestrated-mode/brief.md`
- [idea] Redesign Notion project setup: unified Backlog (Idea/Feature/Task with per-type statuses, self-relation), standalone brief pages, Decisions with feature link, Templates page. Includes agent-reads-from-Notion architectural gap. [-> architect review] → `docs/plan/notion-project-setup/brief.md`
- [idea] Agent Artifact API: expose ArtifactStore as callable interface (CLI subcommands or lightweight API server) so agents can read/write artifacts directly without file-sync round-trips. Research MCP viability vs plain CLI/REST. [-> architect review] → `docs/plan/agent-artifact-api/brief.md`
- [idea] Slim AGENTS.md — cut to ≤60 lines; move repo tree, consumer setup, and changelog to README.md; add file-scoped commands and commit attribution [-> architect review] → `docs/plan/slim-agents-md/brief.md`
