---
sub_step_id: STEP-010.10
parent_step: STEP-010
title: Retrieval and abstention evaluation sets
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-AI-004, REQ-AI-009]
blast_radius_id: TBD
depends_on: [STEP-010.09]
last_updated: 2026-09-04
---

# STEP-010.10 — Retrieval and abstention evaluation sets

## 1. Outcome
Retrieval quality and abstention behaviour are measured, with the degenerate answers excluded.

## 2. Scope and boundary
**In scope:** The retrieval corpus; abstention evaluation; the regression gate.

**Not in this sub-step:** Extraction evaluation (`STEP-009.08`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-AI-004, REQ-AI-009 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | *(record at execution)* — run `npx gitnexus status` and confirm it matches HEAD |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | `impact` on each symbol to be modified, **each cross-checked against grep** — `RISK-016`: the graph under-reports dependants, reproduced twelve times |
| Migration present? | If this sub-step adds one, `RISK-017` applies: the graph holds one node per `.sql` file, so the blast radius comes from the migration and from **mutation against the deployed schema** |
| Unknown / low-confidence areas | **The corpus does not exist and must be hand-built.** Its limits must be stated, as `BR-046` §8 did — a hand-built adversarial set measures correctness on hard cases, not production accuracy. |
| Blast radius | **TBD** — assigned at execution. Pre-assigned numbers in STEP-005 and STEP-006 were wrong in every case, so this record does not invent one |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] Labelled queries with expected evidence and expected abstentions
- [ ] **Two metrics, because each alone has a degenerate answer**: retrieving nothing abstains perfectly; retrieving everything recalls perfectly
- [ ] Numbers pinned by a test so degradation is loud
- [ ] An adversarial subset covering injection and evidence-free queries
- [ ] Corpus provenance and limits recorded alongside the numbers

## 6. Contracts and schema changes
None.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-AI-004 | evaluation | Retrieval precision and recall on the labelled set |
| — | evaluation | **Abstention rate measured against expected abstentions**, not in isolation |
| — | meta | Recorded numbers are pinned |
| — | adversarial | Evidence-free queries abstain in every case |

**Mutation testing is required**, per the practice established from STEP-004.09
onward: seed a defect for each rule this sub-step claims and confirm a test fails.
A rule no mutant can break is a rule nothing is checking.

## 8. Telemetry, security and accessibility
Offline.

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
Revert the commit; retrieval and abstention ship unmeasured.

## 12. Acceptance criteria
- [ ] Corpus exists with stated provenance
- [ ] Both metrics measured and pinned
- [ ] Adversarial subset included
- [ ] A regression gate exists

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
| Notes / surprises | **Abstention has the same degenerate answer as precision did in STEP-005.07 and STEP-009.08 — abstain from everything and score perfectly.** Third occurrence of the pattern, which is enough to treat as a rule: any metric with a trivially optimal degenerate strategy needs its counterpart measured in the same breath, or the number is decoration. |
