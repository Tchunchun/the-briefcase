**Status: draft**
---
## Problem
The Notion backlog write path always includes the Automation Trace property, but some provisioned backlog databases do not actually have that property. In those workspaces, backlog upserts fail with a Notion property error, which blocks agent routing and backlog maintenance until the schema is repaired.
## Goal
Define the smallest safe fix that guarantees Notion-backed backlog updates are not blocked by a missing Automation Trace property on newly provisioned or existing workspaces.
## Acceptance Criteria
- [ ] The brief identifies why Automation Trace can be missing from a provisioned Notion backlog even though backlog writes expect it.
- [ ] The scoped fix ensures backlog upserts no longer fail solely because the Automation Trace property is absent.
- [ ] The architect can evaluate whether the fix should live in provisioning, upgrade-repair, write-path tolerance, or a combination of those paths.
- [ ] Validation expectations include regression coverage for the schema expectation and the affected backlog upsert path.
## Non-Functional Requirements
- **Expected load / scale:** low-frequency CLI and agent backlog writes against a single Notion workspace at a time
- **Latency / response time:** any schema validation or repair should remain small relative to current Notion API calls
- **Availability / reliability:** missing schema must not leave core backlog operations blocked; any repair path should stay additive and idempotent
- **Cost constraints:** no new services or persistent infrastructure
- **Compliance / data residency:** planning metadata only; must not broaden credential or workspace-data exposure
- **Other constraints:** stay compatible with the current Python CLI, Notion backend, and existing workspace upgrade flow
## Out of Scope
- Redesigning the full Notion schema-health system
- Changing the meaning or format of automation trace data
- Reworking unrelated backlog properties or board views
## Open Questions
- Should backlog writes tolerate a missing Automation Trace property temporarily, or should the system require immediate schema repair before writing?
- Should provisioning alone be fixed, or must upgrade/repair also backfill existing workspaces that already lack the property?
## Technical Approach
