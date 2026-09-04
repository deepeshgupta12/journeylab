---
sub_step_id: STEP-007.01
parent_step: STEP-007
title: Coverage read model and the public coverage API
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-TRIP-002, REQ-EVID-006]
blast_radius_id: TBD
depends_on: [STEP-006.09]
last_updated: 2026-09-04
---

# STEP-007.01 — Coverage read model and the public coverage API

## 1. Outcome
`API-017` serves the coverage read model STEP-006.09 already builds, and the response names no supplier.

## 2. Scope and boundary
**In scope:** The `GET /coverage` handler; wiring `coverage_read_model` to `Coverage`; the first FastAPI route that serves a product operation.

**Not in this sub-step:** The public page (`.02`); degradation disclosure wiring (`.05`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-TRIP-002, REQ-EVID-006 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | *(record at execution)* — run `npx gitnexus status` and confirm it matches HEAD |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | `impact` on each symbol to be modified, **each cross-checked against grep** — `RISK-016`: the graph under-reports dependants, reproduced twelve times |
| Migration present? | If this sub-step adds one, `RISK-017` applies: the graph holds one node per `.sql` file, so the blast radius comes from the migration and from **mutation against the deployed schema** |
| Unknown / low-confidence areas | This is the **first product route handler in the repository**. Every contract in STEP-004 is `PROPOSED`; making one real will expose whatever the contract left implicit. |
| Blast radius | **TBD** — assigned at execution. Pre-assigned numbers in STEP-005 and STEP-006 were wrong in every case, so this record does not invent one |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] Route handler bound to the contract's `Coverage` schema, generated types rather than hand-written
- [ ] Reads `coverage_read_model` through a tenant-bound unit of work (`STEP-006.04`)
- [ ] **Response carries one aggregate health value** — never a list, never a count, never a supplier name (`REQ-EVID-006`)
- [ ] Cache key includes the tenant (`REQ-SEC-001`) — this is the first cache in the system, so it is also the first time that clause is testable
- [ ] Contract compatibility check passes against the committed baseline

## 6. Contracts and schema changes
Implements `API-017` as declared. **No contract change is expected**, and one would be a finding: the contract was written first precisely so the handler discovers nothing new. If it does, that is `CONTRACT_CHANGE_POLICY` work and a blast-radius record of its own.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-TRIP-002 | contract | The response validates against the committed OpenAPI schema |
| — | security | **No provider name, count or quota appears in any response field** — asserted structurally, as in STEP-005.10 |
| — | integration | Tenant A's coverage request cannot return tenant B's regions |
| — | security | **The cache key includes the tenant** — the first pending R7 vector this closes |
| — | unit | A region with no read-model row is reported as uncovered, not as healthy |

**Mutation testing is required**, per the practice established from STEP-004.09
onward: seed a defect for each rule this sub-step claims and confirm a test fails.
A rule no mutant can break is a rule nothing is checking.

## 8. Telemetry, security and accessibility
Traces carry a tenant-safe correlation ID. **`REQ-SEC-002`'s cache vector becomes testable here** — `test_pending_vector_is_still_absent[cache]` will fire the moment a cache appears, exactly as the outbox placeholder did at STEP-006.06, and a real isolation test is then owed.

## 9. Documentation to update
- [ ] Sub-step completion record
- [ ] [IMPLEMENTATION_LOG](../../../10-logs/IMPLEMENTATION_LOG.md) · [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) · [BUG_REGISTER](../../../10-logs/BUG_REGISTER.md) if applicable
- [ ] Blast-radius record, post-change section
- [ ] Parent step §21 · [MASTER_TRACKER](../../../02-delivery/MASTER_TRACKER.md)

## 10. Regression cross-check (R1–R7)
| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression suite | | All prior sub-steps + every `VERIFIED` step |
| R2 contract compatibility | | No unintended breaking diff |
| R3 graph diff as expected | | `detect_changes()`; by inspection where a migration is involved |
| R4 untested requirements | | Not increased |
| R5 orphan/unowned nodes | | Not increased |
| R6 closed-bug regression tests | | All passing |
| R7 tenant isolation | | **Pass — non-negotiable** |

**Overall:** PASS / FAIL — a FAIL means this sub-step is not done.

## 11. Rollback
Revert the commit; the route disappears and the read model is untouched. No migration.

## 12. Acceptance criteria
- [ ] `GET /coverage` returns the read model, validated against the contract
- [ ] No supplier identity, count or quota is reachable through the API
- [ ] The cache key is tenant-scoped, with a test that fails if it is not
- [ ] A region absent from the read model reads as uncovered

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Commit SHA | — |
| Pushed | — |
| Graph re-indexed at | — |
| `main` green and deployable | — |
| Mutation testing | — |
| Bugs found | — |
| Notes / surprises | **A region missing from the read model must not read as healthy.** The projection is derived, so a rebuild in progress or a consumer that never ran leaves rows absent — and absent must mean *unknown*, not *fine*. This is the same shape as STEP-005.10's untracked dependency, and the same shape as `Unreconciled`: the absence of evidence is not evidence. |
