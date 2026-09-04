---
sub_step_id: STEP-013.08
parent_step: STEP-013
title: Explanation generation with claim-to-span validation
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-AI-003, REQ-AI-010, REQ-EVID-004]
blast_radius_id: TBD
depends_on: [STEP-013.07]
last_updated: 2026-09-04
---

# STEP-013.08 — Explanation generation with claim-to-span validation

## 1. Outcome
Prose explanations are generated only from pack evidence, and every claim is validated against a span before it is shown.

## 2. Scope and boundary
**In scope:** `AI-003` explanation; claim-to-span validation; the refusal path.

**Not in this sub-step:** Extraction (`STEP-009.04`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-AI-003, REQ-AI-010, REQ-EVID-004 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | *(record at execution)* — run `npx gitnexus status` and confirm it matches HEAD |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | `impact` on each symbol to be modified, **each cross-checked against grep** — `RISK-016`: the graph under-reports dependants, reproduced twelve times |
| Migration present? | If this sub-step adds one, `RISK-017` applies: the graph holds one node per `.sql` file, so the blast radius comes from the migration and from **mutation against the deployed schema** |
| Unknown / low-confidence areas | Validation strictness. Too strict and nothing renders; too loose and the validation is decorative. |
| Blast radius | **TBD** — assigned at execution. Pre-assigned numbers in STEP-005 and STEP-006 were wrong in every case, so this record does not invent one |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] Explanation generated **only from pack content**, never from model memory (`REQ-AI-004`)
- [ ] **Every claim validated against a span before display** — an unvalidated claim is not shown
- [ ] No visa, health, legal or safety guarantees in any output (`REQ-AI-010`), enforced by a refusal list
- [ ] Retrieved content stays data, never instruction (`REQ-SEC-006`)
- [ ] Validation failure degrades to the structured surfaces, which are complete on their own

## 6. Contracts and schema changes
None changed.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-AI-003 | integration | **Every rendered claim resolves to a span in the pack** |
| — | adversarial | No output contains a visa, health, legal or safety guarantee |
| — | integration | An unvalidated claim is withheld, not shown with a caveat |
| — | integration | Generation failure degrades to the structured surfaces |

**Mutation testing is required**, per the practice established from STEP-004.09
onward: seed a defect for each rule this sub-step claims and confirm a test fails.
A rule no mutant can break is a rule nothing is checking.

## 8. Telemetry, security and accessibility
Validation rejection rate — a rising rate means the model is drifting from the evidence.

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
Revert the commit; explanations disappear and the structured surfaces remain complete. **A clean rollback, by design.**

## 12. Acceptance criteria
- [ ] Generated only from pack content
- [ ] Every claim span-validated
- [ ] No prohibited guarantees
- [ ] Degrades to structured surfaces

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
| Notes / surprises | **A fluent explanation is the most trusted surface in the product and the least verifiable by the reader.** `REQ-AI-010` forbids visa, health, legal and safety guarantees precisely because a model will produce them confidently and a traveller will act on them — so the check must be a refusal list applied to output, not an instruction in a prompt that a sufficiently unusual input can talk around. |
