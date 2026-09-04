---
sub_step_id: STEP-010.05
parent_step: STEP-010
title: Conflict detection and source hierarchy
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-EVID-002]
blast_radius_id: TBD
depends_on: [STEP-010.04]
last_updated: 2026-09-04
---

# STEP-010.05 — Conflict detection and source hierarchy

## 1. Outcome
Sources that disagree stay visibly in disagreement, with a stated hierarchy for which is preferred and why.

## 2. Scope and boundary
**In scope:** Conflict detection across sources; the source hierarchy; conflict rendering in the pack.

**Not in this sub-step:** The evidence drawer UI (`STEP-013.07`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-EVID-002 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | *(record at execution)* — run `npx gitnexus status` and confirm it matches HEAD |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | `impact` on each symbol to be modified, **each cross-checked against grep** — `RISK-016`: the graph under-reports dependants, reproduced twelve times |
| Migration present? | If this sub-step adds one, `RISK-017` applies: the graph holds one node per `.sql` file, so the blast radius comes from the migration and from **mutation against the deployed schema** |
| Unknown / low-confidence areas | The hierarchy itself. Official beats crowd-sourced is easy; official-but-stale against crowd-sourced-and-current is not. |
| Blast radius | **TBD** — assigned at execution. Pre-assigned numbers in STEP-005 and STEP-006 were wrong in every case, so this record does not invent one |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] Conflicts detected across sources for the same field and window
- [ ] **Conflicts are retained and rendered, never resolved into an average** (`REQ-EVID-002`)
- [ ] A stated hierarchy chooses a *preferred* value; the alternatives remain visible
- [ ] The hierarchy is data, reviewable without reading code
- [ ] Freshness participates: a stale official value does not automatically win

## 6. Contracts and schema changes
Consumes `Evidenced.conflicts[]`, whose shape `BUG-020` fixed.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-EVID-002 | integration | **Conflicting values are both retained and both rendered** |
| — | unit | No conflict is resolved by averaging |
| — | unit | The hierarchy is data and is reviewable |
| — | integration | A stale higher-tier source does not silently beat a fresh lower-tier one |

**Mutation testing is required**, per the practice established from STEP-004.09
onward: seed a defect for each rule this sub-step claims and confirm a test fails.
A rule no mutant can break is a rule nothing is checking.

## 8. Telemetry, security and accessibility
Conflict counts by field class.

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
Revert the commit; conflicts go undetected and the pack presents one value as if uncontested — a `REQ-EVID-002` regression.

## 12. Acceptance criteria
- [ ] Conflicts retained and visible
- [ ] Nothing averaged
- [ ] Hierarchy is data
- [ ] Freshness participates in the choice

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
| Notes / surprises | **The exclusion constraint in STEP-006.02 was deliberately keyed by `source_id` so that cross-source disagreement remains storable** — this sub-step is why. If that key had been wider, the second source's fact would have been rejected at insert and this feature would have had nothing to detect, with the constraint error looking like a data-quality problem. |
