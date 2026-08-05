# ADR-010 — Repository ownership assigned to a single accountable owner

> Full ADR. Indexed in [DECISION_LOG](../product/02-delivery/DECISION_LOG.md) §1.
> Accepted ADRs are **superseded, never edited** — a reversal creates a new ADR
> that links back to this one.

- **Date:** 2026-08-05 · **Owner:** Deepesh Kumar Gupta · **Status:** Accepted
- **Context:** `BLK-001` — no step, document or gate had a named owner. Every step file carried `owners: []`, no exit gate could be signed off, and `STEP-001.03` was hard-blocked because `CODEOWNERS` cannot be written without a name. This was the highest-exposure realised risk in the register (`RISK-011`, exposure 20).
- **Decision:** **Deepesh Kumar Gupta** (GitHub `@deepeshgupta12`) is the named owner for all roles, paths and gates until the team grows.
- **Consequences:**
  - `BLK-001` is **closed**; steps may now leave `READY` and gates can be signed off.
  - `CODEOWNERS` gains a catch-all owner, unblocking `STEP-001.03`.
  - **A single owner cannot satisfy four-eyes approval** (`REQ-ADMIN-002` high-impact fact overrides, `SC-GOV-02`). That control is now **structurally unsatisfiable** and is recorded as a live gap, not quietly dropped — it must be resolved before `STEP-021` ships, either by a second reviewer or by an explicit accepted-risk decision.
  - The same person authoring and approving a change conflicts with `WAYS_OF_WORKING` §3 ("the author may never approve their own change"). Pragmatic for a solo repository, but it means review is a self-check, and the automated gates carry proportionally more weight.
- **Alternatives rejected:** Leaving ownership unassigned (blocks all progress); inventing placeholder owners (fabricates accountability that does not exist).
- **Review trigger:** A second contributor joins, or `STEP-021` reaches implementation.

---

## Review trigger
See the entry above where stated; otherwise revisit when a dependent step is
implemented or a stated assumption is invalidated.

## Related
- [DECISION_LOG](../product/02-delivery/DECISION_LOG.md) — index of all decisions
- [ADR template](../product/09-templates/ADR_TEMPLATE.md)
- [00-START-HERE](../product/00-START-HERE.md)
