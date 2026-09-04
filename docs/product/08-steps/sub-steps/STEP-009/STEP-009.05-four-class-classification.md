---
sub_step_id: STEP-009.05
parent_step: STEP-009
title: Four-class classification and inferred-field labelling
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-AI-002, REQ-CONS-001]
blast_radius_id: TBD
depends_on: [STEP-009.04]
last_updated: 2026-09-04
---

# STEP-009.05 — Four-class classification and inferred-field labelling

## 1. Outcome
Every extracted constraint is labelled hard, soft, inferred or unresolved — and inferred is visibly not something the traveller said.

## 2. Scope and boundary
**In scope:** Classification into the four classes; inferred-field labelling; the review surface.

**Not in this sub-step:** The clarification flow (`.06`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-AI-002, REQ-CONS-001 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | *(record at execution)* — run `npx gitnexus status` and confirm it matches HEAD |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | `impact` on each symbol to be modified, **each cross-checked against grep** — `RISK-016`: the graph under-reports dependants, reproduced twelve times |
| Migration present? | If this sub-step adds one, `RISK-017` applies: the graph holds one node per `.sql` file, so the blast radius comes from the migration and from **mutation against the deployed schema** |
| Unknown / low-confidence areas | Where the boundary between soft and inferred sits for phrasing like *"ideally somewhere quiet"*. |
| Blast radius | **TBD** — assigned at execution. Pre-assigned numbers in STEP-005 and STEP-006 were wrong in every case, so this record does not invent one |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] Four classes, four fields, as `constraint-class.json` requires
- [ ] **Inferred entries carry their provenance** — what text produced them — and are rendered differently from stated ones
- [ ] An inferred hard constraint is not permitted: inference cannot create a hard requirement
- [ ] Unresolved entries block solving rather than defaulting
- [ ] The traveller can reclassify anything, and reclassification is recorded

## 6. Contracts and schema changes
Writes `DATA-005`'s four columns.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-AI-002 | unit | Each class rejects its seeded misclassification |
| — | unit | **Inference cannot produce a hard constraint** |
| — | browser | Inferred entries are visually and semantically distinct from stated ones |
| — | unit | Reclassification is recorded with who did it |

**Mutation testing is required**, per the practice established from STEP-004.09
onward: seed a defect for each rule this sub-step claims and confirm a test fails.
A rule no mutant can break is a rule nothing is checking.

## 8. Telemetry, security and accessibility
Class counts, never class contents.

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
Revert the commit; extraction output becomes unclassified and therefore unusable, so `.04` must be reverted with it.

## 12. Acceptance criteria
- [ ] Four classes maintained end to end
- [ ] Inferred is never hard
- [ ] Inferred is visibly distinct
- [ ] Reclassification is recorded

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
| Notes / surprises | **`constraint-class.json` says merging inferred into either hard or soft "hides that a machine put words in the traveller's mouth".** The place that happens is the review screen, where showing all constraints in one tidy list is the obvious design — and the traveller confirms a sentence they never said, in a product whose entire premise is that its plans are grounded. |
