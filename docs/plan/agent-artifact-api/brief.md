**Status: draft**
## Problem
Agents currently interact with planning artifacts through repo-local files or shelling out to the CLI, which is workable but awkward for richer automation and remote agent execution. The system already has an `ArtifactStore` abstraction, but there is no first-class callable surface for agents to use directly, so every integration has to choose between brittle file-sync patterns and ad hoc command execution.
## Goal
Define a first-class artifact access interface for agents that exposes the existing planning operations through a deliberate callable surface, while preserving the current storage abstractions and avoiding unnecessary coupling to a single transport.
## Acceptance Criteria
- [ ] The brief defines the scope of an agent-facing artifact access interface built on top of the existing `ArtifactStore` capabilities.
- [ ] The architect can evaluate at least the main interface options already identified in the backlog notes, including CLI subcommands versus a lightweight API service or similar callable surface.
- [ ] The design explains how agents will read and write briefs, backlog rows, inbox items, and related planning artifacts without relying on file-sync round trips.
- [ ] The proposal preserves backend independence so Local and Notion storage remain behind the same operational contract.
- [ ] The brief makes explicit what should remain out of scope in a first slice, such as broad workflow orchestration or a general-purpose remote control platform.
## Non-Functional Requirements
- **Expected load / scale:** single-project, low-concurrency agent interactions, but should support repeated read/write calls within one working session
- **Latency / response time:** artifact operations should feel close to current CLI responsiveness for common reads and writes
- **Availability / reliability:** the interface must fail clearly, preserve idempotent semantics where practical, and avoid corrupting planning artifacts across supported backends
- **Cost constraints:** prefer reusing the existing Python codebase and local execution model; avoid adding paid infrastructure or long-lived hosted dependencies unless strongly justified
- **Compliance / data residency:** planning metadata only; interface design must not expand secret exposure beyond existing backend credentials
- **Other constraints:** must build on the current `ArtifactStore` abstraction and respect role ownership rules in the playbook
## Out of Scope
- Replacing the storage backend layer itself
- Designing a full multi-tenant orchestration platform
- Solving arbitrary remote execution beyond artifact access
- Rewriting all existing agent workflows before an initial callable interface exists
## Open Questions
- Is the right first surface an expanded CLI contract, an embedded local API server, MCP-style tooling, or another minimal wrapper around `ArtifactStore`?
- How should authentication, process boundaries, and lifecycle be handled if the interface is not just local CLI execution?
- What operations need strong idempotency or transaction-like behavior versus best-effort CRUD semantics?
- How should the interface expose backend-specific limitations without leaking storage implementation details to agents?
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
