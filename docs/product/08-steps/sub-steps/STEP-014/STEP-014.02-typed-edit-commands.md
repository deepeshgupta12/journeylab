---
sub_step_id: STEP-014.02
parent_step: STEP-014
title: Typed edit commands and validation
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-CONS-010]
blast_radius_id: TBD
depends_on: [STEP-014.01]
last_updated: 2026-09-04
---

# STEP-014.02 — Typed edit commands and validation

## 1. Outcome
Edits are typed commands validated before anything changes, not arbitrary mutations.

## 2. Scope and boundary
**In scope:** The edit command vocabulary; validation; the command log.

**Not in this sub-step:** Incremental solve (`.05`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-CONS-010 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | *(record at execution)* — run `npx gitnexus status` and confirm it matches HEAD |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | `impact` on each symbol to be modified, **each cross-checked against grep** — `RISK-016`: the graph under-reports dependants, reproduced twelve times |
| Migration present? | If this sub-step adds one, `RISK-017` applies: the graph holds one node per `.sql` file, so the blast radius comes from the migration and from **mutation against the deployed schema** |
| Unknown / low-confidence areas | The vocabulary's size. Too few commands and users cannot express what they want; too many and each needs its own validation and undo. |
| Blast radius | **TBD** — assigned at execution. Pre-assigned numbers in STEP-005 and STEP-006 were wrong in every case, so this record does not invent one |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] A closed command vocabulary — **no free-form mutation path**
- [ ] Every command validated against hard constraints **before** it is applied
- [ ] Commands are logged, which is what makes undo (`\.06`) and merge (`\.07`) possible
- [ ] A command that would violate a hard constraint is refused with the constraint named
- [ ] Commands are the only way to change a scenario version

## 6. Contracts and schema changes
Consumes `ScenarioEdit` as declared.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-CONS-010 | unit | Each command validates before applying |
| — | unit | **A command violating a hard constraint is refused, with the constraint named** |
| — | structural | No mutation path exists outside the command vocabulary |
| — | integration | Commands are logged in order |

**Mutation testing is required**, per the practice established from STEP-004.09
onward: seed a defect for each rule this sub-step claims and confirm a test fails.
A rule no mutant can break is a rule nothing is checking.

## 8. Telemetry, security and accessibility
Command frequency by type.

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
Revert the commit; scenarios are read-only.

## 12. Acceptance criteria
- [ ] Closed command vocabulary
- [ ] Validation precedes application
- [ ] No path outside the commands
- [ ] Commands logged

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
| Notes / surprises | **A free-form edit path is how `REQ-CONS-004` stops being true after generation.** The solver guarantees zero violations for what it produced; an edit applied without re-validation produces a plan the solver never approved, still carrying the scenario's claim of feasibility. The command vocabulary being *closed* is the property that matters, and it is the one a convenience helper quietly breaks. |
