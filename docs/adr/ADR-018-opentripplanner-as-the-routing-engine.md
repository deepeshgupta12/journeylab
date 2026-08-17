# ADR-018 — OpenTripPlanner 2, self-hosted, is the routing engine

> Full ADR. Indexed in [DECISION_LOG](../product/02-delivery/DECISION_LOG.md) §1.

- **Date:** 2026-08-17 · **Owner:** Deepesh Kumar Gupta · **Status:** Accepted
- Proposed by the implementer at `STEP-005.05` under `ADR-007`'s propose-then-confirm
  rule; **confirmed by the repository owner the same day.**

## Context

`DEC-008` (routing provider) was flagged in `STEP-005.05` §4 with the instruction to
propose a provider with rationale once the sub-step was reached. It was reached, and
the sub-step deliberately did **not** block on it: the scope asked for a
provider-independent profile interface, and that is what shipped.

The binding constraint is `REQ-A11Y-003` plus this repository's prohibition on
substituting a walking route for a wheelchair one. A routing engine that cannot
answer step-free must be able to *say so*, and one that can answer must do it using
real kerb, lift and platform data.

## Decision

**OpenTripPlanner 2, self-hosted.**

## Consequences

### Why it fits

- It consumes **exactly the two feeds `ADR-016` already chose** — Swiss national
  GTFS and OpenStreetMap. No new data dependency, and no licence question beyond the
  ODbL one already open.
- It is the only open-source option that routes **transit and step-free together**,
  using GTFS accessibility fields alongside OSM kerb, lift and ramp tags. That is
  what `Profile.WHEELCHAIR` needs in order to be answerable at all.
- Zero licence spend, satisfying the constraint set for `DEC-002`.

### The cost, stated rather than buried

Self-hosting is an operational burden that **arrives before Phase 1**: graph builds
on every feed change, memory proportional to network size, and a service to keep
alive and monitored. This is the same shape as `ADR-015`'s Kafka decision and should
be understood as accepted with that cost in view, not on the licence argument alone.

It also couples to `DEC-007`: where the graph builder runs and how much memory it
gets is a deployment question nobody has answered.

### What it does not change

Nothing in `services/routing/src/matrix.py`. The interface is provider-independent
by design, `ProfileSupport` is a **declaration** a provider makes rather than
something inferred, and `resolve_profile` refuses rather than downgrades regardless
of which engine is behind it. Swapping engines changes a declaration and a client.

## Alternatives rejected

- **Valhalla** — lighter to operate and faster. Its pedestrian profile is not
  step-free routing, so `Profile.WHEELCHAIR` would have to be declared unsupported.
  That is *permitted* by `STEP-005.05`'s design and is exactly what the refusal path
  exists for — it is simply a worse product for the travellers who most need the
  answer.
- **OSRM** — no transit, no accessibility. Fast at the wrong problem.
- **A hosted routing API** — would breach the open-data, zero-spend constraint
  (`ADR-016`) and reintroduce the Open-Meteo trap: a free tier that is
  non-commercial.

## Review trigger

Operational load from graph builds proves disproportionate to Phase 1 volume; or
`DEC-007` selects a platform where hosting OTP is impractical; or OSM step-free
coverage in the chosen corridor turns out too sparse to answer with, in which case
the honest response is to declare `WHEELCHAIR` unsupported rather than to lower the
bar.

---

## Related
- [DEC-008](../product/02-delivery/DECISION_LOG.md) — the decision this closes
- [ADR-016](ADR-016-phase-1-destination-region.md) — the feeds this reuses
- [STEP-005.05](../product/08-steps/sub-steps/STEP-005/STEP-005.05-routing-adapter.md) · [BR-044](../product/10-logs/blast-radius/BR-044-routing-adapter.md)
