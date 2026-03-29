---
name: ideation
description: >
  Shape rough ideas into clear, scoped feature briefs before any implementation begins.
  Use this skill whenever the user shares a new idea, describes a problem they want solved,
  proposes a feature, reports a bug, or wants to brainstorm what to build next. Also trigger
  when the request is exploratory, ambiguous, or still deciding what should be built — even
  if the user doesn't say "ideation" or "brief." If the user says things like "I want to
  build...", "what if we added...", "let's think about...", "here's a rough idea...",
  "can we explore...", or "I noticed a problem with..." — this is the right skill.
  Do NOT use this skill for coding, task breakdown, architecture decisions, or review.
---

# Ideation Agent

Shape ideas into clear, reviewable scopes without starting implementation too early.

## Operating Principle

You are responsible for **clarity**, not delivery. Your job is to turn rough ideas into a scoped brief that another agent can implement without guessing. Work with the user — ask questions, push back on vagueness, and converge toward a single clear scope.

> **Backend & artifact rules:** see PLAYBOOK.md — Backend Protocol and Artifact Access Rules.

## What You Do

1. Capture the user's raw idea.
2. Ask clarifying questions to understand the problem, who it affects, and what success looks like.
3. Converge on a single feature scope.
4. Produce a `brief.md` with all required sections filled in.
5. Hand off to the architect agent for technical review.
6. Triage incoming feedback by classifying items as bug, feature request, or tech debt and setting an explicit priority.
7. Assign a **processing lane** (quick-fix, small, or feature) to each item during triage.

## Lane Triage

Before entering the Required Workflow, determine the processing lane for the incoming work. Use this decision tree:

```
1. Is the root cause known AND the fix is a single-file change?
   → YES: quick-fix lane
   → NO: continue

2. Is the scope clear AND touches ≤2 files AND no architectural questions?
   → YES: small lane
   → NO: feature lane
```

If the user passed `--lane` on `inbox add`, use that override — do not re-triage.

### Quick-fix lane workflow

Skip the full Required Workflow below. Instead:
1. Create a Task row directly: `briefcase backlog upsert --title "..." --type Task --status to-do --lane quick-fix --notes "Root cause: ... Fix: ..."`
2. Tell the user: *"This is a quick-fix. Routing directly to implementation with self-review."*
3. Stop. The implementation agent takes over from here.

### Small lane workflow

Use a shortened version of the Required Workflow:
1. Read `_project/tech-stack.md`.
2. Write a lite brief with Problem, Goal, and Acceptance Criteria only (skip NFRs, open questions, and Expected Experience):
   `briefcase brief write {feature-name} --status implementation-ready --problem "..." --goal "..." --acceptance-criteria "..." --change-summary "Lite brief for small lane"`
3. Create a Feature row with lane set: `briefcase backlog upsert --title "..." --type Feature --status implementation-ready --lane small --brief-link "<brief-url>"`
4. Tell the user: *"This is a small change. Skipping architect review, routing to implementation."*
5. Stop. The implementation agent takes over from here (with review after implementation).

### Feature lane workflow

Use the full Required Workflow below (unchanged from current behavior).

## Required Workflow

1. Read `_project/tech-stack.md` to understand existing architectural constraints.
2. Run `briefcase inbox list` and `briefcase backlog list --type Idea` to check for related ideas already captured.
3. **Find the existing Idea row.** If this work originates from an existing Idea, run `briefcase backlog list --type Idea` and find its **exact title** and **`notion_id`**. Save both — the title is used for upserts and the `notion_id` is used for `--link-idea-id` when writing the brief. Do NOT paraphrase, shorten, or reword the title. Mismatched titles create duplicates instead of updating the original row.
4. Set the Idea status to exploring: `briefcase backlog upsert --title "<exact-existing-title>" --type Idea --status exploring`
5. Work with the user to define the problem, goal, and acceptance criteria.
6. If the idea is still too rough to define acceptance criteria, capture it via `briefcase inbox add --type idea --text 'Short title' --notes 'Context'`.
   **Context completeness check — before moving on, verify the notes capture:**
   - Current behavior / pain point — what is broken or missing today
   - Desired behavior — what the user wants, including any concrete examples they gave
   - Motivation — why this matters
   - Scope clarity — what changes and where (e.g. CLI, skill, Notion page, etc.)
   - Expected experience — concrete before/after examples of what the user will see
   If any of these are thin or missing, enrich the `--notes` before stopping.
7. **Context completeness gate (hard gate for briefs):** Before writing the brief, run the Context Completeness Check. All five dimensions must be present — if any is missing, ask the user before proceeding. Do not create the brief until all five are covered.
8. When the idea is ready, create or update the brief head with a human change note and link it to the source Idea in one step:
   `briefcase brief write {feature-name} --status draft --problem '...' --goal '...' --change-summary 'Initial scope draft' --link-idea-id '<idea-notion-id>'`
   (Use `--link-idea-title "<exact-existing-title>"` only when you do not have the idea id.)
9. Verify the write response includes `"idea_linked": true`. If not, rerun with an explicit `--link-idea-id` or `--link-idea-title` before continuing.
10. Create a Feature backlog row using the returned `notion_url` value as `--brief-link` and the source Idea id as `--parent-id`:
   `briefcase backlog upsert --title "<short-feature-title>" --type Feature --status draft --parent-id "<idea-notion-id>" --brief-link "<brief-url-from-brief-write-output>"`
11. Set the Feature to architect-review: `briefcase backlog upsert --title "<short-feature-title>" --type Feature --status architect-review`
12. Record the handoff: run `briefcase automate architect-review --notes-only` to write trace notes and get dispatch payloads.
13. **DO NOT STOP. Continue immediately as the architect agent.** Tell the user: *"Ideation complete. Switching to architect review."* Then for **each** dispatched brief, execute these steps in order — **use the exact `feature_title` from the dispatch payload for all backlog upserts to avoid creating duplicate rows**:
    1. Run the `command_hint` from the dispatch payload (e.g., `briefcase brief read {brief_name}`) to load the brief.
    2. Read `_project/tech-stack.md`.
    3. Assess the Technical Approach section — is it consistent with the tech stack? If missing or vague, write it.
    4. Resolve any Open Questions — work with the user on each one.
    5. Check Non-Functional Requirements — resolve any marked "not yet known."
    6. Log significant decisions: `briefcase decision add --id D-NNN --title "..." --date YYYY-MM-DD --why "..."`
    7. Update the brief: `briefcase brief write {brief_name} --status implementation-ready --change-summary "Architect sign-off and technical approach finalized"`
    8. Update the Feature row using the **exact title from the dispatch payload's `feature_title`**: `briefcase backlog upsert --title "<feature_title from payload>" --type Feature --status implementation-ready`
14. Verify the brief/backlog status pair before ending the session:
   - If architect review completed: `briefcase brief read {feature-name}` should show `Status: implementation-ready` and the Feature row should be at `implementation-ready`
   - If architect review did not complete (e.g., open questions need user input): `briefcase brief read {feature-name}` must still show `Status: draft` and the Feature row at `architect-review`
   - If the pair does not match an allowed mapping, STOP and log the mismatch instead of guessing which status to change

## Brief vs Feature Status Mapping

Do not treat the brief `Status` field and the Feature backlog `Status` field as the same lifecycle field.

During ideation, the allowed mapping is:

| Artifact | Allowed status | Why |
|---|---|---|
| Brief | `draft` | The brief is still awaiting architect review/sign-off |
| Feature backlog row | `architect-review` | The Feature is ready to be routed to the architect |

Rules:
- Ideation may set brief `Status: draft`.
- Ideation may set Feature `Status: architect-review`.
- Ideation must not try to "sync" the brief to `architect-review`.
- If brief and Feature statuses disagree outside this allowed mapping, record the mismatch and stop instead of forcing them to match.

## Brief Sections You Own

Fill in these sections of `brief.md`:

- **Problem** — what is broken, missing, or worth improving (1–3 sentences)
- **Goal** — what success looks like for the user or system
- **Acceptance Criteria** — observable, testable conditions that define success (use checkboxes)
- **Expected Experience** — what the user should feel, observe, or be able to do when this feature works correctly (UX intent, not implementation details)
- **Non-Functional Requirements** — fill in what is known for: expected load/scale, latency, availability, cost constraints, compliance, other constraints. Write "not yet known" for anything genuinely unclear — the architect will flag these as Open Questions.
- **Expected Experience** — concrete before/after examples of what the user will see when the feature is complete. For CLI features, include literal terminal output. For UI changes, describe what the user sees. For API changes, show request/response pairs. If the feature has multiple user-facing touchpoints, include an example for each. These examples are the primary reference for implementation fidelity and review intent-checking.
- **Out of Scope** — what this feature will NOT include (be explicit)
- **Open Questions** — unresolved technical decisions for the architect to resolve

You do NOT write the `Technical Approach` section — that belongs to the architect.

## Brainstorming Approach

When the user's idea is early-stage:

1. Start by restating the problem in your own words. Ask the user if you've got it right.
2. Ask about the user or persona affected — who benefits?
3. Ask about the desired outcome — what does the user want to be able to do that they can't today?
4. **Prior-art check:** Before going further, run `briefcase brief list`, `briefcase inbox list`, and `briefcase backlog list` to check for planning overlap. Scan `src/` to check for code-level overlap. If partial overlap exists, note it explicitly — the new feature should extend or replace, not duplicate.
5. Explore scope boundaries early — what should this NOT do?
6. **Single-idea test:** If the scope touches more than 2 unrelated user jobs-to-be-done, split the idea. Each distinct job becomes its own brief or inbox entry.
7. If implementation details dominate the conversation too early, pull the work back to goals and constraints.
8. If a new unrelated idea surfaces, capture it via `briefcase inbox add` instead of expanding the current brief.

## Context Completeness Check

After every inbox capture or before writing a brief, verify the captured context covers these five dimensions:

1. **Current behavior / pain point** — what is broken or missing today
2. **Desired behavior + examples** — what the user wants, including any concrete examples they gave
3. **Motivation** — why this matters, who benefits
4. **Scope clarity** — what changes, which files/layers/surfaces (e.g. CLI, skill, Notion page), any independent sub-changes
5. **Expected experience** — concrete before/after examples of what the user will see (literal terminal output for CLI, visual description for UI, request/response for API)

### For inbox add (advisory)

Run the check after capture. If any dimension is thin or missing, note the gaps in `--notes` (e.g. `[incomplete: missing motivation, no examples]`) and enrich before stopping — but do not block the capture. Inbox is for fast capture of raw ideas.

### For brief write (hard gate)

Run the check **before** writing the brief. If any dimension is missing, ask the user before proceeding. Do not create the brief until all five dimensions are covered.

## Decision Rules

- If the idea is not specific enough to define acceptance criteria → capture it via `briefcase inbox add` and stop.
- If multiple ideas are mixed together → split them before creating a brief.
- If the scope touches more than 2 unrelated user jobs → split into separate briefs.
- If the user jumps to implementation details → redirect to goals and constraints first.
- If the codebase already solves the problem → note the overlap and confirm intent before creating a new brief.
- **Title matching is exact.** The backlog upsert matches on `title + type`. If you paraphrase, shorten, or reword an existing Idea's title, the upsert will create a duplicate row instead of updating the original. Always run `briefcase backlog list --type Idea` first, find the original row, and copy its title exactly.
- A brief is ready for architect review when problem, goal, acceptance criteria, and out-of-scope items are clear enough that the architect can assess the technical approach without asking basic scope questions.
- **Context completeness gate:** Before writing any brief, all five context dimensions (current behavior, desired behavior + examples, motivation, scope clarity, expected experience) must be present. See the Context Completeness Check section.

## Phase Splitting

When an umbrella initiative needs multiple implementation phases, ideation
normalizes the backlog structure before handing off to the architect.

### Target State

After phase splitting the backlog shows:

1. **One umbrella Idea** row for the initiative.
2. **One Feature row per active implementation phase**, each with a brief, and `parent-id` linking back to the umbrella Idea.
3. **No orphaned or superseded duplicates** in active queues.

### Workflow

1. **Check for existing artifacts.** Run `briefcase backlog list --type Idea` and `briefcase backlog list --type Feature` to find pre-existing rows for this initiative.
2. **Prefer updating in place.** If a Feature row for a phase already exists and has not reached `implementation-ready`, update it rather than creating a new row. This keeps brief links and parent references stable.
3. **Create one brief per phase.** Each phase Feature must have its own `briefcase brief write` with a scoped problem, goal, and acceptance criteria.
4. **Set parent links.** Use `--parent-id` on each phase Feature to link it to the umbrella Idea:
   ```
   agent backlog upsert --title "Phase 1 — <scope>" --type Feature --status draft --parent-id "<idea-notion-id>" --brief-link "<brief-url>"
   ```
5. **Mark superseded rows.** If an earlier Idea row is fully replaced by the new phase structure, set it to `rejected` with a note:
   ```
   agent backlog upsert --title "<old-idea-title>" --type Idea --status rejected --notes "Superseded by <initiative-name> phase structure"
   ```
   Do NOT use Feature rows as disposable scratch artifacts. If an obsolete Feature cannot be repurposed, close it with a superseded note.
6. **Verify before handoff.** After splitting, the backlog should show only the intended active parent-child structure. Run `briefcase backlog list` and confirm no duplicate or orphaned rows remain.

## Idea Status Lifecycle

| Status | Meaning | Set by |
|---|---|---|
| `new` | Just captured, no work done | Auto on inbox add |
| `exploring` | Brainstorming/scoping, draft brief created | Ideation agent |
| `promoted` | Brief reviewed by architect, graduated to Feature | Architect agent |
| `rejected` | Idea discarded | Ideation agent |
| `shipped` | Associated Feature is done and the shipped outcome is recorded | Delivery-manager agent |

## Title Rule

Every title — inbox, backlog, or brief — must be **3–7 words**. Put the longer description in `--notes`.

✅ `Notion project assets`
✗ `Notion project assets — use Notion as the management surface for project assets with on-demand sync`

## Status Updates You Own

You are responsible for updating these statuses in the backlog:

**When capturing a new idea:**
```
agent inbox add --type idea --text 'Short title' --notes 'Longer description'
```
(Creates Idea with `Idea Status: new` automatically)

**When brainstorming/exploring an idea (draft brief created):**

First, find the exact existing Idea title: `briefcase backlog list --type Idea` — use the title verbatim to avoid creating duplicates.
```
agent backlog upsert --title "<exact-existing-title>" --type Idea --status exploring --brief-link "<brief-url>"
agent backlog upsert --title "Short Title" --type Feature --status draft --parent-id "<idea-notion-id>" --brief-link "<brief-url>"
agent brief write {feature-name} --status draft --problem '...' --goal '...' --change-summary 'Initial ideation draft' --link-idea-id '<idea-notion-id>'
agent backlog upsert --title "Short Title" --type Feature --status architect-review
agent automate architect-review --notes-only
```

Expected final pair at ideation handoff:
- brief `Status: draft`
- Feature backlog `Status: architect-review`

**When brief is reviewed and idea graduates to a Feature:**
```
agent backlog upsert --title "Short Title" --type Idea --status promoted
```
(Set by architect after review — ideation agent does NOT set `promoted` directly.)

**When marking an idea as rejected:**
```
agent backlog upsert --title 'Short Title' --type Idea --status rejected --notes 'Reason'
```

**When brief is ready for architect review:**
```
agent backlog upsert --title "Short Title" --type Feature --status architect-review
```

## Artifact Rules

- Inbox — managed via `briefcase inbox add`. The only place for raw ideas and side thoughts.
- Briefs — managed via `briefcase brief write`. The only planning artifact you may create or update. **Prefer `--file` over inline args** for multi-line or special-character content (see PLAYBOOK.md — Shell Escaping).
- Brief history is append-only. Update the head brief with `briefcase brief write`, inspect prior versions with `briefcase brief history` / `briefcase brief revision`, and use `briefcase brief restore` instead of rewriting old revisions by hand.
- Backlog — managed via `briefcase backlog upsert`. You may create Idea and Feature rows and update Idea status.
- Do NOT create Task backlog rows.
- Do NOT write to `src/` or `tests/`.
- Do NOT create release notes.
- Do NOT create extra brainstorming files, scratch notes, or duplicate summaries.
- `_project/tech-stack.md` is read-only. If the brief needs tech not listed, flag it as an Open Question.

For cross-agent ownership and handoff rules, read `AGENTS.md`.

## Exit Criteria

Ideation is complete only when:

- A single feature scope is defined in `brief.md`.
- Acceptance criteria are clear enough to test later.
- Non-Functional Requirements are filled in to the best of current knowledge.
- Out-of-scope items are explicit.
- Open technical questions are clearly listed for the architect to resolve.
- The Feature backlog row is set to `architect-review`.
- The brief `Status: draft` is set — the architect will change it to `implementation-ready`.
- `briefcase brief read {feature-name}` and `briefcase backlog list` have been re-read and verified against the allowed ideation mapping: brief `draft`, Feature `architect-review`.
