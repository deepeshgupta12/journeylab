---
sub_step_id: STEP-009.07
parent_step: STEP-009
title: Interpretation confirmation and EVT-001
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-AI-001, REQ-CONS-001]
blast_radius_id: TBD
depends_on: [STEP-009.06]
last_updated: 2026-09-04
---

# STEP-009.07 — Interpretation confirmation and EVT-001

## 1. Outcome
The traveller sees exactly what the system understood, confirms it, and only then does a brief exist.

## 2. Scope and boundary
**In scope:** The confirmation surface; brief version write; `EVT-001` emission through the outbox.

**Not in this sub-step:** Evidence assembly (`STEP-010`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-AI-001, REQ-CONS-001 | See §12 | See §7 |

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
- [ ] The confirmation surface shows all four classes, with inferred entries marked
- [ ] **Nothing is written until confirmation** — this is `REQ-AI-001`'s authorisation point
- [ ] Confirmation writes the brief version and the `EVT-001` outbox row **in one transaction** (`STEP-006.04`)
- [ ] The traveller can edit anything from the confirmation surface without losing the rest
- [ ] Confirmation is keyboard-complete and announced

## 6. Contracts and schema changes
Emits `EVT-001` as declared. No change.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-AI-001 | e2e | **No brief exists until the traveller confirms** |
| — | integration | The brief version and the `EVT-001` row commit or roll back together |
| — | browser | All four classes are visible at confirmation, inferred distinctly |
| — | axe | Zero violations |

**Mutation testing is required**, per the practice established from STEP-004.09
onward: seed a defect for each rule this sub-step claims and confirm a test fails.
A rule no mutant can break is a rule nothing is checking.

## 8. Telemetry, security and accessibility
`EVT-001` carries IDs only (`EVENT_CONTRACTS` §2).

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
Revert the commit; briefs cannot be confirmed and the step is inert. Emitted events remain valid.

## 12. Acceptance criteria
- [ ] Nothing written before confirmation
- [ ] Brief and event are atomic
- [ ] All classes visible, inferred marked
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
| Notes / surprises | **This is where `ADR-002`'s authorisation boundary is actually enforced**, and it is one transaction: brief version plus outbox row. If the event is emitted outside it, a consumer starts assembling evidence for a brief that rolled back — the phantom event STEP-006.06 exists to make impossible, arriving through the first real producer. |
