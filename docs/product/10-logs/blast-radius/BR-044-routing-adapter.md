---
blast_radius_id: BR-044
sub_step_id: STEP-005.05
title: Travel-time matrices and explicit profile support
author: Deepesh Kumar Gupta
date: 2026-08-17
score: MEDIUM
confidence: HIGH
approval_required: false
---

# BR-044 — Routing adapter

## 1. Graph state

| Field | Value |
| --- | --- |
| Indexed commit | `8bf34e0` |
| HEAD at check | `8bf34e0` |
| Freshness | ✅ up to date |
| Result | **NOT BLOCKED** |
| Confidence | **HIGH** — additive; nothing imports it yet |

## 2. Queries run

| # | Query | Result |
| --- | --- | --- |
| 1 | `cypher` over `services/routing` | 0 nodes — additive, a new service root |
| 2 | `detect_changes(staged)` | Run pre-commit; recorded in the regression entry |

## 3. The prohibition this sub-step exists to enforce

§5: *"silent fallback from wheelchair to walking is prohibited."*

If a provider cannot route step-free and we quietly return walking times, a
wheelchair user receives an itinerary computed for somebody who can take stairs.
**It will look correct.** Every duration is plausible; the transfer at Bern that
needs a footbridge reads as nine minutes. There is no way for the person to know,
and that is what makes it worse than a refusal — being told "we cannot route this
reliably" is useful information.

So `resolve_profile` returns either the requested profile **or** a
`ProfileUnsupported`, and the return type gives a consumer no third option: a
caller that asked for wheelchair cannot silently receive walking, because handling
the refusal is a typecheck obligation.

`ProfileUnsupported` carries **no duration field of any kind** — not a nullable
one. A nullable duration is one `or 0` away from becoming a travel time, and a
travel time is exactly what must not exist on that path.

**The disclosure is asserted on its wording, not just its presence.** "No step-free
data" must not read as "step-free", so the test requires the text to say access was
*not checked*, that the journey is *not shown as accessible*, and that walking
times were *not substituted*.

## 4. Two further refusals

**Straight-line distance is not a route.** Crow-flies across Lake Thun is not a
walk; across a valley it is a physical impossibility rendered as a duration. This
is enforced twice: a non-positive duration raises, and a test asserts the module
exposes **no** haversine, distance or great-circle helper — so the substitution
cannot be made by reaching for a convenience that happens to be lying around.

**A duration with no recorded assumptions is not evidence.** Walking speed,
transfer buffer and whether a lift was trusted all change the answer, and
`REQ-EVID-001` needs a derived volatile value to be interrogable. `assumptions`
is required even when it states the default.

## 5. Why the cache key carries the licence

A matrix derived from a source with a maximum cache duration must expire on **that
source's** terms. Keying by mode and window alone would serve a result past its
permitted retention — a contract breach that looks exactly like a cache hit.

`licence_id` is therefore part of the key's identity, not metadata attached to it,
and `is_expired` treats `None` as "this licence sets no limit" rather than as a
missing value. That distinction matters for the ODbL question `ADR-016` §1 leaves
open: OSM-derived and `opentransportdata.swiss`-derived matrices have different
retention rules and must not share a cache entry.

## 6. Twelve impact categories

| # | Category | Assessment |
| --- | --- | --- |
| 1 | **Callers / call graph** | None yet. Solver consumption is `STEP-012` |
| 2 | **Public API / contracts** | None |
| 3 | **Database / schema** | None. Matrix persistence is `STEP-006` |
| 4 | **Events** | None |
| 5 | **Configuration** | A new service root, `services/routing/src`, added to `pythonpath` and `mypy_path` |
| 6 | **Infrastructure** | None yet — **`DEC-008` is unresolved**, §8 |
| 7 | **Security** | None directly; fetching goes through `.01`'s connector |
| 8 | **Privacy** | None. Origins and destinations here are public stops |
| 9 | **Accessibility** | **This is the substance of the sub-step.** `REQ-A11Y-003` enforced structurally rather than by convention |
| 10 | **Performance** | Pure construction; the cache-key design is what bounds real cost later |
| 11 | **Tenancy** | None |
| 12 | **Documentation** | This record, `IMPL-041`, the regression entry, the sub-step, parent §21, `MASTER_TRACKER` |

## 7. Mandatory data-flow inspection

| Hazard | Control | Evidence |
| --- | --- | --- |
| A wheelchair request answered with walking times | `resolve_profile` returns a refusal; the type admits no downgrade | Seeded the downgrade; killed |
| Walking support read as implying wheelchair support | `supports` is exact membership | Seeded; killed by 2 |
| A refusal a caller can coerce into a duration | No duration field exists on `ProfileUnsupported` | Asserted by attribute absence |
| "No data" reading as "accessible" | Disclosure wording asserted, not just presence | Asserted on three phrases |
| An unreviewable accessibility claim | `declared_by` and `evidence` required | Seeded; killed |
| Straight-line distance as a travel time | Non-positive durations raise; no distance helper exists | Seeded; killed, plus a structural assertion |
| A duration nobody can interrogate | `assumptions` required | Seeded; killed |
| A cached matrix served past its licence terms | `licence_id` in the key; `is_expired` honours the limit | Both seeded; both killed |
| A resolver that refuses everything | A supported profile must return unchanged | Asserted — guards the guard |

## 8. `DEC-008` is unresolved, and a recommendation is owed

§4 of the sub-step says: *"propose a provider with rationale when this sub-step is
reached."* It has been reached, so the recommendation is on the table rather than
deferred — but **nothing in this sub-step depends on the answer**, which is why it
did not block: the scope asked for a *provider-independent* interface and that is
what was built.

The recommendation and its trade-offs are put to the owner in the sub-step's §13
and in `MASTER_TRACKER`. `DEC-008` stays open until confirmed, per `ADR-007`.

## 9. Score

| Dimension | Value | Reason |
| --- | --- | --- |
| Reach | Medium | Every travel time the solver consumes flows through these types |
| Reversibility | High | A new service root; nothing imports it |
| Detectability | High | 20 assertions, 8 mutants, 8 killed |
| Security exposure | None | No I/O |
| Performance | None | Construction only |
| **Overall** | **MEDIUM** | **Confidence HIGH.** No owner approval required for the code; `DEC-008` needs a decision |

## 10. Post-change verification

| Check | Result |
| --- | --- |
| Python suite | **863 passed, 5 skipped** (up from 843) |
| Mutation | 8 seeded, 8 killed |
| `pnpm verify`, `pnpm ci:local`, R1–R7 | Recorded in the regression entry |
