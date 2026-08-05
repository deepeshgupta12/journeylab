# ADR-008 — Sub-step files are written just-ahead-of-need

> Full ADR. Indexed in [DECISION_LOG](../product/02-delivery/DECISION_LOG.md) §1.
> Accepted ADRs are **superseded, never edited** — a reversal creates a new ADR
> that links back to this one.

- **Date:** 2026-08-05 · **Owner:** Repository owner (user directive) · **Status:** Accepted
- **Context:** The 28 steps decompose into **228 sub-steps**. Writing all of them now would produce ~186 files describing work whose shape depends on decisions not yet made.
- **Decision:** Sub-step files for the **foundation chain (`STEP-002` … `STEP-006`, 42 files)** are written upfront because that work is well-determined. Sub-steps for `STEP-007` … `STEP-028` are created when their step moves `READY` → `IN_PROGRESS`, and must exist and be reviewed **before** that step's first line of code.
- **Consequences:** The full sub-step layer is never visible as one artifact until late; the tracker and each step's §21 table carry the plan in the interim. In exchange, sub-step files describe real work rather than speculation.
- **Alternatives rejected:** Generating all 228 upfront (speculative rewrites once `DEC-002`/`DEC-004`/`DEC-007`/`DEC-009` land).

---

## Review trigger
See the entry above where stated; otherwise revisit when a dependent step is
implemented or a stated assumption is invalidated.

## Related
- [DECISION_LOG](../product/02-delivery/DECISION_LOG.md) — index of all decisions
- [ADR template](../product/09-templates/ADR_TEMPLATE.md)
- [00-START-HERE](../product/00-START-HERE.md)
