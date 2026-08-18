---
blast_radius_id: BR-046
sub_step_id: STEP-005.07
title: Canonical place entity resolution and the provider identifier graph
author: Deepesh Kumar Gupta
date: 2026-08-18
score: MEDIUM
confidence: MEDIUM
approval_required: false
---

# BR-046 — Entity resolution

## 1. Graph state

| Field | Value |
| --- | --- |
| Indexed commit | `5eac52e` |
| HEAD at check | `5eac52e` |
| Freshness | ✅ up to date |
| Result | **NOT BLOCKED** |
| Confidence | **MEDIUM** — and §2 explains why it is not HIGH |

## 2. Queries run, and a finding about the tool itself

| # | Query | Result |
| --- | --- | --- |
| 1 | `impact CanonicalPlace --direction upstream --depth 3 --include-tests` | `impactedCount: 0`, risk **LOW** |
| 2 | `impact adapt --direction upstream --depth 3 --include-tests` | `impactedCount: 0`, risk **LOW** |
| 3 | `impact Provenance --direction upstream --depth 3 --include-tests` | `impactedCount: 0`, risk **LOW** |
| 4 | `context CanonicalPlace` | `incoming: {}` |
| 5 | `cypher` — edges out of `tests/integrations/test_places_adapter.py` | **one** cross-file edge, to `places/hours.py` |
| 6 | `cypher` — edges into `places/adapter.py` | one, and it is the directory-contains edge |
| 7 | grep for the same symbols | `test_places_adapter.py` imports `adapt` and calls it **11 times** |
| 8 | `detect-changes` at pre-commit | Reported **8 files, 4 symbols — all of them the excluded agent-config files**, and none of the 17 staged. Scope was verified from the staged file list instead |

**Queries 1–4 are wrong, and query 7 is how I know.**

The MCP tools are not exposed in this session, so these were run through the CLI —
which is the same graph. It reports zero dependants for a symbol with eleven live
call sites. The test file *is* indexed (55 nodes); what is missing is the
**cross-file call and import edges** from test modules to the code they exercise,
and `--include-tests` does not supply them.

This matters beyond today. A `LOW / 0 dependants` verdict is the answer this
repository has been treating as reassurance, and for any symbol whose only callers
are tests — which is **every symbol in `services/`, because no application wires
them yet** — that verdict is produced by an absence of edges rather than by an
absence of callers. It is the failure mode already recorded for `gitnexus_query` in
`BR-029` §3: a degraded signal that reads exactly like a real answer.

So the blast radius below is scored from the grep, and the confidence on this record
is **MEDIUM rather than HIGH** — not because the change is unclear, but because the
tool that is supposed to bound it under-reports and I can only bound it by hand.
Logged as `RISK-016`.

## 3. What changed

| Category | Assessment |
| --- | --- |
| Code | `services/ingestion/src/entity_resolution.py` **new**; `places/adapter.py` modified (BUG-027) |
| Public API contract | **Untouched.** `CanonicalPlace` is the internal record, deliberately wider than the contract's `Place` |
| Events | None |
| Data / schema | `CanonicalPlace` gains `coordinate` and `category`, both **required** |
| Configuration | `pyproject.toml` — `services/ingestion/src` added to `pythonpath` and `mypy_path` |
| Infrastructure | None |
| Security | No new egress, no credential, no personal data |
| Privacy | Places are reference data — see §7 |
| Accessibility | No user surface in this sub-step; the review queue is a service-layer type |
| Telemetry | None |
| Performance | Pairwise comparison is O(n²) and **not** blocked — see §9 |
| Documentation | This record, `IMPL-045`, `BUG-027`, the sub-step record, parent §21, `MASTER_TRACKER` |

**Direct blast radius (from grep, not from the graph):** `tests/integrations/
test_places_adapter.py` — 11 call sites, all updated; `tests/integrations/
test_routing_matrix.py` — one guard hardened (§8); no non-test caller of `adapt`
exists anywhere in the repository.

## 4. A false merge and a missed merge are not the same size of mistake

A missed merge leaves a duplicate in a list: visible, irritating, harmless. A false
merge produces an itinerary that is internally consistent, carries plausible travel
times, and **sends the traveller to the wrong building** — and nothing downstream
can detect it, because the merged record looks exactly like a correct one.

The two errors are not comparable, so the matcher is not tuned for accuracy. It is
tuned so the only automatic answer is one that cannot be wrong, and everything else
is asked about. That makes the review queue the main path rather than the exception,
and §8 reports the rate rather than implying otherwise.

## 5. Signals are gated, never summed

The obvious implementation scores distance and name similarity, weights them, and
merges above a threshold. That is precisely how two branches of one chain get
merged: an identical name (`Coop Bahnhofstrasse`) buys enough score to pay for being
400 m apart.

**Compensation between independent signals is the false-merge mechanism.** So each
signal has its own gate and every gate must be cleared — a perfect name cannot
rescue a failing distance. The same rule runs in reverse for evidence *against* a
merge: the declared category can only ever **demote** a decision, never promote one.

That asymmetry is load-bearing in both directions:

- A cafe inside a museum sits at the museum's coordinate, is often listed under the
  museum's name, and is a different place with different opening hours. Only the
  category separates them, and in the labelled sample it is the **only** thing
  standing between that pair and a false merge.
- "Same point and same category, therefore the same place" is the obvious next step
  and it is wrong. A station concourse holds a dozen venues that all declare
  `restaurant`. That pair is in the sample too, so the optimisation cannot be added
  later without a test failing.

## 6. An identifier conflict is not settled by proximity

Two records four metres apart carrying **different** Wikidata entities are not a
near-certain match with a small data problem. They are two sources asserting
different identities, and `REQ-EVID-002` forbids averaging that away.

So the conflict outranks the geometry: it goes to review, never to a merge, however
close the records sit. Agreement is treated with the same care in the other
direction — identifiers that agree while the coordinates disagree by kilometres also
go to review, because one of the two sources is wrong about where the place is and
merging silently would bury that.

**What an identifier is allowed to mean** is an allowlist, and the test for
membership is stated rather than assumed: *a namespace carries identity only if its
identifiers denote at most one venue.* An identifier denoting something **coarser**
than a venue — a building, a street address, a phone number, a chain website —
merges distinct venues by construction, and does it with the confidence of an exact
match. `gtfs_stop` is excluded for a second, independent reason established in
STEP-005.04: those identifiers are scoped to a feed publication and are not stable
across publications.

## 7. Tenancy, stated rather than assumed

`REQ-SEC-001` puts a tenant ID on every row. Nothing here carries one, and that is a
decision rather than an omission: a place is reference data, not tenant data.
Scoping the canonical graph per tenant would fragment it, multiply every merge
decision by the tenant count, and make one tenant's review work invisible to the
next.

The consequence is that **review decisions are global**, so a reviewer's judgement
about two Bern museums applies to everyone. That is correct for reference data and
wrong for anything derived from a traveller's behaviour, and nothing here derives
from behaviour. `STEP-006` owns persistence and must enforce this boundary at the
table, not just at the type.

## 8. Measured, on a labelled sample, with the sample's limits stated

| Metric | Value |
| --- | --- |
| Pairs | 13 |
| Automatic merges | 3 |
| Sent to review | 7 |
| Declared distinct | 3 |
| **False merges** | **0** — precision 1.000 |
| **True duplicates silently discarded** | **0** |
| Recall (merged without asking) | 0.500 |
| Review rate | 0.538 |

Two metrics rather than one, because **precision alone is satisfiable by merging
nothing** — a matcher that answers DISTINCT to everything scores 1.000. The second
metric counts true duplicates it declared distinct, which are the ones no human will
ever be asked about. Both are asserted, and the exact figures above are pinned by a
test so they cannot drift away from the code silently.

**What this sample is not.** It is hand-written from Swiss venue patterns; **no
provider fetch has been made**, which is the same disclosure carried through
`.02`–`.06`. Every pair in it is a case a naive matcher gets wrong, so it measures
whether the matcher is **correct on the hard cases** and says nothing about how
often those cases occur. The 0.538 review rate is an upper bound on an adversarial
sample, **not a forecast of production review load** — at corpus scale that rate
would be operationally impossible, and the real figure cannot be known until there
is a real corpus.

**Mutation testing: 13 seeded, 13 killed.** Three survived the first run and each
survival was a real gap rather than a nuisance:

1. The conflicting-identifier mutant survived because the sample's conflict pair had
   names similar enough that the same-doorstep rule caught it anyway — the conflict
   rule was never actually exercised. Fixed by a pair where distance, name and
   category all demand a merge and only the conflict prevents it.
2. The category-promotion mutant survived because no pair had two distinct venues
   sharing one point *and* one category. That is the station concourse, and it was
   missing from the sample.
3. The single-normalisation mutant survived because the assertion was `>= 0.9` and
   diacritic-stripping alone scores 0.974 on `Zürich`/`Zuerich`. The second
   normalisation only changes a verdict on **short** names — `Bär` against `Baer` is
   0.857 stripped, which fails the merge gate, and 1.000 with umlaut expansion. The
   test now pins that number, because "it helps with umlauts" is not a claim anything
   can check.

**A guard from `.05` had gone stale and this sub-step is what stales it.**
`test_the_module_offers_no_way_to_build_a_time_from_coordinates` blocks the names
`haversine`, `distance`, `euclidean`, `great_circle`. The distance function written
here is called `metres_between` and contains none of them, so the convenience that
test exists to keep out of routing's reach had just become importable without the
test noticing. A blocklist only blocks the names somebody thought of; the check now
also refuses any import of the resolution module from routing.

## 9. What this does not close

| Gap | Why it is open |
| --- | --- |
| **Thresholds are not tuned on real data** | `DEC-002` is closed (Switzerland) but no provider corpus has been fetched. The gates are measured against a hand-built adversarial sample, which proves correctness and not calibration |
| **Comparison is O(n²)** | Fine for a sample, not for a region. Blocking by geohash or grid cell is the standard fix and belongs where the corpus arrives, not before it — tuning a blocking strategy against imagined data is how you get a blocking strategy that fits imagined data |
| **The API contract cannot express a location** | `Place` has `name`, `time_zone` and `place_id` and no coordinate, so the map that `REQ-A11Y-003` presumes has nothing to draw. Out of scope here; logged as `ENH-003` |
| **The review queue has no interface** | It is a service-layer type. A reviewer needs a screen, and that screen is `REQ-A11Y-001` and `REQ-A11Y-003` work in the UI steps |
| **`Stop` still carries raw floats** | `transit/feed.py` validates its own latitude and longitude rather than using `Coordinate`. Unifying them would touch STEP-005.04's pinned feed semantics for no behavioural gain today |

## 10. Score

| Dimension | Assessment |
| --- | --- |
| Reversibility | Revert the commit. `.02`'s adapter returns to accepting incomplete payloads, which is the defect, so the revert is not free |
| Contract exposure | None — no public surface changed |
| Data exposure | None — reference data, no personal data, no new egress |
| Correctness risk | **The false merge**, mitigated by gating, by demotion-only category logic, by precision measured at 1.000 and by 13 killed mutants |
| Confidence | **MEDIUM** — the graph under-reports (§2) and the thresholds are unvalidated against real data (§9) |

**Score: MEDIUM.** No owner approval required.
