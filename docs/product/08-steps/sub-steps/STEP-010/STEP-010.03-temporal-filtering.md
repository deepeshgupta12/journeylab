---
sub_step_id: STEP-010.03
parent_step: STEP-010
title: Temporal filtering on effective windows
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-AI-003, REQ-EVID-005]
blast_radius_id: TBD
depends_on: [STEP-010.02]
last_updated: 2026-09-04
---

# STEP-010.03 — Temporal filtering on effective windows

## 1. Outcome
Evidence is filtered on when it is true, not on when it was fetched.

## 2. Scope and boundary
**In scope:** Effective-window filtering in retrieval, using `domain.temporal.effective_during`.

**Not in this sub-step:** Freshness thresholds (`.06`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-AI-003, REQ-EVID-005 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | *(record at execution)* — run `npx gitnexus status` and confirm it matches HEAD |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | `impact` on each symbol to be modified, **each cross-checked against grep** — `RISK-016`: the graph under-reports dependants, reproduced twelve times |
| Migration present? | If this sub-step adds one, `RISK-017` applies: the graph holds one node per `.sql` file, so the blast radius comes from the migration and from **mutation against the deployed schema** |
| Unknown / low-confidence areas | None material — the helpers exist and name their axis. |
| Blast radius | **TBD** — assigned at execution. Pre-assigned numbers in STEP-005 and STEP-006 were wrong in every case, so this record does not invent one |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] Retrieval filters with `effective_during`, never `observed_since`
- [ ] A fact whose window does not cover the trip is a **coverage gap**, recorded in the report
- [ ] Partial cover does not count as cover (`TemporalValidity.covers`)
- [ ] Open-ended windows are included: absent is not expired
- [ ] No raw axis comparison in retrieval code — the helpers are the only path

## 6. Contracts and schema changes
None changed.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-DATA-007 | integration | A fresh fact outside the trip window is excluded and recorded as a gap |
| — | integration | A four-month-old seasonal fact covering the trip is included |
| — | unit | Partial cover is a gap, not a fact about the uncovered days |
| — | structural | **Retrieval contains no raw `observed_at` comparison** |

**Mutation testing is required**, per the practice established from STEP-004.09
onward: seed a defect for each rule this sub-step claims and confirm a test fails.
A rule no mutant can break is a rule nothing is checking.

## 8. Telemetry, security and accessibility
Gap counts per pack.

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
Revert the commit; retrieval returns facts regardless of applicability, which is a correctness regression rather than a feature loss.

## 12. Acceptance criteria
- [ ] Filtering uses the effective axis only
- [ ] Out-of-window facts become recorded gaps
- [ ] Partial cover is a gap
- [ ] No raw axis comparisons

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
| Notes / surprises | **`DATA_ARCHITECTURE` §3 calls this the most common source of wrong travel plans**, and STEP-006.02 built the helpers precisely so the axis choice is a word somebody types. The regression is not a wrong filter — it is a developer writing `observed_at > x` directly because it was quicker, in a query nobody reads again. |
