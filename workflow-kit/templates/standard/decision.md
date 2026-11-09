# Decision record

- Work item: `<issue URL and stable ID>`
- Decision ID: `<D-NNN or ADR-NNN>`
- Approved requirement revision: `<same revision as the Standard brief sign-off>`
- ADR link: `<path to docs/plan/_reference/adr/ADR-NNN.md, or "none">`
- Recorded by: `<architect>`
- Date: `<YYYY-MM-DD>`

## Decision

`<State the decision in one sentence: "We will [X] because [Y].">`

## Alternatives rejected

| Alternative | Why rejected |
|---|---|
| `<Option A>` | `<reason>` |
| `<Option B>` | `<reason>` |

Each alternative must have a stated rejection reason. At minimum, include every
alternative that was seriously evaluated before the decision was made.

## Consequences

**Positive:**
- `<benefit>`

**Negative / risks:**
- `<risk or cost>`

**Action items:**
- [ ] `<follow-up task, e.g. update tech-stack.md, migrate existing pattern>`

---

This record is append-only. Record supersession as a new entry referencing this
one; never overwrite a prior decision. The sign-off in the Standard brief names
this record's ID or ADR path.
