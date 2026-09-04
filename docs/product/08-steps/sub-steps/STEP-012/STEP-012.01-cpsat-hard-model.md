---
sub_step_id: STEP-012.01
parent_step: STEP-012
title: CP-SAT hard-constraint model and minimal conflict extraction
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-CONS-004, REQ-CONS-005]
blast_radius_id: TBD
depends_on: [STEP-011.05]
last_updated: 2026-09-04
---

# STEP-012.01 — CP-SAT hard-constraint model and minimal conflict extraction

## 1. Outcome
Hard constraints are never violated, and an infeasible brief returns the smallest set of constraints that conflict.

## 2. Scope and boundary
**In scope:** The CP-SAT model; hard-constraint encoding; minimal conflict extraction.

**Not in this sub-step:** Soft objectives (`.02`); simulation (`.04`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-CONS-004, REQ-CONS-005 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | *(record at execution)* — run `npx gitnexus status` and confirm it matches HEAD |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | `impact` on each symbol to be modified, **each cross-checked against grep** — `RISK-016`: the graph under-reports dependants, reproduced twelve times |
| Migration present? | If this sub-step adds one, `RISK-017` applies: the graph holds one node per `.sql` file, so the blast radius comes from the migration and from **mutation against the deployed schema** |
| Unknown / low-confidence areas | Conflict-set minimality cost. A truly minimal set may require many solver calls, and `REQ-NFR-004` bounds latency. |
| Blast radius | **TBD** — assigned at execution. Pre-assigned numbers in STEP-005 and STEP-006 were wrong in every case, so this record does not invent one |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] Every hard constraint encoded in the model — **none enforced in post-processing**
- [ ] **Zero hard-constraint violations in delivered scenarios** (`REQ-CONS-004`) — an S1 if breached
- [ ] Infeasibility returns a **minimal conflict set**, never a plausible invalid plan (`REQ-CONS-005`)
- [ ] Infeasible and failed stay distinct, as `TripAggregate` already models them
- [ ] The model is reproducible from the pack, config and seed

## 6. Contracts and schema changes
Consumes `ConflictSet` as declared.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-CONS-004 | property | **No delivered scenario violates a hard constraint** — adversarial briefs |
| — | integration | An infeasible brief returns a minimal conflict set |
| — | unit | A conflict set is minimal: removing any member makes it feasible |
| — | integration | Infeasible and failed produce different states and different recovery paths |

**Mutation testing is required**, per the practice established from STEP-004.09
onward: seed a defect for each rule this sub-step claims and confirm a test fails.
A rule no mutant can break is a rule nothing is checking.

## 8. Telemetry, security and accessibility
Solve time, conflict-set size; no constraint content.

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
Revert the commit; no scenarios can be generated at all.

## 12. Acceptance criteria
- [ ] All hard constraints in the model, none post-processed
- [ ] Zero violations on adversarial briefs
- [ ] Conflict sets are minimal and proven so
- [ ] Infeasible ≠ failed

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
| Notes / surprises | **A constraint enforced after the solve is a constraint the solver optimised against.** It will produce a plan that violates it, get corrected, and the correction will look like a bug in the fixer rather than in the model. `REQ-CONS-004` calls a violation an S1, and the only defensible place for a hard constraint is inside the model. |
