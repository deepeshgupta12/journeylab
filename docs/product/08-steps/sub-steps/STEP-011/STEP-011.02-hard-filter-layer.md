---
sub_step_id: STEP-011.02
parent_step: STEP-011
title: Hard filter layer with recorded exclusion reasons
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-CONS-003, REQ-CONS-005]
blast_radius_id: TBD
depends_on: [STEP-011.01]
last_updated: 2026-09-04
---

# STEP-011.02 — Hard filter layer with recorded exclusion reasons

## 1. Outcome
Every candidate excluded by a hard constraint carries the reason it was excluded.

## 2. Scope and boundary
**In scope:** Hard filtering; `candidates.exclusion_reason` writes; the filter-before-rank ordering.

**Not in this sub-step:** Ranking (`.03`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-CONS-003, REQ-CONS-005 | See §12 | See §7 |

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
- [ ] Hard constraints filter **before** ranking, never after — a filter applied post-rank is a filter that can be outvoted
- [ ] Every exclusion records its reason, in the column that already exists
- [ ] Accessibility exclusions are never relaxed, whatever the score cost
- [ ] Exclusion reasons feed the minimal conflict set (`REQ-CONS-005`)
- [ ] A fully-excluded class produces a stated infeasibility, not an empty result

## 6. Contracts and schema changes
Writes `DATA-009.exclusion_reason`.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-CONS-003 | integration | **A hard filter cannot be bypassed by ranking** — adversarial candidates |
| — | integration | Every excluded candidate has a reason |
| — | unit | An accessibility constraint is never relaxed to improve a score |
| — | integration | Full exclusion produces a stated infeasibility |

**Mutation testing is required**, per the practice established from STEP-004.09
onward: seed a defect for each rule this sub-step claims and confirm a test fails.
A rule no mutant can break is a rule nothing is checking.

## 8. Telemetry, security and accessibility
Exclusion counts by reason class.

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
Revert the commit; hard constraints stop being enforced at candidate level — a `REQ-CONS-004` regression.

## 12. Acceptance criteria
- [ ] Filters precede ranking
- [ ] Every exclusion has a reason
- [ ] Accessibility is never relaxed
- [ ] Full exclusion is stated, not empty

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
| Notes / surprises | **`BUG_REGISTER` already names "hard filter bypassed by ranking" as a class to watch**, and the mechanism is always the same: ranking runs first because it is cheaper to write that way, and a high-scoring candidate survives a constraint it violates. `TST-CONS-003` exists for this and needs adversarial candidates, not representative ones. |
