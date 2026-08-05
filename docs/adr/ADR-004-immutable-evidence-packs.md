# ADR-004 — Immutable evidence packs as solver input

> Full ADR. Indexed in [DECISION_LOG](../product/02-delivery/DECISION_LOG.md) §1.
> Accepted ADRs are **superseded, never edited** — a reversal creates a new ADR
> that links back to this one.

- **Date:** 2026-08-05 · **Owner:** Data Architect · **Status:** Accepted (blueprint §10.140)
- **Context:** `REQ-CONS-006` requires reproducible scenario runs. Live provider data is not reproducible.
- **Decision:** An `EvidencePack` is assembled, versioned and frozen before solving. Solvers read only from the pack, never from arbitrary web content or live provider calls.
- **Consequences:** Requires cache rights from providers (`ASM-019`). Stale packs must be detected and rebuilt. Storage grows per generation run and needs a retention policy.
- **Alternatives rejected:** Live provider calls during solve (unreproducible, latency-unbounded, quota-fragile).

---

## Review trigger
See the entry above where stated; otherwise revisit when a dependent step is
implemented or a stated assumption is invalidated.

## Related
- [DECISION_LOG](../product/02-delivery/DECISION_LOG.md) — index of all decisions
- [ADR template](../product/09-templates/ADR_TEMPLATE.md)
- [00-START-HERE](../product/00-START-HERE.md)
