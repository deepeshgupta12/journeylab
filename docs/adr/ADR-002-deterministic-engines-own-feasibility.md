# ADR-002 — Deterministic engines own feasibility; the LLM owns language

> Full ADR. Indexed in [DECISION_LOG](../product/02-delivery/DECISION_LOG.md) §1.
> Accepted ADRs are **superseded, never edited** — a reversal creates a new ADR
> that links back to this one.

- **Date:** 2026-08-05 · **Owner:** AI/ML Architect · **Status:** Accepted (inherited from blueprint §1.3, portfolio standard §4.20)
- **Context:** Travel planning is a constrained decision problem. Model fluency is not feasibility.
- **Decision:** CP-SAT and deterministic validators own time, route, budget, eligibility, permissions and workflow state. The LLM parses intent, asks clarifications and explains trade-offs. Model output can never mutate trip state without command validation and user authorization (`REQ-AI-001`).
- **Consequences:** Every AI capability needs a non-AI fallback (`REQ-AI-007`). Scenario scores are never model-generated.
- **Alternatives rejected:** LLM-orchestrated planning with tool calls deciding feasibility — unreproducible and unverifiable against `REQ-CONS-004`.

---

## Review trigger
See the entry above where stated; otherwise revisit when a dependent step is
implemented or a stated assumption is invalidated.

## Related
- [DECISION_LOG](../product/02-delivery/DECISION_LOG.md) — index of all decisions
- [ADR template](../product/09-templates/ADR_TEMPLATE.md)
- [00-START-HERE](../product/00-START-HERE.md)
