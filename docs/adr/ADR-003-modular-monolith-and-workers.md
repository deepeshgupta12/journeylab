# ADR-003 — Modular monolith plus isolated compute workers for the MVP

> Full ADR. Indexed in [DECISION_LOG](../product/02-delivery/DECISION_LOG.md) §1.
> Accepted ADRs are **superseded, never edited** — a reversal creates a new ADR
> that links back to this one.

- **Date:** 2026-08-05 · **Owner:** Product Architect · **Status:** Accepted (blueprint §9.117)
- **Context:** Blueprint names 14 service boundaries. Deploying 14 services at MVP adds operational cost without scaling need.
- **Decision:** Start as one deployable API application with enforced internal module boundaries, plus separately scaled solver, simulation and ingestion workers. Split only when scaling, ownership or failure isolation justifies it.
- **Consequences:** Module boundaries must be enforced in CI (import rules), otherwise the split becomes impossible later. Solver workers get explicit CPU/memory budgets.
- **Alternatives rejected:** Microservices from day one (premature); single process including solvers (a solver timeout would degrade API availability).

---

## Review trigger
See the entry above where stated; otherwise revisit when a dependent step is
implemented or a stated assumption is invalidated.

## Related
- [DECISION_LOG](../product/02-delivery/DECISION_LOG.md) — index of all decisions
- [ADR template](../product/09-templates/ADR_TEMPLATE.md)
- [00-START-HERE](../product/00-START-HERE.md)
