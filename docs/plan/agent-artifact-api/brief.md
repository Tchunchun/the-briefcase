# Agent Artifact API (v3)

**Status: draft** `[-> architect review]`

---

## Problem

When Notion is the active backend, LLM agents (ideation, architect, implementation, review, delivery-manager) read and write local markdown files. This requires a sync-before / sync-after workflow — `agent sync local` to pull Notion → local, then `agent sync notion` to push changes back. The sync round-trip adds friction, risks stale reads if the user forgets to sync, and makes Notion feel like a secondary store rather than a live workspace. Agents should be able to interact with the artifact store directly, regardless of which backend is active.

## Goal

Expose the `ArtifactStore` protocol as a set of callable interfaces that LLM agents can invoke directly during a session — eliminating the sync step for reads and writes. The interface should work with any agent that has shell access (Claude Code, VS Code Copilot, OpenAI Codex, Gemini Code Assist) and optionally with MCP-capable clients.

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
- [ ] Agent skills can be updated to use CLI commands instead of file paths (optional, non-breaking — file access still works)
- [ ] Error output goes to stderr; data output goes to stdout (for clean piping)

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

- **Skill file updates**: Should agent skills be updated to prefer CLI commands over file paths? This would mean changing instructions like "Read `docs/plan/_inbox.md`" to "Run `agent inbox list`". This is a behavior change across all five skills. The architect should assess whether this is a separate brief or part of this one.
- **Write conflict handling**: If an agent reads via CLI (from Notion) and writes via CLI (to Notion), but also writes local files during the same session, which version wins? The architect should define the precedence rule.
- **Authentication flow**: CLI commands calling Notion need the API token. Currently loaded from `.env` / environment variable. Confirm this is sufficient or whether a session-based auth cache is needed.

## Technical Approach

*Owned by architect agent.*

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
