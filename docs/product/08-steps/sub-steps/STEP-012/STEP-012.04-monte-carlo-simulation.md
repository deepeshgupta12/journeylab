---
sub_step_id: STEP-012.04
parent_step: STEP-012
title: Monte Carlo simulation with calibrated distributions and intervals
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-CONS-008]
blast_radius_id: TBD
depends_on: [STEP-012.03]
last_updated: 2026-09-04
---

# STEP-012.04 — Monte Carlo simulation with calibrated distributions and intervals

## 1. Outcome
Uncertainty is simulated from calibrated distributions, and results are presented as intervals rather than points.

## 2. Scope and boundary
**In scope:** Monte Carlo over the solved plan; distribution calibration; interval computation.

**Not in this sub-step:** Fragility scoring (`.05`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-CONS-008 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | *(record at execution)* — run `npx gitnexus status` and confirm it matches HEAD |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | `impact` on each symbol to be modified, **each cross-checked against grep** — `RISK-016`: the graph under-reports dependants, reproduced twelve times |
| Migration present? | If this sub-step adds one, `RISK-017` applies: the graph holds one node per `.sql` file, so the blast radius comes from the migration and from **mutation against the deployed schema** |
| Unknown / low-confidence areas | **Calibration data does not exist.** Distributions must come from somewhere; inventing their parameters is `BUG-026`'s shape at a much larger scale. |
| Blast radius | **TBD** — assigned at execution. Pre-assigned numbers in STEP-005 and STEP-006 were wrong in every case, so this record does not invent one |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] Distributions declared with their **source and calibration basis**, never invented
- [ ] **An uncalibrated distribution reports unavailable** rather than producing a confident interval
- [ ] Intervals rendered as intervals; a point estimate is never presented as certain (`REQ-EVID-003`)
- [ ] Simulation is reproducible from the seed (`REQ-CONS-006`)
- [ ] Sample count is recorded with the result — an interval from 50 runs is not one from 5,000

## 6. Contracts and schema changes
None changed.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-CONS-008 | integration | Results are intervals, and a point is never rendered as certain |
| — | unit | **An uncalibrated distribution yields unavailable, not a default** |
| — | integration | Simulation is reproducible from the seed |
| — | unit | Sample count travels with the interval |

**Mutation testing is required**, per the practice established from STEP-004.09
onward: seed a defect for each rule this sub-step claims and confirm a test fails.
A rule no mutant can break is a rule nothing is checking.

## 8. Telemetry, security and accessibility
Sample counts and simulation time.

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
Revert the commit; scenarios carry point estimates with no uncertainty — a `REQ-EVID-003` regression.

## 12. Acceptance criteria
- [ ] Distributions declare their calibration basis
- [ ] Uncalibrated reports unavailable
- [ ] Intervals never collapse to certain points
- [ ] Reproducible from seed

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
| Notes / surprises | **A simulation with invented distribution parameters produces confident-looking intervals that mean nothing**, and it is worse than a point estimate because the interval implies the uncertainty was quantified. `BUG-026` was one constant justified by a belief about the world; this is a whole distribution, and the output is specifically designed to look rigorous. |
