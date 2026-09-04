---
sub_step_id: STEP-014.01
parent_step: STEP-014
title: Dependency graph and minimal affected-set computation
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-CONS-010]
blast_radius_id: TBD
depends_on: [STEP-013.10]
last_updated: 2026-09-04
---

# STEP-014.01 — Dependency graph and minimal affected-set computation

## 1. Outcome
An edit's consequences are computed precisely, so a small change does not trigger a full re-solve.

## 2. Scope and boundary
**In scope:** The itinerary dependency graph; affected-set computation; minimality.

**Not in this sub-step:** The edit commands (`.02`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-CONS-010 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | *(record at execution)* — run `npx gitnexus status` and confirm it matches HEAD |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | `impact` on each symbol to be modified, **each cross-checked against grep** — `RISK-016`: the graph under-reports dependants, reproduced twelve times |
| Migration present? | If this sub-step adds one, `RISK-017` applies: the graph holds one node per `.sql` file, so the blast radius comes from the migration and from **mutation against the deployed schema** |
| Unknown / low-confidence areas | Graph density. If most items depend on most others, the minimal affected set is the whole day and incremental solving buys nothing. |
| Blast radius | **TBD** — assigned at execution. Pre-assigned numbers in STEP-005 and STEP-006 were wrong in every case, so this record does not invent one |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] Dependencies derived from the itinerary, not declared by hand
- [ ] The affected set is **minimal and proven so** — removing a member leaves a stale item
- [ ] A change with no dependents affects only itself, and that is the common case
- [ ] The computation is reproducible from the scenario version
- [ ] Affected-set size is exposed for the impact preview (`.03`)

## 6. Contracts and schema changes
None changed.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-CONS-010 | unit | The affected set is minimal: removing any member leaves a stale item |
| — | unit | An independent edit affects only itself |
| — | unit | The computation is reproducible |
| — | property | Adversarial itineraries do not produce an under-sized affected set |

**Mutation testing is required**, per the practice established from STEP-004.09
onward: seed a defect for each rule this sub-step claims and confirm a test fails.
A rule no mutant can break is a rule nothing is checking.

## 8. Telemetry, security and accessibility
Affected-set sizes.

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
Revert the commit; every edit triggers a full re-solve, which is slow rather than wrong.

## 12. Acceptance criteria
- [ ] Dependencies derived, not declared
- [ ] Minimality proven
- [ ] Independent edits stay local
- [ ] Reproducible

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
| Notes / surprises | **An affected set that is too small is far worse than one that is too large.** Too large costs time; too small leaves a stale item in a plan that now claims to be consistent — and nothing downstream can detect it, because the scenario version looks complete. The property test must hunt under-sizing specifically, not just check the happy path. |
