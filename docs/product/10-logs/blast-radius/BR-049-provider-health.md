---
blast_radius_id: BR-049
sub_step_id: STEP-005.10
title: Provider health events, coverage and trip refusal
author: Deepesh Kumar Gupta
date: 2026-08-18
score: MEDIUM
confidence: MEDIUM
approval_required: false
---

# BR-049 — Provider health and coverage refusal

## 1. Graph state

| Field | Value |
| --- | --- |
| Indexed commit | `2411165` |
| HEAD at check | `2411165` |
| Freshness | ✅ up to date |
| Result | **NOT BLOCKED** |
| Confidence | **MEDIUM** — `RISK-016`, fifth reproduction |

## 2. Queries run, with the mandatory cross-check

| Symbol | Graph | Grep |
| --- | --- | --- |
| `CircuitBreaker` | 1, LOW | **13** |
| `CircuitState` | 1, LOW | **16** |
| `Quota` | 1, LOW | **12** |
| `Reconciliation` | 1, LOW | **16** |

Every symbol reports exactly one dependant against twelve to sixteen real
references. Five sub-steps, five reproductions; `RISK-016` is now the most reliably
reproducible finding in this repository.

**Actual blast radius:** additive. `provider_health.py` is new and imports nothing
from the existing modules — it models the circuit breaker's *verdict* as an input
rather than reaching into `CircuitBreaker`, so the coupling is one boolean parameter
rather than a dependency.

## 3. Four internal states, three published, and that is not a mistake

§5 asks for `healthy → degraded → circuit-open → recovering`. `EVT-008`'s payload
enum is `healthy | degraded | unavailable` and the schema is closed.

Neither is wrong. The internal machine describes **our mechanics**; the event tells a
consumer **what it can do**, and no consumer responds differently to "circuit open"
than to "unavailable". The mapping is explicit, and one row carries weight:

> `RECOVERING → degraded`, never `healthy`.

A provider that has begun answering again is not one we trust yet. Publishing
`healthy` on the strength of a probe sends full traffic back to a half-recovered
provider, which is how a recovery becomes a second outage.

## 4. Emission on published-state change, and why that reads §5's intent over its wording

§5 says "emitted on every transition". Against the mapping above, `RECOVERING →
DEGRADED` would emit an event whose previous and new states are both `degraded` — a
self-transition carrying nothing a consumer can act on, and one the contract's own
dedupe key (`provider_id + new_state`) discards anyway.

So every internal transition is **recorded in the history** and an event is emitted
when the published state changes. Nothing is hidden; the stream stays meaningful.
Recorded here rather than left as a discrepancy for someone to find.

**Writing the test for this found something.** My first version used
`DEGRADED → CIRCUIT_OPEN → RECOVERING` and failed, because that path crosses
`unavailable → degraded` and does publish. Working out why exposed the real
structure: **the four-to-three mapping collapses at exactly one adjacency**,
`RECOVERING → DEGRADED` — a provider that started answering and then failed again
without tripping the breaker. Every other transition crosses a published boundary.
That is the flap, it is the only case the design needed to handle, and I had written
a test for a case that cannot occur.

## 5. Recovery needs hysteresis or it is a flap

One success after an outage means the next request *might* work. Promoting on it
oscillates: healthy, open, healthy, open. That is an event storm on the stream, and
coverage that accepts and refuses trips at random — **worse for a traveller than a
steady refusal, because it is not reproducible.** They retry, it works, they retry
later, it does not.

`RECOVERY_SUCCESSES = 3` is provisional pending `DEC-005`. What is not provisional is
that it must exceed one, and that is asserted directly.

## 6. Refusal, and the line REQ-TRIP-002 actually draws

`REQ-TRIP-002` refuses a request *"outside current coverage"*, with an explanation
and no partial simulation. So:

- **Unavailable dependency ⇒ refused.** The region is outside coverage.
- **Degraded dependency ⇒ accepted with disclosure.** Degraded is *inside* coverage
  and less certain. Refusing on every degradation would refuse most of the time and
  teach people the product is broken rather than that the data is thin.

Three refusals are structural rather than remembered: `TripRefused` requires a
reason, no type in the module has a field that could hold a partial itinerary, and an
**undeclared region raises** rather than being answered — answering would invent a
coverage claim.

The same principle governs unknowns: an untracked dependency is `UNAVAILABLE`, not
healthy. "No news is good news" is how an unmonitored provider stays green through an
outage.

## 7. Two requirements that look opposed and are not

`REQ-EVID-006` requires degradation to be **surfaced**. `Coverage` in the contract
requires the opposite of detail: *"an aggregate. Never a list, never named, never a
count — each of those leaks the shape of the supply chain."*

Both hold because they are about different things. The traveller learns **that** the
answer is degraded; they never learn **who** degraded it or how many. `PublicRegion`
and `PublicCoverage` have nowhere to put a provider identity, a provider count or a
quota — the same construction as `.06`'s attribution record, where the field a leak
would need does not exist to be filled in. A count is enough to infer the supply
chain's size, and quota proximity tells an attacker exactly when the product
degrades.

## 8. Assessment

| Category | Assessment |
| --- | --- |
| Code | `services/ingestion/src/provider_health.py` **new**; nothing modified |
| Public API contract | Consumed, not changed. `PublicCoverage` matches `Coverage`; `PublicRegion.freshness` matches `CoverageRegion.freshness` |
| Events | `HealthChanged` implements `EVT-008` including its dedupe key. AsyncAPI unchanged |
| Security / privacy | **The main surface of this sub-step.** Provider identity is dropped by the shape of the public type, not by a stripping step |
| Accessibility | No user surface; disclosures are strings a UI step will render |
| Performance | In-memory state, no I/O |

**Mutation testing: 14 seeded, 14 killed.** One appeared to survive and was an
**equivalent mutant of my own making** — I wrote `disclosures=() or (...)`, which
still evaluates to a non-empty tuple. Re-seeded honestly as `disclosures=()` it dies,
and a second mutant now checks that the disclosure actually says the sources are
degraded, since a disclosure that discloses nothing satisfies a non-empty assertion
perfectly.

## 9. What this does not close

| Gap | Why |
| --- | --- |
| Nothing calls `record_failure` yet | The connector framework owns the call path; wiring is `STEP-006` and the observability step |
| No event is actually published | Kafka is chosen (`ADR-015`) and no broker exists. `HealthChanged` is the payload, not the transport |
| Coverage is in memory | `DEC-007` has not chosen a platform; `STEP-006` owns persistence |
| The admin surface is not built | `STEP-021`. This provides the state and the history it will read |
| `RECOVERY_SUCCESSES` is provisional | `DEC-005`. The invariant that it exceeds one is asserted |

## 10. Score

Additive and unwired, but it decides refusal and it is the boundary where provider
identity could leak. **MEDIUM**, confidence MEDIUM for `RISK-016`. No owner approval
required.
