---
blast_radius_id: BR-048
sub_step_id: STEP-005.09
title: Reconciliation, backfill and checkpointing
author: Deepesh Kumar Gupta
date: 2026-08-18
score: LOW
confidence: MEDIUM
approval_required: false
---

# BR-048 — Reconciliation and backfill

## 1. Graph state

| Field | Value |
| --- | --- |
| Indexed commit | `77f5abf` |
| HEAD at check | `77f5abf` |
| Freshness | ✅ up to date |
| Result | **NOT BLOCKED** |
| Confidence | **MEDIUM** — `RISK-016` again (§2) |

## 2. Queries run, with the mandatory cross-check

| Symbol | Graph | Grep |
| --- | --- | --- |
| `ResumableRun` | 0, LOW | **11** |
| `Checkpoint` | 0, LOW | 0 |
| `CheckpointStore` | 0, LOW | 0 |
| `commit_batch` | 4, LOW | **7** |

Fourth consecutive reproduction of `RISK-016`. `commit_batch` is the interesting
row: the graph found four dependants and grep found seven, so the under-reporting is
partial rather than total — which is worse for a reader, because a non-zero answer
looks like a real answer.

**Actual blast radius:** `BackfillRun` wraps `ResumableRun` rather than modifying it.
No existing symbol changed. The one coupling is to `commit_batch`'s contract, and §5
records what that coupling cost.

## 3. What a matching count proves

A hundred records ingested against a hundred at the source proves a hundred of
something arrived. **One record dropped and one duplicated reconciles exactly**, and
so does a page fetched twice while another was skipped.

`DC-EXT-001` asks for "record count + checksum vs. provider index" for this reason.
Both methods exist here, and the weaker one carries its limitation as data:
`detects_substitution` is `False` for a count reconciliation, and the detail string
says so. A verdict that overstates what it checked is worse than no verdict, because
it retires the suspicion that would have led someone to look properly.

## 4. A source that cannot be counted is not reconciled

Several providers publish no total and no index. Treating "nothing to compare
against" as a pass makes every one of them report perfect completeness forever, and
the dashboard stays clean precisely where the evidence is weakest.

`Unreconciled` is the honest value — the same shape as `ProfileUnsupported` in
routing, `TransitUnavailable` in transit and `ObjectiveWithdrawn` in weather. Not a
pass, not a failure: **the absence of evidence, carried where it can be seen.** That
this is now the fourth module to need the same shape suggests it is the house
pattern rather than four separate decisions.

## 5. The threshold classifies; it does not suppress

The obvious design gives reconciliation a tolerance — under one percent, pass. That
is how a slow leak survives a year: every run green, the gap widening, nothing
crossing the line in any single step.

So **every** discrepancy is recorded whatever its size, and `ALERT_THRESHOLD` decides
only how loudly. `drift_series` then makes the trend visible, and a test seeds four
runs at 0%, 0.2%, 0.4% and 0.6% — none of which alert, all of which are recorded, and
the rise is unmistakable in the series and invisible anywhere else.

## 6. Replay safety is proved by replaying

The framework's commit ordering makes re-delivery **likely**, not exceptional: it
commits after handling, so a crash in between replays the batch. That is the correct
trade — the alternative loses records instead of repeating them, and only one of
those is detectable — but it means the backfill runner must be replay-safe in normal
operation rather than in a disaster.

`apply_batch` skips identities already applied and counts the duplicates separately
from progress. Keeping them separate matters: collapsed, a replayed page looks like
fresh progress, and a backfill that appears to advance while re-reading one page is
exactly what the counter exists to expose.

**Cancellation leaves the checkpoint intact.** A cancel that discarded the cursor
turns a pause into a restart from zero, so on a large backfill nobody ever cancels —
and a backfill nobody dares stop is a backfill that cannot be stopped.

## 7. Assessment

| Category | Assessment |
| --- | --- |
| Code | `services/ingestion/src/reconciliation.py` **new**; nothing modified |
| Public API contract | Untouched |
| Data / schema | None |
| Security / privacy | No egress, no credential, no personal data. Record identities are provider keys, not personal identifiers |
| Accessibility | No user surface |
| Performance | Set operations over identity lists; no I/O |

**Mutation testing: 12 seeded, 12 killed.** One survived the first run, and it is
worth the space: `commit_batch(handled=len(identities))` instead of `len(fresh)`,
which counts replayed records as newly handled.

Nothing in this module's own logic changes, which is why every reconciliation test
still passed — `reconcile` reads `applied_identities()`, not the checkpoint. What it
corrupts is `Checkpoint.records_seen`, a field the framework added, in its own words,
*"so a resume that re-delivers a batch is visible in the numbers rather than only in
theory"*. Inflating it with duplicates makes three fresh records and three replays
report the same number, defeating exactly the thing the field exists for.

**The gap was at the seam.** My tests covered this module and the framework's tests
covered that one; nothing asserted on what this module writes *through* the seam into
the other's state. That is where the defect lived.

## 8. What this does not close

| Gap | Why |
| --- | --- |
| No provider actually publishes an index yet | No live fetch has been made — the same disclosure carried since `.02`. `IDENTITY_DIGEST` is implemented and unexercised against a real source |
| `ALERT_THRESHOLD` is provisional | `DEC-005`. It classifies rather than suppresses, so a wrong value changes loudness and never coverage |
| Checkpoints are in memory | `CheckpointStore` is a port; `DEC-007` has not chosen a platform and `STEP-006` owns persistence |
| Alerting is a property, not a channel | `alerts` is computed; wiring it to a destination is `STEP-005.10` and the observability step |

## 9. Score

Additive, no consumer, no contract, no I/O. **LOW**, confidence MEDIUM for
`RISK-016`. No owner approval required.
