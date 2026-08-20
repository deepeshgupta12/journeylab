---
blast_radius_id: BR-051
sub_step_id: STEP-006.02
title: Temporal model — three axes, DST-safe arithmetic, self-overlap exclusion
author: Deepesh Kumar Gupta
date: 2026-08-20
score: MEDIUM
confidence: MEDIUM
approval_required: false
---

# BR-051 — Temporal model

## 1. Graph state

| Field | Value |
| --- | --- |
| Indexed commit | `e918c3b` |
| HEAD at check | `e918c3b` |
| Freshness | ✅ up to date |
| Result | **NOT BLOCKED for Python; `RISK-017` applies to the migration half** |
| Confidence | **MEDIUM** |

## 2. Queries run

`impact` on `bind_tenant`, `app_current_org`, `RequestContext`, each cross-checked
against grep (`RISK-016`, sixth reproduction: 0/0/5 reported against 27/6/63 real).
The migration half is covered by `RISK-017` — `011_temporal.sql` is one node.

Blast radius for the schema change is therefore derived from the migration and from
three mutations applied to the **deployed** constraint (§6).

## 3. The constraint I nearly added would have enforced a requirement violation

The obvious integrity rule for a fact table: *two facts about the same field of the
same place must not have overlapping effective windows* — otherwise the solver picks
one arbitrarily and the answer depends on row order.

That rule is wrong here, and not marginally. **`REQ-EVID-002` requires conflicting
evidence to stay visible and never be averaged or resolved away.** Two sources
disagreeing about the same opening hours over the same dates *is* the conflicting
evidence the product promises to keep. An exclusion constraint over (place, field)
would make storing it impossible — the schema would enforce a requirement violation,
and the second source's fact would be rejected with a constraint error that reads
like a data bug.

The defensible line is narrower: **one source must not contradict itself.** Two facts
from the same source over overlapping windows are not disagreement, they are a double
ingestion or a mis-parsed window. So `source_id` is in the exclusion key, and a test
asserts that two *different* sources may both be stored.

## 4. The bug this module exists to prevent, found inside it

Python subtracts two aware datetimes that share a `tzinfo` object as **wall clock**.
It is documented — *"if both are aware and have the same tzinfo attribute, the common
tzinfo is ignored"* — and it is invisible, because both offsets are perfectly correct:

```python
a = datetime(2026, 3, 28, 9, 0, tzinfo=ZoneInfo("Europe/Zurich"))   # +01:00
b = datetime(2026, 3, 29, 9, 0, tzinfo=ZoneInfo("Europe/Zurich"))   # +02:00
b - a                                  # 24:00:00   WRONG
b.astimezone(UTC) - a.astimezone(UTC)  # 23:00:00   right
```

The first draft of `elapsed_between` was `return end - start`. Every duration
crossing a DST boundary would have been wrong by an hour — **in the direction that
makes a tight itinerary look feasible**, because a 23-hour day reported as 24 gives
the solver an hour that does not exist. `is_dst_transition_day` had the same bug,
which is why it reported the spring-forward day as ordinary.

Found by printing the value rather than by a test, which is worth noting: the
function looked obviously correct and reviewed as correct.

## 5. The asymmetry, since I got it wrong twice

| Operation | Semantics | Safe? |
| --- | --- | --- |
| `aware + timedelta` | wall clock | Yes for calendar questions |
| `aware - aware`, same `tzinfo` | **wall clock** | **No — this is the bug** |
| via `astimezone(UTC)` | elapsed | Yes |

My first test asserted that `+ timedelta(days=1)` moves the clock to 10:00. It does
not: addition is wall-clock under `zoneinfo`, so it lands on 09:00 like the helper.
The test now pins the real asymmetry, and records that the equivalence is a property
of `zoneinfo` which `pytz` does not share — so nobody removes the helper believing it
redundant.

## 6. A nullable column in an exclusion key is not in the key

The first version of the constraint used `place_id WITH =`. In an exclusion
constraint a NULL never conflicts, because `NULL = NULL` is unknown — so every
region-level fact, which has no `place_id`, escaped the check entirely and the
constraint silently did not apply to them.

Caught by the test written for it, which inserted two NULL-place facts and got no
violation. The key is coalesced now.

**Mutation testing: 11 seeded, 11 killed** — 8 against the module, 3 against the
deployed constraint (dropped; widened to all sources, which would forbid REQ-EVID-002
conflict; left nullable, so region facts escape).

## 7. Assessment

| Category | Assessment |
| --- | --- |
| Code | `apps/api/src/domain/temporal.py` and its package `__init__` — new |
| Schema | `011_temporal.sql`: one generated column, one exclusion constraint, two zone checks. Additive; revert drops them |
| Public API contract | Untouched |
| Security / privacy | None — no new data, no egress |
| Accessibility | None |
| Performance | The exclusion constraint adds a GiST index on `evidence_facts`; writes pay for it, and correctness of a fact table is worth an index |

## 8. What this does not close

| Gap | Why |
| --- | --- |
| Nothing calls the helpers yet | Repositories are `.04`; the solver is STEP-011 |
| Only `Europe/Zurich` is exercised | `ADR-016` makes it the region. The property tests are zone-parameterised in shape but run one zone, and a second region would need its own transition dates |
| `AxisFilter` returns SQL text | A query builder is not in scope. The fragment and its parameters travel together so they cannot be bound apart |

## 9. Score

**MEDIUM.** Additive schema and a new module with no callers, but it corrects a
class of error that is invisible in testing and lands in feasibility. Confidence
MEDIUM under `RISK-016` and `RISK-017`.
