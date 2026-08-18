---
blast_radius_id: BR-047
sub_step_id: STEP-005.08
title: Field-specific freshness policy and expiry
author: Deepesh Kumar Gupta
date: 2026-08-18
score: LOW
confidence: MEDIUM
approval_required: false
---

# BR-047 — Freshness policy

## 1. Graph state

| Field | Value |
| --- | --- |
| Indexed commit | `a7a5a04` |
| HEAD at check | `a7a5a04` |
| Freshness | ✅ up to date |
| Result | **NOT BLOCKED** |
| Confidence | **MEDIUM** — additive module, but see §2 |

## 2. Queries run, and the cross-check `RISK-016` now requires

| # | Query | Graph | Grep |
| --- | --- | --- | --- |
| 1 | `impact Provenance --upstream --depth 3 --include-tests` | 0, LOW | **11** call sites |
| 2 | `impact CanonicalPlace` | 0, LOW | — |
| 3 | `impact ResumableRun` | 0, LOW | **11** call sites |
| 4 | `impact CircuitBreaker` | 1, LOW | **12** call sites |

`RISK-016` reproduced exactly. The graph is used, the grep is used, and where they
disagree the grep is believed — which is why confidence is MEDIUM on an otherwise
purely additive change.

**Actual blast radius:** none. `freshness.py` is new and nothing imports it yet. It
consumes no existing symbol; `TemporalFact` mirrors `temporal-validity.json` rather
than importing from the places adapter, because freshness is not a places concept.

## 3. Age is measured from observation, and the alternative is invisible

Measured from ingestion, a value the provider last refreshed three days ago and
served to us one second ago is **zero seconds old**. Every dashboard is green.

The property that makes this dangerous rather than merely wrong: the staler the
upstream cache gets, the **fresher** our numbers look, because each re-fetch resets
the clock we chose to read. Polling more often makes the reported freshness better
and the actual data no newer. A provider silently serving three-day-old cache is
exactly the failure freshness policy exists to detect, and ingestion time makes it
structurally undetectable.

Both timestamps are carried anyway. With only `observed_at` the mistake would be
unrepresentable — and so would the proof that we avoided it. The gap between them is
published as `ingestion_lag`, which is our problem to fix and not evidence about the
fact.

## 4. Freshness and applicability are different axes

A fact observed sixty seconds ago about last summer's ferry timetable is perfectly
fresh and completely inapplicable. A fact observed in March, effective to October,
is four months old in July and exactly right.

`temporal-validity.json` already says this — *"a system with one timestamp will
either discard good data or serve expired data"* — so this module checks both axes
separately and names which failed.

**Applicability is checked first**, and the ordering is a decision. Both can fail at
once; reporting "stale" for a fact about the wrong dates sends someone to re-fetch,
and re-fetching cannot fix it. The verdict names the failure that can actually be
acted on.

**Partial cover is a gap, not a fact about the uncovered days.** A window covering
day one of a three-day trip does not describe days two and three, and letting it
count would silently extend a fact past its own validity.

## 5. What this module refuses to decide

`REQ-EVID-005` requires a stale fact to lower scenario confidence **or** block the
option. Blocking is decided here, because it follows from the field class. The
confidence *curve* is not, and the module publishes `staleness_ratio` instead of a
multiplier.

Inventing a factor here would put a magic constant in the wrong module — `BUG-026`'s
shape exactly, a number justified by a belief rather than by anything checkable. The
scorer owns the curve; this owns the classification.

## 6. The thresholds are provisional and their ordering is not

`DEC-005` (KPI thresholds) is open, so the four values are marked provisional and
each carries a written rationale — a threshold without one is a number nobody can
review.

What is **not** provisional is the ordering. `REQ-DATA-005` requires that hours and
disruptions expire faster than descriptive content, which is a property of the table
rather than of any single number. It is asserted as an invariant, so it survives
whatever `DEC-005` decides the absolute values should be. That is the honest way to
test a constant that has not been signed off: test the property the requirement
states, not the number somebody picked.

There is **no default policy**. An unregistered field class raises, because a
lenient fallback is how a closure inherits a description's ninety-day threshold.

## 7. Assessment

| Category | Assessment |
| --- | --- |
| Code | `services/ingestion/src/freshness.py` **new**. Nothing else modified |
| Public API contract | Untouched |
| Data / schema | None — `TemporalFact` mirrors an existing contract schema |
| Security / privacy | No egress, no credential, no personal data |
| Accessibility | No user surface |
| Performance | Pure computation, no I/O |

**Mutation testing: 10 seeded, 10 killed.** One survived the first run: the
threshold comparison. No test exercised `age == max_age` exactly, so nothing pinned
which side of the boundary is inclusive. It is inclusive — "expires after six hours"
should not expire *at* six hours, and an exclusive bound makes the verdict depend on
clock resolution, so the same fact assessed a microsecond apart would flip.

## 8. What this does not close

| Gap | Why |
| --- | --- |
| The four thresholds are unsigned-off | `DEC-005`. The ordering invariant holds regardless |
| Nothing consumes it yet | Wiring into evidence assembly is `STEP-010`; into scenario confidence, `STEP-011` |
| Absence is not modelled here | "Never observed" is different from "expired", and `places/hours.py` already owns UNKNOWN. Splitting it across two modules would be worse than leaving the boundary where it is |

## 9. Score

Additive, no consumer, no contract, no I/O. **LOW**, confidence MEDIUM because of
`RISK-016`. No owner approval required.
