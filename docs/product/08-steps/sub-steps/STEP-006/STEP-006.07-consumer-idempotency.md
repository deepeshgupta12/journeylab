---
sub_step_id: STEP-006.07
parent_step: STEP-006
title: Consumer idempotency and replay
status: VERIFIED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-DATA-009]
blast_radius_id: BR-056
depends_on: [STEP-006.06]
last_updated: 2026-08-31
---

# STEP-006.07 — Consumer idempotency and replay

## 1. Outcome
Consumers process each event exactly once in effect, so at-least-once delivery and deliberate replay are both safe.

## 2. Scope and boundary
**In scope:** Consumer framework; processed-event tracking; replay tooling; per-trip ordering handling.

**Not in this sub-step:** Specific consumers (their owning steps).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-DATA-009 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | ✅ up to date. **NOT BLOCKED** for the module; **`RISK-017`** for the migration |
| HEAD / indexed commit | `04e8134` — matched HEAD at pre-change |
| Queries run | `impact` on `Envelope`, `Relay`, `Status`, `OutboxRow`, grep cross-checked (`RISK-016`, eleventh reproduction) |
| Unknown / low-confidence areas | Prune and replay limits are unset (`DEC-005`). The **relationship** between them is enforced regardless of the values |
| Blast radius | **[BR-056](../../../10-logs/blast-radius/BR-056-consumer-idempotency.md)** — MEDIUM, confidence MEDIUM |
| Approval required? | No |

## 5. Implementation plan
- [x] Processed events recorded per **`(consumer, event_id)`** — keying by event alone would let the first consumer to finish suppress the rest
- [x] Naturally idempotent effects preferred, and a test asserts they keep **no** records — which is also what frees them from the prune horizon
- [x] **Replay tooling that refuses to cross the prune horizon**, naming both dates — see §6
- [x] Events handed to consumers **grouped by key**, with ties broken deterministically and the difference between reproducible and causal stated
- [x] Unknown wire fields ignored; a missing `tenant_id` still refused, because tolerance is for additions

## 6. Pruning reopens the window the table exists to close

The processed-event table grows without bound, so it must be pruned. But an event
older than the prune horizon has no record, and replaying it applies the effect a
second time with nothing left to stop it.

**The prune horizon and the maximum replay depth are one constraint wearing two
names** — and they are normally set by two different people, at two different times,
for two unrelated reasons: storage cost and operational recovery. Nothing enforces the
relationship unless it is written down.

So `replay` refuses to cross the horizon and names **both dates** in the refusal.
Without it the replay succeeds, and the duplicated effects surface downstream long
afterwards with nothing connecting them to a maintenance job that ran a month earlier.

A naturally idempotent consumer keeps no records, so the horizon does not constrain it
at all. That is the strongest practical argument for preferring idempotent effects,
and it only becomes visible once the horizon exists.

## 6a. Contracts and schema changes
Contracts are declared in [STEP-004](../../STEP-004-contract-first-platform-apis.md); this sub-step consumes them. Any change follows [CONTRACT_CHANGE_POLICY](../../../04-contracts/CONTRACT_CHANGE_POLICY.md).

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-DATA-009 | unit | Duplicate delivery produces one effect |
| — | unit | **A failing handler leaves no record, so the retry still happens** |
| — | unit | Two consumers both process the same event |
| — | unit | A naturally idempotent consumer keeps no records |
| — | unit | **A replay past the prune horizon is refused, naming both dates** |
| — | unit | A replay processes only the requested range |
| — | unit | Pruning moves the horizon in the same call, and the horizon never moves backwards |
| — | unit | Ties are broken deterministically — **reproducible, not causal** |
| — | unit | Events are grouped by key rather than globally sorted |
| — | unit | Unknown wire fields are ignored; a missing `tenant_id` is not |

19 tests. **Mutation testing: 13 seeded, 13 killed.**

## 8. Telemetry, security and accessibility
Traces carry tenant-safe correlation IDs; no PII in telemetry. Any user-facing surface is keyboard and screen-reader complete (`REQ-A11Y-001`) and completable without the map (`REQ-A11Y-003`).

## 9. Documentation to update
- [ ] Sub-step completion record
- [ ] [IMPLEMENTATION_LOG](../../../10-logs/IMPLEMENTATION_LOG.md) · [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) · [BUG_REGISTER](../../../10-logs/BUG_REGISTER.md) if applicable
- [ ] `BR-046` post-change section
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
- [x] Duplicate delivery produces a single effect
- [x] Replay safe and tooled — **and refused when it would not be safe**
- [x] Additive schema changes tolerated
- [x] Ordering assumptions limited to per-trip, with the tiebreak's meaning stated

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | 2026-08-31 |
| Commit SHA | *(this commit)* |
| Pushed | ✅ |
| Graph re-indexed at | post-commit |
| `main` green and deployable | ✅ |
| Mutation testing | **13 of 13 killed** |
| Bugs found | None |
| Notes / surprises | **The prune horizon and the replay depth are one constraint wearing two names**, normally set by two different people for two unrelated reasons — storage cost and operational recovery. Nothing connects them unless it is written down, and the failure mode without it is the worst kind: the replay succeeds, and the duplicated effects appear downstream long afterwards with no visible link to a maintenance job that ran a month earlier.<br><br>**A naturally idempotent consumer is not merely cheaper, it is unconstrained.** It keeps no records, so the horizon does not apply and it can replay from any point. That is the strongest practical argument for preferring idempotent effects, and it only became visible once the horizon existed.<br><br>**The surviving mutant made "replay since yesterday" mean "replay everything".** Every test had passed events inside the requested range only, so dropping the filter changed nothing observable — while in production it turns a targeted recovery into a full-history reprocess nobody authorised.<br><br>**`consumer_prune_horizon` deliberately has no tenant column** — one consumer prunes once across all tenants, so it is operational state rather than tenant data. Recorded because a new table without `organization_id` should be a decision somebody made, not something a reviewer has to catch. |
