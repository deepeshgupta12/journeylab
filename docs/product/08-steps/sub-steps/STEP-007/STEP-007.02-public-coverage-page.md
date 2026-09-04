---
sub_step_id: STEP-007.02
parent_step: STEP-007
title: Public coverage page with limitations and privacy summary
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-TRIP-002, REQ-A11Y-001, REQ-A11Y-002]
blast_radius_id: TBD
depends_on: [STEP-007.01]
last_updated: 2026-09-04
---

# STEP-007.02 — Public coverage page with limitations and privacy summary

## 1. Outcome
A traveller can see, before signing up, which regions are supported and what the honest limitations are.

## 2. Scope and boundary
**In scope:** The `/coverage` page; region list; limitations rendering; the privacy summary; CSV export of the region table.

**Not in this sub-step:** Date validation (`.03`); waitlist (`.04`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-TRIP-002, REQ-A11Y-001, REQ-A11Y-002 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | *(record at execution)* — run `npx gitnexus status` and confirm it matches HEAD |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | `impact` on each symbol to be modified, **each cross-checked against grep** — `RISK-016`: the graph under-reports dependants, reproduced twelve times |
| Migration present? | If this sub-step adds one, `RISK-017` applies: the graph holds one node per `.sql` file, so the blast radius comes from the migration and from **mutation against the deployed schema** |
| Unknown / low-confidence areas | How much limitation detail is useful before it becomes noise. `REQ-TRIP-002` wants an honest scope statement; the failure mode is a wall of caveats nobody reads. |
| Blast radius | **TBD** — assigned at execution. Pre-assigned numbers in STEP-005 and STEP-006 were wrong in every case, so this record does not invent one |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] Region table as the primary surface, **not a map** — `REQ-A11Y-003` says no core action requires one
- [ ] Limitations rendered verbatim from `CoverageRegion.limitations`, not summarised
- [ ] CSV export of the table (`REQ-A11Y-002`)
- [ ] Privacy summary linking to the guest-planning path (`REQ-PRIV-001`) before any account is requested
- [ ] Degraded regions visibly marked, without naming a provider

## 6. Contracts and schema changes
Consumes `API-017`. No change.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-A11Y-002 | browser | The region table is keyboard-traversable and screen-reader complete |
| — | browser | The page is fully usable with map rendering disabled |
| — | unit | Limitations render verbatim; nothing is truncated or summarised away |
| — | browser | CSV export matches the rendered table row for row |
| — | axe | Zero violations across two device profiles |

**Mutation testing is required**, per the practice established from STEP-004.09
onward: seed a defect for each rule this sub-step claims and confirm a test fails.
A rule no mutant can break is a rule nothing is checking.

## 8. Telemetry, security and accessibility
No PII. The page is reachable without a session, so it must not set a tenant-scoped cookie before consent (`REQ-PRIV-001`).

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
Revert the commit. The page is additive and nothing links to it until `.03`.

## 12. Acceptance criteria
- [ ] Regions and limitations visible without an account
- [ ] Completable with the map disabled
- [ ] CSV export matches the table
- [ ] axe clean in both device profiles

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
| Notes / surprises | **The honest scope statement is the product's first promise, and it is made to somebody who has not signed up.** A limitations list that is quietly trimmed to look better is the same defect class as rendering an estimate as confirmed (`REQ-EVID-003`) — it just happens earlier in the funnel, where nobody is measuring. |
