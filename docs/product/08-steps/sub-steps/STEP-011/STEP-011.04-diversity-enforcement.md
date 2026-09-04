---
sub_step_id: STEP-011.04
parent_step: STEP-011
title: Diversity enforcement
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-CONS-003]
blast_radius_id: TBD
depends_on: [STEP-011.03]
last_updated: 2026-09-04
---

# STEP-011.04 — Diversity enforcement

## 1. Outcome
The candidate set is varied enough that the scenarios built from it are meaningfully different.

## 2. Scope and boundary
**In scope:** Diversity constraints on the candidate set; category and geography spread.

**Not in this sub-step:** Scenario diversity (`STEP-012.06`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-CONS-003 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | *(record at execution)* — run `npx gitnexus status` and confirm it matches HEAD |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | `impact` on each symbol to be modified, **each cross-checked against grep** — `RISK-016`: the graph under-reports dependants, reproduced twelve times |
| Migration present? | If this sub-step adds one, `RISK-017` applies: the graph holds one node per `.sql` file, so the blast radius comes from the migration and from **mutation against the deployed schema** |
| Unknown / low-confidence areas | The diversity measure. `RISK-002` names scenario sameness as an active risk with exposure 15, and it starts here. |
| Blast radius | **TBD** — assigned at execution. Pre-assigned numbers in STEP-005 and STEP-006 were wrong in every case, so this record does not invent one |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] Diversity enforced across category and geography, not only by score
- [ ] **Diversity is measured, and the measure is recorded** — not asserted
- [ ] Enforcement never overrides a hard constraint to achieve variety
- [ ] A set that cannot be diversified says so rather than returning near-duplicates
- [ ] The measure is reviewable as data

## 6. Contracts and schema changes
None changed.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-CONS-003 | integration | The candidate set meets the recorded diversity measure |
| — | unit | Diversity never overrides a hard constraint |
| — | integration | **An undiversifiable set is disclosed**, not padded with near-duplicates |
| — | meta | The measure is pinned by a test |

**Mutation testing is required**, per the practice established from STEP-004.09
onward: seed a defect for each rule this sub-step claims and confirm a test fails.
A rule no mutant can break is a rule nothing is checking.

## 8. Telemetry, security and accessibility
Diversity scores per run — a falling trend is `RISK-002` materialising.

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
Revert the commit; candidate sets may be homogeneous, which is `RISK-002` unmitigated.

## 12. Acceptance criteria
- [ ] Diversity measured, not asserted
- [ ] Hard constraints always win
- [ ] Undiversifiable sets disclosed
- [ ] The measure is pinned

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
| Notes / surprises | **`RISK-002` (scenario sameness) has exposure 15 and is the second-highest risk in the register**, and it materialises here rather than in the solver — three near-identical candidate sets produce three near-identical scenarios however good the optimiser is. A diversity number that is asserted rather than measured is the same failure as `.08`'s drift check: a metric that reports success without computing anything. |
