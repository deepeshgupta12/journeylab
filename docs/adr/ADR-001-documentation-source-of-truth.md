# ADR-001 — Documentation is the source of truth before code exists

> Full ADR. Indexed in [DECISION_LOG](../product/02-delivery/DECISION_LOG.md) §1.
> Accepted ADRs are **superseded, never edited** — a reversal creates a new ADR
> that links back to this one.

- **Date:** 2026-08-05 · **Owner:** Documentation lead · **Status:** Accepted
- **Context:** No application code exists. Work must be specifiable and reviewable before implementation.
- **Decision:** `docs/product/` is the operational source of truth for scope, contracts, architecture and delivery status. Markdown explains contracts; when machine-readable contracts exist (`contracts/openapi.yaml`), those become authoritative for schemas and Markdown must link rather than duplicate.
- **Consequences:** Documentation drift becomes a release blocker (`REQ-PLAT-009`). Every contract in [API_CONTRACTS](../04-contracts/API_CONTRACTS.md) is marked `PROPOSED` until a schema file exists.
- **Alternatives rejected:** Code-first with documentation after (loses the pre-change impact discipline required by `REQ-KG-008`).

---

## Review trigger
See the entry above where stated; otherwise revisit when a dependent step is
implemented or a stated assumption is invalidated.

## Related
- [DECISION_LOG](../product/02-delivery/DECISION_LOG.md) — index of all decisions
- [ADR template](../product/09-templates/ADR_TEMPLATE.md)
- [00-START-HERE](../product/00-START-HERE.md)
