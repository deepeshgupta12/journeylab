---
sub_step_id: STEP-013.03
parent_step: STEP-013
title: Budget ledger and scorecard with score components
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-CONS-009, REQ-EVID-003]
blast_radius_id: TBD
depends_on: [STEP-013.02]
last_updated: 2026-09-04
---

# STEP-013.03 — Budget ledger and scorecard with score components

## 1. Outcome
Costs add up, estimates are visibly estimates, and a score can be taken apart.

## 2. Scope and boundary
**In scope:** The budget ledger; the scorecard; score-component breakdown.

**Not in this sub-step:** Evidence citations (`.07`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-CONS-009, REQ-EVID-003 | See §12 | See §7 |

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
- [ ] Money as integer minor units throughout; **no float arithmetic in the ledger**
- [ ] **An estimate is never rendered as confirmed** (`REQ-EVID-003`) — the distinction is visual and semantic
- [ ] Score components shown individually and summing to the total
- [ ] Mixed currencies are shown as mixed, never converted without a stated rate and date
- [ ] Fragility from `STEP-012.05` shown per item, where it is actionable

## 6. Contracts and schema changes
Consumes `Money` and `Evidenced`.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-EVID-003 | browser | **An estimate is visibly and semantically distinct from a confirmed value** |
| — | unit | Ledger totals are computed in integer minor units |
| — | unit | Score components sum to the reported score |
| — | browser | Mixed currencies are not silently converted |

**Mutation testing is required**, per the practice established from STEP-004.09
onward: seed a defect for each rule this sub-step claims and confirm a test fails.
A rule no mutant can break is a rule nothing is checking.

## 8. Telemetry, security and accessibility
None.

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
Revert the commit; scenarios have no cost breakdown.

## 12. Acceptance criteria
- [ ] Integer minor units end to end
- [ ] Estimates never look confirmed
- [ ] Components sum to the total
- [ ] No silent conversion

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
| Notes / surprises | **`REQ-EVID-003` — an estimate is never rendered as confirmed — is a rendering requirement, which means it is enforced in the layer with the least testing.** A styled badge is easy to lose in a refactor and impossible to notice in review; the distinction has to be semantic as well as visual, so a screen reader conveys it and a test can assert it. |
