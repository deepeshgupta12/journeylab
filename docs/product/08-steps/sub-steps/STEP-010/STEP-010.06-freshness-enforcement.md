---
sub_step_id: STEP-010.06
parent_step: STEP-010
title: Freshness enforcement by field class
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-EVID-005, REQ-DATA-005]
blast_radius_id: TBD
depends_on: [STEP-010.05]
last_updated: 2026-09-04
---

# STEP-010.06 — Freshness enforcement by field class

## 1. Outcome
Stale facts are marked, and stale critical facts block the options that rest on them.

## 2. Scope and boundary
**In scope:** Applying `STEP-005.08`'s registry at pack-assembly time; staleness marking; blocking behaviour.

**Not in this sub-step:** Scenario confidence (`STEP-012`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-EVID-005, REQ-DATA-005 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | *(record at execution)* — run `npx gitnexus status` and confirm it matches HEAD |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | `impact` on each symbol to be modified, **each cross-checked against grep** — `RISK-016`: the graph under-reports dependants, reproduced twelve times |
| Migration present? | If this sub-step adds one, `RISK-017` applies: the graph holds one node per `.sql` file, so the blast radius comes from the migration and from **mutation against the deployed schema** |
| Unknown / low-confidence areas | The thresholds are provisional pending `DEC-005`. The **ordering** is required by `REQ-DATA-005` and holds regardless. |
| Blast radius | **TBD** — assigned at execution. Pre-assigned numbers in STEP-005 and STEP-006 were wrong in every case, so this record does not invent one |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] Freshness assessed at **time of use**, not stored — `assess` takes `now`
- [ ] Blocking classes block the option; advisory classes mark it and publish `staleness_ratio`
- [ ] **The confidence curve stays out of this sub-step** — the scorer owns it, as `STEP-005.08` recorded
- [ ] Applicability is checked before freshness, and reported first when both fail
- [ ] The registry is the single source of thresholds; no second set of numbers

## 6. Contracts and schema changes
None changed.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-EVID-005 | integration | A stale hours fact blocks the option; a stale price marks it |
| — | integration | Freshness is computed at use; a pack assessed twice an hour apart differs |
| — | structural | No second threshold table exists |
| — | unit | Applicability is reported before staleness when both fail |

**Mutation testing is required**, per the practice established from STEP-004.09
onward: seed a defect for each rule this sub-step claims and confirm a test fails.
A rule no mutant can break is a rule nothing is checking.

## 8. Telemetry, security and accessibility
Staleness counts by class.

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
Revert the commit; packs carry stale facts unmarked — a `REQ-EVID-005` regression, not a feature loss.

## 12. Acceptance criteria
- [ ] Blocking and advisory behave differently
- [ ] Freshness computed at use
- [ ] One threshold registry
- [ ] Applicability precedes staleness

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
| Notes / surprises | **A second copy of the thresholds is how the registry stops being authoritative**, and it appears innocently: pack assembly needs a number, the import is awkward, someone writes a constant. `STEP-005.08` deliberately provides no default for an unregistered class so that reaching for the registry is the only thing that works. |
