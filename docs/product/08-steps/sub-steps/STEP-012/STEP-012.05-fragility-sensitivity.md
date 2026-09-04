---
sub_step_id: STEP-012.05
parent_step: STEP-012
title: Fragility and sensitivity computation
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-CONS-008]
blast_radius_id: TBD
depends_on: [STEP-012.04]
last_updated: 2026-09-04
---

# STEP-012.05 — Fragility and sensitivity computation

## 1. Outcome
A traveller can see which parts of a plan are fragile and what they are sensitive to.

## 2. Scope and boundary
**In scope:** Fragility scoring; sensitivity analysis; the per-item breakdown.

**Not in this sub-step:** Rendering (`STEP-013.03`).

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
| Unknown / low-confidence areas | What fragility means to a traveller. A statistically fragile connection and a stressful one are not the same thing. |
| Blast radius | **TBD** — assigned at execution. Pre-assigned numbers in STEP-005 and STEP-006 were wrong in every case, so this record does not invent one |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] Fragility computed from the simulation, not from heuristics
- [ ] Sensitivity identifies **which input** a plan is most sensitive to, not just how much
- [ ] Results are per item, so the fragile part is locatable rather than a whole-plan score
- [ ] Fragility derived from an unavailable simulation is itself unavailable
- [ ] The computation is reproducible

## 6. Contracts and schema changes
None changed.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-CONS-008 | integration | Fragility is computed from simulation output, not heuristics |
| — | unit | **Unavailable simulation yields unavailable fragility**, not a default score |
| — | integration | Sensitivity names the input, not only the magnitude |
| — | unit | Per-item scores locate the fragile part |

**Mutation testing is required**, per the practice established from STEP-004.09
onward: seed a defect for each rule this sub-step claims and confirm a test fails.
A rule no mutant can break is a rule nothing is checking.

## 8. Telemetry, security and accessibility
Score distributions.

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
Revert the commit; plans have no fragility signal.

## 12. Acceptance criteria
- [ ] Computed from simulation
- [ ] Unavailable propagates
- [ ] Sensitivity names its input
- [ ] Per-item, not whole-plan

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
| Notes / surprises | **A whole-plan fragility score is unactionable** — the traveller learns their trip is risky and cannot tell which part to change. The value is entirely in locating it, which means the computation must survive being broken down per item rather than aggregated for display convenience. |
