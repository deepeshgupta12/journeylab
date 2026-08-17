---
blast_radius_id: BR-043
sub_step_id: STEP-005.04
title: Transit schedules, calendars, feed pinning and alerts
author: Deepesh Kumar Gupta
date: 2026-08-17
score: MEDIUM
confidence: HIGH
approval_required: false
---

# BR-043 — Transit adapter

## 1. Graph state

| Field | Value |
| --- | --- |
| Indexed commit | `bb84631` |
| HEAD at check | `bb84631` |
| Freshness | ✅ up to date |
| Result | **NOT BLOCKED** |
| Confidence | **HIGH** — additive; nothing imports it yet |

## 2. Queries run

| # | Query | Result |
| --- | --- | --- |
| 1 | `cypher` over `services/integrations/src/transit` | 0 nodes — additive |
| 2 | `detect_changes(staged)` | Run pre-commit; recorded in the regression entry |

## 3. A service day is not a calendar day

GTFS writes a 01:30 departure on the night of the 14th as **`25:30` on service
date 2026-08-14**. Both naive readings are wrong, in opposite directions:

| Reading | Consequence |
| --- | --- |
| Reject as invalid | The night network disappears, and the gap reads as *"no service"* rather than a parsing failure. A solver reports a feasible late journey as impossible |
| Wrap to 01:30 today | Every late departure moves back twenty-four hours. The itinerary contains a train that left last night — `REQ-CONS-004`, **S1 by definition** |

For a region chosen partly for last-funicular and last-boat constraints
(`ADR-016`), this is the specific error that produces a confidently wrong plan.
`ServiceTime` is therefore deliberately **not** a `datetime.time`: `25:30` is not
representable as one, and forcing it into that type is the coercion that loses the
night network.

## 4. An exception always beats the pattern

GTFS states when a service runs in two places, and the precedence failure is
asymmetric:

| Ignored | Consequence |
| --- | --- |
| A **removal** | The plan uses a train that does not run on Christmas Day, and the traveller is at a station |
| An **addition** | A service that does run is invisible; the plan is worse than necessary and nobody learns why |

The first strands somebody, so `runs_on` consults exceptions **first and returns
immediately** — there is no branch where the weekly pattern is reachable after an
explicit date has spoken.

Outside a calendar's range the answer is `UNKNOWN`, not `NO`. The same three-state
discipline as `.02`'s hours and `.03`'s outlook, for the same reason: a feed
ending on 31 December says nothing about January, and answering "does not run"
invents a fact that produces a false infeasibility.

## 5. Why the feed is pinned by content hash

Identifiers are **not** stable across GTFS publications: a `stop_id` can be retired
and later reused for a different platform. An evidence pack that resolves stored
identifiers against whatever feed is current will one day resolve them against a
different stop — and nothing about that failure looks like one. The itinerary is
coherent, the citation resolves, the platform is wrong.

Pinned by **content hash rather than the operator's version string**, because a
feed republished with the same stated version and different contents is exactly
the case a version string cannot catch.

## 6. Twelve impact categories

| # | Category | Assessment |
| --- | --- | --- |
| 1 | **Callers / call graph** | None yet. Travel-matrix computation is `.05` |
| 2 | **Public API / contracts** | None |
| 3 | **Database / schema** | None. Persistence is `STEP-006` |
| 4 | **Events** | None. Provider health is `.10` |
| 5 | **Configuration** | The alert SLO is a **parameter**: a slower provider must not inherit this one's promise |
| 6 | **Infrastructure** | None. No new dependency |
| 7 | **Security** | None directly; fetching goes through `.01`'s connector |
| 8 | **Privacy** | None. Timetables are public |
| 9 | **Accessibility** | The transit-unavailable disclosure names *which* journeys are missing, not merely that something degraded |
| 10 | **Performance** | Parsing and dictionary lookup |
| 11 | **Tenancy** | None |
| 12 | **Documentation** | This record, `IMPL-040`, the regression entry, the sub-step, parent §21, `MASTER_TRACKER` |

## 7. Mandatory data-flow inspection

| Hazard | Control | Evidence |
| --- | --- | --- |
| The night network deleted | `25:30` parses rather than raising | Asserted |
| Late departures shifted a day | Service time resolves onto the following calendar day | Seeded a wrap; killed by 2 |
| Evening services shifted | `23:59` is not treated as past midnight | Boundary asserted from both sides |
| A departure scheduled on an unplanned day | Hours above 48 refused | Asserted |
| A train that does not run on a holiday | Exceptions consulted first, returning immediately | Seeded; killed by 3 |
| A false infeasibility beyond the feed range | `UNKNOWN`, not `NO` | Seeded; killed |
| A stop_id resolving to a different platform | Feed pinned by content hash; drift **raises** | Seeded; killed |
| A traveller at the wrong platform | No nearest-match; an unresolvable stop is a recorded `CoverageGap` | Seeded; killed |
| Stale disruption data trusted | Staleness measured from **observation**, not onset | Seeded the onset variant; killed by 3 |
| A disruption read as over | Absent `active_to` means ongoing | Asserted |
| Transit absence hidden | `TransitUnavailable` requires a disclosure naming the lost modes | Asserted |

## 8. A mutant that survives, and why that is recorded rather than fixed

**Replacing the noon-minus-twelve anchor with a plain wall-clock midnight does not
fail the suite**, and after investigation it should not.

The usual justification for the GTFS anchor is that local midnight may not exist on
a spring-forward date. I tried to observe that and could not: measured across both
2026 Zurich transitions and in Havana, Santiago, Beirut and Asunción — zones whose
transitions fall at or near midnight — the two anchors produce the **identical
instant** every time. Python's `zoneinfo` normalises a non-existent or ambiguous
wall-clock midnight rather than raising, and `noon - 12h` lands on the same
normalisation.

So the honest position, now written into the module docstring, is that the noon
anchor is **specification conformance and not a bug fix**. It is kept because a
feed produced against the spec should be read against the spec, and because a
future tzdata or Python release could separate them —
`test_the_two_anchors_agree_in_every_zone_tested` pins the equivalence so that
divergence becomes a visible failure rather than a silent change in what a
departure time means.

**This is reported as 7 of 8 mutants killed, not 8 of 8.** A survivor with a
reason is a finding; a survivor quietly reclassified is the beginning of a habit.

## 9. Score

| Dimension | Value | Reason |
| --- | --- | --- |
| Reach | Medium | Every departure in a scenario flows through these types |
| Reversibility | High | A new package; nothing imports it yet |
| Detectability | High | 45 assertions; 8 mutants seeded, 7 killed, 1 explained |
| Security exposure | None | No I/O |
| Performance | None | Parsing only |
| **Overall** | **MEDIUM** | **Confidence HIGH.** No owner approval required |

## 10. Post-change verification

| Check | Result |
| --- | --- |
| Python suite | **843 passed, 5 skipped** (up from 798) |
| Mutation | 8 seeded, **7 killed, 1 survivor explained** (§8) |
| `pnpm verify`, `pnpm ci:local`, R1–R7 | Recorded in the regression entry |
