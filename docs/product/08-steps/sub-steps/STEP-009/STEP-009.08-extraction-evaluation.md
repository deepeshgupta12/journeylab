---
sub_step_id: STEP-009.08
parent_step: STEP-009
title: Extraction evaluation set and guardrails
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-AI-002, REQ-AI-008]
blast_radius_id: TBD
depends_on: [STEP-009.07]
last_updated: 2026-09-04
---

# STEP-009.08 — Extraction evaluation set and guardrails

## 1. Outcome
Extraction quality is measured against a labelled set, and the numbers are recorded rather than asserted.

## 2. Scope and boundary
**In scope:** The evaluation corpus; precision and recall per class; the regression gate.

**Not in this sub-step:** Retrieval evaluation (`STEP-010.10`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-AI-002, REQ-AI-008 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | *(record at execution)* — run `npx gitnexus status` and confirm it matches HEAD |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | `impact` on each symbol to be modified, **each cross-checked against grep** — `RISK-016`: the graph under-reports dependants, reproduced twelve times |
| Migration present? | If this sub-step adds one, `RISK-017` applies: the graph holds one node per `.sql` file, so the blast radius comes from the migration and from **mutation against the deployed schema** |
| Unknown / low-confidence areas | **The corpus does not exist.** It must be hand-built, and a hand-built adversarial set measures correctness on hard cases rather than production accuracy — the same limit recorded for entity resolution in `BR-046` §8. |
| Blast radius | **TBD** — assigned at execution. Pre-assigned numbers in STEP-005 and STEP-006 were wrong in every case, so this record does not invent one |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] Labelled corpus of traveller prose with expected classification per constraint
- [ ] **Precision reported per class, and the metric that excludes the degenerate answer alongside it** — extracting nothing scores perfect precision
- [ ] Results pinned by a test so they cannot drift silently
- [ ] A regression gate: quality may not fall below the recorded numbers
- [ ] The corpus's provenance and limits stated — hand-built is not a production sample

## 6. Contracts and schema changes
None.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-AI-002 | evaluation | Per-class precision and recall on the labelled set |
| — | evaluation | **Extracting nothing does not score well** — the degenerate answer is excluded explicitly |
| — | meta | The recorded numbers are pinned; a change fails the suite |
| — | evaluation | Adversarial prose does not produce hard constraints |

**Mutation testing is required**, per the practice established from STEP-004.09
onward: seed a defect for each rule this sub-step claims and confirm a test fails.
A rule no mutant can break is a rule nothing is checking.

## 8. Telemetry, security and accessibility
Evaluation runs offline; no traveller data in the corpus.

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
Revert the commit. **Extraction then ships unmeasured**, which is a knowingly worse position than before.

## 12. Acceptance criteria
- [ ] Corpus exists with labels and stated provenance
- [ ] Per-class precision measured and pinned
- [ ] The degenerate answer is excluded by a second metric
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
| Notes / surprises | **Precision alone is satisfiable by extracting nothing** — exactly as it was for entity resolution in STEP-005.07, where a matcher that merges nothing scores 1.000. The second metric is not a refinement; without it the first one is meaningless, and the failure looks like a very cautious model rather than a broken one. |
