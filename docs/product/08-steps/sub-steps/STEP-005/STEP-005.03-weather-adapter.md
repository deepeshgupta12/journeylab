---
sub_step_id: STEP-005.03
parent_step: STEP-005
title: Weather forecast, alerts and historical normals adapter
status: VERIFIED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-DATA-002, REQ-DATA-005]
blast_radius_id: BR-042
depends_on: [STEP-005.02]
last_updated: 2026-08-14
---

# STEP-005.03 — Weather forecast, alerts and historical normals adapter

## 1. Outcome
Forecasts, alerts and historical normals are ingested **with confidence or ensemble spread**, so simulation models uncertainty rather than inventing it.

## 2. Scope and boundary
**In scope:** `services/integrations/src/weather/`; forecast issue time and validity period; alert ingestion; normals for fallback.

**Not in this sub-step:** Simulation distributions ([STEP-012](../../STEP-012-scenario-optimisation-and-simulation.md)).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-DATA-002, REQ-DATA-005 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | ✅ up to date. **NOT BLOCKED** |
| HEAD / indexed commit | `9a2db57` — matched HEAD at pre-change |
| Queries run | `cypher` over `services/integrations/src/weather` — 0 nodes, additive; `detect_changes(staged)` pre-commit |
| Unknown / low-confidence areas | **"Not all providers expose spread" is now a hard constraint, not a caution.** `Forecast` cannot be built without `Uncertainty`, so a provider that publishes only point values cannot be ingested through this type at all. That is deliberate — it makes the constraint visible at integration time rather than at simulation time. Whether MeteoSwiss publishes ensemble spread on the open endpoints is **unverified**: no live fetch has been made |
| Blast radius | **[BR-042](../../../10-logs/blast-radius/BR-042-weather-adapter.md) — MEDIUM, confidence HIGH.** The record predicted `BR-032`, which STEP-004.05 holds; corrected here |
| Approval required? | **No** — MEDIUM with high confidence |

## 5. Implementation plan
- [x] Forecast with `issued_at` **and** `valid_at`; a forecast valid before it was issued is refused
- [x] **Uncertainty is a required constructor argument** — no default, because a default is a fabricated confidence interval. Nothing widens a bare point value
- [x] Normals as a **separate type**, so a consumer written for `Forecast` fails to typecheck rather than presenting a 30-year average as tomorrow (`REQ-EVID-003`)
- [x] Alerts with the **provider's** severity; an unrecognised level is `UNKNOWN`, never the nearest neighbour
- [x] `weather_resilient` withdrawn **and disclosed** — `ObjectiveWithdrawn` has no score field, so it cannot rank as zero

## 6. Contracts and schema changes
Contracts are declared in [STEP-004](../../STEP-004-contract-first-platform-apis.md); this sub-step consumes them. Any change follows [CONTRACT_CHANGE_POLICY](../../../04-contracts/CONTRACT_CHANGE_POLICY.md).

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-DATA-005 | unit | Forecast beyond horizon falls back to normals, marked as such |
| — | resilience | Provider outage withdraws the objective rather than guessing |

## 8. Telemetry, security and accessibility
Traces carry tenant-safe correlation IDs; no PII in telemetry. Any user-facing surface is keyboard and screen-reader complete (`REQ-A11Y-001`) and completable without the map (`REQ-A11Y-003`).

## 9. Documentation to update
- [x] Sub-step completion record
- [x] [IMPLEMENTATION_LOG](../../../10-logs/IMPLEMENTATION_LOG.md) `IMPL-039` · [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) · BUG_REGISTER n/a — no bug found
- [x] `BR-042`
- [x] Parent step §21 · [MASTER_TRACKER](../../../02-delivery/MASTER_TRACKER.md)

## 10. Regression cross-check (R1–R7)
| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression suite | **PASS** | 798 Python + 63 web + 307 UI + 40 browser |
| R2 contract compatibility | **PASS** | No contract touched |
| R3 graph diff as expected | **PASS** | One package plus one licence record |
| R4 untested requirements | **PASS — improved** | REQ-EVID-003 and REQ-DATA-003 newly covered on the weather path |
| R5 orphan/unowned nodes | **PASS** | Catch-all owner |
| R6 closed-bug regression tests | **PASS** | BUG-001…025; meta-suite 72/72 |
| R7 tenant isolation | **PASS — 18/18** | Untouched |

**Overall:** **PASS**.

## 11. Rollback
Revert this sub-step's commit; prior sub-steps stay intact and `main` stays deployable. Schema work uses expand/contract, so the expand phase is reversible.

## 12. Acceptance criteria
- [ ] Forecasts carry issue time, validity and uncertainty
- [ ] Normals fallback works and is labelled
- [ ] Outage withdraws the weather objective with disclosure

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | 2026-08-14 |
| Commit SHA | *(this commit)* |
| Pushed | ✅ |
| Graph re-indexed at | post-commit |
| `main` green and deployable | ✅ |
| Bugs found | None. Two weaknesses in my own tests, both caught by tooling — see below |
| Notes / surprises | **Two distinctions carry this sub-step, and both are types rather than flags.** A normal is not a forecast: beyond the horizon a climatological average is the honest answer, and returning it through the same type is precisely how `REQ-EVID-003` gets violated. And a point forecast is not an input to a simulation — `18°C` with no spread is treated as certain, which removes the distribution `REQ-CONS-006`'s seed was meant to sample. So `Uncertainty` is a required constructor argument with no default, because a default is a fabricated confidence interval.<br><br>**Withdrawal is a product state, not an error path.** Scoring `weather_resilient` from normals ranks a scenario on an average presented as a forecast; dropping it silently is worse, because the user still believes it was applied. `ObjectiveWithdrawn` therefore has no score field at all — a nullable score is one `None` check away from ranking as zero, and zero is a position.<br><br>**Mutation testing found a test too weak to distinguish two implementations.** Measuring the horizon from `now()` instead of `issued_at` survived, because my timestamps sat near the real present and both readings agreed. The property is that a stored forecast gives the same answer whenever it is read; the original test could not see it.<br><br>**mypy found an assertion that could never fail.** `assert UNKNOWN is not MINOR` is a non-overlapping identity check — the BUG-020/021 vacuous-assertion pattern again, this time in new code and caught by a type checker rather than a later reader. Two tools, two opposite weaknesses, neither reachable by writing more cases.<br><br>**§4's caution became a constraint.** "Not all providers expose spread" is no longer a caveat: a provider publishing only point values cannot be ingested through this type, which surfaces the limitation at integration time rather than at simulation time. Whether MeteoSwiss publishes spread on its open endpoints is **unverified** — no live fetch has been made. |
