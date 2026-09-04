---
sub_step_id: STEP-014.06
parent_step: STEP-014
title: Undo, redo and one-click revert
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-CONS-010]
blast_radius_id: TBD
depends_on: [STEP-014.05]
last_updated: 2026-09-04
---

# STEP-014.06 — Undo, redo and one-click revert

## 1. Outcome
Any edit can be undone, and the whole session can be reverted to where it started.

## 2. Scope and boundary
**In scope:** Undo and redo over the command log; one-click revert to the original scenario.

**Not in this sub-step:** Concurrent merge (`.07`).

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
| Unknown / low-confidence areas | Undo across a re-solve. Undoing an edit whose solve produced a different plan means restoring a version, not inverting a command. |
| Blast radius | **TBD** — assigned at execution. Pre-assigned numbers in STEP-005 and STEP-006 were wrong in every case, so this record does not invent one |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] Undo restores the **previous scenario version**, not an inverted command — versions are immutable and already exist
- [ ] Redo re-applies the command, re-solving as it does
- [ ] One-click revert to the originally selected scenario, always available
- [ ] **Undo out of order is refused**, as `STEP-006.07`'s operation history already establishes
- [ ] Undo is keyboard-accessible and announced

## 6. Contracts and schema changes
None changed.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-CONS-010 | integration | Undo restores the previous version exactly |
| — | integration | Revert returns to the originally selected scenario |
| — | integration | **Out-of-order undo is refused rather than guessed** |
| — | browser | Undo is keyboard-accessible and announced |

**Mutation testing is required**, per the practice established from STEP-004.09
onward: seed a defect for each rule this sub-step claims and confirm a test fails.
A rule no mutant can break is a rule nothing is checking.

## 8. Telemetry, security and accessibility
Undo and revert rates — high revert rates suggest the edit surface is misleading.

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
Revert the commit; edits become one-way.

## 12. Acceptance criteria
- [ ] Undo restores a version, not an inversion
- [ ] Revert always available
- [ ] Out-of-order undo refused
- [ ] Accessible

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
| Notes / surprises | **Inverting a command is not the same as undoing its effect once a solve ran in between** — the inverse command applied to a re-solved plan produces a third plan that is neither the before nor the after. `scenario_versions` is immutable precisely so undo can restore rather than reconstruct, which is the same reasoning that made `STEP-006.07`'s `Operation.before` hold the full prior grouping. |
