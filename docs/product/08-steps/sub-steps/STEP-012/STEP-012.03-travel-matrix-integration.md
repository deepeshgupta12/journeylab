---
sub_step_id: STEP-012.03
parent_step: STEP-012
title: Time-dependent travel matrix integration
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-CONS-004, REQ-A11Y-006]
blast_radius_id: TBD
depends_on: [STEP-012.02]
last_updated: 2026-09-04
---

# STEP-012.03 — Time-dependent travel matrix integration

## 1. Outcome
Travel times reflect the time of day and the traveller's mobility profile, and are never substituted.

## 2. Scope and boundary
**In scope:** `services/routing`'s matrix wired into the solver; profile propagation; departure-time dependence.

**Not in this sub-step:** Provider selection (`ADR-018`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-CONS-004, REQ-A11Y-006 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | *(record at execution)* — run `npx gitnexus status` and confirm it matches HEAD |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | `impact` on each symbol to be modified, **each cross-checked against grep** — `RISK-016`: the graph under-reports dependants, reproduced twelve times |
| Migration present? | If this sub-step adds one, `RISK-017` applies: the graph holds one node per `.sql` file, so the blast radius comes from the migration and from **mutation against the deployed schema** |
| Unknown / low-confidence areas | Matrix size against `REQ-NFR-004`'s latency budget. A time-dependent matrix over many candidates is expensive. |
| Blast radius | **TBD** — assigned at execution. Pre-assigned numbers in STEP-005 and STEP-006 were wrong in every case, so this record does not invent one |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] The solver consumes `TravelTime`, which already records profile, departure time and assumptions
- [ ] **`ProfileUnsupported` propagates** — a wheelchair profile the provider cannot route is disclosed, never silently walked
- [ ] No straight-line substitution anywhere in the path (`STEP-005.05`'s prohibition)
- [ ] Cache keys carry licence terms, as `MatrixKey` already requires
- [ ] Departure-time dependence is real: the same pair at 08:00 and 23:00 are different answers

## 6. Contracts and schema changes
Consumes the routing types from `STEP-005.05`.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-A11Y-006 | integration | **A wheelchair profile is never satisfied by walking times** |
| — | integration | `ProfileUnsupported` reaches the traveller as a disclosure |
| — | structural | No straight-line distance appears in the solve path |
| — | unit | The same pair at different departure times yields different durations |

**Mutation testing is required**, per the practice established from STEP-004.09
onward: seed a defect for each rule this sub-step claims and confirm a test fails.
A rule no mutant can break is a rule nothing is checking.

## 8. Telemetry, security and accessibility
Matrix size and computation time.

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
Revert the commit; the solver has no travel times and cannot sequence a day.

## 12. Acceptance criteria
- [ ] Time-dependent matrix in the solve
- [ ] Profile support propagated honestly
- [ ] No straight-line substitution
- [ ] Licence-aware cache keys

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
| Notes / surprises | **STEP-005.05 built `ProfileUnsupported` so a wheelchair user is told the route cannot be computed rather than given a walker's times.** The value only helps if the solver propagates it: the natural implementation treats an unsupported profile as a missing number and falls back, which reintroduces the exact failure the type was created to prevent — with confident nine-minute transfers over a footbridge. |
