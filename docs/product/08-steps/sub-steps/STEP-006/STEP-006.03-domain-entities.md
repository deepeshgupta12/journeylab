---
sub_step_id: STEP-006.03
parent_step: STEP-006
title: Domain entities, invariants and value objects
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-DATA-007]
blast_radius_id: BR-042
depends_on: [STEP-006.02]
last_updated: 2026-08-05
---

# STEP-006.03 — Domain entities, invariants and value objects

## 1. Outcome
Domain invariants are enforced in code independent of transport and persistence, so an invariant cannot be bypassed by a different entry path.

## 2. Scope and boundary
**In scope:** `apps/api/src/domain/models.py`; entities, value objects, invariant checks; the state machines from [BACKEND_ARCHITECTURE](../../../03-architecture/BACKEND_ARCHITECTURE.md) §3.

**Not in this sub-step:** Repositories (`.04`); API handlers.

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-DATA-007 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | *(record at execution)* — run `npx gitnexus status` and confirm it matches HEAD. **Application code has been indexed since STEP-002.02**, so a `BLOCKED` result here is a real finding to investigate, not the expected default. |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | KG-Q-015 `detect_changes()`; KG-Q-006 once symbols exist |
| Unknown / low-confidence areas | None material |
| Blast radius | BR-042 — scored at execution; **confidence capped while the graph is BLOCKED** |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] Entities for the sixteen data types with invariants as constructor guards
- [ ] Value objects for Money (integer minor units), TemporalValidity, Provenance
- [ ] **Illegal states unrepresentable** — a Scenario cannot be constructed without its four lineage references
- [ ] Trip and scenario state machines with invalid transitions rejected
- [ ] Protected/completed item semantics enforced in the model

## 6. Contracts and schema changes
Contracts are declared in [STEP-004](../../STEP-004-contract-first-platform-apis.md); this sub-step consumes them. Any change follows [CONTRACT_CHANGE_POLICY](../../../04-contracts/CONTRACT_CHANGE_POLICY.md).

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-DATA-007 | unit | Every invariant rejects its violating case |
| — | unit | Invalid state transitions raise rather than silently pass |

## 8. Telemetry, security and accessibility
Traces carry tenant-safe correlation IDs; no PII in telemetry. Any user-facing surface is keyboard and screen-reader complete (`REQ-A11Y-001`) and completable without the map (`REQ-A11Y-003`).

## 9. Documentation to update
- [ ] Sub-step completion record
- [ ] [IMPLEMENTATION_LOG](../../../10-logs/IMPLEMENTATION_LOG.md) · [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) · [BUG_REGISTER](../../../10-logs/BUG_REGISTER.md) if applicable
- [ ] `BR-042` post-change section
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
- [ ] Invariants enforced in constructors, not callers
- [ ] Money never floating point
- [ ] Scenario cannot exist without full lineage
- [ ] Invalid transitions rejected

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Commit SHA | — |
| Pushed | — |
| Graph re-indexed at | — |
| `main` green and deployable | — |
| Bugs found | — |
| Notes / surprises | Invariants in the domain layer rather than the API layer is what keeps them true when a background job writes the same entity. |
