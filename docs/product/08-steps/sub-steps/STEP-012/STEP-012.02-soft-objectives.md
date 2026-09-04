---
sub_step_id: STEP-012.02
parent_step: STEP-012
title: Soft objectives and named objective profiles
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-CONS-007]
blast_radius_id: TBD
depends_on: [STEP-012.01]
last_updated: 2026-09-04
---

# STEP-012.02 — Soft objectives and named objective profiles

## 1. Outcome
Scenarios differ because they optimise different named objectives, not because of solver noise.

## 2. Scope and boundary
**In scope:** Soft-objective encoding; named profiles; the objective recorded on each scenario.

**Not in this sub-step:** Diversity ranking (`.06`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-CONS-007 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | *(record at execution)* — run `npx gitnexus status` and confirm it matches HEAD |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | `impact` on each symbol to be modified, **each cross-checked against grep** — `RISK-016`: the graph under-reports dependants, reproduced twelve times |
| Migration present? | If this sub-step adds one, `RISK-017` applies: the graph holds one node per `.sql` file, so the blast radius comes from the migration and from **mutation against the deployed schema** |
| Unknown / low-confidence areas | Which profiles matter for a 3–7 day trip. Too many and they blur; too few and comparison is uninteresting. |
| Blast radius | **TBD** — assigned at execution. Pre-assigned numbers in STEP-005 and STEP-006 were wrong in every case, so this record does not invent one |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] Named objective profiles, each recorded on the scenario it produced
- [ ] Soft objectives trade off; **hard constraints never participate in the trade**
- [ ] Weights are data, reviewable without reading the model
- [ ] Two scenarios with the same objective and seed are identical (`REQ-CONS-006`)
- [ ] Objective names are meaningful to a traveller, not internal jargon

## 6. Contracts and schema changes
Writes `scenarios.objective`, already `NOT NULL`.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-CONS-007 | integration | Each profile produces a scenario optimising its stated objective |
| — | unit | **No soft objective can outweigh a hard constraint** |
| — | integration | Same objective and seed produce identical scenarios |
| — | unit | Weights are data and reviewable |

**Mutation testing is required**, per the practice established from STEP-004.09
onward: seed a defect for each rule this sub-step claims and confirm a test fails.
A rule no mutant can break is a rule nothing is checking.

## 8. Telemetry, security and accessibility
Objective selection frequency.

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
Revert the commit; only hard-feasible scenarios exist, with no differentiation between them.

## 12. Acceptance criteria
- [ ] Named profiles recorded per scenario
- [ ] Hard constraints outside the trade
- [ ] Reproducible per objective and seed
- [ ] Weights are data

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
| Notes / surprises | **The moment a hard constraint is expressed as a very large weight, it is a soft constraint with a big number** — and a sufficiently unusual brief will find the case where the number is not big enough. `constraint-class.json` keeps the classes distinct for exactly this reason, and the solver encoding is where the distinction is either preserved or quietly collapsed. |
