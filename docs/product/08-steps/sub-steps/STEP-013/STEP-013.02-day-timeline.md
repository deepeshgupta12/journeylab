---
sub_step_id: STEP-013.02
parent_step: STEP-013
title: Day timeline with buffers
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-CONS-009, REQ-A11Y-001]
blast_radius_id: TBD
depends_on: [STEP-013.01]
last_updated: 2026-09-04
---

# STEP-013.02 — Day timeline with buffers

## 1. Outcome
A day is legible as a sequence, with the buffers visible rather than implied.

## 2. Scope and boundary
**In scope:** Timeline rendering; buffer visualisation; the non-visual equivalent.

**Not in this sub-step:** Editing (`STEP-014`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-CONS-009, REQ-A11Y-001 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | *(record at execution)* — run `npx gitnexus status` and confirm it matches HEAD |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | `impact` on each symbol to be modified, **each cross-checked against grep** — `RISK-016`: the graph under-reports dependants, reproduced twelve times |
| Migration present? | If this sub-step adds one, `RISK-017` applies: the graph holds one node per `.sql` file, so the blast radius comes from the migration and from **mutation against the deployed schema** |
| Unknown / low-confidence areas | How to convey a buffer without implying more precision than the simulation supports. |
| Blast radius | **TBD** — assigned at execution. Pre-assigned numbers in STEP-005 and STEP-006 were wrong in every case, so this record does not invent one |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] Timeline rendered from `itinerary_items`, with times in the **destination's zone**
- [ ] **Buffers are visible** — a plan whose slack is invisible looks tighter or looser than it is
- [ ] Every timeline element has a non-visual equivalent (`REQ-A11Y-002`)
- [ ] Durations computed with `elapsed_between`, so a DST day is 23 or 25 hours
- [ ] Protected and completed items are visually and semantically distinct

## 6. Contracts and schema changes
Consumes `ItineraryItem`.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-A11Y-002 | browser | The timeline has a complete non-visual equivalent |
| — | unit | **A day spanning a DST transition renders the correct elapsed durations** |
| — | browser | Buffers are conveyed without relying on colour |
| — | browser | Protected items are distinguishable to a screen reader |

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
Revert the commit; the table remains and comparison still works.

## 12. Acceptance criteria
- [ ] Times in the destination zone
- [ ] Buffers visible
- [ ] Non-visual equivalent complete
- [ ] DST-correct durations

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
| Notes / surprises | **A timeline is the surface where the DST bug from STEP-006.02 becomes visible to a traveller** — 09:00 to 09:00 across spring-forward is 23 hours, and a timeline that lays it out as 24 shows an hour of slack that does not exist. The helper exists; the risk is a component computing its own widths from timestamps because that was simpler than importing it. |
