---
blast_radius_id: BR-042
sub_step_id: STEP-005.03
title: Forecasts, normals, alerts and objective withdrawal
author: Deepesh Kumar Gupta
date: 2026-08-14
score: MEDIUM
confidence: HIGH
approval_required: false
---

# BR-042 — Weather adapter

## 1. Graph state

| Field | Value |
| --- | --- |
| Indexed commit | `9a2db57` |
| HEAD at check | `9a2db57` |
| Freshness | ✅ up to date |
| Result | **NOT BLOCKED** |
| Confidence | **HIGH** — additive; nothing imports it yet |

## 2. Queries run

| # | Query | Result |
| --- | --- | --- |
| 1 | `cypher` over `services/integrations/src/weather` | 0 nodes — additive |
| 2 | `detect_changes(staged)` | Run pre-commit; recorded in the regression entry |

## 3. Two distinctions, both types rather than flags

### A normal is not a forecast

Beyond the horizon the honest answer is a climatological normal. That is a
legitimate input and **not a prediction about next Tuesday**. `REQ-EVID-003` says
an estimate is never rendered as confirmed, and returning a normal through the
same type as a forecast is exactly how it gets rendered as one.

So `Forecast` and `ClimateNormal` are separate types. A consumer written only for
the first fails to typecheck rather than quietly presenting a 30-year average as
tomorrow's weather. `Outlook.beyond_horizon` carries the substitution so the
interface can say so.

### A point forecast is not an input to a simulation

`18°C` tells a simulator nothing about how wrong it might be, so it is treated as
certain — and this product compares **feasible futures**, plural.
`REQ-CONS-006` wants reproducibility from inputs and a seed; a point estimate
silently removes the distribution the seed was meant to sample.

`Forecast` therefore cannot be constructed without `Uncertainty`. There is no
default, because a default here is a fabricated confidence interval. The module
will not widen a bare point into "probably ±2°" — that is inventing the very thing
the requirement preserves, the weather equivalent of the coercion `schema_gate`
refuses.

## 4. Withdrawal is a product state, not an error path

§5: *"Provider down ⇒ `weather_resilient` withdrawn **and disclosed**."* Three
things could happen and two are failures:

| Response | Consequence |
| --- | --- |
| Score it from normals anyway | A scenario ranked "weather resilient" on a 30-year average presented as a forecast — `REQ-EVID-003` |
| Drop it silently | The user compares three scenarios on an objective they still believe was applied — **worse**, because nothing indicates a change |
| **Withdraw and disclose** | The comparison is honestly narrower |

`ObjectiveWithdrawn` carries **no score field at all**. A nullable score is one
`None` check away from ranking as zero, and zero is a position in the ranking.
The disclosure is required: "disclosed" is the half of the rule that makes
withdrawal honest rather than merely safe.

## 5. Change inventory

**Added** — `services/integrations/src/weather/`: `forecast.py`, `alerts.py`,
`degradation.py`; `tests/integrations/test_weather_adapter.py` (26 assertions).

**Modified** — `places/licence.py` gains `METEOSWISS`.

## 6. Twelve impact categories

| # | Category | Assessment |
| --- | --- | --- |
| 1 | **Callers / call graph** | None yet. Simulation is `STEP-012` |
| 2 | **Public API / contracts** | None |
| 3 | **Database / schema** | None |
| 4 | **Events** | None. Provider health events are `.06` |
| 5 | **Configuration** | The horizon is a **parameter**, not a constant: it is a property of the provider and a different source must not inherit ten days silently |
| 6 | **Infrastructure** | None |
| 7 | **Security** | None directly; fetching goes through `.01`'s connector |
| 8 | **Privacy** | None. Weather is not personal data |
| 9 | **Accessibility** | The withdrawal disclosures are user-facing copy and are written as sentences, not codes |
| 10 | **Performance** | Pure construction; no I/O |
| 11 | **Tenancy** | None |
| 12 | **Documentation** | This record, `IMPL-039`, the regression entry, the sub-step, parent §21, `MASTER_TRACKER` |

## 7. Mandatory data-flow inspection

| Hazard | Control | Evidence |
| --- | --- | --- |
| A normal presented as a forecast | Separate types; `beyond_horizon` on the result | Seeded; killed by 2 |
| The same stored forecast valid at breakfast and invalid at lunch | The horizon is measured from `issued_at`, never wall-clock | Seeded — **survived the first attempt**, §8 |
| A point value treated as certain | `Uncertainty` is a required constructor argument | `TypeError` asserted |
| A fabricated interval | Nothing widens a point value; a value outside its own interval is refused | Seeded; killed |
| A one-run "ensemble" | At least two members | Seeded; killed |
| A three-year "normal" | Ten-year minimum | Seeded; killed |
| An objective silently dropped | No score field exists; disclosure required | Seeded; killed |
| A national weather service's severity overridden | Unrecognised levels become `UNKNOWN`, never the nearest neighbour | Seeded; killed |
| An open-ended warning read as expired | Absent expiry means open-ended | Seeded; killed |
| Open-Meteo used commercially | `LicenceRecord` refuses a non-commercial entry; MeteoSwiss is registered instead | Asserted |

## 8. What mutation testing caught that the tests did not

**One mutant survived the first pass**: measuring the horizon from `now()` instead
of `issued_at`. My test used timestamps near the real present, so the two readings
agreed and the mutant passed.

Rewritten with dates well in the past, which separates them — measured from issue
the case is nineteen days out and beyond the horizon; measured from now it is in
the past and would read as within it. The property is that **a stored forecast
gives the same answer whenever it is read**, and the original test could not see
it.

**mypy caught a vacuous assertion.** `assert AlertSeverity.UNKNOWN is not
AlertSeverity.MINOR` is a non-overlapping identity check — statically always true,
so it could never fail. That is the same pattern as `BUG-020` and `BUG-021`, this
time in new code and caught by a type checker rather than a later reader. Replaced
with the behavioural property: no provider string is ever promoted into a level a
meteorological service did not assign.

## 9. Score

| Dimension | Value | Reason |
| --- | --- | --- |
| Reach | Medium | Every weather fact in a scenario flows through these types |
| Reversibility | High | A new package; nothing imports it yet |
| Detectability | High | 26 assertions, 8 mutants, 8 killed after one strengthening |
| Security exposure | None | No I/O |
| Performance | None | Construction only |
| **Overall** | **MEDIUM** | **Confidence HIGH.** No owner approval required |

## 10. Post-change verification

| Check | Result |
| --- | --- |
| Python suite | **798 passed, 5 skipped** (up from 772) |
| Mutation | 8 seeded, 8 killed — one only after the test was strengthened |
| `pnpm verify`, `pnpm ci:local`, R1–R7 | Recorded in the regression entry |
