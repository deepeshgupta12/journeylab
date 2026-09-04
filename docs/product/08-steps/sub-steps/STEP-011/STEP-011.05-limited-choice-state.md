---
sub_step_id: STEP-011.05
parent_step: STEP-011
title: Limited-choice state and the wider-radius option
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-CONS-003, REQ-TRIP-002]
blast_radius_id: TBD
depends_on: [STEP-011.04]
last_updated: 2026-09-04
---

# STEP-011.05 — Limited-choice state and the wider-radius option

## 1. Outcome
When choice is genuinely thin, the product says so and offers a specific way to widen it.

## 2. Scope and boundary
**In scope:** The limited-choice state; the wider-radius option; its disclosure.

**Not in this sub-step:** Refusal outside coverage (`STEP-007.03`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-CONS-003, REQ-TRIP-002 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | *(record at execution)* — run `npx gitnexus status` and confirm it matches HEAD |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | `impact` on each symbol to be modified, **each cross-checked against grep** — `RISK-016`: the graph under-reports dependants, reproduced twelve times |
| Migration present? | If this sub-step adds one, `RISK-017` applies: the graph holds one node per `.sql` file, so the blast radius comes from the migration and from **mutation against the deployed schema** |
| Unknown / low-confidence areas | Where 'limited' begins. Too eager and every rural trip is apologetic; too reluctant and the traveller sees three options and assumes that is all there is. |
| Blast radius | **TBD** — assigned at execution. Pre-assigned numbers in STEP-005 and STEP-006 were wrong in every case, so this record does not invent one |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] A limited-choice state distinct from both a full set and a refusal
- [ ] **The reason is specific** — which constraint or which gap narrowed it
- [ ] A wider-radius option that states what it would relax, before it is taken
- [ ] Widening never relaxes a hard constraint; it changes the search, not the requirements
- [ ] The state is announced, not only rendered

## 6. Contracts and schema changes
None changed.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-CONS-003 | e2e | A thin candidate set produces the limited-choice state with a specific reason |
| — | unit | **Widening never relaxes a hard constraint** |
| — | browser | The state is announced to assistive technology |
| — | integration | The wider-radius option states its effect before it is taken |

**Mutation testing is required**, per the practice established from STEP-004.09
onward: seed a defect for each rule this sub-step claims and confirm a test fails.
A rule no mutant can break is a rule nothing is checking.

## 8. Telemetry, security and accessibility
Limited-choice frequency by region — a coverage signal.

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
Revert the commit; thin sets render as ordinary ones and the traveller cannot tell the difference.

## 12. Acceptance criteria
- [ ] Limited choice is a distinct, stated state
- [ ] The reason is specific
- [ ] Widening preserves hard constraints
- [ ] Announced, not only shown

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
| Notes / surprises | **Three options with no explanation reads as three options, not as a shortage** — the traveller assumes the product surveyed everything. That is the same class as `Unreconciled` and `UNAVAILABLE`: the absence of an answer must be a value the product carries, or it silently becomes a confident one. |
