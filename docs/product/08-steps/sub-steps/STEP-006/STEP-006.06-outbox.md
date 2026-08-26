---
sub_step_id: STEP-006.06
parent_step: STEP-006
title: Transactional outbox publisher with idempotency
status: VERIFIED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-DATA-008, REQ-NFR-005]
blast_radius_id: BR-055
depends_on: [STEP-006.05]
last_updated: 2026-08-26
---

# STEP-006.06 — Transactional outbox publisher with idempotency

## 1. Outcome
Domain events are written in the **same transaction** as the state change and relayed at least once, so no event is lost and none is phantom.

## 2. Scope and boundary
**In scope:** `services/events/src/outbox.py`; outbox table; relay worker; publish offsets; DLQ after retry cap.

**Not in this sub-step:** Consumer implementations (`.07`); queue selection (`DEC-009`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-DATA-008, REQ-NFR-005 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | ✅ up to date. **NOT BLOCKED** for the module; **`RISK-017`** for the migration |
| HEAD / indexed commit | `96670a8` — matched HEAD at pre-change |
| Queries run | `impact` on `UnitOfWork`, `OutboxRecord`, `stamp_envelope`, `HealthChanged`, grep cross-checked (`RISK-016`, tenth reproduction) |
| Unknown / low-confidence areas | No broker exists. `Publisher` is a port; `ADR-015` chose Kafka and the AsyncAPI contract is identical either way (§23) |
| Blast radius | **[BR-055](../../../10-logs/blast-radius/BR-055-outbox.md)** — MEDIUM, confidence MEDIUM |
| Approval required? | No |

## 5. Implementation plan
- [x] Outbox table written inside the aggregate transaction — the atomicity is enforced by `.04`'s unit of work, tested here against PostgreSQL
- [x] Relay publishing at-least-once: marked published **after** the broker accepts, so a crash in between re-sends
- [x] Attempt and error tracking; the row is **marked, never deleted**, because until acknowledgement it is the only place the event exists
- [x] Capped exponential backoff, and a dead-letter policy that **distinguishes a poison message from an outage** — see §6
- [x] **Rollback test against a real database: a failed transaction leaves no outbox row**
- [x] Lag measured from `occurred_at`, not from the last attempt — see §6a

## 6. A retry cap protects against poison, not against an outage

The obvious relay dead-letters at five attempts. A twenty-minute broker outage then
burns every message's attempts inside a couple of minutes of backoff and empties the
**entire backlog** into the dead-letter queue, to be replayed by hand with ordering
lost, after a failure that resolved itself.

| | Signature | Correct response |
| --- | --- | --- |
| Poison | one message fails while its neighbours succeed | dead-letter it, or it blocks the queue |
| Outage | everything fails at once | keep retrying and alert |

`should_dead_letter` therefore takes the **batch outcome** as well as the message.
Nothing is dead-lettered while nothing is getting through. The relay runs two passes
because a single pass would decide the first message's fate before knowing whether
the second succeeds — which is exactly the information that separates the two.

## 6a. Lag is measured from the fact, not the attempt

A relay that died an hour ago has zero time since its last attempt: the metric it
would naturally publish reads healthiest exactly when it is most wrong. Measured from
`occurred_at`, lag grows on its own with nothing running.

**Third occurrence of this shape** — after freshness-from-ingestion (`BUG-026`) and
staleness-stored-rather-than-computed (`STEP-005.08`). The convenient clock is the
one that hides the failure, and it is convenient precisely because it is the one the
failing component still has.

## 6b. Contracts and schema changes
Contracts are declared in [STEP-004](../../STEP-004-contract-first-platform-apis.md); this sub-step consumes them. Any change follows [CONTRACT_CHANGE_POLICY](../../../04-contracts/CONTRACT_CHANGE_POLICY.md).

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-DATA-008 | integration | **A rolled-back transaction leaves no outbox row** — against real PostgreSQL |
| — | unit | A total outage dead-letters **nothing**, however many attempts are burned |
| — | unit | One message failing among successes **is** dead-lettered |
| — | unit | Eligibility alone does not condemn; an empty batch is not an outage |
| — | unit | A row is marked published only after the broker accepts it |
| — | unit | The dead letter preserves the **full envelope**, not just an id and an error |
| — | unit | Lag is measured from `occurred_at`; a stalled relay's lag grows |
| — | integration | A malformed event type cannot reach the stream |
| — | integration | The application has no `UPDATE` grant — it cannot mark its own event delivered |
| — | security | **Tenant A cannot read tenant B's queue** (closes a vector open since STEP-002.06) |
| — | security | **Tenant A cannot write into tenant B's stream** — `WITH CHECK`, not just `USING` |

27 tests. **Mutation testing: 16 seeded, 16 killed** — 13 against the relay, 3
against the deployed schema.

## 8. Telemetry, security and accessibility
Traces carry tenant-safe correlation IDs; no PII in telemetry. Any user-facing surface is keyboard and screen-reader complete (`REQ-A11Y-001`) and completable without the map (`REQ-A11Y-003`).

## 9. Documentation to update
- [ ] Sub-step completion record
- [ ] [IMPLEMENTATION_LOG](../../../10-logs/IMPLEMENTATION_LOG.md) · [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) · [BUG_REGISTER](../../../10-logs/BUG_REGISTER.md) if applicable
- [ ] `BR-045` post-change section
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
- [x] Outbox atomic with the state change
- [x] Failed transaction produces no event
- [x] Retry and DLQ behaviour correct — **and outage-aware**, which the plain reading of "retry cap" is not
- [x] Lag metric published, measured from the fact rather than the attempt

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | 2026-08-26 |
| Commit SHA | *(this commit)* |
| Pushed | ✅ |
| Graph re-indexed at | post-commit |
| `main` green and deployable | ✅ |
| Mutation testing | **16 of 16 killed** |
| Bugs found | None |
| R7 | **A pending vector closed** — outbox isolation, open since STEP-002.06 |
| Notes / surprises | **A test written four steps ago failed on purpose today.** `test_pending_vector_is_still_absent[outbox / events]` had skipped since STEP-002.06 with its reason stated, and the moment migration `012` created the table it went red demanding the real isolation test it had been holding a place for. That construction exists precisely so an unbuilt subsystem cannot be forgotten, and this is the first time one has fired. Both replacements were checked for detection power by weakening the policy to `USING (true)`.<br><br>**The write-side isolation test is the one that matters.** `WITH CHECK`, not merely `USING`: a policy that filters reads and permits writes lets one tenant inject an event into another's stream, where a consumer will process it under that tenant's authority. Reading someone's queue is a disclosure; writing to it is an instruction.<br><br>**The convenient clock hides the failure, for the third time.** Relay lag measured from the last attempt reads zero for a relay that died an hour ago — healthiest exactly when most wrong. The same shape as `BUG-026` and as stored staleness. It is convenient because it is the clock the failing component still has. |
