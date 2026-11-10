# Board Setup Reference

Required GitHub Projects V2 configuration for a Briefcase Standard or Lite
board. Apply this when creating a new board or auditing an existing one.
The fields and views below are the minimum required by the workflow contract.
Existing legacy fields (prefixed `Legacy`) are migration history; never
re-create or populate them for new boards.

## Required fields

| Field name | Type | Used by | Purpose |
|---|---|---|---|
| Status | Single select | Both | Sole execution axis. See status options below. |
| Work Type | Single select | Both | `Idea`, `Feature`, `Task` |
| Priority | Single select | Both | `High`, `Medium`, `Low` |
| Stage | Single select | Both | `Requirements`, `Architecture`, `Build`, `Review`, `Deliver` |
| Review Verdict | Single select | Both | `Pending`, `Accepted`, `Changes requested`, `Blocked` |
| Requirements Link | Text | Both | URL to the canonical approved requirements document |
| Action Owner | Single select | Both | `Requirements`, `Architect`, `Build`, `Review`, `None` |
| Claim Session | Text | Both | The session or agent that has accepted this item |
| Blocking reason | Text | Both | One-line reason this item is Blocked; fill whenever Status → Blocked, clear on unblock |
| Resume Status | Single select | Both | The Status to restore when the item is unblocked; set at the same time as `Blocking reason` |
| Artifact Link | Text | Both | URL to the linked artifact or release record, when applicable |

Standard-only:

| Field name | Type | Purpose |
|---|---|---|
| Release Note Link | Text | URL to the release record once it exists |

## Status options

**Standard board:**

`Inbox` → `Technical shaping` → `Ready` → `In progress` → `In review` → `Done`

Also: `Blocked` (at any stage). `User requirement shaping` is a historical option
for exception cases only; do not create it on new boards.

**Lite board:**

`Inbox` → `Shaping` → `Ready` → `In progress` → `In review` → `Done`

Also: `Blocked`.

## Required views

Create all three views. Existing boards may use any name; the layout and grouping
are what matter.

### 1 — Feature delivery (Board layout)

- Layout: Board
- Group by: `Status`
- Shows Features and their child progress. Filter to `Work Type = Feature` for
  a clean PO read.

### 2 — Task execution (Board layout)

- Layout: Board
- Group by: `Status`
- Filter to `Work Type = Task`. Gives Build and Review a focused work queue.

### 3 — Dependency map (Roadmap layout)

- Layout: Roadmap
- Group by: `Parent issue`
- Marker field: `Status`
- Date field: use `Created` as start and `Updated` as end until a `Target date`
  field is added
- Purpose: shows the Feature → Task hierarchy and surfaces which tasks are
  waiting on which features. Required for PO dependency visibility.

A fourth **All items** (Table layout) is optional but useful for bulk field
edits and exports.

## Dependency relationships

Use native GitHub issue relationships — do not invent a custom field for this.

**Parent → child (Feature/Task hierarchy):**
Use GitHub sub-issues. A Task's `Parent issue` field links to its Feature.
The `Sub-issues progress` field on the Feature card shows % of child Tasks Done.

**Cross-item blocking:**
Use the native "blocked by / blocks" relationship in each issue's sidebar.
Fill `Blocking reason` on the blocked item so the reason is visible on the card
without opening the issue.

Do not close a parent Feature simply because one child Task finished.
Do not mark a Task Done while its `blocked by` dependency is not Done.

## Blocking reason protocol

Fill `Blocking reason` on every item when Status transitions to `Blocked`.
The value is a single short phrase naming the gap and owner, for example:

- `Product decision needed: scope boundary on mode switching (owner: PO)`
- `Dependency on #42 not Done`
- `Missing approved requirement revision`
- `Technical question unresolved (owner: Architect)`

Clear the field (set to empty) when the item is unblocked and transitions out
of `Blocked`. This keeps the Dependency map readable and lets the PO scan
blockers without opening individual cards.

## Creating a new board

1. Create the GitHub Project V2 (private for Standard; Lite may be public).
2. Add all required fields above via `createProjectV2Field` mutations or the
   GitHub UI. Use `TEXT` for text fields, `SINGLE_SELECT` for selects.
3. Add Status options in the order listed; do not add `User requirement shaping`
   to new Standard boards.
4. Create the three required views using `createProjectV2View` mutations or the
   GitHub UI.
5. Set the Roadmap view's group-by to `Parent issue` in the GitHub UI after
   creation (the API does not yet expose grouping configuration).
6. Record the new Project URL in the repository's `AGENTS.md` and backlog policy.

## Auditing an existing board

Check that all required fields exist. Run:

```
gh api graphql -f query='{ user(login: "<owner>") { projectV2(number: <n>) {
  fields(first: 30) { nodes { ... on ProjectV2FieldCommon { name dataType }
  ... on ProjectV2SingleSelectField { name options { name } } } } } } }'
```

Check that all three required views exist:

```
gh api graphql -f query='{ user(login: "<owner>") { projectV2(number: <n>) {
  views(first: 10) { nodes { name layout } } } } }'
```

For any missing field, add it with `createProjectV2Field`. For any missing view,
add it with `createProjectV2View`. Never delete existing fields or views that
active items reference.
