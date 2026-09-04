---
sub_step_id: STEP-013.10
parent_step: STEP-013
title: Progressive rendering, error boundaries and focus management
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-A11Y-001, REQ-NFR-004]
blast_radius_id: TBD
depends_on: [STEP-013.09]
last_updated: 2026-09-04
---

# STEP-013.10 — Progressive rendering, error boundaries and focus management

## 1. Outcome
The comparison surface stays usable while it loads, and a failing component does not take the page with it.

## 2. Scope and boundary
**In scope:** Progressive rendering; error boundaries; focus management across async transitions.

**Not in this sub-step:** Editing (`STEP-014`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-A11Y-001, REQ-NFR-004 | See §12 | See §7 |

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
- [ ] The table renders first, since it is the surface everything else is optional against
- [ ] Error boundaries around each surface — **a map failure must not remove the table**
- [ ] **Focus is managed across async transitions**, so a screen-reader user is not dropped at the page top
- [ ] Loading states announced, not only shown
- [ ] No layout shift that moves a focused element

## 6. Contracts and schema changes
None changed.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-A11Y-001 | browser | Focus is preserved across async transitions |
| — | browser | **A failing map leaves the table fully usable** |
| — | browser | Loading states are announced |
| — | axe | Zero violations during and after load |

**Mutation testing is required**, per the practice established from STEP-004.09
onward: seed a defect for each rule this sub-step claims and confirm a test fails.
A rule no mutant can break is a rule nothing is checking.

## 8. Telemetry, security and accessibility
Render timings against `REQ-NFR-004`.

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
Revert the commit; the page loads as a unit and a single failure removes everything.

## 12. Acceptance criteria
- [ ] Table renders first
- [ ] Per-surface error boundaries
- [ ] Focus preserved across transitions
- [ ] axe clean during load

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
| Notes / surprises | **Focus loss on async transition is the accessibility bug nobody sees in review**, because it is invisible with a mouse and only appears when a screen-reader user is returned to the top of the page after every update. It is also the most likely regression from any future refactor of this page, which is why the assertion belongs in the browser suite rather than in a component test. |
