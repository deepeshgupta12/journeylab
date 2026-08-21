---
blast_radius_id: BR-053
sub_step_id: STEP-006.04
title: Repositories, unit of work and tenant-bound transactions
author: Deepesh Kumar Gupta
date: 2026-08-21
score: MEDIUM
confidence: MEDIUM
approval_required: false
---

# BR-053 — Repositories and unit of work

## 1. Graph state

| Field | Value |
| --- | --- |
| Indexed commit | `d869ad1` |
| HEAD at check | `d869ad1` |
| Freshness | ✅ up to date |
| Result | **NOT BLOCKED** |
| Confidence | **MEDIUM** — `RISK-016`, eighth reproduction (0/5/0 against 27/63/3) |

## 2. Tenant binding is a precondition, not a step

`REQ-SEC-001` puts a tenant on every row. A repository that binds per method is one
`SELECT` away from a leak the first time someone adds a method and forgets.

Here the binding happens when the unit of work opens, and **a repository cannot be
obtained outside one** — so there is no path to the database that skips it. That is
the structural version of the rule rather than the remembered one.

The database is deny-by-default underneath (`app_current_org()` is NULL when unset,
so no row qualifies), which means forgetting produces *nothing found* rather than
*everything found*. This layer exists to turn that silent emptiness into an explicit
refusal, because an empty result looks like an answer.

**The tenant is deliberately not repeated in the `WHERE` clause.** It would work, and
it would make every future query's correctness depend on remembering it — a second
place to get the same thing wrong, with the policy still there to be trusted or not.
A mutant that adds the predicate is killed by a test asserting its absence.

## 3. One aggregate per transaction

Breaking this looks like convenience: a handler that already has a transaction open
reaches for a second repository. It works, until one aggregate lives in a different
database or service, and then the transaction that quietly held the system together
cannot exist.

`UnitOfWork` records the first aggregate and refuses the second. Cross-aggregate
consistency goes through the outbox — which is why the outbox rows are written *in
the same transaction* as the one aggregate, before `COMMIT`, and why a rollback
leaves none. **No phantom events**, tested by raising inside the block and asserting
nothing was written.

`ItineraryItem` is deliberately not an aggregate: it belongs to a `ScenarioVersion`
and is written with it. An aggregate list that grows to include every table has
stopped meaning anything.

## 4. The mutant that survived was the one that mattered

Twelve of thirteen died at once. The survivor flipped `set_config(..., true)` to
`false` — which makes the binding **connection-scoped instead of transaction-scoped**,
so a pooled connection carries one tenant's context into the next tenant's
transaction. That is precisely the leak `test_tenant_isolation.sh` has tested at the
database since STEP-002.01.

My test asserted that `set_config` was called. **Binding happened; binding correctly
did not.** The distinction between "the call is there" and "the call is right" is the
whole of this defect, and only the mutation run found it.

**13 seeded, 13 killed** after the assertion was tightened to the argument.

## 5. Optimistic concurrency

Two advisors editing one trip is a normal Tuesday. `expected_version` is
keyword-only and has **no default** — a default makes the unchecked write the easy
one, and the unchecked write is the one that loses an edit with no error anywhere.
Zero affected rows raises rather than returning quietly.

## 6. Assessment

| Category | Assessment |
| --- | --- |
| Code | `apps/api/src/domain/repositories.py` — new |
| Schema | None. It writes to an `outbox` table that `.06` creates — see §7 |
| Contracts / events | Untouched |
| Security | **The main surface.** Tenant binding, transaction scope, table-name allowlist |
| Performance | No I/O of its own |

Table names are interpolated because a bound parameter cannot name a table, so an
allowlist shape is the whole defence there — refused rather than escaped, and tested
with five hostile inputs.

## 7. What this does not close

| Gap | Why |
| --- | --- |
| The `outbox` table does not exist yet | `.06` creates it. This sub-step owns the *atomicity* — that the row goes in before `COMMIT` — because that is a property of whoever owns the transaction |
| No real connection is exercised | The rules under test are ordering and refusal, and a live round trip would hide both. `.06` tests against PostgreSQL |
| `Repository.load` returns nothing useful | Row mapping needs the entity shapes to settle; `.05` normalizers and `.09` projections are the first real readers |

## 8. Score

**MEDIUM.** No schema, no contract, no callers yet — but it is the boundary every
future write passes through, and the tenant binding is the control R7 exists to
protect. Confidence MEDIUM under `RISK-016`.
