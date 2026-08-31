---
blast_radius_id: BR-056
sub_step_id: STEP-006.07
title: Consumer idempotency, replay and the prune horizon
author: Deepesh Kumar Gupta
date: 2026-08-31
score: MEDIUM
confidence: MEDIUM
approval_required: false
---

# BR-056 — Consumer idempotency

## 1. Graph state

| Field | Value |
| --- | --- |
| Indexed commit | `04e8134` |
| HEAD at check | `04e8134` |
| Freshness | ✅ up to date |
| Result | **NOT BLOCKED** for Python; **`RISK-017`** for the migration |
| Confidence | **MEDIUM** — `RISK-016`, eleventh reproduction (1/1/1/1 against 22/9/18/17) |

## 2. Pruning reopens the window the table exists to close

This is the finding, and it is a constraint **between two policies** that neither one
can see.

The processed-event table grows without bound, so it must be pruned. But an event
older than the prune horizon has no record — and replaying it applies the effect a
second time with nothing left to stop it. So the prune horizon and the maximum replay
depth are one constraint wearing two names, usually set by two different people at two
different times for two unrelated reasons: storage cost and operational recovery.

Nothing enforces the relationship unless it is written down. `replay` refuses to cross
the horizon rather than discovering the problem by double-applying, and **the refusal
names both dates** so whoever chose them can see that they disagree.

The failure mode without it is the reason this deserves the space: the replay
completes successfully, and the duplicated effects surface somewhere downstream long
afterwards, with no obvious connection back to a maintenance job that ran a month
earlier.

## 3. Exactly once in effect, not in delivery

The relay is at-least-once and no amount of care changes that, so duplicates are
certain rather than possible. Two routes to a single effect:

| | Cost | When available |
| --- | --- | --- |
| Naturally idempotent | none | the effect can be repeated safely — `SET status = 'confirmed'` |
| Recorded | a row per event **per consumer**, forever, until pruned | everything else |

The framework prefers the first, and a test asserts a naturally idempotent consumer
keeps **no** records — which is also what frees it from the horizon in §2. That is the
practical argument for preferring it, beyond tidiness.

Records are keyed by `(consumer, event_id)`. Keying by event alone would let whichever
consumer finished first suppress every other one, which is the kind of bug that looks
like a missing feature.

## 4. The ordering that decides whether the retry ever happens

Two orderings are available inside the consumer and both are wrong on their own:

- **effect, then record** — a crash between them replays the effect. Duplicated.
- **record, then effect** — a crash between them means the effect never happens *and
  never will*, because the record says it did.

The second is worse: a duplicate is visible, a silent omission is not. The record is
written only after the handler returns, so a failing handler leaves no record and the
retry still happens — tested with a handler that fails once and then succeeds.

## 5. Timestamps are not a total order, even within one key

`EVENT_CONTRACTS` §3 guarantees per-trip order only, so events are handed to consumers
**grouped by key** rather than as one stream — a consumer given the whole stream will
sort it and believe the result.

Within a key, two events can share `occurred_at` because clocks have resolution, so
the sort breaks ties on `event_id`. That buys **reproducibility, not causality**: two
replays agree with each other, and neither can say which event really happened first.
A test asserts the timestamp still leads, because the output looks identical either
way and the distinction is exactly what a reader would assume away.

## 6. Assessment

| Category | Assessment |
| --- | --- |
| Code | `services/events/src/consumers.py` — new |
| Schema | `013_consumer_idempotency.sql`: two tables, RLS on the tenant-scoped one, two indexes |
| Events | Consumes the `Envelope` contract; nothing published |
| Security | RLS on `processed_events`. `consumer_prune_horizon` is per-consumer operational state with no tenant column — see §7 |
| Privacy | IDs only, as the envelope carries |

**Mutation testing: 13 seeded, 13 killed.** One survived: dropping the `since` filter
so a replay reprocesses all history. Every test had passed events *inside* the range
only, so "replay since yesterday" quietly meaning "replay everything" went unnoticed —
a far larger operation than the operator authorised.

## 7. What this does not close

| Gap | Why |
| --- | --- |
| `ProcessedLog` is in memory | `013` is the table it stands for. The rules worth testing — the horizon interaction and per-consumer keying — are properties of the logic; `.09` exercises persistence |
| `consumer_prune_horizon` has no tenant column | It is per-consumer operational state, not tenant data: one consumer prunes once across all tenants. Recording it because the absence of `organization_id` in a new table should be a decision, not an oversight |
| No consumer exists to be idempotent | Specific consumers belong to their owning steps; the coverage projection in `.09` is the first |
| Prune and replay limits are unset | `DEC-005`. The **relationship** between them is enforced regardless of the values |

## 8. Score

**MEDIUM.** Additive, unwired, but it is the counterpart to at-least-once delivery —
without it every duplicate the relay is designed to produce becomes a duplicated
effect. Confidence MEDIUM under `RISK-016` and `RISK-017`.
