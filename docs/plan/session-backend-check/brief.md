**Status: draft**
---
## Problem
The PLAYBOOK Session Start protocol reads tech-stack.md and testing-strategy.md but never reads _project/storage.yaml. Agents start a session without knowing the active backend, which leads to writing local docs/plan/ files directly when the backend is Notion — bypassing the CLI and creating artifacts invisible to other agents and the backlog.
## Goal
Every agent role reads _project/storage.yaml at session start and enforces CLI-only artifact access when the backend is Notion. The check is explicit in both the PLAYBOOK Session Start protocol and each role skill's pre-flight section, so no agent can miss it.
## Acceptance Criteria
## Non-Functional Requirements
## Out of Scope
## Open Questions
## Technical Approach
