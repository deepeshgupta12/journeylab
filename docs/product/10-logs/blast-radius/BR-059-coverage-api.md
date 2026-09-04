---
blast_radius_id: BR-059
sub_step_id: STEP-007.01
title: Coverage read model and the public coverage API
author: Deepesh Kumar Gupta
date: 2026-09-04
score: MEDIUM
confidence: MEDIUM
approval_required: false
---

# BR-059 — The coverage API

## 1. Graph state

| Field | Value |
| --- | --- |
| Indexed commit | `64c209d` |
| HEAD at check | `64c209d` |
| Freshness | ✅ up to date |
| Result | **NOT BLOCKED** for Python; **`RISK-017`** for the three migrations |
| Confidence | **MEDIUM** |

## 2. Queries run

| Symbol | Graph | Grep |
| --- | --- | --- |
| `coverage_projection` | **14, MEDIUM** | 18 |
| `PublicCoverage` | 1, LOW | 8 |
| `Projection` | 1, LOW | 6 |
| `UnitOfWork` | 0, LOW | **17** |

`coverage_projection` is the **first non-trivial answer the graph has given** —
fourteen dependants against eighteen real references. `RISK-016` is narrowing where a
symbol has many same-language callers and unchanged where it does not; `UnitOfWork`
still reports zero against seventeen.

## 3. The first product route, and what it found in the data model

This is the first FastAPI handler in the repository. Writing it surfaced three defects
in work already marked `VERIFIED`, which is the pattern `BUG-027` established: **the
next sub-step is how the last one's defect is found.**

**`BUG-028` — the endpoint could not read its own read model.** `API-017` is declared
`security: []`, because putting coverage behind a login means asking somebody to
register in order to be told *no*. STEP-006.09 built the read model tenant-scoped. A
public request has no tenant, so RLS denied every row — and the endpoint **does not
error**, it returns an empty region list. "We support nowhere", well-formed and
plausible, served to the person deciding whether to sign up. Fixed by `016`.

**`BUG-029` — two contract-required fields had no source.** `CoverageRegion` requires
`display_name` and `date_bounds` and forbids extra properties; the read model had
neither and carried `accepting_trips`, which the contract does not allow. The
projection was designed from the event stream and the contract from the traveller's
need, and nothing had compared them. Fixed by `017`, which makes both NOT NULL and
seeds **no region** — an empty coverage list is the honest current answer, and the
schema now forces whoever declares the first region to decide its name and dates.

**`BUG-030` — R7 reported PASS about a database nobody asked it to test.** Found by
running `pnpm guard:meta`, which turned out never to have been run. See §6.

## 4. Declared and derived are different kinds of column

`freshness` and `accepting_trips` are folded from `EVT-008`. `display_name` and
`date_bounds` are the product's own statement, which no event produces.

That distinction reached back into STEP-006.09: **a rebuild must UPDATE the derived
columns, never DELETE and reinsert.** Deleting is the natural implementation — it is
how you guarantee no stale row survives — and it would erase every region's name and
dates, leaving a projection that rebuilt perfectly and a coverage page that cannot
render. The rebuild test now asserts the declared half survives.

## 5. The cache is global because the data is

`REQ-SEC-001` requires a tenant on every cache key. This cache has none, and that is
the rule applied to data with no tenant rather than an exception to it.

The safety property is therefore different in kind — not *"the key is scoped"* but
**"nothing scoped is in here"** — so it is tested on the value and on every key the
cache has held. The cache refuses a second key: the moment it holds two documents,
one has a caller with something else to store, and the one after that will have a
tenant.

**The `[cache]` pending R7 vector fired**, exactly as the outbox one did at
STEP-006.06. It was **narrowed rather than closed**, which is the honest outcome: the
first cache in the system is public and tenant-free, so it is not the cross-tenant
vector `REQ-SEC-002` names. The detector now requires a tenant, org or trip in a cache
key, so it fires when the real thing arrives with STEP-010 retrieval.

## 6. A guard suite that runs only on request reports whatever it reported last

`pnpm guard:meta` was not in `pnpm verify`. It had therefore not run for twenty
sub-steps — while twenty regression entries recorded *"meta-suite 72/72"*, a number
that was wrong in both directions: the suite has 74 tests and three were failing.

The three failures were the STEP-001.07 assertions written to stop `BUG-023`
recurring, and they were failing about exactly that class of defect. `BUG-030`.

The correction is recorded at the top of `REGRESSION_LOG` rather than by editing the
twenty entries, because rewriting them to look correct would destroy the only useful
thing about the episode. `guard:meta` is now in `verify`.

## 7. The guard I wrote caught me one step later

`platform/` shadows the standard library's `platform` module, and `apps/api/src` is on
`pythonpath` — so `platform.system()` would have resolved to my package for the whole
process, failing inside some unrelated dependency with nothing pointing back.

Caught by importing it before writing a line of the handler. I then wrote
`no-stdlib-shadowing.sh` with a seeded-violation meta-test, wired it into `verify` —
and it immediately failed on **`tests/platform`**, which I had just created and which
shadows the same module because `tests` is also on `pythonpath`.

A guard that catches its own author one step after being written is the best evidence
it was worth writing.

## 8. Assessment

| Category | Assessment |
| --- | --- |
| Code | `apps/api/src/platform_api/coverage.py` — new, the first product handler |
| Schema | `016` (contract phase, named as such) and `017` |
| Contracts | `API-017` implemented as declared. **No contract change** — the implementation moved, not the contract |
| Security | Public by design. No supplier identity in the response, enforced in the projection, the table and the handler |
| Guards | `no-stdlib-shadowing` added; `guard:meta` added to `verify` |

**Mutation testing: 13 seeded, 13 killed.** Four survived the first run: an echoed
`display_name`, a tenant predicate in the handler's own query, and **two database
constraints with no test behind them** — the third occurrence of that gap after
STEP-006.08 and STEP-006.09.

## 9. What this does not close

| Gap | Why |
| --- | --- |
| No HTTP server routes to the handler | `get_coverage` is the operation; wiring an ASGI app, its middleware and its error mapping is `.02`'s surface plus operations work |
| No region is declared | Deliberate. Declaring one is a product decision about what we support and for which dates, and `017` forces it to be made rather than defaulted |
| `[cache]` R7 vector still open | Narrowed, not closed — a tenant-scoped cache does not exist yet |

## 10. Score

**MEDIUM.** Two migrations and the first public surface, against an empty table with
no consumer — but it found three defects in `VERIFIED` work, one of which weakened
the check this repository calls non-negotiable.
