# ADR-007 — Decisions are resolved just-in-time at the step that needs them

> Full ADR. Indexed in [DECISION_LOG](../product/02-delivery/DECISION_LOG.md) §1.
> Accepted ADRs are **superseded, never edited** — a reversal creates a new ADR
> that links back to this one.

- **Date:** 2026-08-05 · **Owner:** Repository owner (user directive) · **Status:** Accepted
- **Context:** Eight decisions (`DEC-002` … `DEC-009`) are open. Forcing them all now would mean deciding region, cloud provider and identity vendor before the work that depends on them has surfaced any real constraints.
- **Decision:** Two linked rules.
  1. **Resolution timing.** A decision is resolved when its blocking step is reached, not before. Until then it stays open in §2 and the step stays `BLOCKED` in the tracker.
  2. **Resolution method — propose, then confirm.** When a step is reached, the implementer researches the options and puts a **specific recommendation with rationale** to the repository owner, who approves or overrides. The outcome becomes an ADR and closes the `DEC-*` entry.
- **Consequences:** Steps blocked on a decision cannot be marked `READY`, and unblocked steps proceed in parallel. The implementer carries the burden of a researched recommendation rather than an open question — an unresearched "which region?" is not an acceptable escalation. Decisions arrive later, so architecture must stay substitutable where it can (`ADR-003`, provider-independent interfaces).
- **Alternatives rejected:** Deciding everything upfront (guesses become commitments); building fully behind abstractions to defer indefinitely (`DEC-002` region and `DEC-007` residency genuinely block and cannot be abstracted away).

---

## Review trigger
See the entry above where stated; otherwise revisit when a dependent step is
implemented or a stated assumption is invalidated.

## Related
- [DECISION_LOG](../product/02-delivery/DECISION_LOG.md) — index of all decisions
- [ADR template](../product/09-templates/ADR_TEMPLATE.md)
- [00-START-HERE](../product/00-START-HERE.md)
