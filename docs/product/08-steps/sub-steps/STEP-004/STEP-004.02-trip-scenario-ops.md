---
sub_step_id: STEP-004.02
parent_step: STEP-004
title: Trip, brief and scenario operations (API-001…009)
status: NOT_STARTED
owners: []
requirement_ids: [REQ-PLAT-005, REQ-PLAT-008]
blast_radius_id: BR-023
depends_on: [STEP-004.01]
last_updated: 2026-08-05
---

# STEP-004.02 — Trip, brief and scenario operations (API-001…009)

## 1. Outcome
The core planning surface is fully specified in OpenAPI with request/response schemas, error cases and examples, before any handler exists.

## 2. Scope and boundary
**In scope:** `API-001`–`API-009`: create/read trip, replace brief, build evidence pack, generate scenarios, list/read scenarios, select, edit.

**Not in this sub-step:** Handler implementations (their owning steps); collaboration and booking operations (`.03`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-PLAT-005, REQ-PLAT-008 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | **BLOCKED — static fallback** (no application symbols indexed yet) |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | KG-Q-015 `detect_changes()`; KG-Q-006 once symbols exist |
| Unknown / low-confidence areas | Impact-preview token semantics for API-009 need design alongside STEP-014 |
| Blast radius | BR-023 — scored at execution; **confidence capped while the graph is BLOCKED** |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] `API-001`/`API-002` trip create and read with ETag
- [ ] `API-003` brief replace with **`If-Match` required**
- [ ] `API-004`/`API-005` async operations returning a **job handle within 500 ms**
- [ ] `API-006`/`API-007` scenario list and detail, every volatile field carrying provenance
- [ ] `API-008` select — **owner-only** in the security scheme
- [ ] `API-009` typed edit with impact-preview token
- [ ] `422` responses carrying **minimal conflict sets**, not bare errors

## 6. Contracts and schema changes
Contracts are declared in [STEP-004](../../STEP-004-contract-first-platform-apis.md); this sub-step consumes them. Any change follows [CONTRACT_CHANGE_POLICY](../../../04-contracts/CONTRACT_CHANGE_POLICY.md).

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-PLAT-005 | contract | All examples validate against schemas |
| TST-CONS-005 | contract | Infeasible response shape carries a conflict set |

## 8. Telemetry, security and accessibility
Traces carry tenant-safe correlation IDs; no PII in telemetry. Any user-facing surface is keyboard and screen-reader complete (`REQ-A11Y-001`) and completable without the map (`REQ-A11Y-003`).

## 9. Documentation to update
- [ ] Sub-step completion record
- [ ] [IMPLEMENTATION_LOG](../../../10-logs/IMPLEMENTATION_LOG.md) · [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) · [BUG_REGISTER](../../../10-logs/BUG_REGISTER.md) if applicable
- [ ] `BR-023` post-change section
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
- [ ] Nine operations specified with all response codes
- [ ] Async operations declare the job-handle contract
- [ ] Owner-only operations declare it in the security scheme
- [ ] Every volatile field carries source, observed time, effective time, confidence

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Commit SHA | — |
| Pushed | — |
| Graph re-indexed at | — |
| `main` green and deployable | — |
| Bugs found | — |
| Notes / surprises | Encoding provenance in the response schema is what makes REQ-EVID-001 enforceable rather than aspirational — a handler cannot omit what the contract requires. |
