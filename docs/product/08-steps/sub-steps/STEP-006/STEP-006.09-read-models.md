---
sub_step_id: STEP-006.09
parent_step: STEP-006
title: Read-model projection and rebuild proof
status: VERIFIED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-DATA-010]
blast_radius_id: BR-058
depends_on: [STEP-006.08]
last_updated: 2026-09-03
---

# STEP-006.09 — Read-model projection and rebuild proof

## 1. Outcome
Read models are projected from events and **provably rebuildable** from the log, so a corrupt projection is a recoverable inconvenience rather than data loss.

## 2. Scope and boundary
**In scope:** Projection framework; coverage read model; rebuild command; rebuild verification.

**Not in this sub-step:** Warehouse models ([STEP-022](../../STEP-022-analytics-feedback-and-experimentation.md)).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-DATA-010 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | ✅ up to date. **NOT BLOCKED** for the module; **`RISK-017`** for the migration |
| HEAD / indexed commit | `8c501ce` — matched HEAD at pre-change |
| Queries run | `impact` on `IdempotentConsumer`, `ProcessedLog`, `PublicCoverage`, `HealthChanged`, grep cross-checked (`RISK-016`, twelfth reproduction) |
| Unknown / low-confidence areas | Only one projection exists. Coverage is first because `STEP-005.10` already produces its events |
| Blast radius | **[BR-058](../../../10-logs/blast-radius/BR-058-read-models.md)** — MEDIUM, confidence MEDIUM |
| Approval required? | No |

## 5. Implementation plan
- [x] Projection framework folding declared event types — a projection that stops matching a type is a visible change, not a quietly emptier model
- [x] Coverage read model, carrying **no provider identity** in the type or the table
- [x] **Rebuild that resets before folding** — and therefore never routed through `.07`'s idempotent consumer, see §6
- [x] Verification that **compares** rebuilt against live, separating only-live, only-rebuilt and differing
- [x] Lag measured from the fact, not from `rebuilt_at`

## 6. Replay and rebuild are opposites

`STEP-006.07` spent its whole effort ensuring a replayed event does **not** re-apply
its effect. This sub-step needs the exact reverse: a rebuild re-applies every event,
from the beginning, into an empty projection.

Route a rebuild through an idempotent consumer and every event is already in the
processed log, so all of them are skipped. **The rebuild succeeds and raises
nothing.** The read model is reconstructed from whatever was left, and the output
looks like missing data rather than a broken repair.

The two paths share an event stream and share nothing else. The reason they must not
share a *mechanism* is that their correctness conditions contradict each other, and a
test demonstrates it directly: the same events consumed twice through an idempotent
consumer fold zero the second time; through `rebuild`, they fold all of them.

Resetting is also what makes a rebuild idempotent. Folding into existing state would
double counters and leave stale keys no event removes — a projection **more** wrong
after being repaired.

## 6a. Contracts and schema changes
Contracts are declared in [STEP-004](../../STEP-004-contract-first-platform-apis.md); this sub-step consumes them. Any change follows [CONTRACT_CHANGE_POLICY](../../../04-contracts/CONTRACT_CHANGE_POLICY.md).

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-DATA-010 | integration | **The read model is dropped and rebuilt, and matches** — against real PostgreSQL |
| — | unit | A rebuild resets before folding, so stale keys do not survive |
| — | unit | **Rebuilding through an idempotent consumer would lose every event** |
| — | unit | A rebuild is idempotent; two projections rebuilt from one log agree |
| — | unit | A drifted projection is **detected**, not merely rebuilt |
| — | unit | Missing and extra keys are reported separately from drift |
| — | unit | The fold reads only its arguments — checked by AST walk |
| — | meta | **The purity checker is shown failing on a seeded impure module** |
| — | unit | No provider identity reaches the read model |
| — | unit | A region takes its worst provider; a degraded region still accepts trips |
| — | integration | The table has no provider column and constrains its freshness vocabulary |

23 tests. **Mutation testing: 15 seeded, 15 killed.**

## 8. Telemetry, security and accessibility
Traces carry tenant-safe correlation IDs; no PII in telemetry. Any user-facing surface is keyboard and screen-reader complete (`REQ-A11Y-001`) and completable without the map (`REQ-A11Y-003`).

## 9. Documentation to update
- [ ] Sub-step completion record
- [ ] [IMPLEMENTATION_LOG](../../../10-logs/IMPLEMENTATION_LOG.md) · [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) · [BUG_REGISTER](../../../10-logs/BUG_REGISTER.md) if applicable
- [ ] `BR-048` post-change section
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
- [x] Projections rebuildable from the log — **proved by dropping and rebuilding**
- [x] Rebuild output verified against live, with the difference classes separated
- [x] Rebuild idempotent, because it resets rather than folding into what is there
- [x] Lag computed from the fact rather than the rebuild timestamp

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | 2026-09-03 |
| Commit SHA | *(this commit)* |
| Pushed | ✅ |
| Graph re-indexed at | post-commit |
| `main` green and deployable | ✅ |
| Mutation testing | **15 of 15 killed** — 12 of 15 before the negative control and the vocabulary test existed |
| Bugs found | None |
| Notes / surprises | **A checker no test could distinguish from `return True`.** `reads_only_its_arguments` was only ever asserted to pass, so replacing its whole body with `True` killed no mutant. A one-sided assertion on a detector is worth nothing — the same lesson as the axe negative control and as `BR-029` §3's degraded signal. It now has a seeded impure module it must reject.<br><br>**The replay/rebuild inversion is the finding.** Two sub-steps of this step have contradictory correctness conditions over the same event stream, and the failure of confusing them is a rebuild that completes successfully while producing a half-empty read model.<br><br>**A second equivalent mutant of my own making**, in three sub-steps. I filtered the log by `last_event_id`, which `rebuild` has just set to `None`, so nothing was mutated. A mutant that cannot change behaviour teaches nothing about the tests.<br><br>**The mutation restore failed for the third time in this step, and the fix was available at the first.** `.01` and `.08` cleaned up by guessing which org slugs their tests inserted; this one used a slug I had not guessed. Keying cleanup on the **table the constraint belongs to** cannot go stale. |
