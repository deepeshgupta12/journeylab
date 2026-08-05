---
sub_step_id: STEP-003.02
parent_step: STEP-003
title: Form and input primitives with validation states
status: NOT_STARTED
owners: []
requirement_ids: [REQ-A11Y-001]
blast_radius_id: BR-015
depends_on: [STEP-003.01]
last_updated: 2026-08-05
---

# STEP-003.02 — Form and input primitives with validation states

## 1. Outcome
Accessible inputs, selects, checkboxes and field groups exist with error, warning, disabled and busy states, each announced correctly to assistive technology.

## 2. Scope and boundary
**In scope:** Text, number, date, select, checkbox, radio and fieldset primitives; label/description/error association; inline validation.

**Not in this sub-step:** Product forms — the trip brief editor is [STEP-009](../../STEP-009-trip-brief-and-structured-constraints.md).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-A11Y-001 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | **BLOCKED — static fallback** (no application symbols indexed yet) |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | KG-Q-015 `detect_changes()`; KG-Q-006 once symbols exist |
| Unknown / low-confidence areas | ICU message loading strategy interacts with server components — resolve before STEP-003.07 |
| Blast radius | BR-015 — scored at execution; **confidence capped while the graph is BLOCKED** |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] Inputs with programmatic label, description and error association
- [ ] Validation states announced via live regions without stealing focus
- [ ] Numeric input honouring locale separators
- [ ] **Date input handling time zones explicitly** — never a naive local date
- [ ] Disabled vs. read-only distinguished correctly

## 6. Contracts and schema changes
Contracts are declared in [STEP-004](../../STEP-004-contract-first-platform-apis.md); this sub-step consumes them. Any change here follows [CONTRACT_CHANGE_POLICY](../../../04-contracts/CONTRACT_CHANGE_POLICY.md).

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-A11Y-001 | component | Every primitive is keyboard and screen-reader complete |
| — | component | Errors are announced without focus theft |

## 8. Telemetry, security and accessibility
Traces carry tenant-safe correlation IDs; no PII in telemetry. Any user-facing surface is keyboard and screen-reader complete (`REQ-A11Y-001`) and completable without the map (`REQ-A11Y-003`).

## 9. Documentation to update
- [ ] Sub-step completion record
- [ ] [IMPLEMENTATION_LOG](../../../10-logs/IMPLEMENTATION_LOG.md) · [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) · [BUG_REGISTER](../../../10-logs/BUG_REGISTER.md) if applicable
- [ ] `BR-015` post-change section
- [ ] Parent step §21 · [MASTER_TRACKER](../../../02-delivery/MASTER_TRACKER.md)

## 10. Regression cross-check (R1–R7)
| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression suite | | All prior sub-steps + every `VERIFIED` step |
| R2 contract compatibility | | No unintended breaking diff |
| R3 graph diff as expected | | `detect_changes()` |
| R4 untested requirements | | Not increased |
| R5 orphan/unowned nodes | | Not increased |
| R6 closed-bug regression tests | | All passing |
| R7 tenant isolation | | **Pass — non-negotiable** |

**Overall:** PASS / FAIL — a FAIL means this sub-step is not done.

## 11. Rollback
Revert this sub-step's commit; prior sub-steps stay intact and `main` stays deployable. Schema work uses expand/contract, so the expand phase is reversible.

## 12. Acceptance criteria
- [ ] Every primitive passes axe with zero AA violations
- [ ] Errors announced politely and associated programmatically
- [ ] Locale-aware numeric and date entry verified

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Commit SHA | — |
| Pushed | — |
| Graph re-indexed at | — |
| `main` green and deployable | — |
| Bugs found | — |
| Notes / surprises | Date inputs are where time-zone bugs enter the product; a naive local date here becomes an infeasible itinerary in STEP-012. |
