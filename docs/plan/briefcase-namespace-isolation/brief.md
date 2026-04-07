**Status: implementation-ready**
## Problem
When this framework is installed into a consumer project, its `src/` folder collides with the consumer's own `src/core/`. Skill path references also break because the framework uses `.skills/` internally but consumer projects install to `.briefcase/skills/`. These two issues share a root cause: framework code has no dedicated namespace and bleeds into consumer project structure.
## Goal
All framework code (CLI, storage backends, skills, templates) ships inside a single `.briefcase/` folder. Consumer projects gain an isolated namespace: their `src/`, `tests/`, and `docs/` are never touched by the framework. The framework repo itself defines what the post-install `.briefcase/` layout looks like.
## Acceptance Criteria
- [ ] Target `.briefcase/` layout is defined and documented: `.briefcase/src/`, `.briefcase/skills/`, `.briefcase/template/`, with no framework files written into consumer-owned folders during install
- [ ] Skill `SKILL.md` files reference paths using `.briefcase/skills/` consistently for consumer installs
- [ ] PLAYBOOK.md and AGENTS.md reference `.briefcase/` as the canonical install location/runtime sentinel for consumer projects
- [ ] The framework repo documents the mapping from source repo folders to installed `.briefcase/` subfolders
- [ ] No framework file is written into consumer `src/`, `tests/`, `docs/`, or any other consumer-owned folder
- [ ] Config and runtime resolution paths are compatible with `.briefcase/` layout and do not assume `src/` is at project root
## Out of Scope
Writing the install script itself (that is the install script brief); implementing the `./agent` entry point behavior in full (separate brief); migrating existing consumer projects already installed under the old layout; renaming the framework repo's own `src/`, `skills/`, or `template/` folders in this repository
## Open Questions
All resolved. The framework repo keeps its current source layout and `.briefcase/` exists only as a post-install artifact, `.briefcase/storage.yaml` is the runtime config location and project sentinel, and consumer-owned engineering docs remain in `_project/` rather than moving into `.briefcase/`.
## Technical Approach
Treat `.briefcase/` as an installed runtime namespace, not as a source-repo reorganization. The framework repo continues to develop and test from its existing root folders (`src/`, `skills/`, `template/`), while install maps those folders into `.briefcase/src/`, `.briefcase/skills/`, and `.briefcase/template/` inside consumer projects.
Use `.briefcase/` as the single runtime/config sentinel. Config resolution for consumer installs should read `.briefcase/storage.yaml`, and entry-point discovery should walk up to `.briefcase/` rather than relying on `_project/` as the framework sentinel. This keeps `_project/` consumer-owned for engineering governance artifacts such as tech stack, testing strategy, and decisions.
Framework-owned runtime files must stay inside `.briefcase/` except for the generated `./agent` wrapper at project root. That means no copying framework code into consumer `src/`, `tests/`, or `docs/`, and no assumptions that the framework's Python package lives at project root.
This decision also sets the ownership boundary for a Notion-first workflow: Notion owns PM and operational artifacts, while local Git continues to own source-controlled implementation assets and engineering-governance docs. No new dependencies are required and there is no new cloud cost because this is a layout and ownership decision, not a new service.
