---
sub_step_id: STEP-006.03
parent_step: STEP-006
title: Domain entities, invariants and value objects
status: VERIFIED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-DATA-007]
blast_radius_id: BR-052
depends_on: [STEP-006.02]
last_updated: 2026-08-20
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
| Graph status | ✅ up to date. **NOT BLOCKED** |
| HEAD / indexed commit | `d6318a2` — matched HEAD at pre-change |
| Queries run | `impact` on `Money`, `TemporalValidity`, `Provenance`, grep cross-checked (`RISK-016`, seventh reproduction: 2/0/0 against 27/9/14) |
| Unknown / low-confidence areas | None material — additive, no callers yet |
| Blast radius | **[BR-052](../../../10-logs/blast-radius/BR-052-domain-entities.md)** — LOW, confidence MEDIUM |
| Approval required? | No |

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
- [x] Invariants enforced in constructors, not callers
- [x] Money never floating point — **and never a `bool`**, which mypy accepts
- [x] Scenario cannot exist without full lineage
- [x] Invalid transitions rejected, with `INFEASIBLE` and `FAILED` recovering differently

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | 2026-08-20 |
| Commit SHA | *(this commit)* |
| Pushed | ✅ |
| Graph re-indexed at | post-commit |
| `main` green and deployable | ✅ |
| Mutation testing | **14 of 14 killed** |
| Bugs found | None |
| Notes / surprises | **mypy is happy with `Money(True, "CHF")`.** `bool` is a subtype of `int`, so a flag type-checks where a price belongs. I added a `type: ignore` from habit and mypy reported it unused — which is the finding rather than the nuisance. The test now records that the runtime guard exists precisely because the type system cannot express the rule.<br><br>**A shared rule is not shared coverage.** The one surviving mutant was an out-of-range confidence on `Provenance`. The places adapter has the identical guard *and a test for it*, and that is exactly what made the gap invisible — I had already watched that rule be tested, in a different class in another module.<br><br>**Two tests assert properties of the transition table rather than transitions.** Every state has a row, and every state can reach `ARCHIVED` — because `REQ-PRIV-006` deletion runs from there, so a state that cannot reach it is a trip nobody can ever delete. Neither is a transition anyone would have written a test for. |
