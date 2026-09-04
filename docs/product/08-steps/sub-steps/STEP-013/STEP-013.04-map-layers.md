---
sub_step_id: STEP-013.04
parent_step: STEP-013
title: MapLibre layers, clustering and list fallback
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-A11Y-003, REQ-CONS-009]
blast_radius_id: TBD
depends_on: [STEP-013.03]
last_updated: 2026-09-04
---

# STEP-013.04 — MapLibre layers, clustering and list fallback

## 1. Outcome
A map that helps, and never one that anything depends on.

## 2. Scope and boundary
**In scope:** MapLibre layers; clustering; the list fallback; map-disabled behaviour.

**Not in this sub-step:** Selection sync (`.05`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-A11Y-003, REQ-CONS-009 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | *(record at execution)* — run `npx gitnexus status` and confirm it matches HEAD |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | `impact` on each symbol to be modified, **each cross-checked against grep** — `RISK-016`: the graph under-reports dependants, reproduced twelve times |
| Migration present? | If this sub-step adds one, `RISK-017` applies: the graph holds one node per `.sql` file, so the blast radius comes from the migration and from **mutation against the deployed schema** |
| Unknown / low-confidence areas | Tile source licensing. `ADR-016` chose open data; tiles are a separate licence question that `RISK-001` touches. |
| Blast radius | **TBD** — assigned at execution. Pre-assigned numbers in STEP-005 and STEP-006 were wrong in every case, so this record does not invent one |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] Map is additive: **every action it offers exists elsewhere first** (`.01`, `.02`)
- [ ] List fallback is the same data, not a reduced version
- [ ] Map failure degrades to the list without an error state
- [ ] Attribution rendered as the tile licence requires (`REQ-DATA-001`)
- [ ] No core action reachable only by clicking the map

## 6. Contracts and schema changes
None changed.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-A11Y-003 | browser | **Every MVP task completes with map rendering disabled** |
| — | browser | A map load failure degrades to the list silently |
| — | browser | No action exists only on the map |
| — | unit | Tile attribution is rendered |

**Mutation testing is required**, per the practice established from STEP-004.09
onward: seed a defect for each rule this sub-step claims and confirm a test fails.
A rule no mutant can break is a rule nothing is checking.

## 8. Telemetry, security and accessibility
Map load failures.

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
Revert the commit; the list surfaces remain complete. **The cleanest rollback in the step**, by design.

## 12. Acceptance criteria
- [ ] Every task completes with the map off
- [ ] Failure degrades silently
- [ ] No map-only actions
- [ ] Attribution rendered

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
| Notes / surprises | **The map is the feature most likely to acquire a unique action** — a click-to-add, a drag-to-reorder — because it is the surface where those gestures feel natural. Each one silently makes `REQ-A11Y-003` false, and the test that catches it is the one that runs the whole task list with rendering disabled, not a component test. |
