---
sub_step_id: STEP-012.09
parent_step: STEP-012
title: Degradation ordering under latency pressure
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-NFR-004, REQ-CONS-004]
blast_radius_id: TBD
depends_on: [STEP-012.08]
last_updated: 2026-09-04
---

# STEP-012.09 — Degradation ordering under latency pressure

## 1. Outcome
When time runs short, the product gives up the right things in the right order and says what it gave up.

## 2. Scope and boundary
**In scope:** The degradation ladder; what is sacrificed first; disclosure of what was skipped.

**Not in this sub-step:** Provider degradation (`STEP-005.10`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-NFR-004, REQ-CONS-004 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | *(record at execution)* — run `npx gitnexus status` and confirm it matches HEAD |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | `impact` on each symbol to be modified, **each cross-checked against grep** — `RISK-016`: the graph under-reports dependants, reproduced twelve times |
| Migration present? | If this sub-step adds one, `RISK-017` applies: the graph holds one node per `.sql` file, so the blast radius comes from the migration and from **mutation against the deployed schema** |
| Unknown / low-confidence areas | The ladder's order is a product decision. Fewer scenarios, fewer simulation samples and coarser matrices are all defensible first sacrifices. |
| Blast radius | **TBD** — assigned at execution. Pre-assigned numbers in STEP-005 and STEP-006 were wrong in every case, so this record does not invent one |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] A stated ladder, as data rather than as nested conditionals
- [ ] **Hard-constraint satisfaction is never on the ladder** — it is not something to trade for latency
- [ ] Every degradation is disclosed with what was reduced
- [ ] Degraded output is marked as degraded in the result, not only in a log
- [ ] The ladder is reviewable and its order is testable

## 6. Contracts and schema changes
None changed.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-NFR-004 | integration | Under a latency budget, the ladder is followed in order |
| — | integration | **Hard-constraint satisfaction is never degraded** |
| — | integration | Every degradation is disclosed in the result |
| — | unit | The ladder is data and its order is asserted |

**Mutation testing is required**, per the practice established from STEP-004.09
onward: seed a defect for each rule this sub-step claims and confirm a test fails.
A rule no mutant can break is a rule nothing is checking.

## 8. Telemetry, security and accessibility
Degradation frequency by rung — a rung hit constantly is a capacity signal.

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
Revert the commit; generation either completes or times out with nothing.

## 12. Acceptance criteria
- [ ] Ladder is data and ordered
- [ ] Hard constraints never degraded
- [ ] Every degradation disclosed
- [ ] Degraded results marked

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
| Notes / surprises | **Under time pressure the tempting sacrifice is the expensive check**, and the most expensive check is the one that proves hard constraints hold. `REQ-CONS-004` makes a violation an S1; the ladder must make that rung unreachable by construction rather than by convention, because the pressure to move it will be real and will arrive during an incident. |
