---
sub_step_id: STEP-013.05
parent_step: STEP-013
title: Synchronized, URL-addressable selection state
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-CONS-009]
blast_radius_id: TBD
depends_on: [STEP-013.04]
last_updated: 2026-09-04
---

# STEP-013.05 — Synchronized, URL-addressable selection state

## 1. Outcome
Selecting an item anywhere selects it everywhere, and the state survives a reload or a shared link.

## 2. Scope and boundary
**In scope:** Selection state across table, timeline and map; URL addressability.

**Not in this sub-step:** Editing (`STEP-014`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-CONS-009 | See §12 | See §7 |

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
- [ ] One selection state, consumed by every surface — not three synchronised copies
- [ ] URL-addressable, so a comparison can be shared or reloaded
- [ ] **Selection is announced** on change, not only rendered
- [ ] Keyboard selection is equivalent to pointer selection in every surface
- [ ] A URL naming a scenario the viewer cannot access denies rather than reveals its existence

## 6. Contracts and schema changes
None changed.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-CONS-009 | browser | Selection in any surface updates every other |
| — | browser | A reloaded URL restores the same selection |
| — | security | **A URL for another tenant's scenario denies without revealing it exists** |
| — | browser | Keyboard selection is equivalent to pointer selection |

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
Revert the commit; surfaces select independently.

## 12. Acceptance criteria
- [ ] One selection state
- [ ] URL-addressable
- [ ] Cross-tenant URLs deny without disclosure
- [ ] Keyboard parity

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
| Notes / surprises | **A URL-addressable scenario is an enumeration surface.** `REQ-SEC-002` already requires denial shape to reveal nothing — the existing `test_enumeration_vector_denial_shape_reveals_nothing` covers the API, and this is the first time a user-facing URL carries a tenant-scoped identifier, so the denial has to be identical whether the scenario is missing or forbidden. |
