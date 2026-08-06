# ADR-006 — Commit messages carry no AI co-authorship attribution

> Full ADR. Indexed in [DECISION_LOG](../product/02-delivery/DECISION_LOG.md) §1.
> Accepted ADRs are **superseded, never edited** — a reversal creates a new ADR
> that links back to this one.

- **Date:** 2026-08-05 · **Owner:** Repository owner (user directive) · **Status:** Accepted
- **Context:** Default tooling appends a `Co-Authored-By: Claude` trailer to commits.
- **Decision:** Commit messages and pull-request descriptions in this repository must **not** contain AI co-authorship trailers or attribution.
- **Consequences:** Contributors and agents must strip the trailer. The baseline commit was amended to comply (`73766ca`). This rule is restated in `CLAUDE.md`, [CONTRACT_CHANGE_POLICY](../product/04-contracts/CONTRACT_CHANGE_POLICY.md) and [CHANGE_IMPACT_PROTOCOL](../product/05-knowledge-graph/CHANGE_IMPACT_PROTOCOL.md).
- **Alternatives rejected:** Leaving the default trailer (contradicts an explicit repository-owner directive).

---

## Review trigger
See the entry above where stated; otherwise revisit when a dependent step is
implemented or a stated assumption is invalidated.

## Related
- [DECISION_LOG](../product/02-delivery/DECISION_LOG.md) — index of all decisions
- [ADR template](../product/09-templates/ADR_TEMPLATE.md)
- [00-START-HERE](../product/00-START-HERE.md)
