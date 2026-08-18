---
sub_step_id: STEP-005.10
parent_step: STEP-005
title: Provider health events and coverage wiring
status: VERIFIED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-EVID-006, REQ-TRIP-002]
blast_radius_id: BR-049
depends_on: [STEP-005.09]
last_updated: 2026-08-18
---

# STEP-005.10 — Provider health events and coverage wiring

## 1. Outcome
Provider degradation surfaces as `EVT-008`, drives the public coverage model, and causes new trips in affected regions to be **refused rather than partially simulated**.

## 2. Scope and boundary
**In scope:** Health state machine; `EVT-008` emission; coverage model updates; admin surface wiring.

**Not in this sub-step:** Coverage UI ([STEP-007](../../STEP-007-discovery-landing-and-destination-coverage.md)); admin console ([STEP-021](../../STEP-021-administration-and-curation-console.md)).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-EVID-006, REQ-TRIP-002 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | ✅ up to date. **NOT BLOCKED** |
| HEAD / indexed commit | `2411165` — matched HEAD at pre-change |
| Queries run | `impact` on `CircuitBreaker`, `CircuitState`, `Quota`, `Reconciliation`, each cross-checked against grep per `RISK-016` |
| **Finding** | `RISK-016` fifth reproduction — each symbol reported **1** dependant against 12–16 real references |
| Unknown / low-confidence areas | **One found during execution:** §5's four states against `EVT-008`'s three-value enum. Resolved by an explicit mapping rather than by changing the contract — see §6 |
| Blast radius | **[BR-049](../../../10-logs/blast-radius/BR-049-provider-health.md)** — MEDIUM, confidence MEDIUM |
| Approval required? | No |

## 5. Implementation plan
- [x] Health state machine: healthy → degraded → circuit-open → recovering, with **recovery hysteresis** so it cannot flap
- [x] Every transition **recorded**; `EVT-008` emitted when the published state changes — see §6 for why that reads the intent rather than the wording
- [x] Coverage model consumes health; a region takes the **worst** state among its declared dependencies
- [x] **An unavailable region refuses new trips**, with a required explanation and no type able to hold a partial itinerary
- [x] Health surfaced with **nowhere to put a provider identity, count or quota**

## 6. Contracts and schema changes

**No contract changed.** Both are consumed as declared, and one mismatch had to be
resolved without changing either.

§5 asks for four states. `EVT-008`'s payload enum is `healthy | degraded |
unavailable`, closed, with `additionalProperties: false`. Rather than widen the
contract, the internal machine keeps its four states and maps down:

| Internal | Published | Why |
| --- | --- | --- |
| `HEALTHY` | `healthy` | — |
| `DEGRADED` | `degraded` | — |
| `CIRCUIT_OPEN` | `unavailable` | No consumer responds differently to the two |
| `RECOVERING` | **`degraded`** | Publishing `healthy` on one probe sends full traffic back to a half-recovered provider |

The consequence is that `RECOVERING → DEGRADED` produces no published change. §5 says
"emitted on every transition"; taken literally that emits a self-transition the
stream's own dedupe key (`provider_id + new_state`) would discard. So **every
transition is recorded in the history and an event is emitted when the published
state changes** — the intent of §5 without filling the stream with events carrying no
information.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-EVID-006 | unit | Degradation is disclosed — and the disclosure says what is wrong |
| TST-TRIP-002 | unit | An unavailable region refuses, with an explanation |
| — | structural | **No type in the module can hold a partial itinerary** |
| — | structural | No public type has a field for a provider, a count or a quota |
| — | unit | One success after an outage does not restore health |
| — | unit | A failure during recovery resets the run |
| — | unit | `RECOVERING` publishes as `degraded`, never `healthy` |
| — | unit | The one adjacency where the mapping collapses is recorded and not emitted |
| — | unit | An untracked dependency is unavailable, not healthy |
| — | unit | An undeclared region raises rather than being answered |
| — | unit | The region takes the worst dependency; the aggregate takes the worst region |
| — | unit | The dedupe key matches `x-journeylab-dedupe-key` |

26 tests. **Mutation testing: 14 seeded, 14 killed.**

## 8. Telemetry, security and accessibility
Traces carry tenant-safe correlation IDs; no PII in telemetry. Any user-facing surface is keyboard and screen-reader complete (`REQ-A11Y-001`) and completable without the map (`REQ-A11Y-003`).

## 9. Documentation to update
- [ ] Sub-step completion record
- [ ] [IMPLEMENTATION_LOG](../../../10-logs/IMPLEMENTATION_LOG.md) · [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) · [BUG_REGISTER](../../../10-logs/BUG_REGISTER.md) if applicable
- [ ] `BR-039` post-change section
- [ ] Parent step §21 · [MASTER_TRACKER](../../../02-delivery/MASTER_TRACKER.md)

## 10. Regression cross-check (R1–R7)
| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression suite | **PASS** | 1062 Python + 63 web + 307 UI + 40 browser |
| R2 contract compatibility | **PASS** | `EVT-008` and `Coverage` consumed, not changed |
| R3 graph diff as expected | **PASS** | One new module, one new test module |
| R4 untested requirements | **PASS — improved** | REQ-EVID-006 and REQ-TRIP-002 newly covered |
| R5 orphan/unowned nodes | **PASS** | Catch-all owner |
| R6 closed-bug regression tests | **PASS** | BUG-001…027; meta-suite 72/72 |
| R7 tenant isolation | **PASS — 18/18** | Untouched |

**Overall:** **PASS** — and STEP-005 closes at 10/10.

## 11. Rollback
Revert this sub-step's commit; prior sub-steps stay intact and `main` stays deployable. Schema work uses expand/contract, so the expand phase is reversible.

## 12. Acceptance criteria
- [x] Health state machine with all four states and hysteresis on recovery
- [x] `EVT-008` emitted on published-state change; every transition recorded
- [x] Coverage consumes health and marks regions degraded
- [x] Region degradation refuses new trips, with an explanation and no partial simulation
- [x] Health surfaced without exposing provider identity

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | 2026-08-18 |
| Commit SHA | *(this commit)* |
| Pushed | ✅ |
| Graph re-indexed at | post-commit |
| `main` green and deployable | ✅ |
| Mutation testing | **14 of 14 killed** |
| Bugs found | None |
| Notes / surprises | **A failing test taught me the structure of my own state machine.** I wrote the published-state-collapse test for `DEGRADED → CIRCUIT_OPEN → RECOVERING` and it failed, because that path crosses `unavailable → degraded` and does publish. Working out why exposed the real structure: **the four-to-three mapping collapses at exactly one adjacency** — `RECOVERING → DEGRADED`, a provider that starts answering then fails again without tripping the breaker. Every other transition crosses a published boundary. That single case is the flap; my test had been written for a case that cannot occur.<br><br>**One mutant "survived" and was my own equivalent mutant.** `disclosures=() or (...)` still evaluates to a non-empty tuple, so nothing was mutated. Re-seeded as `disclosures=()` it dies at once — and it exposed a weak assertion on the way: the test only required a non-empty tuple, so a disclosure saying nothing would pass. A fourteenth mutant now blanks the text.<br><br>**Hysteresis is a traveller-facing property, not an operational one.** The obvious argument is suppressing event storms. The real one is that a flapping provider makes coverage accept and refuse at random, and an intermittent refusal is worse than a steady one because it is not reproducible — the traveller retries, it works, they retry later, it does not, and nothing visible explains the difference.<br><br>**Two requirements that look opposed are about different things.** `REQ-EVID-006` wants degradation surfaced; `Coverage` forbids naming, listing or counting providers. The traveller learns *that* the answer is degraded, never *who* degraded it — and the public types have nowhere to put the answer, which is the `.06` construction again rather than a stripping step somebody must remember. |
