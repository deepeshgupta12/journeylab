---
sub_step_id: STEP-014.07
parent_step: STEP-014
title: Merge and review state for concurrent edits
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-CONS-010]
blast_radius_id: TBD
depends_on: [STEP-014.06]
last_updated: 2026-09-04
---

# STEP-014.07 — Merge and review state for concurrent edits

## 1. Outcome
Two people editing one trip see each other's changes rather than overwriting them.

## 2. Scope and boundary
**In scope:** Concurrent-edit detection; the review state; conflict presentation.

**Not in this sub-step:** Real-time collaboration.

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
| Unknown / low-confidence areas | Whether Phase 1 needs merge or only detection. Detection plus a clear refusal may be sufficient and is much simpler. |
| Blast radius | **TBD** — assigned at execution. Pre-assigned numbers in STEP-005 and STEP-006 were wrong in every case, so this record does not invent one |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] Concurrent edits detected via optimistic concurrency (`STEP-006.04`) — a version conflict, not a lost update
- [ ] **The loser's edit is preserved and shown**, never discarded
- [ ] A review state where both edits are visible, with neither auto-applied
- [ ] Auto-merge is not attempted where a hard constraint could be affected
- [ ] Conflict presentation is accessible and announced

## 6. Contracts and schema changes
None changed.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-CONS-010 | integration | Concurrent edits produce a conflict, not a lost update |
| — | integration | **The losing edit is preserved and presented** |
| — | integration | No auto-merge where a hard constraint is involved |
| — | browser | The conflict state is announced |

**Mutation testing is required**, per the practice established from STEP-004.09
onward: seed a defect for each rule this sub-step claims and confirm a test fails.
A rule no mutant can break is a rule nothing is checking.

## 8. Telemetry, security and accessibility
Conflict rates.

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
Revert the commit; concurrent edits produce a version conflict with no review surface — safe but abrupt.

## 12. Acceptance criteria
- [ ] Conflicts detected, not lost
- [ ] Losing edit preserved
- [ ] No risky auto-merge
- [ ] Accessible conflict state

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
| Notes / surprises | **Discarding the losing edit is the version that ships first and looks correct** — the version conflict fires, the second writer is told to retry, and their work is gone with no way to recover it. `STEP-006.04` guarantees the *data* is not overwritten; nothing guarantees the *user's intent* survives, and that is this sub-step's job. |
