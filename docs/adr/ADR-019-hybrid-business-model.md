# ADR-019 — The business model is hybrid: affiliate handoff plus a paid tier

> Full ADR. Indexed in [DECISION_LOG](../product/02-delivery/DECISION_LOG.md) §1.

- **Date:** 2026-10-19 · **Owner:** Deepesh Kumar Gupta · **Status:** Accepted
- Closes `DEC-003`. **Owner directive**, recorded by the implementer the same day. One
  owner holds every role (`ADR-010`), so the four-eyes gap applies to this record as to
  every other: author and approver are the same person, stated rather than glossed.

## Context

The blueprint names affiliate deep links as the MVP revenue mechanism and advisor
white-label as a Phase 4 one. It says nothing about pricing, a subscription, or a
freemium boundary. `DEC-003` has been open since 2026-08-05 with three options — (a)
affiliate-only, (b) freemium with paid comparison depth, (c) advisor-licensing-first —
and it blocked two things: whether a billing step `STEP-029` exists at all, and the
targets for `KPI-007` (unit economics).

## Decision

**Both.** Affiliate deep-link attribution on booking handoff stays exactly as the
blueprint states it (§6.10, no payment processing, not merchant of record), **and** the
product carries a paid consumer tier. The free tier remains genuinely useful; the paid
tier deepens comparison. That is the shape of option (b) layered on option (a). Advisor
licensing (option (c)) remains Phase 4 and is unaffected.

## Options considered

| Option | What it is | Why not, or why |
| --- | --- | --- |
| (a) affiliate-only | Revenue only when a traveller books through a handoff | Single leg, and it rests entirely on `ASM-012` (partners preserve itinerary context). If that assumption fails there is no revenue at all |
| (b) freemium + paid depth | A useful free plan; paid tier deepens comparison | Second leg independent of partners. Risk: paywalling the wrong thing hollows out the product claim — addressed below |
| (c) advisor-licensing-first | Sell to advisors before consumers | Reverses the roadmap; the MVP user and payer are the same traveller (`PRODUCT_CHARTER` §3) |
| **(a) + (b) — chosen** | Two legs | Neither leg alone carries the product; together, one failing does not zero the other |

## Consequences

1. **`STEP-029` (billing) is now required.** `PRODUCT_SCOPE`'s billing note has always said
   a paid tier means a *new* step rather than billing folded into an existing one. That step
   is **not defined by this ADR** — no scope, sub-steps or requirements exist for it, and
   inventing them here would be editing product scope through a decision record.
2. **`GATE-001` must be read against a subscription processor before `STEP-029` is scoped.**
   `GATE-001` forbids payment processing, ticket issuance and merchant-of-record status,
   and it was written about *travel bookings*. A subscription takes payment for the
   product's own fee through a processor. That is a different thing — but it is still
   payment, and whether `GATE-001`'s PCI and liability review is triggered is **a decision
   the owner has not yet taken.** This ADR does not take it.
3. **One constraint is fixed now, before anyone designs the paywall:** nothing that makes a
   free plan *less feasible or less honest* may be premium. Evidence, source and freshness
   on every fact (`REQ-EVID-001/003`), constraint violations (`REQ-CONS-004`), the minimal
   conflict set on infeasibility (`REQ-CONS-005`), and the table/CSV equivalents
   (`REQ-A11Y-002/003`) are never behind the paid tier. "Comparison depth" may mean more
   scenarios, more what-if edits, or richer explanation — it may not mean a free user is
   shown a worse-checked plan. **This is the guardrail that stops the business model
   eating the product claim**, and `STEP-029` inherits it as a testable rule.
4. **`KPI-007` needs a margin model** now that revenue has two legs. Target still unset
   (`DEC-005`).
5. **Phase 1 exit is no longer blocked on this decision.** It is now blocked on defining
   `STEP-029`, which is a smaller and more concrete thing.

## Affected knowledge-graph nodes

Documentation only today: `DEC-003` in `DECISION_LOG` and `OUT_OF_SCOPE`, the billing
note in `PRODUCT_SCOPE`, the open-decisions row in `00-START-HERE`. No code node exists
for billing, so no code node is affected.

## Migration

None. No billing surface exists to migrate from.

## Security and privacy implications

A paid tier introduces two new data categories: payment instruments (held by the
processor, **never** stored in this system) and a subscription state on the account —
personal data with its own retention and deletion path that `DATA_RETENTION_AND_DELETION`
does not yet list. Owed at `STEP-029`, not here.

## Operational implications

None until `STEP-029`. The affiliate leg's operational shape is unchanged.

## Tests

None today. `STEP-029` inherits consequence 3 as a contract rule: a test must prove that
no evidence, violation or freshness field differs between a free and a paid response for
the same brief.

## Rollback

Revert to affiliate-only by removing `STEP-029` before it is built. Cheap now; expensive
once a subscription state exists on real accounts.

## Review trigger

Either of: `STEP-029` is scoped (this ADR's consequences become requirements), or
`ASM-012` is falsified (the affiliate leg then yields no revenue and the model is
effectively single-leg again).
