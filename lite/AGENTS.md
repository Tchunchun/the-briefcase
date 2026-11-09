# Briefcase Lite

Read the project's [PRODUCT.md](PRODUCT.md) for context and its shared
planning branch, and use [the task template](tasks/task-template.md) for new
tasks. Work from the latest committed version of the shared branch. Apply the
project's engineering, testing, and review rules throughout.

For tasks linked to GitHub Projects, the board's **Status** field is
authoritative. Use one issue per task and link the issue and the committed
task file to each other. Keep scope, dependencies, and verification in the
task file. Report any board access failure before dispatching issue-backed
work. For local tasks, use the Markdown status.

## Requirements loop

When the user says **“Run the requirements loop”**, shape the requested
feature, bug, or feedback into an independently verifiable task.

1. Read the relevant product references, existing tasks, and the source issue
   if supplied. Check for duplicates. Add new feedback issues to the board
   if connected. With no topic, surface open decisions or suggest small
   candidates from the inbox or backlog.
2. Clarify who is affected, what happens today, and what should happen next.
   Agree on scope boundaries and a concrete example. Draft acceptance criteria,
   a verification plan, and dependencies by task path. Use `draft` or
   **Shaping** while defining scope, and record the decision needed if blocked.
3. Present the scope and criteria for approval. After approval, record durable
   decisions in `PRODUCT.md` and save the task on the shared branch through
   the project's normal Git workflow. For a local task, record `ready` in the
   task file. For an issue-backed task, remove the Markdown status, publish
   and link the committed task, and then move the issue card to **Ready**.
4. Give the user the build prompt with the exact issue number or task path.
   For blocked work, return it to Ready only after resolving the blocker.

## Build loop

When the user says **“Run the build loop”**, process assigned tasks one at a
time. Naming a task or issue assigns it to the session.

1. Before each task, read the latest task and product decisions. Check that
   the task is Ready and its dependencies are Done. Check the issue, branch,
   and open PRs for an existing assignment or implementation before
   claiming it. Resume existing work only when explicitly assigned to do so.
   Stop when no eligible assigned work remains.
   For review fixes, resume the existing task, move it to In progress, and
   reuse its branch and PR. Address each blocker, rerun the affected checks,
   and return the task to In review with the new commit and verification.
2. Record the claim on the shared task or move the board card to **In progress**.
   Use a dedicated branch and worktree from a revision containing the task.
   Reuse the task branch when resuming. Keep product decisions with the
   product session. Coordinate before assigning parallel changes to the same
   area.
3. Implement within scope and run the agreed checks. If a decision blocks
   progress, record the question on the issue or shared task, mark it Blocked,
   and continue with independent assigned tasks.
4. Commit the verified change, push the task branch, and open a PR against the
   configured shared branch if remote access is available. Reference the
   issue, record the PR and checks, and mark the task In review once the PR
   exists. If PR creation is unavailable, report the local commit and checks.
   Leave the PR open for review.
5. Hand off the PR or local implementation commit to a separate review
   session. The product session marks the task Done and closes its issue
   after confirming that the reviewed changes were accepted and landed on
   the intended base.

## Review loop

When the user says **“Run the review loop for PR #123”**, review the named PR
in a separate session from the one that implemented it. For local work, use
the task path and implementation commit.

1. Identify the PR base and head commit. Find the linked task and read the
   approved version from the shared branch. Use its scope, acceptance
   criteria, verification plan, and linked decisions as the review baseline.
   Read the source issue for context. Send missing or conflicting requirements
   to the product session to resolve.
2. Read the diff and relevant surrounding code. Check each acceptance
   criterion against observable behavior or test evidence. Look for scope
   drift, regressions, and meaningful gaps in tests. Inspect CI for the
   reviewed commit and run focused checks where needed. Record checks you
   could not perform. If the PR head changes before the verdict, review
   the new changes and refresh the evidence.
3. Report the reviewed commit, evidence for each criterion, and findings.
   For each finding, give its severity, file and line or reproduction steps,
   expected and actual behavior, and how to verify the fix. Separate merge
   blockers from suggestions.
4. Give one verdict:
   - **Accepted** when the requirements are verified, required checks pass,
     and no blockers remain. Leave the task In review until merge.
   - **Changes requested** for blockers within approved scope. Hand them
     back to the coding session to fix on the existing PR.
   - **Blocked** when a product decision or required evidence is missing.
     Route scope questions to the product session and missing evidence to
     whoever can provide it.
5. Return the verdict in chat. If asked to publish the review, record it on
   the PR. Update the board when authorized. Use In progress when the fix
   is assigned and Blocked when a decision or evidence prevents review. If GitHub
   disallows formal approval from the authenticated account, report the
   verdict and leave formal approval to an eligible reviewer. On re-review,
   check the fixes and any other changes before accepting the new head.

The review session owns the verdict, the coding session owns fixes, and
the product session owns changes to approved scope. Merge follows the
project's normal approval process.

Use `draft`, `ready`, `in-progress`, `in-review`, `blocked`, and `done` in
local task files. Keep credentials and sensitive records out of task files,
issues, and PRs.
