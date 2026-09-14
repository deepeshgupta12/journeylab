---
blast_radius_id: BR-064
sub_step_id: STEP-007.05
title: Provider-degradation disclosure, and the projection write that did not exist
author: Deepesh Kumar Gupta
date: 2026-09-14
score: MEDIUM
confidence: HIGH
approval_required: false
---

# BR-064 — Degradation disclosure

## 1. Graph state

| Field | Value |
| --- | --- |
| Indexed commit | `8d9d28b` |
| HEAD at check | `8d9d28b` |
| Freshness | ✅ `status` up to date before any edit |
| Result | **NOT BLOCKED** |
| Confidence | **HIGH — from grep and the type-checker, not the graph** |

## 2. Queries run — `RISK-016`'s fifteenth reproduction

| Symbol | Graph (`upstream`) | Grep | Agreed? |
| --- | --- | --- | --- |
| `get_coverage` | **0, LOW, `"epistemic": "exact"`** | **8 call sites** | ❌ |
| `read_coverage` | not queried separately — same module, same blind spot | 13 call sites | — |

The eight `get_coverage` sites grep found: the production call at
`apps/api/src/app.py:189`, one in `tests/security/test_tenant_isolation.py`, and six in
`tests/platform_api/test_coverage_api.py`.

This is the shape `BR-063` §2 predicted precisely: **intra-file edges in `app.py`
resolve; cross-file edges into it do not.** `get_coverage` is defined in
`platform_api/coverage.py` and called from `app.py` — a cross-file call into the API
application — so the graph cannot see its one production caller. Confidence is HIGH
anyway, because a changed keyword-only signature is a `TypeError` at every call site
that omits it, and all eight were found and updated by running the suites.

## 3. What the sub-step was written to do, and what it actually needed

The plan listed *"coverage projection consumes `EVT-008` through the STEP-006.07
consumer framework"* as the first item. **That was already true** — `fold_coverage`
has consumed `EVT-008` since STEP-006.09.

The missing thing was one step further on, and nothing recorded it: **no production
code wrote `coverage_read_model`.** The projection folded health into an in-memory dict
and nothing carried it to the table `API-017` reads. A provider degrading changed a
projection no traveller could ever observe.

## 4. The rule that lived only in a test

How to write that table safely was known. STEP-006.09's
`test_rebuilding_restores_derived_fields_without_destroying_declared_ones` asserted it,
**as inline SQL inside the test**:

> UPDATE the derived columns. Never DELETE-and-reinsert — the declared columns
> (`display_name`, `date_bounds_*`, `time_zone`) are produced by no event, so a rebuild
> cannot restore them.

A rule whose only statement is in a test is a rule production code cannot obey. It now
lives in `services/events/src/read_models.py::apply_coverage_state`, and the test that
used to carry it is exercised through that function in `test_read_models.py`.

## 5. Where the write could not go

The natural home was `projections.py`, beside the fold. **That module is asserted
pure**: `reads_only_its_arguments` AST-walks it and fails on `execute`, `fetchall`,
`now` or `getenv`, because a fold that queries current state produces today's answer
while replaying a year-old event.

The first draft put the writer there and broke that check —
`test_the_module_reaches_no_clock_and_no_database` failed, correctly. Persistence is
impure by definition, so it moved to its own module rather than provoking anybody into
relaxing the purity rule.

`apps/api` was not given an import of `services/events` either. It has never had one,
and the cache invalidation contract is expressed as a return value — the set of
regions that changed — so whichever process consumes `EVT-008` can invalidate without
the API knowing about projections.

## 6. The cache, and what `REQ-EVID-006` actually forbids

The requirement is not "do not cache". It is: *degradation masked by cached data
**presented as current***. Two independent guarantees answer it, and each is
insufficient alone:

| Guarantee | Mechanism | Alone, it would leave |
| --- | --- | --- |
| The answer says when it was taken | `Coverage.observed_at`, stamped **before** caching | honest staleness for the full 30-second TTL |
| A real change busts the cache | `apply_coverage_state` returns what changed; the caller invalidates | a cache hit that still claims to be a fresh read |

**The timestamp is stamped inside `read_coverage`, not on the way out.** Stamping on
the way out is the tempting implementation — it is always accurate to the request —
and it inverts the guarantee: every cache hit would claim to be a fresh read, which is
the forbidden thing with the field added as decoration. Mutant #1 is exactly that, and
it is killed.

`observed_at` is an **additive** contract change — `[ADDITIVE] Coverage.observed_at`
from the compatibility gate. It is also `REQ-EVID-001` applied: provider health is the
most volatile fact on the page, and every volatile fact carries its observed time.

## 7. Scoring

| Category | Assessment |
| --- | --- |
| Code | `platform_api/coverage.py` (signature), `app.py` (one call), `read_models.py` (new) |
| Contract | `Coverage.observed_at` — **`[ADDITIVE]`** |
| Schema | **None.** `limitations` is already `jsonb`; the writer serialises and casts explicitly |
| Web | `degradation.tsx` (new), `page.tsx` (sentence map moved into the component) |
| Security / tenancy | None — coverage is platform data (`BUG-028`, `016`) |
| **Score** | **MEDIUM** |
| Approval | **Not required** — MEDIUM, confidence HIGH, no open product question |

## 8. Mutation testing — 12 killed, and one idea killed with them

| # | Seeded defect | Rule |
| --- | --- | --- |
| 1 | `observed_at` stamped on the way out | a cache hit must not claim to be fresh |
| 2 | `observed_at` dropped | every response carries it |
| 3 | the cache cannot be invalidated | a change reaches the traveller |
| 4 | the writer nulls `display_name` | the declared half survives |
| 5 | every row reported as changed | the invalidation signal means something |
| 6 | `accepting_trips` defaults to `true` | a stale region is not published as bookable |
| 7 | a row with no `freshness` is written | a fold that changed shape is refused |
| 8 | the fold carries `provider_id` into state | no supplier identity (`REQ-EVID-006`) |
| 9b | the effect's dependency array widened | announced once per change, not per render |
| 10 | observation time hidden when healthy | every answer says how old it is |
| 11 | the banner made assertive | a disclosure is not an emergency |
| 12 | limitations composed in the UI | text comes from the read model |

**Mutant 9 survived, and that was the finding.** The component originally held a
`useRef` guard *in addition to* the `[health]` dependency array — defence in depth
against a future unrelated dependency. Removing the guard changed nothing observable,
because the array already prevents the effect re-running. No test could tell the two
versions apart.

A guard nothing can distinguish from its absence is not protection; it is code
maintained forever on the strength of a comment. It was deleted, and mutant 9b —
widening the dependency array, the protection that is real — was seeded instead and
killed.

## 9. Follow-up created

| Item | Type |
| --- | --- |
| Nothing runs `apply_coverage_state` in production yet — no `EVT-008` consumer process exists. The seam is built and tested end to end; deployment wires it | `STEP-027` / `ENH-007` |
| `get_coverage` 0-dependant verdict against 8 call sites | `RISK-016` #15 |
