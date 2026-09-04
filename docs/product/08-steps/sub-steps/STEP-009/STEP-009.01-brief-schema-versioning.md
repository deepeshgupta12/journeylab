---
sub_step_id: STEP-009.01
parent_step: STEP-009
title: Brief schema and immutable versioning
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-CONS-001]
blast_radius_id: TBD
depends_on: [STEP-008.07]
last_updated: 2026-09-04
---

# STEP-009.01 — Brief schema and immutable versioning

## 1. Outcome
A confirmed brief is an immutable version, and every scenario can name the exact brief it was solved against.

## 2. Scope and boundary
**In scope:** `trip_briefs` writes; version-on-confirm; the four constraint-class columns.

**Not in this sub-step:** Extraction (`.04`); the editor UI (`.03`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-CONS-001 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | *(record at execution)* — run `npx gitnexus status` and confirm it matches HEAD |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | `impact` on each symbol to be modified, **each cross-checked against grep** — `RISK-016`: the graph under-reports dependants, reproduced twelve times |
| Migration present? | If this sub-step adds one, `RISK-017` applies: the graph holds one node per `.sql` file, so the blast radius comes from the migration and from **mutation against the deployed schema** |
| Unknown / low-confidence areas | Whether an unconfirmed draft is a brief version or a separate shape. Versioning drafts makes the table noisy; not versioning them loses the edit history. |
| Blast radius | **TBD** — assigned at execution. Pre-assigned numbers in STEP-005 and STEP-006 were wrong in every case, so this record does not invent one |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] Confirm writes a new version; the table already refuses UPDATE (`STEP-006.01`)
- [ ] The four classes stay in four columns — hard, soft, inferred, unresolved
- [ ] A brief with unresolved questions is storable but **not solvable** (`TripBrief.is_solvable`)
- [ ] `confirmed_by_user_id` recorded, because a brief is a statement somebody made
- [ ] Draft state kept out of the versioned table

## 6. Contracts and schema changes
Writes `DATA-005`; consumes `TripBrief` from `STEP-006.03`.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-CONS-001 | integration | A confirmed brief is immutable at the database |
| — | unit | The four classes cannot be merged into one list |
| — | integration | A brief with unresolved questions cannot start a solve |
| — | integration | Each confirmation creates a version, not an update |

**Mutation testing is required**, per the practice established from STEP-004.09
onward: seed a defect for each rule this sub-step claims and confirm a test fails.
A rule no mutant can break is a rule nothing is checking.

## 8. Telemetry, security and accessibility
Brief content is trip content — never in an event payload or a trace attribute.

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
Revert the commit; existing versions stay and remain citable.

## 12. Acceptance criteria
- [ ] Confirmed briefs are immutable
- [ ] Four classes stay separate
- [ ] Unresolved blocks solving
- [ ] Every confirmation is a version

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
| Notes / surprises | **An immutable brief is only useful if something cites it.** `scenarios.brief_id` is already `NOT NULL`, so the lineage exists — but a draft that is edited in place and then confirmed produces a version whose history nobody kept, and the reproducibility claim quietly covers less than it appears to. |
