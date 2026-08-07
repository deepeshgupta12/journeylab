---
sub_step_id: STEP-005.09
parent_step: STEP-005
title: Reconciliation, backfill and checkpointing
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-DATA-002]
blast_radius_id: BR-038
depends_on: [STEP-005.08]
last_updated: 2026-08-05
---

# STEP-005.09 — Reconciliation, backfill and checkpointing

## 1. Outcome
Ingestion completeness is provable: totals reconcile against the source, and backfill resumes from a checkpoint without duplication.

## 2. Scope and boundary
**In scope:** Reconciliation jobs; backfill runner; checkpoint store; discrepancy alerting.

**Not in this sub-step:** Data-quality expectations ([STEP-006](../../STEP-006-canonical-data-model-and-event-backbone.md)).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-DATA-002 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | *(record at execution)* — run `npx gitnexus status` and confirm it matches HEAD. **Application code has been indexed since STEP-002.02**, so a `BLOCKED` result here is a real finding to investigate, not the expected default. |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | KG-Q-015 `detect_changes()`; KG-Q-006 once symbols exist |
| Unknown / low-confidence areas | Source-side count endpoints may not exist for every provider — fallback reconciliation method needed |
| Blast radius | BR-038 — scored at execution; **confidence capped while the graph is BLOCKED** |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] Per-provider reconciliation comparing ingested totals against source counts
- [ ] Discrepancy threshold that alerts rather than silently tolerating drift
- [ ] Resumable backfill from checkpoint, **idempotent on replay**
- [ ] Backfill progress visible and cancellable
- [ ] Reconciliation results retained as evidence

## 6. Contracts and schema changes
Contracts are declared in [STEP-004](../../STEP-004-contract-first-platform-apis.md); this sub-step consumes them. Any change follows [CONTRACT_CHANGE_POLICY](../../../04-contracts/CONTRACT_CHANGE_POLICY.md).

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-DATA-002 | integration | Reconciliation detects a seeded shortfall |
| — | integration | Backfill replay produces no duplicates |

## 8. Telemetry, security and accessibility
Traces carry tenant-safe correlation IDs; no PII in telemetry. Any user-facing surface is keyboard and screen-reader complete (`REQ-A11Y-001`) and completable without the map (`REQ-A11Y-003`).

## 9. Documentation to update
- [ ] Sub-step completion record
- [ ] [IMPLEMENTATION_LOG](../../../10-logs/IMPLEMENTATION_LOG.md) · [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) · [BUG_REGISTER](../../../10-logs/BUG_REGISTER.md) if applicable
- [ ] `BR-038` post-change section
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
- [ ] Reconciliation runs per provider and detects seeded discrepancies
- [ ] Backfill resumes and is idempotent
- [ ] Discrepancies alert with context

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Commit SHA | — |
| Pushed | — |
| Graph re-indexed at | — |
| `main` green and deployable | — |
| Bugs found | — |
| Notes / surprises | Ingestion that cannot be reconciled is indistinguishable from ingestion that silently lost half its records. |
