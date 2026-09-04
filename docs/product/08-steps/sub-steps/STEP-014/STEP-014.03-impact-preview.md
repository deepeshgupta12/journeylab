---
sub_step_id: STEP-014.03
parent_step: STEP-014
title: Impact preview with estimated recompute time
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-CONS-010]
blast_radius_id: TBD
depends_on: [STEP-014.02]
last_updated: 2026-09-04
---

# STEP-014.03 — Impact preview with estimated recompute time

## 1. Outcome
Before committing an edit, the traveller sees what it will change and roughly how long it will take.

## 2. Scope and boundary
**In scope:** The impact preview; the recompute estimate; the preview-to-commit flow.

**Not in this sub-step:** The solve itself (`.05`).

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
| Unknown / low-confidence areas | Estimate accuracy. A wrong estimate is worse than none if it is presented confidently. |
| Blast radius | **TBD** — assigned at execution. Pre-assigned numbers in STEP-005 and STEP-006 were wrong in every case, so this record does not invent one |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] Preview computed from the affected set (`.01`), not from a guess
- [ ] **The estimate is presented as an estimate** (`REQ-EVID-003`) — never a countdown
- [ ] The preview names what changes, not only how much
- [ ] Preview is free of side effects: nothing is written until commit
- [ ] Preview is announced and keyboard-reachable

## 6. Contracts and schema changes
None changed.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-CONS-010 | integration | The preview matches what the commit actually changes |
| — | browser | **The estimate is rendered as an estimate**, not as a precise duration |
| — | integration | Preview writes nothing |
| — | browser | Preview is announced and keyboard-reachable |

**Mutation testing is required**, per the practice established from STEP-004.09
onward: seed a defect for each rule this sub-step claims and confirm a test fails.
A rule no mutant can break is a rule nothing is checking.

## 8. Telemetry, security and accessibility
Estimate accuracy — predicted against actual, which is the only way to know it is useful.

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
Revert the commit; edits apply without preview.

## 12. Acceptance criteria
- [ ] Preview derived from the affected set
- [ ] Estimate presented as an estimate
- [ ] No side effects
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
| Notes / surprises | **A preview that does not match what the commit does is worse than no preview** — the traveller approves one change and receives another, and they have no reason to check. Comparing preview against actual outcome is the only test that catches drift between the two code paths, and they will drift, because they are two code paths. |
