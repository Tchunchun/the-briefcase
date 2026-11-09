# Briefcase Lite

Briefcase Lite is a workflow for turning product feedback into approved tasks
that coding agents can implement and hand back for review. It uses Markdown
and Git. A GitHub Project can provide a shared board and mobile feedback inbox.

## Set up a project

1. Copy [PRODUCT.md](PRODUCT.md) and [tasks/task-template.md](tasks/task-template.md)
   to the same paths in the consumer repo. If the project already has a product
   document, add the missing sections to it.
2. Add the [agent instructions](AGENTS.md) to the consumer repo's root
   `AGENTS.md` and preserve its existing engineering rules. If a client uses
   a different entry file such as `CLAUDE.md`, tell it to read `AGENTS.md`.
3. In `PRODUCT.md`, record the shared branch that holds the approved task
   queue and serves as the PR base. If it is a pilot branch, publish it before
   opening PRs against it and confirm the repository's CI covers that base.
   Commit the setup on the shared branch.

These files are the Lite setup. The full Briefcase installer is a separate
entry point.

## Run the two loops

1. In a product chat, say **“Run the requirements loop for [idea or bug].”**
   Review the proposed scope and acceptance criteria. After you approve them,
   the agent records a ready task and gives you the build prompt.
2. In a coding chat, say **“Run the build loop for tasks/example.md.”** The
   agent creates or resumes a task branch, implements the change, runs the
   agreed checks, and opens a PR when a remote base is available.
3. Review and merge the PR. Ask the product agent to confirm the merge and
   close out the task. Give independent tasks to separate sessions and
   worktrees. Assign only one active session to each task.

## Connect a GitHub Project

1. Enable Issues for the consumer repository. Create or select a Project
   linked to that repo. Configure a board grouped by **Status**, with **Inbox**,
   **Shaping**, **Ready**, **In progress**, **In review**, **Blocked**, and
   **Done**. Set the initial status to **Inbox** if available. Configure any
   automatic transitions to respect the approval and merge gates in the
   agent instructions.
2. Record the repository and board URL in `PRODUCT.md`. If agents use GitHub
   CLI to edit the board, authorize Projects access with
   `gh auth refresh -h github.com -s project` and verify access to the selected
   project before using the loops.
3. Add one issue per buildable task to the Project. Link the issue and its task
   file to each other. For issue-backed tasks, the board owns status and the
   task file owns scope and verification. Use Markdown status for local tasks.

From your phone, open the consumer repository's **Issues → New issue**. Add a
short title, what happened, and what you expected. Use synthetic examples for
sensitive data. Then say **“Run the requirements loop for GitHub issue #123.”**
The product agent adds the issue to the board if needed. To show new issues
automatically, configure the Project's auto-add workflow for that repository.
After approval, you can say **“Run the build loop for issue #123.”** Moving a
card to **Ready** makes it eligible for assignment. You start the build loop
with a prompt.
