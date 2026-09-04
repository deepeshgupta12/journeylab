---
sub_step_id: STEP-013.06
parent_step: STEP-013
title: Material-difference detection and confidence ranges
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-CONS-009, REQ-CONS-008]
blast_radius_id: TBD
depends_on: [STEP-013.05]
last_updated: 2026-09-04
---

# STEP-013.06 — Material-difference detection and confidence ranges

## 1. Outcome
Differences between scenarios are shown only when they are larger than the uncertainty around them.

## 2. Scope and boundary
**In scope:** Material-difference detection; confidence-range rendering; the not-meaningfully-different state.

**Not in this sub-step:** Diversity ranking (`STEP-012.06`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-CONS-009, REQ-CONS-008 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | *(record at execution)* — run `npx gitnexus status` and confirm it matches HEAD |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | `impact` on each symbol to be modified, **each cross-checked against grep** — `RISK-016`: the graph under-reports dependants, reproduced twelve times |
| Migration present? | If this sub-step adds one, `RISK-017` applies: the graph holds one node per `.sql` file, so the blast radius comes from the migration and from **mutation against the deployed schema** |
| Unknown / low-confidence areas | The materiality threshold, which depends on `STEP-012.04`'s intervals being calibrated. |
| Blast radius | **TBD** — assigned at execution. Pre-assigned numbers in STEP-005 and STEP-006 were wrong in every case, so this record does not invent one |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] A difference is material only if it **exceeds the confidence intervals** around both values
- [ ] Non-material differences are shown as *not meaningfully different*, not as small numbers
- [ ] **Two scenarios that differ by less than their uncertainty are disclosed as equivalent** — `RISK-002`'s visible symptom
- [ ] Ranges rendered as ranges throughout
- [ ] Materiality is computed, not styled

## 6. Contracts and schema changes
Consumes `Evidenced` and the simulation output.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-CONS-009 | integration | A difference smaller than its confidence interval is not presented as a difference |
| — | browser | **Near-identical scenarios are labelled as such** |
| — | unit | Materiality is computed from intervals, not from a fixed percentage |
| — | browser | Ranges are conveyed non-visually |

**Mutation testing is required**, per the practice established from STEP-004.09
onward: seed a defect for each rule this sub-step claims and confirm a test fails.
A rule no mutant can break is a rule nothing is checking.

## 8. Telemetry, security and accessibility
Material-difference counts per comparison — persistently zero is `RISK-002` materialising.

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
Revert the commit; every numeric difference is presented as meaningful.

## 12. Acceptance criteria
- [ ] Materiality computed against intervals
- [ ] Non-material differences labelled
- [ ] Ranges rendered as ranges
- [ ] Computed, not styled

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
| Notes / surprises | **Presenting a 3-minute difference between two scenarios as a reason to choose one is the product lying with true numbers** — the figure is accurate and the implication is not, because the simulation's interval is wider than the gap. This is where `REQ-EVID-003`'s spirit reaches comparison: an estimate presented as a distinction is the same error as an estimate presented as confirmed. |
