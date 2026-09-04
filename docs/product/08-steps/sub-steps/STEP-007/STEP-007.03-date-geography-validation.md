---
sub_step_id: STEP-007.03
parent_step: STEP-007
title: Date and geography validation with honest refusal states
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-TRIP-001, REQ-TRIP-002]
blast_radius_id: TBD
depends_on: [STEP-007.02]
last_updated: 2026-09-04
---

# STEP-007.03 — Date and geography validation with honest refusal states

## 1. Outcome
A request outside coverage is refused with an explanation and produces no partial simulation.

## 2. Scope and boundary
**In scope:** Date-range and destination validation; the refusal surface; `CoverageModel.assess` wired to the UI.

**Not in this sub-step:** Brief capture (`STEP-009`); waitlist (`.04`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-TRIP-001, REQ-TRIP-002 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | *(record at execution)* — run `npx gitnexus status` and confirm it matches HEAD |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | `impact` on each symbol to be modified, **each cross-checked against grep** — `RISK-016`: the graph under-reports dependants, reproduced twelve times |
| Migration present? | If this sub-step adds one, `RISK-017` applies: the graph holds one node per `.sql` file, so the blast radius comes from the migration and from **mutation against the deployed schema** |
| Unknown / low-confidence areas | Trip length bounds. `PRODUCT_SCOPE` says 3–7 days for Phase 1; whether 8 days is a refusal or a warning is a product decision, not an implementation one. |
| Blast radius | **TBD** — assigned at execution. Pre-assigned numbers in STEP-005 and STEP-006 were wrong in every case, so this record does not invent one |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] Dates validated in the destination's zone, using `domain.temporal` — **not the browser's zone**
- [ ] `TripRefused` rendered with its reason, which the type already requires (`STEP-005.10`)
- [ ] **No partial result path** — a refused request produces no itinerary, no scenario, no placeholder
- [ ] Degraded coverage is accepted with its disclosure, not refused
- [ ] Refusal states are announced to assistive technology, not only shown

## 6. Contracts and schema changes
Consumes `API-017`. Trip creation is `STEP-008.06`.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-TRIP-002 | e2e | An out-of-coverage request is refused, with the reason shown |
| — | e2e | **No partial simulation is produced** — asserted on the absence of any scenario artefact |
| — | unit | Dates validate in the destination zone, across a DST boundary |
| — | browser | The refusal is announced, not merely rendered |
| — | unit | A degraded region is accepted with a disclosure rather than refused |

**Mutation testing is required**, per the practice established from STEP-004.09
onward: seed a defect for each rule this sub-step claims and confirm a test fails.
A rule no mutant can break is a rule nothing is checking.

## 8. Telemetry, security and accessibility
Refusal reasons are logged without the destination string until consent, since a destination plus a timestamp is close to a travel plan.

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
Revert the commit; `.02` remains a read-only page.

## 12. Acceptance criteria
- [ ] Out-of-coverage refused with an explanation
- [ ] No partial simulation on any refusal path
- [ ] Dates validated in the destination's zone
- [ ] Refusals announced to assistive technology

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
| Notes / surprises | **Validating dates in the browser's time zone is the bug that will look like a one-day off-by-one and be reported as a rendering issue.** A traveller in Sydney planning Bern crosses the date boundary in the opposite direction to the destination, and `domain.temporal` exists precisely so this is a call somebody makes rather than a default they inherit. |
