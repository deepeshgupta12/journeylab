---
sub_step_id: STEP-006.04
parent_step: STEP-006
title: Repository interfaces and unit-of-work boundaries
status: VERIFIED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-DATA-007, REQ-SEC-001]
blast_radius_id: BR-053
depends_on: [STEP-006.03]
last_updated: 2026-08-21
---

# STEP-006.04 — Repository interfaces and unit-of-work boundaries

## 1. Outcome
Persistence sits behind repository interfaces with explicit transaction boundaries, and every repository operation runs inside a tenant-scoped session.

## 2. Scope and boundary
**In scope:** `apps/api/src/domain/repositories.py`; unit-of-work; tenant-session binding; one-aggregate-per-transaction rule.

**Not in this sub-step:** Read-model projections (`.09`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-DATA-007, REQ-SEC-001 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | ✅ up to date. **NOT BLOCKED** |
| HEAD / indexed commit | `d869ad1` — matched HEAD at pre-change |
| Queries run | `impact` on `bind_tenant`, `RequestContext`, `TripAggregate`, grep cross-checked (`RISK-016`, eighth reproduction) |
| Unknown / low-confidence areas | The `outbox` table is created in `.06`; this sub-step owns only the atomicity of writing to it |
| Blast radius | **[BR-053](../../../10-logs/blast-radius/BR-053-repositories.md)** — MEDIUM, confidence MEDIUM |
| Approval required? | No |

## 5. Implementation plan
- [ ] Repository interfaces per aggregate
- [ ] Unit-of-work with an explicit transaction boundary
- [ ] **One aggregate per transaction** — cross-aggregate consistency via events, never distributed transactions
- [ ] Every operation binds the tenant session
- [ ] Optimistic concurrency via version/ETag on mutable aggregates

## 6. Contracts and schema changes
Contracts are declared in [STEP-004](../../STEP-004-contract-first-platform-apis.md); this sub-step consumes them. Any change follows [CONTRACT_CHANGE_POLICY](../../../04-contracts/CONTRACT_CHANGE_POLICY.md).

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-SEC-001 | integration | Repository operation without tenant context fails |
| — | integration | Concurrent update raises a version conflict |

## 8. Telemetry, security and accessibility
Traces carry tenant-safe correlation IDs; no PII in telemetry. Any user-facing surface is keyboard and screen-reader complete (`REQ-A11Y-001`) and completable without the map (`REQ-A11Y-003`).

## 9. Documentation to update
- [ ] Sub-step completion record
- [ ] [IMPLEMENTATION_LOG](../../../10-logs/IMPLEMENTATION_LOG.md) · [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) · [BUG_REGISTER](../../../10-logs/BUG_REGISTER.md) if applicable
- [ ] `BR-043` post-change section
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
- [x] Repositories cover the aggregates — five, and `ItineraryItem` deliberately is not one
- [x] Transaction boundary is one aggregate, refused structurally
- [x] Tenant session bound on open, and a repository cannot be obtained outside it
- [x] Optimistic concurrency enforced, with **no default** for `expected_version`

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | 2026-08-21 |
| Commit SHA | *(this commit)* |
| Pushed | ✅ |
| Graph re-indexed at | post-commit |
| `main` green and deployable | ✅ |
| Mutation testing | **13 of 13 killed** — 12 of 13 before the binding assertion was tightened |
| Bugs found | None in the code. One in my test, and it was the important one |
| Notes / surprises | **The mutant that survived was the one that mattered.** Flipping `set_config(..., true)` to `false` makes the tenant binding connection-scoped instead of transaction-scoped, so a pooled connection carries one tenant's context into the next tenant's transaction — the exact leak `test_tenant_isolation.sh` has tested at the database since STEP-002.01, reintroduced one layer up. My test asserted that `set_config` was *called*. **Binding happened; binding correctly did not**, and only the mutation run could tell those apart.<br><br>**The tenant is deliberately absent from the `WHERE` clause**, and a test asserts its absence. Adding it would work and would make every future query's correctness depend on remembering it — a second place to get the same thing wrong, with RLS still there to be trusted or not.<br><br>**Writing the outbox row belongs here even though the table belongs to `.06`.** Atomicity is a property of whoever owns the transaction. The test raises inside the block and asserts no event was written, which is what makes a phantom event impossible rather than unlikely. |
