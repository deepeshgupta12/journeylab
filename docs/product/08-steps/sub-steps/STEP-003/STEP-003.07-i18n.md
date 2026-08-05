---
sub_step_id: STEP-003.07
parent_step: STEP-003
title: Locale, time zone, currency and DST handling
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-NFR-007, REQ-NFR-008]
blast_radius_id: BR-020
depends_on: [STEP-003.06]
last_updated: 2026-08-05
---

# STEP-003.07 — Locale, time zone, currency and DST handling

## 1. Outcome
Dates, numbers, currencies and time zones render correctly per locale, **including across DST transitions**, with right-to-left-ready structure.

## 2. Scope and boundary
**In scope:** `apps/web/src/lib/i18n.ts`; ICU message loading; locale-aware formatters; IANA time-zone handling; RTL-ready layout primitives.

**Not in this sub-step:** RTL *implementation* (Phase 2); translation content.

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-NFR-007, REQ-NFR-008 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | **BLOCKED — static fallback** (no application symbols indexed yet) |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | KG-Q-015 `detect_changes()`; KG-Q-006 once symbols exist |
| Unknown / low-confidence areas | Whether formatting runs server-side, client-side or both affects hydration — decide and document |
| Blast radius | BR-020 — scored at execution; **confidence capped while the graph is BLOCKED** |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] ICU message loading with a documented fallback locale
- [ ] Locale-aware date, number and currency formatters
- [ ] **Money as integer minor units** — never floating point
- [ ] IANA time-zone-aware date handling with explicit DST tests
- [ ] Logical CSS properties throughout so RTL is a configuration change

## 6. Contracts and schema changes
Contracts are declared in [STEP-004](../../STEP-004-contract-first-platform-apis.md); this sub-step consumes them. Any change here follows [CONTRACT_CHANGE_POLICY](../../../04-contracts/CONTRACT_CHANGE_POLICY.md).

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-NFR-007 | unit | Dates, numbers and currency correct across the locale matrix |
| — | unit | **A date range spanning a DST transition computes the correct duration** |
| TST-NFR-008 | component | Layout does not break under an RTL locale |

## 8. Telemetry, security and accessibility
Traces carry tenant-safe correlation IDs; no PII in telemetry. Any user-facing surface is keyboard and screen-reader complete (`REQ-A11Y-001`) and completable without the map (`REQ-A11Y-003`).

## 9. Documentation to update
- [ ] Sub-step completion record
- [ ] [IMPLEMENTATION_LOG](../../../10-logs/IMPLEMENTATION_LOG.md) · [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) · [BUG_REGISTER](../../../10-logs/BUG_REGISTER.md) if applicable
- [ ] `BR-020` post-change section
- [ ] Parent step §21 · [MASTER_TRACKER](../../../02-delivery/MASTER_TRACKER.md)

## 10. Regression cross-check (R1–R7)
| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression suite | | All prior sub-steps + every `VERIFIED` step |
| R2 contract compatibility | | No unintended breaking diff |
| R3 graph diff as expected | | `detect_changes()` |
| R4 untested requirements | | Not increased |
| R5 orphan/unowned nodes | | Not increased |
| R6 closed-bug regression tests | | All passing |
| R7 tenant isolation | | **Pass — non-negotiable** |

**Overall:** PASS / FAIL — a FAIL means this sub-step is not done.

## 11. Rollback
Revert this sub-step's commit; prior sub-steps stay intact and `main` stays deployable. Schema work uses expand/contract, so the expand phase is reversible.

## 12. Acceptance criteria
- [ ] Locale matrix renders correctly
- [ ] DST-spanning ranges compute correct durations
- [ ] Currency handled as integer minor units
- [ ] Missing locale falls back without crashing
- [ ] RTL structure does not break layout

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Commit SHA | — |
| Pushed | — |
| Graph re-indexed at | — |
| `main` green and deployable | — |
| Bugs found | — |
| Notes / surprises | DST correctness is a feasibility concern, not formatting: an itinerary crossing a transition computes wrong travel windows, which STEP-012 will then present as a valid plan. |
