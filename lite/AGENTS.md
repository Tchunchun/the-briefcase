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
5. The product session marks the task Done and closes its issue after verifying
   that the implementation PR merged into the intended base. For a local
   repository, verify that the implementation landed on the shared branch.

Use `draft`, `ready`, `in-progress`, `in-review`, `blocked`, and `done` in
local task files. Keep credentials and sensitive records out of task files,
issues, and PRs.
