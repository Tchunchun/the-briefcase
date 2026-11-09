# Legacy Briefcase

The existing framework is retained as legacy while the unified product is
built alongside it. Legacy does not mean removed, migrated, or newly broken.

| Existing path | Purpose | Compatibility policy |
|---|---|---|
| `install.sh` | Existing full-framework installer | Existing invocations and installed consumers retain their behavior |
| `src/`, `skills/`, `template/` | Python CLI, five-role framework, and templates | Not the implementation base for the new GitHub-only product |
| `lite/` | Existing Markdown Lite workflow | Preserved, including its optional/local workflow |

The new product has Lite and Standard profiles over a shared workflow core.
Both new profiles use GitHub Issues + Projects through `gh`, separate-session
review, and explicit role invocation, without a required Briefcase Python
runtime. Do not mix the legacy playbook with new-profile instructions.

New work begins with [GitHub backlog setup](workflow/README.md). That bootstrap
is not yet a complete mode installer. Existing installations must not be
silently redirected to it, and existing Projects require explicit migration
before incompatible Status options can be changed.
