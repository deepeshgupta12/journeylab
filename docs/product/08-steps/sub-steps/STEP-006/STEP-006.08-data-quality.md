---
sub_step_id: STEP-006.08
parent_step: STEP-006
title: Data-quality expectations and quarantine
status: NOT_STARTED
owners: []
requirement_ids: [REQ-DATA-005, REQ-DATA-002]
blast_radius_id: BR-047
depends_on: [STEP-006.07]
last_updated: 2026-08-05
---

# STEP-006.08 — Data-quality expectations and quarantine

## 1. Outcome
Executable expectations run against every ingestion batch, and failing data is quarantined rather than silently entering planning.

## 2. Scope and boundary
**In scope:** `data/quality/domain_expectations.yml`; expectation runner; quarantine store; alerting.

**Not in this sub-step:** Provider reconciliation (`STEP-005.09`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-DATA-005, REQ-DATA-002 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | **BLOCKED — static fallback** (no application symbols indexed yet) |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | KG-Q-015 `detect_changes()`; KG-Q-006 once symbols exist |
| Unknown / low-confidence areas | Drift thresholds need a real destination pack to calibrate (DEC-002) |
| Blast radius | BR-047 — scored at execution; **confidence capped while the graph is BLOCKED** |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] Expectations for schema, freshness, completeness, uniqueness, referential integrity, distribution drift
- [ ] **Referential integrity as a hard block** — no itinerary item may reference an unresolved location (`REQ-NFR-012`)
- [ ] Failing batch quarantined with the failure reason
- [ ] Quarantine visible to curators, not just logged
- [ ] Drift detection on price and duration distributions

## 6. Contracts and schema changes
Contracts are declared in [STEP-004](../../STEP-004-contract-first-platform-apis.md); this sub-step consumes them. Any change follows [CONTRACT_CHANGE_POLICY](../../../04-contracts/CONTRACT_CHANGE_POLICY.md).

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-DATA-005 | data quality | Each expectation catches its seeded violation |
| TST-NFR-012 | integration | Unresolved location blocks rather than warns |

## 8. Telemetry, security and accessibility
Traces carry tenant-safe correlation IDs; no PII in telemetry. Any user-facing surface is keyboard and screen-reader complete (`REQ-A11Y-001`) and completable without the map (`REQ-A11Y-003`).

## 9. Documentation to update
- [ ] Sub-step completion record
- [ ] [IMPLEMENTATION_LOG](../../../10-logs/IMPLEMENTATION_LOG.md) · [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) · [BUG_REGISTER](../../../10-logs/BUG_REGISTER.md) if applicable
- [ ] `BR-047` post-change section
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
- [ ] All six expectation classes implemented
- [ ] Seeded violations caught
- [ ] Quarantine visible and actionable
- [ ] Unresolved locations hard-blocked

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Commit SHA | — |
| Pushed | — |
| Graph re-indexed at | — |
| `main` green and deployable | — |
| Bugs found | — |
| Notes / surprises | Quarantine that only logs is quarantine nobody acts on — visibility to the curator is what closes the loop. |
