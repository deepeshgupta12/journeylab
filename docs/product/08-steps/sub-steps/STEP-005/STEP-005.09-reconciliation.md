---
sub_step_id: STEP-005.09
parent_step: STEP-005
title: Reconciliation, backfill and checkpointing
status: VERIFIED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-DATA-002]
blast_radius_id: BR-048
depends_on: [STEP-005.08]
last_updated: 2026-08-18
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
| Graph status | ✅ up to date. **NOT BLOCKED** |
| HEAD / indexed commit | `77f5abf` — matched HEAD at pre-change |
| Queries run | `impact` on `ResumableRun`, `Checkpoint`, `CheckpointStore`, `commit_batch`, each cross-checked against grep per `RISK-016` |
| **Finding** | `RISK-016` fourth reproduction, and a new variant: `commit_batch` reported **4** dependants against 7 real ones — partial under-reporting, which reads more like a real answer than a zero does |
| Unknown / low-confidence areas | **Resolved by design, not by luck:** a provider with no count endpoint yields `Unreconciled`, an explicit verdict that is neither pass nor fail. Treating it as a pass was the trap |
| Blast radius | **[BR-048](../../../10-logs/blast-radius/BR-048-reconciliation.md)** — LOW, confidence MEDIUM |
| Approval required? | No |

## 5. Implementation plan
- [x] Per-provider reconciliation, by count **and** by identity digest — and the weaker method declares its own limitation
- [x] **The threshold classifies; it does not suppress.** Every discrepancy is recorded whatever its size, so a sub-threshold leak is visible as a trend
- [x] Resumable backfill, **idempotent on replay — proved by replaying**, not asserted
- [x] Progress visible, with duplicates counted separately from applied records; cancellation leaves a resumable checkpoint
- [x] Results retained in an append-only log with no method that edits or removes

## 6. Contracts and schema changes
Contracts are declared in [STEP-004](../../STEP-004-contract-first-platform-apis.md); this sub-step consumes them. Any change follows [CONTRACT_CHANGE_POLICY](../../../04-contracts/CONTRACT_CHANGE_POLICY.md).

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-DATA-002 | integration | Reconciliation detects a seeded shortfall |
| — | integration | Backfill replay applies nothing and counts the duplicates |
| — | unit | **One dropped and one duplicated reconciles perfectly by count** — the limitation, demonstrated |
| — | unit | The same data is caught when the source publishes an index |
| — | unit | No index yields `UNRECONCILED`, which is neither a pass nor an alert |
| — | unit | A sub-threshold discrepancy is still recorded, and a rising leak is visible as a series |
| — | unit | Cancelling leaves a resumable checkpoint; a new run resumes from it |
| — | unit | **The stored checkpoint counts applied records, not delivered ones** |
| — | structural | The evidence log has no method that edits or removes |

25 tests. **Mutation testing: 12 seeded, 12 killed.**

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
| R1 full regression suite | **PASS** | 1036 Python + 63 web + 307 UI + 40 browser |
| R2 contract compatibility | **PASS** | No contract touched |
| R3 graph diff as expected | **PASS** | One new module, one new test module; `ResumableRun` wrapped, not modified |
| R4 untested requirements | **PASS — improved** | REQ-DATA-002's reconciliation and backfill clauses newly covered |
| R5 orphan/unowned nodes | **PASS** | Catch-all owner |
| R6 closed-bug regression tests | **PASS** | BUG-001…027; meta-suite 72/72 |
| R7 tenant isolation | **PASS — 18/18** | Untouched |

**Overall:** **PASS**.

## 11. Rollback
Revert this sub-step's commit; prior sub-steps stay intact and `main` stays deployable. Schema work uses expand/contract, so the expand phase is reversible.

## 12. Acceptance criteria
- [x] Reconciliation compares ingested totals against source counts, per provider
- [x] Discrepancies alert rather than being silently tolerated — **and are recorded even when they do not alert**
- [x] Backfill resumes from a checkpoint and is idempotent on replay
- [x] Progress is visible and the run is cancellable without losing the cursor
- [x] Results are retained as evidence in an append-only log

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | 2026-08-18 |
| Commit SHA | *(this commit)* |
| Pushed | ✅ |
| Graph re-indexed at | post-commit |
| `main` green and deployable | ✅ |
| Mutation testing | **12 of 12 killed** — 11 of 12 before the seam test existed |
| Bugs found | None |
| Notes / surprises | **The surviving mutant lived at the seam between two modules.** Passing `handled=len(identities)` rather than `len(fresh)` breaks nothing here, because `reconcile` reads the applied identities and not the checkpoint — all 24 tests passed. What it corrupts is `Checkpoint.records_seen` in the *framework* module, a field added there "so a resume that re-delivers a batch is visible in the numbers rather than only in theory". Inflated with duplicates, three fresh records and three replays report the same number. My tests covered this module and the framework's covered that one; **nothing asserted on what this module writes through the seam into the other's state.**<br><br>**The fourth module to need the same shape.** `Unreconciled` joins `ProfileUnsupported`, `TransitUnavailable` and `ObjectiveWithdrawn` — four sub-steps independently arriving at a value meaning *we could not answer this*, carried where it can be seen. At four occurrences that is the house pattern rather than four separate decisions.<br><br>**Re-delivery is the normal path.** The framework commits after handling, so a crash between the two replays the batch — the right trade, since the alternative loses records and only one of those is detectable. Replay safety therefore has to hold in ordinary operation, which is why the test replays rather than asserting idempotence in prose.<br><br>**A tolerance band was the trap I nearly walked into.** "Under one percent, pass" is the obvious design and it is how a leak survives a year: every run green, the gap widening, nothing crossing the line in a single step. Recording every discrepancy and letting the threshold decide only loudness costs nothing and makes the trend visible. |
