---
sub_step_id: STEP-006.02
parent_step: STEP-006
title: Temporal model: observed, effective and recorded time
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-DATA-007, REQ-DATA-005]
blast_radius_id: BR-041
depends_on: [STEP-006.01]
last_updated: 2026-08-05
---

# STEP-006.02 — Temporal model: observed, effective and recorded time

## 1. Outcome
Every fact table carries three distinct time axes, and queries filter on the correct one — the single highest-value correctness decision in the data layer.

## 2. Scope and boundary
**In scope:** Temporal columns on all fact tables; helper types; query helpers enforcing correct axis use; DST-aware date handling.

**Not in this sub-step:** Freshness thresholds (`STEP-005.08`); UI display.

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-DATA-007, REQ-DATA-005 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | *(record at execution)* — run `npx gitnexus status` and confirm it matches HEAD. **Application code has been indexed since STEP-002.02**, so a `BLOCKED` result here is a real finding to investigate, not the expected default. |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | KG-Q-015 `detect_changes()`; KG-Q-006 once symbols exist |
| Unknown / low-confidence areas | None material — this is well-determined, just easy to get wrong |
| Blast radius | BR-041 — scored at execution; **confidence capped while the graph is BLOCKED** |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] `observed_at`, `effective_from`, `effective_to`, `recorded_at` on every fact table
- [ ] Exclusion or overlap constraints where two facts cannot both be effective
- [ ] **Query helpers that make axis choice explicit** — solvers filter on effective time, freshness checks on observed time
- [ ] Local dates stored with an IANA zone, never naive
- [ ] Property-based tests over DST transitions and seasonal windows

## 6. Contracts and schema changes
Contracts are declared in [STEP-004](../../STEP-004-contract-first-platform-apis.md); this sub-step consumes them. Any change follows [CONTRACT_CHANGE_POLICY](../../../04-contracts/CONTRACT_CHANGE_POLICY.md).

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-DATA-007 | property | Effective-window queries correct across DST transitions |
| — | property | A fresh fact outside the trip window is excluded, not used |
| — | unit | Duration across a DST boundary is computed correctly |

## 8. Telemetry, security and accessibility
Traces carry tenant-safe correlation IDs; no PII in telemetry. Any user-facing surface is keyboard and screen-reader complete (`REQ-A11Y-001`) and completable without the map (`REQ-A11Y-003`).

## 9. Documentation to update
- [ ] Sub-step completion record
- [ ] [IMPLEMENTATION_LOG](../../../10-logs/IMPLEMENTATION_LOG.md) · [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) · [BUG_REGISTER](../../../10-logs/BUG_REGISTER.md) if applicable
- [ ] `BR-041` post-change section
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
- [ ] Three axes present on every fact table
- [ ] Query helpers enforce correct axis usage
- [ ] DST and seasonal property tests pass
- [ ] No naive local timestamps anywhere

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Commit SHA | — |
| Pushed | — |
| Graph re-indexed at | — |
| `main` green and deployable | — |
| Bugs found | — |
| Notes / surprises | This is the defect class most likely to reach production unnoticed, because both wrong answers look plausible in a test fixture that avoids DST. |
