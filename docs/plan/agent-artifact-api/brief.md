# Agent Artifact API (v3)

**Status: implementation-ready**

---

## Problem

When Notion is the active backend, LLM agents (ideation, architect, implementation, review, delivery-manager) read and write local markdown files. This requires a sync-before / sync-after workflow — `agent sync local` to pull Notion → local, then `agent sync notion` to push changes back. The sync round-trip adds friction, risks stale reads if the user forgets to sync, and makes Notion feel like a secondary store rather than a live workspace. Agents should be able to interact with the artifact store directly, regardless of which backend is active.

## Goal

Expose the `ArtifactStore` protocol as CLI subcommands that LLM agents can invoke directly — routing transparently to whichever backend is active (local or Notion) via `_project/storage.yaml`. Agent skills get dual-mode instructions: CLI commands (primary, works with any backend) with file-path fallback (local backend only). The interface should work with any agent that has shell access (Claude Code, VS Code Copilot, OpenAI Codex, Gemini Code Assist).

## Acceptance Criteria

- [ ] CLI subcommands exist for every `ArtifactStore` method, outputting structured JSON
- [ ] `agent inbox list` → returns inbox entries as JSON
- [ ] `agent inbox add --type idea --text "..."` → appends an inbox entry
- [ ] `agent brief read <name>` → returns structured brief data as JSON
- [ ] `agent brief write <name> --file <path>` → creates or updates a brief
- [ ] `agent brief list` → returns brief summaries as JSON
- [ ] `agent decision list` → returns decisions as JSON
- [ ] `agent decision add --id D-NNN --title "..." --date YYYY-MM-DD --status accepted --why "..."` → appends a decision
- [ ] `agent backlog list` → returns backlog rows as JSON
- [ ] `agent backlog upsert --id T-NNN --type Feature --title "..." --priority High --status "To Do" --feature <name>` → creates or updates a backlog row
- [ ] All commands respect the active backend from `_project/storage.yaml` (local or Notion) transparently
- [ ] All commands return consistent JSON with `{"success": bool, "data": ..., "error": ...}` envelope
- [ ] Agent skills updated with dual-mode instructions: CLI commands (primary) with file-path fallback (local backend only)
- [ ] Error output goes to stderr; data output goes to stdout (for clean piping)
- [ ] Consumer projects using `backend: local` work with both CLI commands and direct file access
- [ ] Consumer projects using `backend: notion` work with CLI commands only (no local file dependency)

## Non-Functional Requirements

- **Expected load / scale:** Single-user CLI; < 5 API calls per invocation for Notion backend
- **Latency / response time:** CLI response < 2 s for local backend; < 5 s for Notion backend
- **Availability / reliability:** Graceful error messages when Notion API is unreachable; local backend always available
- **Cost constraints:** No new dependencies beyond existing stack (Click, notion-client, httpx)
- **Compliance / data residency:** Same as current — tokens in `.env` only, no PII
- **Other constraints:** Must not break existing `agent setup`, `agent sync` commands; CLI is the primary interface; MCP wrapper is optional/future

## Out of Scope

- MCP server implementation (`agent mcp serve`) — may be added as a follow-up if MCP ecosystem stabilizes (see Research Notes below)
- Changes to `ArtifactStore` protocol interface — commands wrap existing methods
- UI or web interface for artifacts
- Real-time sync or push notifications from Notion
- Template read/write CLI commands (low priority — templates rarely change)

## Open Questions

All resolved — see Technical Approach and `_project/decisions.md` (D-017 through D-020).

## Technical Approach

### Architecture

CLI subcommand groups wrapping the existing `ArtifactStore` protocol. Each command:
1. Calls `load_config()` → `get_store()` to get the active backend
2. Calls the corresponding `ArtifactStore` method
3. Outputs JSON to stdout with `{"success": true, "data": ...}` envelope
4. Outputs errors to stderr with `{"success": false, "error": "..."}`

```
agent inbox list       → store.read_inbox()       → JSON
agent inbox add        → store.append_inbox()      → JSON
agent brief list       → store.list_briefs()       → JSON
agent brief read <n>   → store.read_brief(n)       → JSON
agent brief write <n>  → store.write_brief(n, ...) → JSON
agent decision list    → store.read_decisions()    → JSON
agent decision add     → store.append_decision()   → JSON
agent backlog list     → store.read_backlog()      → JSON
agent backlog upsert   → store.write_backlog_row() → JSON
```

### CLI Structure

New Click command groups added to `src/cli/main.py`:

```python
cli.add_command(inbox)    # src/cli/commands/inbox.py
cli.add_command(brief)    # src/cli/commands/brief.py
cli.add_command(decision) # src/cli/commands/decision.py
cli.add_command(backlog)  # src/cli/commands/backlog.py
```

Each command module follows the same pattern:
```python
@click.group()
def inbox():
    pass

@inbox.command(name="list")
@click.option("--project-dir", default=".", ...)
def inbox_list(project_dir):
    store = _get_store(project_dir)
    data = store.read_inbox()
    _output({"success": True, "data": data})
```

A shared `_cli_helpers.py` provides `_get_store(project_dir)` and `_output(result)` to avoid duplication.

### Skill Dual-Mode Format (Decision D-017)

Each skill gets a standardized artifact access section:

```markdown
## How to Access Artifacts

**CLI (works with any backend — local or Notion):**
- List inbox: `agent inbox list`
- Add idea: `agent inbox add --type idea --text "description"`
- Read brief: `agent brief read {name}`
- List backlog: `agent backlog list`

**File paths (local backend only — fallback if CLI unavailable):**
- Inbox: `docs/plan/_inbox.md`
- Brief: `docs/plan/{name}/brief.md`
- Backlog: `docs/plan/_shared/backlog.md`
- Decisions: `_project/decisions.md`
```

Ownership rules and read/write permissions stay the same per role.

### Write Conflict Handling (Decision D-018)

- **Notion backend**: No conflict — CLI is the only write path. Agents cannot edit Notion by writing local files.
- **Local backend**: CLI commands write directly to the same markdown files that agents can edit. Both paths converge to the same files via `LocalBackend`. No conflict — they're equivalent operations on the same data.
- **Rule**: When backend is `notion`, agents MUST use CLI commands (file paths don't reach Notion). When backend is `local`, agents MAY use either CLI or file paths.

### Authentication (Decision D-019)

Existing pattern is sufficient: `NOTION_API_TOKEN` loaded from `.env` or environment variable by `NotionClient.__init__()`. No session cache needed — each CLI invocation is stateless. Token is never logged or echoed.

### Backlog Schema Translation (Decision D-020)

The CLI `agent backlog upsert` accepts parameters matching the Notion schema (the canonical form):
```
agent backlog upsert --title "Build login UI" --type Task --status to-do --priority High
```

For **local backend**: `LocalBackend.write_backlog_row()` translates to the local markdown table format (with ID, Use Case, Feature columns). Local-only fields default to empty if not provided.

For **Notion backend**: `NotionBackend.write_backlog_row()` writes directly to the unified Backlog database with type-specific status.

The CLI parameters match the Notion schema because Notion is the more structured/expressive format. The local backend's translator handles the downgrade to flat markdown. This keeps the CLI interface clean and forward-compatible.

Optional local-specific flags (for backward compatibility):
```
agent backlog upsert --title "..." --type Task --status to-do --id T-027 --feature calendar-chat-ops --use-case "Cancel events"
```
These are accepted by the CLI and passed through. `LocalBackend` uses them; `NotionBackend` ignores them (or maps `--feature` to `Parent` lookup).

### Files to Create/Modify

**New files:**
- `src/cli/commands/inbox.py` — inbox list/add subcommands
- `src/cli/commands/brief.py` — brief list/read/write subcommands
- `src/cli/commands/decision.py` — decision list/add subcommands
- `src/cli/commands/backlog.py` — backlog list/upsert subcommands
- `src/cli/helpers.py` — shared `_get_store()` and `_output()` helpers

**Modified files:**
- `src/cli/main.py` — register new command groups
- `skills/ideation/SKILL.md` — add dual-mode artifact access section
- `skills/architect/SKILL.md` — add dual-mode artifact access section
- `skills/implementation/SKILL.md` — add dual-mode artifact access section
- `skills/review/SKILL.md` — add dual-mode artifact access section
- `skills/delivery-manager/SKILL.md` — add dual-mode artifact access section

**Not modified:**
- `src/core/storage/protocol.py` — stable
- `src/integrations/notion/backend.py` — stable
- `src/core/storage/local_backend.py` — stable
- `src/core/storage/factory.py` — stable

### Cost Estimate

No new dependencies. All commands wrap existing `ArtifactStore` methods. Each command is ~20 lines of Click boilerplate + one method call. Total new code: ~300 lines across 5 command files + 1 helper.

---

## Research Notes: MCP vs CLI vs REST (March 2026)

### MCP Current Status

MCP is **not dead but under real pressure**. Massive corporate adoption (100+ remote servers — Notion, Figma, Slack, GitHub, Stripe) coexists with widespread practitioner frustration:

- **Context window bloat** is the #1 complaint. A single GitHub MCP server uses ~23% of context. Users loading multiple MCPs start at 50% context consumed before typing a prompt.
- **Tool count ceiling**: LangChain research found ~10 tools is optimal; more tools degrade model selection quality. Claude Code ships with ~17 built-in tools; adding MCP servers quickly exceeds this.
- **Transport protocol complexity**: Technical criticism of HTTP+SSE and "Streamable HTTP" as over-engineered vs WebSockets, with poor documentation and security concerns.
- **Perplexity's CTO** publicly dropped MCP internally (~March 2026), triggering fresh "MCP is dead" discourse.

### The Emerging Pattern: CLI-First

The community is converging on **CLI subcommands with JSON output** as the primary agent tool interface:

- Claude Code itself removed its built-in `ls` tool in favor of the CLI `ls` command — the direction is *more CLI, not more MCP*.
- OpenAI Codex ships with **only CLI tools** — no MCP.
- Claude Code's native integration path for project-local tools is bash commands described in `CLAUDE.md` or Skills, not MCP.
- CLI tools discovered via instructions cost **zero context tokens** until invoked; MCP tool schemas are loaded upfront.
- Works with **all agents** that have shell access, not just MCP-capable ones.

### When MCP Still Makes Sense

- Cross-boundary scenarios: web apps, mobile clients, security-sensitive workflows where shell access isn't available
- Service discovery across organizations (100+ corporate connectors)
- If this tool needs to work from Claude Desktop (no shell) or web-only chat

### Recommendation

**Primary: CLI subcommands wrapping `ArtifactStore` methods with `--format json` output.**

The existing Click CLI already has the right structure. Adding subcommand groups (`agent inbox`, `agent brief`, `agent backlog`, `agent decision`) that delegate to `get_store()` is straightforward.

**Future/optional: `agent mcp serve` command** that wraps the same methods as an MCP stdio server, reusing the existing protocol implementation. Only add this if MCP ecosystem stabilizes and a concrete use case requires non-shell access.

### Key Sources

| Source | Summary |
|---|---|
| r/ClaudeCode "MCP isn't dead — tool calling is what's dying" (Mar 2026) | Argues execution model is broken, not MCP itself; Cloudflare/Pydantic converging on code-execution mode |
| r/ClaudeAI "MCP: becoming irrelevant?" (597 upvotes) | Community consensus favoring Skills + CLI over always-on MCP |
| Perplexity CTO drops MCP (Mar 2026) | Triggered "will MCP be dead soon?" discourse |
| raz.sh "A Critical Look at MCP" | Transport/spec critique — HTTP+SSE over-engineered vs WebSockets |
| LangChain agent benchmarking | ~10 tools optimal; more degrades selection quality |
| Claude Code docs (code.claude.com) | Native path for project tools is bash + CLAUDE.md; MCP is for external services |
