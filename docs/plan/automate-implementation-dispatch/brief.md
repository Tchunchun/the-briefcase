**Status: draft**
---
## Problem
When a feature reaches implementation-ready there is no automated signal to trigger the implementation agent. The delivery manager is expected to detect this transition and route the work, but agent automate only covers the ideation to architect step. Every other forward transition requires a manual invocation, creating a gap in the orchestrated mode flow and making it easy to miss features that are ready to build.
## Goal
agent automate implementation-dispatch detects features newly entered into implementation-ready status, emits a structured dispatch payload, and optionally shells out to a configurable command — exactly mirroring the existing architect-review automation — so that implementation work starts without manual polling.
## Acceptance Criteria
## Non-Functional Requirements
## Out of Scope
## Open Questions
## Technical Approach
