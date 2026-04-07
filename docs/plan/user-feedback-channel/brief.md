**Status: implementation-ready**
---
## Problem
User feedback has no defined channel. The old _project/feedback/ folder bypassed the inbox pipeline, had no lifecycle tracking, and lived in architect-owned space. Users don't know how to submit bugs or feature requests.
## Goal
Establish briefcase inbox add as the single feedback entry point. Ideation agent triages incoming feedback (bug vs feature request vs tech-debt) and routes it through the standard workflow pipeline. Users see clear instructions in README and post-install output.
## Acceptance Criteria
- [ ] README contains a Feedback section with examples for bug, feature request, and tech-debt submissions
- [ ] install.sh post-install output includes a Feedback block pointing users to briefcase inbox add
- [ ] _project/feedback/ folder is deleted
- [ ] All previously open items from the feedback file are captured in the inbox
- [ ] Ideation skill SKILL.md documents triage responsibility for incoming feedback
## Non-Functional Requirements
No new dependencies. Documentation and workflow change only.
## Out of Scope
Automated feedback routing or classification. GitHub Issues integration. Feedback form UI.
## Open Questions
Resolved: The existing capture-and-classify flow in the ideation skill is sufficient. Add a short Feedback Triage paragraph to SKILL.md under What You Do to make the responsibility explicit, but no new named workflow step is needed.
## Technical Approach
Three file changes: (1) README.md — add Feedback section between Usage and How It Works with three example commands (bug, feature, tech-debt). (2) install.sh — append Feedback block to post-install summary output. (3) skills/ideation/SKILL.md — add a Feedback Triage paragraph under What You Do clarifying that the ideation agent triages incoming feedback by classifying items as bug/feature/tech-debt and setting priority. Deletion of _project/feedback/ and inbox capture of open items are pre-work already completed.
