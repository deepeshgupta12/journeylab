---
sub_step_id: STEP-014.04
parent_step: STEP-014
title: Protected-item locking
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-CONS-011]
blast_radius_id: TBD
depends_on: [STEP-014.03]
last_updated: 2026-09-04
---

# STEP-014.04 — Protected-item locking

## 1. Outcome
A booked or pinned item cannot be moved by any automated path until the traveller unlocks it.

## 2. Scope and boundary
**In scope:** Protection enforcement across every edit path; the unlock flow.

**Not in this sub-step:** Repair proposals (Phase 3).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-CONS-011 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | *(record at execution)* — run `npx gitnexus status` and confirm it matches HEAD |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | `impact` on each symbol to be modified, **each cross-checked against grep** — `RISK-016`: the graph under-reports dependants, reproduced twelve times |
| Migration present? | If this sub-step adds one, `RISK-017` applies: the graph holds one node per `.sql` file, so the blast radius comes from the migration and from **mutation against the deployed schema** |
| Unknown / low-confidence areas | None material — the model already enforces it. |
| Blast radius | **TBD** — assigned at execution. Pre-assigned numbers in STEP-005 and STEP-006 were wrong in every case, so this record does not invent one |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] Enforcement uses `ItineraryItem.edited`, which already refuses (`STEP-006.03`)
- [ ] **Every edit path goes through the model** — a repair, a replan and a bulk edit are three callers
- [ ] Unlocking is explicit, attributed, and the one edit a protected item accepts
- [ ] Protection state is visible and screen-reader conveyed
- [ ] A refused edit names the protection, not a generic error

## 6. Contracts and schema changes
None changed.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-CONS-011 | integration | **No edit path can move a protected item**, including bulk and automated ones |
| — | unit | Unlocking is the only accepted change on a protected item |
| — | browser | Protection is conveyed to a screen reader |
| — | integration | A refused edit names the protection |

**Mutation testing is required**, per the practice established from STEP-004.09
onward: seed a defect for each rule this sub-step claims and confirm a test fails.
A rule no mutant can break is a rule nothing is checking.

## 8. Telemetry, security and accessibility
Protection refusal counts.

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
Revert the commit; protection exists in the model but not in the UI paths — a `REQ-CONS-011` regression.

## 12. Acceptance criteria
- [ ] All edit paths enforce protection
- [ ] Unlock is explicit and attributed
- [ ] Protection is conveyed non-visually
- [ ] Refusals are specific

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
| Notes / surprises | **`REQ-CONS-011` was written for the automated path, not the manual one.** A traveller moving their own booked flight is at least deliberate; a replan doing it silently is the failure — and the bulk-edit path is the one most likely to call something other than `edited()` because iterating the model felt slow. |
