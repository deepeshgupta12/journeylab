---
blast_radius_id: BR-055
sub_step_id: STEP-006.06
title: Transactional outbox, relay and dead-letter policy
author: Deepesh Kumar Gupta
date: 2026-08-26
score: MEDIUM
confidence: MEDIUM
approval_required: false
---

# BR-055 — Transactional outbox

## 1. Graph state

| Field | Value |
| --- | --- |
| Indexed commit | `96670a8` |
| HEAD at check | `96670a8` |
| Freshness | ✅ up to date |
| Result | **NOT BLOCKED** for Python; **`RISK-017`** for the migration |
| Confidence | **MEDIUM** |

## 2. Queries run

| Symbol | Graph | Grep |
| --- | --- | --- |
| `UnitOfWork` | 0, LOW | **17** |
| `OutboxRecord` | 0, LOW | 7 |
| `stamp_envelope` | 0, LOW | **11** |
| `HealthChanged` | 1, LOW | 7 |

`RISK-016`, tenth consecutive reproduction. Migration `012` is one node (`RISK-017`),
so the schema half of the blast radius comes from three mutations against the
deployed constraints (§6).

## 3. A retry cap protects against a poison message, not against an outage

This is the decision that shapes the module, and the obvious implementation gets it
backwards.

The obvious relay counts attempts per message and dead-letters at five. Then the
broker goes down for twenty minutes: every message fails, every message burns its
five attempts inside a couple of minutes of backoff, and **the entire backlog lands
in the dead-letter queue** — where a human replays it by hand, ordering lost, having
been paged for an outage that resolved itself.

A poison message and an outage are indistinguishable one message at a time, and they
need opposite responses:

| | Signature | Correct response |
| --- | --- | --- |
| Poison | one message fails while its neighbours succeed | dead-letter it, or it blocks the queue forever |
| Outage | everything fails at once | keep retrying and alert; dead-lettering makes a transient failure permanent |

So `should_dead_letter` takes the **batch outcome** as well as the message. Nothing
is dead-lettered while nothing is getting through, however many attempts it has
burned. A message becomes poison only once it can be seen failing on its own — which
is why `Relay.run` is two passes: a single pass would have to decide the first
message's fate before knowing whether the second succeeds, and that is precisely the
information that separates the two cases.

## 4. Lag is measured from when the fact happened

A relay that died an hour ago has, by its own reckoning, **zero time since its last
attempt** — the metric it would naturally publish reads healthiest exactly when it is
most wrong. `oldest_pending_age` measures from `occurred_at`, so a stalled relay's lag
grows on its own with nothing running.

Same shape as measuring freshness from ingestion time rather than observation time
(`STEP-005.08`, `BUG-026`): the convenient clock is the one that hides the failure.
Third time this pattern has appeared, which suggests it is a class rather than a
coincidence.

## 5. The placeholder from STEP-002.06 converted itself into a failure

`test_pending_vector_is_still_absent[outbox / events]` had skipped since STEP-002.06
with a stated reason. The moment migration `012` created the table it **failed**,
demanding a real isolation test — which is exactly what that construction was built
to do. A placeholder that cannot notice its own dependency arriving is a comment.

Two real tests replace it, and both were proven to have detection power by weakening
the policy to `USING (true)` and confirming they go red:

- tenant A cannot read tenant B's queue, by listing or by naming it;
- tenant A cannot **write** an event into tenant B's stream — `WITH CHECK`, not just
  `USING`, because a policy that filters reads and permits writes lets one tenant
  inject an event a consumer will then process under the other's authority.

The event stream is the isolation vector people forget, because it does not look like
a store. It holds one row per state change, keyed by tenant.

## 6. Assessment

| Category | Assessment |
| --- | --- |
| Code | `services/events/src/outbox.py` — new; `pyproject.toml` paths |
| Schema | `012_outbox.sql`: one table, two indexes, RLS, four check constraints, a `journeylab_relay` role |
| Events | Implements delivery for the `Envelope` contract. AsyncAPI unchanged |
| Security | RLS on the queue; **the application has no `UPDATE` grant** — a producer that can set `status` can mark its own event delivered without sending it |
| Privacy | `payload_ids` only. `EVENT_CONTRACTS` §2 — an event stream carrying trip content is a store `REQ-PRIV-006` deletion must traverse, and the one nobody thinks of as a store |
| Reversibility | Expand phase; revert drops the table |

**Mutation testing: 16 seeded, 16 killed** — 13 against the relay, 3 against the
deployed schema (event-type shape dropped, dead-letter reason dropped, `UPDATE`
granted to the application).

## 7. What this does not close

| Gap | Why |
| --- | --- |
| No broker exists | `DEC-009` chose Kafka (`ADR-015`); `Publisher` is a port and the AsyncAPI contract is identical either way (§23) |
| No relay process runs | A worker loop, its scheduling and its deployment are operations work; this is the logic it will run |
| `acknowledged` is modelled and unused | The state exists in the table because the lifecycle in §10 names it; nothing acknowledges until a consumer does, which is `.07` |
| `MAX_ATTEMPTS` is provisional | `DEC-005`. The *policy* — that eligibility alone does not condemn — does not depend on the number |

## 8. Score

**MEDIUM.** Additive schema and an unwired module, but it is the delivery guarantee
the whole event backbone rests on, and it closes a tenant-isolation vector that has
been open since STEP-002.06. Confidence MEDIUM under `RISK-016` and `RISK-017`.
