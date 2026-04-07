**Status: draft**
---
## Problem
When implementation completes and a feature moves to review-ready, there is no automated signal to trigger the review agent. The delivery manager is responsible for this handoff, but agent automate has no review-dispatch subcommand. The gap means review work must be manually initiated, making it easy to let review-ready features sit unreviewed and blocking the rest of the ship pipeline.
## Goal
agent automate review-dispatch detects features newly entered into review-ready status and emits a dispatch payload, completing the forward-dispatch coverage alongside the existing architect-review and the planned implementation-dispatch commands.
## Acceptance Criteria
## Non-Functional Requirements
## Out of Scope
## Open Questions
## Technical Approach
