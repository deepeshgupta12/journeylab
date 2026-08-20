---
sub_step_id: STEP-006.02
parent_step: STEP-006
title: Temporal model: observed, effective and recorded time
status: VERIFIED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-DATA-007, REQ-DATA-005]
blast_radius_id: BR-051
depends_on: [STEP-006.01]
last_updated: 2026-08-20
---

# STEP-006.02 — Temporal model: observed, effective and recorded time

## 1. Outcome
Every fact table carries three distinct time axes, and queries filter on the correct one — the single highest-value correctness decision in the data layer.

## 2. Scope and boundary
**In scope:** Temporal columns on all fact tables; helper types; query helpers enforcing correct axis use; DST-aware date handling.

**Not in this sub-step:** Freshness thresholds (`STEP-005.08`); UI display.

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-DATA-007, REQ-DATA-005 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | ✅ up to date. **NOT BLOCKED** for the module; **`RISK-017`** for the migration |
| HEAD / indexed commit | `e918c3b` — matched HEAD at pre-change |
| Queries run | `impact` on `bind_tenant`, `app_current_org`, `RequestContext`, each grep cross-checked (`RISK-016`, sixth reproduction) |
| Unknown / low-confidence areas | Only `Europe/Zurich` is exercised. `ADR-016` makes it the region; a second region needs its own transition dates |
| Blast radius | **[BR-051](../../../10-logs/blast-radius/BR-051-temporal-model.md)** — MEDIUM, confidence MEDIUM |
| Approval required? | No |

## 5. Implementation plan
- [x] All four axes on `evidence_facts` (STEP-006.01), plus a generated `effective_range`
- [x] Exclusion constraint — **keyed by `source_id`**, because the obvious version would have forbidden the conflicting evidence `REQ-EVID-002` requires us to keep. See §6
- [x] **Query helpers that name their axis**, and no general-purpose time filter to reach for
- [x] Zones required at the database (`CHECK`) and refused when naive in code
- [x] Property tests over both 2026 transitions, asserting elapsed time never disagrees with UTC

## 6. The constraint that would have enforced a requirement violation

The obvious integrity rule — *no two facts about the same field of the same place may
have overlapping effective windows* — is wrong here.

`REQ-EVID-002` requires conflicting evidence to stay visible and never be averaged
away. Two sources disagreeing about the same opening hours over the same dates **is**
that evidence. A constraint over (place, field) would make storing it impossible: the
schema would enforce a requirement violation, and the second source's fact would be
rejected with an error that reads like a data bug.

The defensible line is narrower: **one source must not contradict itself.** Two facts
from one source over overlapping windows are a double ingestion or a mis-parsed
window, not disagreement. `source_id` is in the exclusion key, and a test asserts two
different sources may both be stored.

## 6a. Contracts and schema changes
Contracts are declared in [STEP-004](../../STEP-004-contract-first-platform-apis.md); this sub-step consumes them. Any change follows [CONTRACT_CHANGE_POLICY](../../../04-contracts/CONTRACT_CHANGE_POLICY.md).

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-DATA-007 | property | Elapsed time never disagrees with UTC, over windows straddling both 2026 transitions (200 examples) |
| — | property | "Same local time" preserves the wall clock across 400 days (100 examples) |
| — | integration | A fresh fact outside the trip window is excluded by the effective filter — **and returned by the observed filter**, which is the confusion being prevented |
| — | unit | **Spring-forward is 23 elapsed hours; autumn-back is 25** |
| — | unit | The trap is in subtraction, not addition — the asymmetry pinned |
| — | unit | Calendar days are not elapsed days: a two-hour overnight stay is one night |
| — | integration | One source may not contradict itself over an overlapping window |
| — | integration | **Two sources may disagree and both are kept** (`REQ-EVID-002`) |
| — | structural | No general-purpose time filter exists to pass the wrong axis to |

23 tests. **Mutation testing: 11 seeded, 11 killed** — 8 against the module, 3
against the deployed constraint.

## 8. Telemetry, security and accessibility
Traces carry tenant-safe correlation IDs; no PII in telemetry. Any user-facing surface is keyboard and screen-reader complete (`REQ-A11Y-001`) and completable without the map (`REQ-A11Y-003`).

## 9. Documentation to update
- [ ] Sub-step completion record
- [ ] [IMPLEMENTATION_LOG](../../../10-logs/IMPLEMENTATION_LOG.md) · [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) · [BUG_REGISTER](../../../10-logs/BUG_REGISTER.md) if applicable
- [ ] `BR-041` post-change section
- [ ] Parent step §21 · [MASTER_TRACKER](../../../02-delivery/MASTER_TRACKER.md)

## 10. Regression cross-check (R1–R7)
| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression suite | **PASS** | 1103 Python + 63 web + 307 UI + 40 browser |
| R2 contract compatibility | **PASS** | No contract touched |
| R3 graph diff as expected | **PASS — by inspection** | `RISK-017` for the migration half |
| R4 untested requirements | **PASS — improved** | REQ-DATA-007, REQ-EVID-002 |
| R5 orphan/unowned nodes | **PASS** | Catch-all owner |
| R6 closed-bug regression tests | **PASS** | BUG-001…027; meta-suite 72/72 |
| R7 tenant isolation | **PASS — 18/18** | Untouched |

**Overall:** **PASS**.

## 11. Rollback
Revert this sub-step's commit; prior sub-steps stay intact and `main` stays deployable. Schema work uses expand/contract, so the expand phase is reversible.

## 12. Acceptance criteria
- [x] Three axes present on every fact table
- [x] Query helpers enforce correct axis usage, and no generic filter exists
- [x] DST and seasonal property tests pass
- [x] No naive local timestamps anywhere — refused in code, checked in the schema

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | 2026-08-20 |
| Commit SHA | *(this commit)* |
| Pushed | ✅ |
| Graph re-indexed at | post-commit |
| `main` green and deployable | ✅ |
| Mutation testing | **11 of 11 killed** |
| Bugs found | **Two of my own, both in this sub-step's own work** — see below |
| Notes / surprises | **The DST bug was inside the module written to prevent it.** Python subtracts two aware datetimes sharing a `tzinfo` as *wall clock* — documented, and invisible because both offsets are correct. `b - a` across spring-forward gives 24 hours where UTC gives 23. My first `elapsed_between` was `return end - start`, so every duration crossing a boundary would have been wrong by an hour, **in the direction that makes a tight itinerary look feasible** — an hour that does not exist, handed to the solver as slack. Found by printing a value; the function read as obviously correct.<br><br>**I had the asymmetry backwards.** My first test asserted `+ timedelta(days=1)` moves 09:00 to 10:00. Under `zoneinfo`, *addition* is wall-clock and lands on 09:00 exactly like the helper — only subtraction is the trap. The test now pins that, and records that the equivalence is a `zoneinfo` property `pytz` does not share, so the helper is not later removed as redundant.<br><br>**A nullable column in an exclusion key is not in the key.** `place_id WITH =` never conflicts when NULL, because `NULL = NULL` is unknown, so every region-level fact escaped the constraint silently. The test written for the constraint found it.<br><br>**Rows left by a failed test blocked the constraint's own re-creation** — the same shape as `.01`'s mutation-restore failure, one sub-step later. Twice now, a partial failure has left state that makes the *next* operation fail with a message about data rather than about the test. |
