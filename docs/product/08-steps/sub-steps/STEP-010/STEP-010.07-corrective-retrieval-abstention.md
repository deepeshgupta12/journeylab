---
sub_step_id: STEP-010.07
parent_step: STEP-010
title: Corrective retrieval and abstention
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-AI-004]
blast_radius_id: TBD
depends_on: [STEP-010.06]
last_updated: 2026-09-04
---

# STEP-010.07 — Corrective retrieval and abstention

## 1. Outcome
When evidence is thin, the product says so instead of filling the gap from model memory.

## 2. Scope and boundary
**In scope:** `AI-004` corrective retrieval; the abstention path; the low-evidence threshold.

**Not in this sub-step:** Explanation generation (`STEP-013.08`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-AI-004 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | *(record at execution)* — run `npx gitnexus status` and confirm it matches HEAD |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | `impact` on each symbol to be modified, **each cross-checked against grep** — `RISK-016`: the graph under-reports dependants, reproduced twelve times |
| Migration present? | If this sub-step adds one, `RISK-017` applies: the graph holds one node per `.sql` file, so the blast radius comes from the migration and from **mutation against the deployed schema** |
| Unknown / low-confidence areas | Where 'low evidence' sits. Too high and the product abstains constantly; too low and it backfills. |
| Blast radius | **TBD** — assigned at execution. Pre-assigned numbers in STEP-005 and STEP-006 were wrong in every case, so this record does not invent one |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] A retrieval pass that recognises insufficient evidence and retries with a widened query
- [ ] **Abstention when evidence remains thin** — never backfill from model memory (`REQ-AI-004`)
- [ ] Abstention is a value the pack carries, not an error — the house pattern from `ProfileUnsupported` onward
- [ ] The abstention threshold is recorded with its rationale, not embedded in a condition
- [ ] Abstention is visible to the traveller as a gap, not hidden as an absence

## 6. Contracts and schema changes
None changed.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-AI-004 | evaluation | **Thin evidence produces abstention, not a plausible answer** |
| — | integration | Abstention is carried in the pack and rendered as a gap |
| — | unit | The threshold has a recorded rationale |
| — | adversarial | A query with no supporting evidence never yields a confident claim |

**Mutation testing is required**, per the practice established from STEP-004.09
onward: seed a defect for each rule this sub-step claims and confirm a test fails.
A rule no mutant can break is a rule nothing is checking.

## 8. Telemetry, security and accessibility
Abstention rate by field class — a rising rate is a coverage signal.

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
Revert the commit; the pack has no abstention path and thin evidence produces confident output. **This is the most consequential rollback in the step.**

## 12. Acceptance criteria
- [ ] Thin evidence abstains
- [ ] Abstention is a carried value
- [ ] The threshold has a rationale
- [ ] No backfill from model memory

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
| Notes / surprises | **Backfilling from model memory is indistinguishable from good retrieval at the point of use** — the answer is fluent, plausible and cited to nothing. `REQ-AI-004` is the requirement, but the test that matters is adversarial: a query about a place with no evidence at all must produce an abstention, and the natural failure is a confident sentence about a museum that does not exist. |
