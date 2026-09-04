---
sub_step_id: STEP-008.06
parent_step: STEP-008
title: Trip lifecycle: create, duplicate, archive, export, delete
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-TRIP-003, REQ-TRIP-005]
blast_radius_id: TBD
depends_on: [STEP-008.05]
last_updated: 2026-09-04
---

# STEP-008.06 — Trip lifecycle: create, duplicate, archive, export, delete

## 1. Outcome
A trip moves through its full lifecycle, and every transition is one the state machine allows.

## 2. Scope and boundary
**In scope:** Trip CRUD; duplication; archive; export; delete; the `TripAggregate` state machine wired to real handlers.

**Not in this sub-step:** Brief capture (`STEP-009`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-TRIP-003, REQ-TRIP-005 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | *(record at execution)* — run `npx gitnexus status` and confirm it matches HEAD |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | `impact` on each symbol to be modified, **each cross-checked against grep** — `RISK-016`: the graph under-reports dependants, reproduced twelve times |
| Migration present? | If this sub-step adds one, `RISK-017` applies: the graph holds one node per `.sql` file, so the blast radius comes from the migration and from **mutation against the deployed schema** |
| Unknown / low-confidence areas | What duplication copies. A duplicated trip that carries the original's evidence pack is reproducible; one that re-fetches is current. Both are defensible and they are different products. |
| Blast radius | **TBD** — assigned at execution. Pre-assigned numbers in STEP-005 and STEP-006 were wrong in every case, so this record does not invent one |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] Handlers bound to `TripAggregate.transition_to`, so no path bypasses the transition table
- [ ] Duplication decision recorded explicitly — pack carried or re-fetched, with the reason
- [ ] Archive is reversible; delete is not, and the UI must not present them as neighbours
- [ ] Export includes the scenario lineage, so an exported trip is reproducible
- [ ] Optimistic concurrency on every mutation (`STEP-006.04`)

## 6. Contracts and schema changes
Implements the trip operations declared in `STEP-004`.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-TRIP-005 | e2e | A trip moves create → brief → archive through allowed transitions only |
| — | integration | An invalid transition is refused by the handler, not just by the model |
| — | integration | Two concurrent edits produce a version conflict rather than a lost update |
| — | e2e | A duplicated trip's lineage points at what it actually used |

**Mutation testing is required**, per the practice established from STEP-004.09
onward: seed a defect for each rule this sub-step claims and confirm a test fails.
A rule no mutant can break is a rule nothing is checking.

## 8. Telemetry, security and accessibility
Trip lifecycle events carry IDs only (`EVENT_CONTRACTS` §2).

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
Revert the commit; trips already created stay and remain readable.

## 12. Acceptance criteria
- [ ] All lifecycle operations available and state-machine bound
- [ ] Invalid transitions refused at the handler
- [ ] Concurrent edits produce a conflict, not a lost update
- [ ] Duplication's semantics are recorded, not implied

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
| Notes / surprises | **Archive and delete next to each other in a menu is how somebody deletes a trip they meant to keep.** The model makes one reversible and one terminal; the interface has to make that difference visible, and `REQ-A11Y-001` means the difference must be conveyed to a screen reader too, not only by colour or position. |
