---
sub_step_id: STEP-006.06
parent_step: STEP-006
title: Transactional outbox publisher with idempotency
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-DATA-008, REQ-NFR-005]
blast_radius_id: BR-045
depends_on: [STEP-006.05]
last_updated: 2026-08-05
---

# STEP-006.06 — Transactional outbox publisher with idempotency

## 1. Outcome
Domain events are written in the **same transaction** as the state change and relayed at least once, so no event is lost and none is phantom.

## 2. Scope and boundary
**In scope:** `services/events/src/outbox.py`; outbox table; relay worker; publish offsets; DLQ after retry cap.

**Not in this sub-step:** Consumer implementations (`.07`); queue selection (`DEC-009`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-DATA-008, REQ-NFR-005 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | **BLOCKED — static fallback** (no application symbols indexed yet) |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | KG-Q-015 `detect_changes()`; KG-Q-006 once symbols exist |
| Unknown / low-confidence areas | **DEC-009 unresolved.** Propose managed queue vs. Kafka with rationale when this sub-step is reached |
| Blast radius | BR-045 — scored at execution; **confidence capped while the graph is BLOCKED** |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] Outbox table written inside the aggregate transaction
- [ ] Relay worker publishing with at-least-once delivery
- [ ] Publish offset and retry tracking
- [ ] Capped exponential backoff, then dead-letter with the full envelope preserved
- [ ] **Rollback test: a failed transaction leaves no outbox row** — no phantom events
- [ ] Lag metric exposed for `ALRT-QUEUE-001`

## 6. Contracts and schema changes
Contracts are declared in [STEP-004](../../STEP-004-contract-first-platform-apis.md); this sub-step consumes them. Any change follows [CONTRACT_CHANGE_POLICY](../../../04-contracts/CONTRACT_CHANGE_POLICY.md).

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-DATA-008 | integration | Event and state change commit or roll back together |
| — | integration | Relay failure retries then dead-letters with context |

## 8. Telemetry, security and accessibility
Traces carry tenant-safe correlation IDs; no PII in telemetry. Any user-facing surface is keyboard and screen-reader complete (`REQ-A11Y-001`) and completable without the map (`REQ-A11Y-003`).

## 9. Documentation to update
- [ ] Sub-step completion record
- [ ] [IMPLEMENTATION_LOG](../../../10-logs/IMPLEMENTATION_LOG.md) · [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) · [BUG_REGISTER](../../../10-logs/BUG_REGISTER.md) if applicable
- [ ] `BR-045` post-change section
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
- [ ] Outbox atomic with state change
- [ ] Failed transaction produces no event
- [ ] Retry and DLQ behaviour correct
- [ ] Lag metric published

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Commit SHA | — |
| Pushed | — |
| Graph re-indexed at | — |
| `main` green and deployable | — |
| Bugs found | — |
| Notes / surprises | The phantom-event test is the one that matters: an event published for a rolled-back change tells every consumer something happened that did not. |
