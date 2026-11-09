# Install Briefcase Lite

Lite is a Markdown workflow, not the full Briefcase CLI. You do not need
`install.sh`, Python, Notion, or a `.briefcase/` directory.

## Set up another project

1. Open the target project in your agent client. Commit or back up existing
   work. Use a Git repository with an initial commit and choose its shared
   planning branch, usually `main`.
2. Copy these files from this framework checkout:

   | Source | Destination in the target project |
   |---|---|
   | [PRODUCT.md](PRODUCT.md) | `PRODUCT.md` |
   | [tasks/task-template.md](tasks/task-template.md) | `tasks/task-template.md` |
   | [AGENTS.md](AGENTS.md) | `AGENTS.md` |

   Create `tasks/` if needed. If a destination already exists, merge the
   missing sections instead of overwriting it. In particular, keep the
   project's existing engineering rules in `AGENTS.md`. If your client reads
   `CLAUDE.md` instead, add an instruction there to read `AGENTS.md`.
3. Fill in the root `PRODUCT.md`: what the project does, product references,
   and the shared planning branch/PR base. Leave GitHub integration
   unconfigured unless you want it.
4. Commit the setup on the shared branch. If you want PRs, publish that branch
   and ensure CI checks it.
5. In your product chat, start with:

   > Run the requirements loop for [describe the idea or bug].

   After approving the resulting task, open a separate coding chat:

   > Run the build loop for tasks/[task-name].md.

   Then use a separate review chat:

   > Run the review loop for PR #[number].

   Without a PR, provide the task path and implementation commit instead.

## Optional: use GitHub issues and a board

Follow [Connect a GitHub Project](README.md#connect-a-github-project), then
record the repository and Project URL in the target project's `PRODUCT.md`.
Verify the agent can read and update the board before using issue-number
prompts. Without a configured board, use task-file paths even if a GitHub issue
is linked as context.

For the full workflow and review/merge gates, see [the Lite guide](README.md).
