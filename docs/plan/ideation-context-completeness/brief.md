**Status: implementation-ready**
---
## Problem
The ideation agent sometimes closes inbox capture too early, missing key context the user provided. Bugs land without current-behavior descriptions, feature requests without concrete examples, and scope details get lost. This forces the architect or implementer to re-ask questions that were already answered in the original conversation.
## Goal
Add a Context Completeness Check to the ideation SKILL.md that the agent runs after every inbox/backlog capture. The check verifies four dimensions are present before the agent moves on: (1) current behavior / pain point, (2) desired behavior + examples, (3) motivation / why, (4) scope clarity — what changes, where it lives, any independent sub-changes.
## Acceptance Criteria
- [ ] skills/ideation/SKILL.md contains a Context Completeness Check section
- [ ] The check lists four required dimensions: current behavior, desired behavior + examples, motivation, scope clarity
- [ ] The check is positioned in the workflow after inbox add / backlog upsert capture steps
- [ ] If any dimension is missing, the agent must ask the user before proceeding
- [ ] The check applies to both inbox add captures and brief write drafts
## Non-Functional Requirements
Skill documentation change only. No code changes. No new dependencies.
## Out of Scope
Automated validation or linting of captured content. Changes to the CLI. Changes to other agent skills.
## Open Questions
Resolved: The check should be a hard gate for brief write drafts (all four dimensions required before creating a brief) and advisory for quick inbox add captures (flag missing dimensions but allow proceeding with a note in --notes about what's incomplete). Rationale: inbox is meant for fast capture of raw ideas — blocking it defeats the purpose. Briefs are the quality gate where completeness matters.
## Technical Approach
Single change to skills/ideation/SKILL.md:
Add a **Context Completeness Check** section after the Brainstorming Approach section. Contents:
1. Define the four dimensions as a checklist: (a) Current behavior / pain point — what is broken or missing today, (b) Desired behavior + examples — what it should look like, including any concrete examples the user provided, (c) Motivation — why this matters, who benefits, (d) Scope clarity — what changes, which files/layers, any independent sub-changes.
2. For inbox add: run the check after capture. If dimensions are missing, note gaps in --notes (e.g. '[incomplete: missing examples]') but do not block the capture.
3. For brief write: run the check before writing. If any dimension is missing, ask the user before proceeding. Do not create the brief until all four are covered.
4. Add a reference to this check in the Required Workflow steps (after step 5, before step 6) and in the Decision Rules section.
No code changes. This is a skill instruction update that changes agent behavior through prompt guidance.
