---
sub_step_id: STEP-011.01
parent_step: STEP-011
title: Category generation across the five candidate classes
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-CONS-003]
blast_radius_id: TBD
depends_on: [STEP-010.10]
last_updated: 2026-09-04
---

# STEP-011.01 — Category generation across the five candidate classes

## 1. Outcome
Candidates are generated across every class a day needs, not only the ones that are easy to source.

## 2. Scope and boundary
**In scope:** `candidates` writes; generation across the five classes; the pack as the only input.

**Not in this sub-step:** Filtering (`.02`); ranking (`.03`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-CONS-003 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | *(record at execution)* — run `npx gitnexus status` and confirm it matches HEAD |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | `impact` on each symbol to be modified, **each cross-checked against grep** — `RISK-016`: the graph under-reports dependants, reproduced twelve times |
| Migration present? | If this sub-step adds one, `RISK-017` applies: the graph holds one node per `.sql` file, so the blast radius comes from the migration and from **mutation against the deployed schema** |
| Unknown / low-confidence areas | Whether all five classes are sourceable in Switzerland from open data alone (`ADR-016`). A class with no candidates is a coverage gap, not an empty list. |
| Blast radius | **TBD** — assigned at execution. Pre-assigned numbers in STEP-005 and STEP-006 were wrong in every case, so this record does not invent one |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] Generation reads **only the evidence pack** — no live fetch, so a run is reproducible
- [ ] All five classes attempted; a class with no candidates is recorded as a gap
- [ ] Every candidate carries the pack facts it rests on
- [ ] **A class with zero candidates is disclosed**, never silently omitted from the day
- [ ] Generation is deterministic given the same pack and seed

## 6. Contracts and schema changes
Writes `DATA-009`.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-CONS-003 | integration | All five classes are attempted for every day |
| — | integration | **A class with no candidates is recorded as a gap**, not dropped |
| — | unit | Generation is deterministic given pack and seed |
| — | structural | Generation makes no provider call |

**Mutation testing is required**, per the practice established from STEP-004.09
onward: seed a defect for each rule this sub-step claims and confirm a test fails.
A rule no mutant can break is a rule nothing is checking.

## 8. Telemetry, security and accessibility
Candidate counts by class; a class that is persistently empty is a coverage signal.

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
Revert the commit; no candidates exist and the solver has nothing to work with.

## 12. Acceptance criteria
- [ ] All five classes attempted
- [ ] Empty classes disclosed as gaps
- [ ] Deterministic given pack and seed
- [ ] No live fetch during generation

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
| Notes / surprises | **A class that is silently omitted becomes a plan with no lunch in it**, and the traveller cannot tell whether that was a choice or a gap. `REQ-CONS-005` requires infeasibility to return a minimal conflict set rather than a plausible invalid plan; the same honesty applies one layer earlier, where an empty class must be visible rather than absent. |
