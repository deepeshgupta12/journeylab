---
sub_step_id: STEP-012.06
parent_step: STEP-012
title: Scenario diversity ranking
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-CONS-007, REQ-AI-008]
blast_radius_id: TBD
depends_on: [STEP-012.05]
last_updated: 2026-09-04
---

# STEP-012.06 — Scenario diversity ranking

## 1. Outcome
The scenarios offered are meaningfully different from each other, and the difference is measured.

## 2. Scope and boundary
**In scope:** Diversity ranking across scenarios; the material-difference measure.

**Not in this sub-step:** Difference rendering (`STEP-013.06`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-CONS-007, REQ-AI-008 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | *(record at execution)* — run `npx gitnexus status` and confirm it matches HEAD |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | `impact` on each symbol to be modified, **each cross-checked against grep** — `RISK-016`: the graph under-reports dependants, reproduced twelve times |
| Migration present? | If this sub-step adds one, `RISK-017` applies: the graph holds one node per `.sql` file, so the blast radius comes from the migration and from **mutation against the deployed schema** |
| Unknown / low-confidence areas | `RISK-002` again. Candidate diversity (`STEP-011.04`) is necessary and not sufficient — three diverse candidate sets can still produce three similar plans. |
| Blast radius | **TBD** — assigned at execution. Pre-assigned numbers in STEP-005 and STEP-006 were wrong in every case, so this record does not invent one |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] Diversity measured **across delivered scenarios**, not just candidate sets
- [ ] The measure is recorded and pinned by a test
- [ ] Diversity never promotes an infeasible or lower-quality scenario past a feasible better one
- [ ] **Scenarios that are not meaningfully different are disclosed as such**, not presented as three choices
- [ ] `AI-008` ranking has a deterministic fallback (`REQ-AI-007`)

## 6. Contracts and schema changes
None changed.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-CONS-007 | integration | Delivered scenarios meet the recorded diversity measure |
| — | integration | **Near-identical scenarios are disclosed rather than presented as choices** |
| — | unit | Diversity never promotes an infeasible scenario |
| — | integration | The deterministic fallback ranks without a model |

**Mutation testing is required**, per the practice established from STEP-004.09
onward: seed a defect for each rule this sub-step claims and confirm a test fails.
A rule no mutant can break is a rule nothing is checking.

## 8. Telemetry, security and accessibility
Inter-scenario diversity per run — the direct `RISK-002` signal.

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
Revert the commit; scenarios may be near-duplicates.

## 12. Acceptance criteria
- [ ] Diversity measured across scenarios
- [ ] Near-identical sets disclosed
- [ ] Feasibility and quality outrank diversity
- [ ] Fallback works without a model

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
| Notes / surprises | **`RISK-002` is that the product offers three scenarios which are the same trip with different orderings**, and the traveller cannot see it because each looks reasonable alone. Comparison is the product's core value; three indistinguishable options do not fail loudly, they just quietly waste the user's time. |
