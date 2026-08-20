---
blast_radius_id: BR-052
sub_step_id: STEP-006.03
title: Domain entities, invariants and state machines
author: Deepesh Kumar Gupta
date: 2026-08-20
score: LOW
confidence: MEDIUM
approval_required: false
---

# BR-052 — Domain entities

## 1. Graph state

| Field | Value |
| --- | --- |
| Indexed commit | `d6318a2` |
| HEAD at check | `d6318a2` |
| Freshness | ✅ up to date |
| Result | **NOT BLOCKED** |
| Confidence | **MEDIUM** — `RISK-016`, seventh reproduction |

## 2. Queries run

| Symbol | Graph | Grep |
| --- | --- | --- |
| `Money` | 2, LOW | **27** |
| `TemporalValidity` | 0, **UNKNOWN** | 9 |
| `Provenance` | 0, LOW | **14** |

`TemporalValidity` returns `UNKNOWN` because the only definition the graph can see is
in a generated Pydantic model. Additive change: nothing imports `domain.models` yet.

## 3. Invariants live in constructors

An invariant checked by the caller is an invariant checked by *some* callers. Every
rule here refuses at construction, so a second entry path — an admin tool, a replay,
a fixture — cannot bypass it by not knowing it exists.

`ScenarioLineage` is a separate type for the same reason: `Scenario` cannot be given
three of its four required references, and there is no partially-built scenario to
repair later. `REQ-CONS-006` has no recovery point — a run whose inputs were not
recorded is unreproducible permanently.

## 4. Infeasible is not Failed, and the table says so

`BACKEND_ARCHITECTURE` §3 gives them different recovery paths, and the transition
table encodes exactly that: `INFEASIBLE → BRIEF_CONFIRMED` (relax the constraints)
and `FAILED → EVIDENCE_READY` (retry with what we have). Neither can reach the
other's target.

Telling a traveller "no plan fits your constraints" when a provider timed out is a
different product answer, not a cosmetic difference — so an invalid transition raises
rather than logging and continuing.

The table is data rather than `if` statements so it can be compared to the diagram by
eye, and two tests check properties of the table itself: every state has a row, and
**every state can reach `ARCHIVED`** — because `REQ-PRIV-006` deletion runs from
there, and a state that cannot get there is a trip that can never be deleted.

## 5. Protection is enforced on the model

`REQ-CONS-011`: an edit touching a protected item is refused until explicitly
unlocked. A replan, a repair and a bulk edit are three callers and only one would
have remembered, so `edited()` refuses.

Unlocking is itself an edit, and is the single change a protected item accepts —
otherwise protection could never be removed, which is a different bug with the same
cause. A mutant that blocks unlocking too is killed by its own test.

## 6. What the type checker cannot catch

`Money(True, "CHF")` passes mypy cleanly, because `bool` is a subtype of `int` in
Python. There is no `type: ignore` on that test and its absence is the point: the
static checker is satisfied, so the runtime guard is the only thing standing between
a flag and a price.

That generalises — the guards here that matter most are the ones the type system
cannot express: a float amount, a currency mismatch, a seed of zero being falsy but
valid.

**Mutation testing: 14 seeded, 14 killed.** One survived first time: nothing asserted
that `Provenance` refuses an out-of-range confidence. The places adapter has the same
guard *and its own test*, which is what made the gap easy to miss — **a shared rule is
not shared coverage**, and a second class needs its own assertion.

## 7. Assessment

| Category | Assessment |
| --- | --- |
| Code | `apps/api/src/domain/models.py` — new. Nothing modified |
| Schema / contracts / events | Untouched |
| Security / privacy | None — pure value objects and state |
| Performance | Constructor validation only |

## 8. What this does not close

| Gap | Why |
| --- | --- |
| Nothing persists these yet | Repositories are `.04` |
| `Money` has no subtraction or multiplication | Not needed yet, and each needs its own decision about rounding and negative totals. Absent rather than guessed |
| The generated Pydantic `Money` still exists separately | The contract's model is the wire shape; this is the domain shape. Merging them would make an internal invariant a public promise |

## 9. Score

**LOW.** Additive, no callers, no I/O, no contract. Confidence MEDIUM under
`RISK-016`.
