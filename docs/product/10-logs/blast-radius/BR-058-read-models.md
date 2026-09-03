---
blast_radius_id: BR-058
sub_step_id: STEP-006.09
title: Read-model projection, rebuild and verification
author: Deepesh Kumar Gupta
date: 2026-09-03
score: MEDIUM
confidence: MEDIUM
approval_required: false
---

# BR-058 — Read models

## 1. Graph state

| Field | Value |
| --- | --- |
| Indexed commit | `8c501ce` |
| HEAD at check | `8c501ce` |
| Freshness | ✅ up to date |
| Result | **NOT BLOCKED** for Python; **`RISK-017`** for the migration |
| Confidence | **MEDIUM** — `RISK-016`, twelfth reproduction (1/1/1/1 against 9/11/8/7) |

## 2. Replay and rebuild are opposites

`STEP-006.07` spent its whole effort ensuring a replayed event does **not** re-apply
its effect. This sub-step needs the exact reverse: a rebuild re-applies every event,
from the beginning, into an empty projection.

Run a rebuild through an idempotent consumer and every event is already in the
processed log, so all of them are skipped. **The rebuild succeeds.** Nothing raises.
The read model is reconstructed from whatever happened to be left, and the output is
wrong in a way that looks like missing data.

So `rebuild` resets the target first and never consults the processed log. The two
paths share an event stream and share nothing else — and the reason they must not
share a *mechanism* is that their correctness conditions contradict each other. A
test demonstrates the hazard directly: the same events, consumed twice through an
idempotent consumer, fold zero the second time; through `rebuild`, they fold all of
them.

Resetting is also what makes a rebuild idempotent. Folding into existing state would
double counters and leave stale keys that no event removes — a projection **more**
wrong after being repaired than before.

## 3. A projection that reads anything but its events is not rebuildable

A fold that queries current state — *what is this provider's health now* — produces
today's answer while folding a year-old event. The rebuild finishes, the numbers
differ from the original, and nothing points at the cause.

`REQ-DATA-010`'s claim holds only if the fold is a pure function of the event stream,
so `Projection.fold` receives state and one envelope and has no other input. Checked
by an AST walk, not a text scan — the same check failed against its own docstring in
`STEP-006.05`.

## 4. Finishing is not matching

A rebuild that completes proves the code ran. `verify_rebuild` compares rebuilt
against live key by key and separates three outcomes — only-live, only-rebuilt, and
differing — because the causes differ: a projection that stopped folding is not the
same defect as one that folded wrongly.

## 5. Mutation testing — 15 seeded, 15 killed

Three survived the first run.

**One was an equivalent mutant of mine.** I filtered the log by `last_event_id`, which
`rebuild` has just set to `None`, so it filtered nothing. Re-seeded as the defect it
was meant to model: routing the rebuild through an `IdempotentConsumer`.

**One was a checker no test could distinguish from `return True`.**
`reads_only_its_arguments` was only ever asserted to pass, so replacing its entire
body with `True` killed nothing. A one-sided assertion on a detector is worth nothing
— the same lesson as the axe negative control in the browser suite, and as `BR-029`
§3's degraded-signal finding. It now has a seeded impure module it must reject.

**One was a database constraint with no test behind it.** The freshness vocabulary is
enumerated in the type *and* in the table; every test wrote through the projection,
which is the layer a future writer bypasses.

**The restore failed for the third time in this step**, and the diagnosis is finally
useful: my cleanup deleted a hardcoded org slug, and the new test used a different
one. Keying cleanup on the *table the constraint belongs to* is the version that
cannot go stale — `.01` and `.08` both cleaned by guessing at what the tests inserted.

## 6. Assessment

| Category | Assessment |
| --- | --- |
| Code | `services/events/src/projections.py` — new |
| Schema | `015_read_models.sql`: two tables, RLS on both, one check constraint |
| Contracts | Serves `Coverage` / `CoverageRegion`; nothing changed |
| Security | RLS on both tables. **No provider column** in the read model — `REQ-EVID-006` |
| Reversibility | **Higher than any other migration in this step.** Dropping a read model loses nothing the log cannot produce again, which is the property being claimed |

## 7. What this does not close

| Gap | Why |
| --- | --- |
| The projection state is in memory | The table is the target; wiring the fold's output to it on every event is the worker loop, which is operations work. The rebuild test does write and re-read through PostgreSQL |
| No rebuild CLI | `pnpm`-level tooling belongs with the worker that runs it |
| Only one projection exists | Coverage is the first because `STEP-005.10` already produces the events. Others arrive with their owning steps |
| Lag is computed, not published | Same position as the outbox lag metric in `.06` — an observability wiring task |

## 8. Score

**MEDIUM.** Additive and unwired, but it is the recovery property `REQ-DATA-010`
claims, and the replay/rebuild inversion is the kind of defect that produces a
successful-looking repair.
