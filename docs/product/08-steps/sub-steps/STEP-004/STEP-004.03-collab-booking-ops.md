---
sub_step_id: STEP-004.03
parent_step: STEP-004
title: Collaboration, booking, live and feedback operations (API-010…014)
status: NOT_STARTED
owners: []
requirement_ids: [REQ-PLAT-005]
blast_radius_id: BR-024
depends_on: [STEP-004.02]
last_updated: 2026-08-05
---

# STEP-004.03 — Collaboration, booking, live and feedback operations (API-010…014)

## 1. Outcome
Phase 2–3 surfaces are contract-specified now so later steps implement against a stable shape rather than inventing one.

## 2. Scope and boundary
**In scope:** `API-010` invitations, `API-011` booking handoff, `API-012` activation, `API-013` repairs, `API-014` feedback.

**Not in this sub-step:** Implementations (Phase 2–3 steps).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-PLAT-005 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | **BLOCKED — static fallback** (no application symbols indexed yet) |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | KG-Q-015 `detect_changes()`; KG-Q-006 once symbols exist |
| Unknown / low-confidence areas | Offline manifest shape depends on STEP-017 device constraints — mark the schema extensible |
| Blast radius | BR-024 — scored at execution; **confidence capped while the graph is BLOCKED** |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] `API-010` invitations with scope, expiry and revocation
- [ ] `API-011` handoff — **no payment-credential field exists in any schema**
- [ ] `API-012` activation returning an offline manifest
- [ ] `API-013` repair generation **separate from acceptance** so generation cannot mutate the canonical plan
- [ ] `API-014` feedback with a required consent scope
- [ ] Estimated vs. confirmed modelled as distinct states, not a boolean flag

## 6. Contracts and schema changes
Contracts are declared in [STEP-004](../../STEP-004-contract-first-platform-apis.md); this sub-step consumes them. Any change follows [CONTRACT_CHANGE_POLICY](../../../04-contracts/CONTRACT_CHANGE_POLICY.md).

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-BOOK-002 | contract | No schema permits a payment credential |
| TST-LIVE-005 | contract | Repair generation and acceptance are distinct operations |

## 8. Telemetry, security and accessibility
Traces carry tenant-safe correlation IDs; no PII in telemetry. Any user-facing surface is keyboard and screen-reader complete (`REQ-A11Y-001`) and completable without the map (`REQ-A11Y-003`).

## 9. Documentation to update
- [ ] Sub-step completion record
- [ ] [IMPLEMENTATION_LOG](../../../10-logs/IMPLEMENTATION_LOG.md) · [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) · [BUG_REGISTER](../../../10-logs/BUG_REGISTER.md) if applicable
- [ ] `BR-024` post-change section
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
- [ ] Five operations specified
- [ ] Payment credentials structurally impossible
- [ ] Repair generation cannot mutate canonical state
- [ ] Estimated/confirmed distinction is structural

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Commit SHA | — |
| Pushed | — |
| Graph re-indexed at | — |
| `main` green and deployable | — |
| Bugs found | — |
| Notes / surprises | Making payment credentials unrepresentable in the schema is stronger than validating them away — there is nothing to forget to validate. |
