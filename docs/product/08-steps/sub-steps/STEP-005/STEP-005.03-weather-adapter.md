---
sub_step_id: STEP-005.03
parent_step: STEP-005
title: Weather forecast, alerts and historical normals adapter
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-DATA-002, REQ-DATA-005]
blast_radius_id: BR-032
depends_on: [STEP-005.02]
last_updated: 2026-08-05
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
| Graph status | **BLOCKED — static fallback** (no application symbols indexed yet) |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | KG-Q-015 `detect_changes()`; KG-Q-006 once symbols exist |
| Unknown / low-confidence areas | Not all providers expose spread — may constrain provider choice |
| Blast radius | BR-032 — scored at execution; **confidence capped while the graph is BLOCKED** |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] Forecast ingestion with issue time and validity period
- [ ] **Confidence or ensemble spread required** — a bare point forecast is insufficient for AI-007
- [ ] Historical normals as a documented fallback when forecast horizon is exceeded
- [ ] Weather alerts with severity
- [ ] Degradation: provider down ⇒ `weather_resilient` objective withdrawn and disclosed

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
- [ ] Sub-step completion record
- [ ] [IMPLEMENTATION_LOG](../../../10-logs/IMPLEMENTATION_LOG.md) · [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) · [BUG_REGISTER](../../../10-logs/BUG_REGISTER.md) if applicable
- [ ] `BR-032` post-change section
- [ ] Parent step §21 · [MASTER_TRACKER](../../../02-delivery/MASTER_TRACKER.md)

## 10. Regression cross-check (R1–R7)
| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression suite | | All prior sub-steps + every `VERIFIED` step |
| R2 contract compatibility | | No unintended breaking diff |
| R3 graph diff as expected | | `detect_changes()` |
| R4 untested requirements | | Not increased |
| R5 orphan/unowned nodes | | Not increased |
| R6 closed-bug regression tests | | All passing |
| R7 tenant isolation | | **Pass — non-negotiable** |

**Overall:** PASS / FAIL — a FAIL means this sub-step is not done.

## 11. Rollback
Revert this sub-step's commit; prior sub-steps stay intact and `main` stays deployable. Schema work uses expand/contract, so the expand phase is reversible.

## 12. Acceptance criteria
- [ ] Forecasts carry issue time, validity and uncertainty
- [ ] Normals fallback works and is labelled
- [ ] Outage withdraws the weather objective with disclosure

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Commit SHA | — |
| Pushed | — |
| Graph re-indexed at | — |
| `main` green and deployable | — |
| Bugs found | — |
| Notes / surprises | Without ensemble spread the Monte Carlo model in STEP-012 would fabricate a distribution — better to withdraw the objective than to simulate confidence we do not have. |
