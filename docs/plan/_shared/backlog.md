# Backlog

Cross-feature source of truth for task priority and execution status.

| ID | Type | Use Case | Feature | Title | Priority | Status | Notes |
|---|---|---|---|---|---|---|---|
| T-001 | Feature | Agents need a stable interface to read/write artifacts regardless of backend | artifact-storage | Define ArtifactStore + SyncableStore protocols | High | Done | 7/7 tests pass |
| T-002 | Feature | CLI and agents need to know which backend is active | artifact-storage | Implement storage config loader (storage.yaml) | High | Done | 10/10 tests pass |
| T-003 | Feature | Existing workflow must work through the new interface | artifact-storage | Implement LocalBackend (markdown files) | High | Done | 15/15 tests pass |
| T-004 | Feature | Users choose their backend during project setup | artifact-storage | Factory + `agent setup` CLI (local backend) | High | Done | 7/7 tests pass; Phase 1 complete (39/39 total) |
| T-005 | Feature | Notion backend needs a clean API client layer | artifact-storage | Notion API client wrapper | Medium | Done | 12/12 tests pass |
| T-006 | Feature | Setup must provision Notion workspace automatically | artifact-storage | Notion schemas + provisioner | Medium | Done | 15/15 tests pass |
| T-007 | Feature | Agents read/write artifacts in Notion via the interface | artifact-storage | NotionBackend (ArtifactStore + SyncableStore) | Medium | Done | 15/15 tests pass |
| T-008 | Feature | Users set up Notion backend with one CLI command | artifact-storage | `agent setup --backend notion` CLI extension | Medium | Done | Tested in T-004 setup tests |
| T-009 | Feature | Users generate local markdown from Notion for git audit | artifact-storage | `agent sync local` command + sync logic | Medium | Done | Sync logic + CLI implemented |
| T-010 | Feature | Non-technical users edit templates in Notion and sync back | artifact-storage | `agent sync templates` command | Low | Done | Template sync + version comparison implemented |
| T-011 | Feature | Teams need explicit orchestration across role handoffs | delivery-manager-handoffs | Add delivery-manager routing + handoff checkpoints to PLAYBOOK | High | Done | PLAYBOOK updated for fifth role + orchestration sequence; delivery-manager routed feature to review on 2026-03-16 14:12 PT |
| T-012 | Feature | Orchestration behavior needs explicit, reusable role guidance | delivery-manager-handoffs | Create `skills/delivery-manager/SKILL.md` | High | Done | New skill includes packet contract, checklists, and escalation |
| T-013 | Feature | Handoffs need a consistent data format across transitions | delivery-manager-handoffs | Standardize handoff packet + review verdict in tasks template | Medium | Done | `template/tasks.md` updated with handoff and verdict sections |
| T-014 | Feature | Users need a single interface for implementation + delivery flow | delivery-manager-orchestrated-mode | Add orchestrated mode and mode toggle documentation in PLAYBOOK | High | Done | Added explicit single-entrypoint behavior and orchestrated/manual mode rules; review accepted on 2026-03-16; delivery-manager closed orchestration on 2026-03-16 14:33 PT |
| T-015 | Feature | Delivery-manager should delegate work using existing role skills | delivery-manager-orchestrated-mode | Define delivery-manager dispatch, retry, and escalation contract | High | Done | Delivery-manager skill now specifies subagent dispatch and retry/blocked escalation; delivery-manager routed accepted review to implementation ship path on 2026-03-16 14:30 PT |
| T-016 | Feature | Existing role skills need orchestrated-mode compatibility notes | delivery-manager-orchestrated-mode | Update implementation/review skills for delivery-manager delegation path | Medium | Done | Added delegated invocation notes while preserving ownership boundaries; shipped with release-notes addendum on 2026-03-16 |

## Rules

- `ID`: unique task identifier, prefixed with `T-`
- `Type`: `Feature`, `Tech Debt`, or `Bug`
- `Use Case`: user scenario or job-to-be-done
- `Feature`: matches `docs/plan/{feature-name}`
- `Title`: short, action-oriented task name
- `Priority`: `High`, `Medium`, or `Low`
- `Status`: `To Do`, `In Progress`, `Done`, or `Blocked`
- `Notes`: blockers, context, dependencies, or meaningful test outcomes

**Type guidance:**
- `Feature` — new user-facing capability or planned behaviour from a `brief.md`
- `Tech Debt` — internal improvement with no user-visible change (refactor, dependency upgrade, test coverage gap). Log the item in `_inbox.md` first; the ideation agent decides whether to promote it to a brief.
- `Bug` — deviation from an existing, accepted acceptance criterion

Backlog state must match reality, not intent.
