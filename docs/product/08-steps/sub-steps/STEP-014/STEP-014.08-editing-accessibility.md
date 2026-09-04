---
sub_step_id: STEP-014.08
parent_step: STEP-014
title: Keyboard alternatives and editing accessibility
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-A11Y-005, REQ-A11Y-001]
blast_radius_id: TBD
depends_on: [STEP-014.07]
last_updated: 2026-09-04
---

# STEP-014.08 — Keyboard alternatives and editing accessibility

## 1. Outcome
Every edit is possible without a pointer, including anything offered as a drag.

## 2. Scope and boundary
**In scope:** Keyboard equivalents for every edit; drag alternatives; focus and announcement across edits.

**Not in this sub-step:** Comparison surfaces (`STEP-013.10`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-A11Y-005, REQ-A11Y-001 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | *(record at execution)* — run `npx gitnexus status` and confirm it matches HEAD |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | `impact` on each symbol to be modified, **each cross-checked against grep** — `RISK-016`: the graph under-reports dependants, reproduced twelve times |
| Migration present? | If this sub-step adds one, `RISK-017` applies: the graph holds one node per `.sql` file, so the blast radius comes from the migration and from **mutation against the deployed schema** |
| Unknown / low-confidence areas | None material — this is a gate. |
| Blast radius | **TBD** — assigned at execution. Pre-assigned numbers in STEP-005 and STEP-006 were wrong in every case, so this record does not invent one |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] **Every drag interaction has a keyboard equivalent** (`REQ-A11Y-005`) that is discoverable, not hidden
- [ ] Edit results announced, including the affected set and the score delta
- [ ] Focus is preserved across a re-solve, not reset to the page top
- [ ] Undo and revert are keyboard-reachable
- [ ] axe clean during and after every edit, with the seeded control still failing

## 6. Contracts and schema changes
None changed.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-A11Y-005 | browser | **Every edit, including drags, is completable by keyboard alone** |
| — | browser | Edit results and score deltas are announced |
| — | browser | Focus survives a re-solve |
| — | axe | Zero violations during and after an edit, with a working negative control |

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
Revert the commit. **An accessibility regression** — emergency only, and recorded as one.

## 12. Acceptance criteria
- [ ] Every edit keyboard-completable
- [ ] Results announced
- [ ] Focus survives re-solve
- [ ] axe clean with a working control

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
| Notes / surprises | **Drag-to-reorder is the natural interaction for a timeline and the one that excludes keyboard users completely.** `REQ-A11Y-005` requires the alternative to exist; the harder requirement is that it be *discoverable*, because an equivalent nobody can find is an equivalent nobody has. This is also the last accessibility gate before the Phase 1 surfaces are complete, so anything missed here ships. |
