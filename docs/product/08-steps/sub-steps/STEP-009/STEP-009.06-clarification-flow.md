---
sub_step_id: STEP-009.06
parent_step: STEP-009
title: Blocking-only clarification flow
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-CONS-002, REQ-AI-005]
blast_radius_id: TBD
depends_on: [STEP-009.05]
last_updated: 2026-09-04
---

# STEP-009.06 — Blocking-only clarification flow

## 1. Outcome
The product asks a question only when it genuinely cannot proceed without the answer.

## 2. Scope and boundary
**In scope:** Unresolved-question surfacing; the blocking test; the clarification UI.

**Not in this sub-step:** Confirmation (`.07`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-CONS-002, REQ-AI-005 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | *(record at execution)* — run `npx gitnexus status` and confirm it matches HEAD |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | `impact` on each symbol to be modified, **each cross-checked against grep** — `RISK-016`: the graph under-reports dependants, reproduced twelve times |
| Migration present? | If this sub-step adds one, `RISK-017` applies: the graph holds one node per `.sql` file, so the blast radius comes from the migration and from **mutation against the deployed schema** |
| Unknown / low-confidence areas | How to decide *blocking* without a solver run. A question is blocking if no feasible plan exists across the possible answers, and that is expensive to establish before `STEP-012`. |
| Blast radius | **TBD** — assigned at execution. Pre-assigned numbers in STEP-005 and STEP-006 were wrong in every case, so this record does not invent one |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] A question is asked **only if it blocks solving** — `REQ-CONS-002`
- [ ] Non-blocking ambiguity is recorded as soft or inferred and surfaced later, not asked about now
- [ ] Each question states what it blocks, so the traveller knows why they are being asked
- [ ] Answering writes back into the brief as a **stated** constraint, not an inferred one
- [ ] No question is asked twice within one brief version

## 6. Contracts and schema changes
None changed.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-CONS-002 | integration | A non-blocking ambiguity produces no question |
| — | integration | A blocking ambiguity blocks the solve until answered |
| — | unit | An answered question becomes a stated constraint, not an inferred one |
| — | browser | Each question names what it blocks |

**Mutation testing is required**, per the practice established from STEP-004.09
onward: seed a defect for each rule this sub-step claims and confirm a test fails.
A rule no mutant can break is a rule nothing is checking.

## 8. Telemetry, security and accessibility
Question counts by class; no question text with trip content.

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
Revert the commit; unresolved questions block solving with no way to resolve them, so `.05` must be reverted with it.

## 12. Acceptance criteria
- [ ] Only blocking questions are asked
- [ ] Each question states what it blocks
- [ ] Answers become stated constraints
- [ ] No repeated questions

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
| Notes / surprises | **A product that asks about everything it is unsure of is a form, not an assistant** — and one that asks about nothing produces a confident plan built on guesses. `REQ-CONS-002` draws the line at *blocking*, which is the only defensible place, and also the expensive one to compute: knowing whether an ambiguity blocks requires knowing whether a plan exists either way. |
