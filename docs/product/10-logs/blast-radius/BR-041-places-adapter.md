---
blast_radius_id: BR-041
sub_step_id: STEP-005.02
title: Places, hours and accessibility adapter
author: Deepesh Kumar Gupta
date: 2026-08-13
score: MEDIUM
confidence: HIGH
approval_required: false
---

# BR-041 — Places, hours and accessibility adapter

## 1. Graph state

| Field | Value |
| --- | --- |
| Indexed commit | `9a82fa4` |
| HEAD at check | `9a82fa4` |
| Freshness | ✅ up to date |
| Result | **NOT BLOCKED** |
| Confidence | **HIGH** — additive into `services/integrations/`, which only `.01` occupies |

## 2. What the sub-step record assumed, and what changed

`.02` §4 says *"No provider selected (EXT-001). Build against fixtures."* That was
written before `DEC-002` closed. **`ADR-016` has since selected Switzerland and
named the sources**, so this is built against real licences —
`opentransportdata.swiss`, `opendata.swiss` and OpenStreetMap — rather than an
abstract provider.

The consequence is that `ADR-016`'s licence finding stops being a document and
becomes a field: `Provenance.licence_id`, added in STEP-004.06 and unused until
now, carries ODbL and non-ODbL facts side by side from the first ingestion.

## 3. The decision this sub-step exists to get right

**Unknown is not closed**, and a boolean cannot hold both. Collapsing them breaks
the solver in **opposite** directions, and both failures are ones this product
exists to prevent:

| Collapse | Consequence |
| --- | --- |
| unknown read as **CLOSED** | a feasible plan is reported infeasible — `REQ-CONS-005` gives the user a conflict set for a constraint that does not exist |
| unknown read as **OPEN** | an itinerary is built on a place that was shut — `REQ-CONS-004`, which `BUG_REGISTER` defines as **S1 by definition** |

So `Availability` has three states and every consumer must handle the third. That
is the reason it is a type rather than `list[Interval] | None`, and it is the
single most consequential line in the module.

The same rule governs seasons: no applicable window returns **UNKNOWN**. A railway
with summer hours and no winter entry tells us nothing about January, and
reporting `CLOSED` would invent a fact the source never stated.

## 4. Midnight, and why the rule lives in one place

`Fr 22:00-02:00` is one span ending on Saturday. Stored as written it has
`start > end`, and every downstream comparison silently reverses. It is split at
midnight into two same-day intervals, so `Interval` can enforce `start < end` in
its constructor and no consumer needs to know the rule exists.

## 5. Change inventory

**Added** — `services/integrations/src/places/`: `licence.py`, `hours.py`,
`adapter.py`; `tests/integrations/test_places_adapter.py` (36 assertions).

**Modified** — none. The sub-step is additive.

## 6. Twelve impact categories

| # | Category | Assessment |
| --- | --- | --- |
| 1 | **Callers / call graph** | None yet. Entity resolution is `.07`, freshness policy `.08` |
| 2 | **Public API / contracts** | None. `CanonicalPlace` is deliberately **wider** than the contract's `Place`, so an internal field cannot become a public promise by accident |
| 3 | **Database / schema** | None. Persistence is `STEP-006` |
| 4 | **Events** | None |
| 5 | **Configuration** | Licence records are **code, not config** — adding a source is a licence decision and belongs in a diff |
| 6 | **Infrastructure** | None. No new dependency; `zoneinfo` is stdlib |
| 7 | **Security** | Indirect. Outbound fetching goes through `.01`'s connector; nothing here opens a socket |
| 8 | **Privacy** | **Material.** `REQ-PRIV-003`: accessibility is declared-only. An unknown key is **dropped**, never mapped to the nearest neighbour, and an empty list means *not declared* rather than *no features* |
| 9 | **Accessibility** | The data itself. A wrong accessibility fact is worse for the person relying on it than a missing one, which is why nothing is inferred |
| 10 | **Performance** | Parsing only; no I/O |
| 11 | **Tenancy** | None. Place data is public and not tenant-scoped |
| 12 | **Documentation** | This record, `IMPL-038`, the regression entry, the sub-step, parent §21, `MASTER_TRACKER` |

## 7. Mandatory data-flow inspection

**Flow:** provider payload → licence gate → hours parse → accessibility filter →
provenance → `CanonicalPlace`.

| Hazard | Control | Evidence |
| --- | --- | --- |
| Ingesting without recorded terms | `licence` is a **required keyword argument** — REQ-DATA-001's "before ingestion is enabled" is a sequencing claim, kept by structure | `TypeError` asserted |
| A non-commercial source ingested | `LicenceRecord` **refuses to exist** for one. Open-Meteo is the live example (`ADR-016` §2) | Seeded and killed |
| ODbL obligations lost in the pack | `share_alike` recorded per source; `licence_id` on every fact | Asserted for OSM and `opendata.swiss` |
| "Terms not read" confused with "terms impose nothing" | `ShareAlike` is **three-valued** | Asserted |
| An unrenderable attribution obligation | A record requiring attribution with no text is refused | Asserted |
| Unknown hours read as closed or open | Three-state `Availability` | Seeded both ways; killed by 3 and 1 |
| A guessed schedule | An unsupported rule **raises**; the caller records UNKNOWN | Seeded; killed by 2 |
| Midnight reversal | Split at midnight; `Interval` enforces `start < end` | Seeded; killed by 3 |
| Hours evaluated in the wrong zone | Comparison happens after `astimezone`; a naive moment is refused | Seeded; killed |
| A DST boundary computed by arithmetic | The zone does it; the test asserts the offsets differ either side | Asserted on 25 Oct 2026 |
| Inferred accessibility | A closed vocabulary; unknown keys dropped with a warning | Seeded; killed |
| A place silently discarded over bad hours | Unparseable hours degrade **that field only** | Asserted |

## 8. Score

| Dimension | Value | Reason |
| --- | --- | --- |
| Reach | Medium | Every place fact in the evidence pack flows through this |
| Reversibility | High | A new package; nothing imports it yet |
| Detectability | High | 36 assertions, 8 mutants seeded, 8 killed |
| Security exposure | Low | No I/O; the connector owns egress |
| Performance | None | Parsing only |
| **Overall** | **MEDIUM** | **Confidence HIGH.** No owner approval required |

## 9. Post-change verification

| Check | Result |
| --- | --- |
| Python suite | **772 passed, 5 skipped** (up from 736) |
| Mutation | 8 seeded, 8 killed |
| `pnpm verify`, `pnpm ci:local`, R1–R7 | Recorded in the regression entry |
