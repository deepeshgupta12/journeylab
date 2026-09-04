---
sub_step_id: STEP-013.01
parent_step: STEP-013
title: Accessible scenario table and CSV export, built first
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-A11Y-002, REQ-A11Y-003, REQ-CONS-009]
blast_radius_id: TBD
depends_on: [STEP-012.10]
last_updated: 2026-09-04
---

# STEP-013.01 — Accessible scenario table and CSV export, built first

## 1. Outcome
Scenarios are comparable in a table before any map exists, so the map can never become load-bearing.

## 2. Scope and boundary
**In scope:** The scenario comparison table; CSV export; column semantics.

**Not in this sub-step:** The map (`.04`); the timeline (`.02`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-A11Y-002, REQ-A11Y-003, REQ-CONS-009 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | *(record at execution)* — run `npx gitnexus status` and confirm it matches HEAD |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | `impact` on each symbol to be modified, **each cross-checked against grep** — `RISK-016`: the graph under-reports dependants, reproduced twelve times |
| Migration present? | If this sub-step adds one, `RISK-017` applies: the graph holds one node per `.sql` file, so the blast radius comes from the migration and from **mutation against the deployed schema** |
| Unknown / low-confidence areas | None material. The ordering is the decision, and it is already made. |
| Blast radius | **TBD** — assigned at execution. Pre-assigned numbers in STEP-005 and STEP-006 were wrong in every case, so this record does not invent one |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] **Built before the map**, deliberately — a table added afterwards is a fallback, and a fallback is what gets skipped
- [ ] Every scenario attribute comparable in the table, not only the visual ones
- [ ] CSV export matching the table exactly (`REQ-A11Y-002`)
- [ ] Keyboard-complete with visible focus and a screen-reader-sensible column order
- [ ] Intervals rendered as intervals; no point estimate presented as certain

## 6. Contracts and schema changes
Consumes `ScenarioSummary` as declared.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-A11Y-002 | browser | The table is keyboard-traversable and screen-reader complete |
| — | browser | **Scenario comparison is fully possible with the map disabled** |
| — | browser | CSV matches the table row for row and column for column |
| — | axe | Zero violations, two device profiles, with the seeded control still failing |

**Mutation testing is required**, per the practice established from STEP-004.09
onward: seed a defect for each rule this sub-step claims and confirm a test fails.
A rule no mutant can break is a rule nothing is checking.

## 8. Telemetry, security and accessibility
No trip content in telemetry.

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
Revert the commit; there is no comparison surface at all. **This is the surface `REQ-A11Y-003` depends on**, so it must not be reverted while the map exists.

## 12. Acceptance criteria
- [ ] Table built before the map
- [ ] Every attribute comparable
- [ ] CSV matches the table
- [ ] axe clean with a working negative control

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
| Notes / surprises | **`REQ-A11Y-003` says no core action may require the map, and building the table first is what makes that structurally true rather than aspirational.** Built afterwards, the table inherits whatever the map's design assumed, and the assumptions that leak in are exactly the ones that make it a second-class surface — which is the state in which nobody notices it breaking. |
