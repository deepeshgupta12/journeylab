---
sub_step_id: STEP-013.09
parent_step: STEP-013
title: Scenario selection and EVT-004
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-CONS-009]
blast_radius_id: TBD
depends_on: [STEP-013.08]
last_updated: 2026-09-04
---

# STEP-013.09 — Scenario selection and EVT-004

## 1. Outcome
Choosing a scenario sets the trip's canonical plan, atomically with the event that announces it.

## 2. Scope and boundary
**In scope:** Selection handler; `trips.canonical_scenario_id`; `EVT-004` through the outbox.

**Not in this sub-step:** Activation (Phase 3).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-CONS-009 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | *(record at execution)* — run `npx gitnexus status` and confirm it matches HEAD |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | `impact` on each symbol to be modified, **each cross-checked against grep** — `RISK-016`: the graph under-reports dependants, reproduced twelve times |
| Migration present? | If this sub-step adds one, `RISK-017` applies: the graph holds one node per `.sql` file, so the blast radius comes from the migration and from **mutation against the deployed schema** |
| Unknown / low-confidence areas | None material. |
| Blast radius | **TBD** — assigned at execution. Pre-assigned numbers in STEP-005 and STEP-006 were wrong in every case, so this record does not invent one |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] Selection writes the canonical pointer and the `EVT-004` outbox row **in one transaction**
- [ ] The trip transitions `scenarios_ready → selected` through the state machine, not by assignment
- [ ] Optimistic concurrency: two selections race to a version conflict, not a lost update
- [ ] Re-selecting a different scenario is allowed and audited
- [ ] Selection is keyboard-accessible and announced

## 6. Contracts and schema changes
Emits `EVT-004` as declared.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-CONS-009 | integration | Selection and `EVT-004` commit or roll back together |
| — | integration | The trip transitions through the state machine |
| — | integration | **Concurrent selections produce a conflict, not a lost update** |
| — | browser | Selection is keyboard-accessible and announced |

**Mutation testing is required**, per the practice established from STEP-004.09
onward: seed a defect for each rule this sub-step claims and confirm a test fails.
A rule no mutant can break is a rule nothing is checking.

## 8. Telemetry, security and accessibility
`EVT-004` carries IDs only.

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
Revert the commit; scenarios can be compared but not chosen.

## 12. Acceptance criteria
- [ ] Pointer and event are atomic
- [ ] State machine enforced
- [ ] Concurrent selection conflicts
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
| Notes / surprises | **Two advisors on one trip selecting different scenarios is a normal Tuesday**, and without the version check the second write wins silently — the first advisor's choice disappears with no error anywhere. `STEP-006.04` made `expected_version` required with no default for exactly this, and the handler has to actually pass the version it read. |
