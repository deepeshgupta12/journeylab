# JourneyLab — Success Metrics and KPI Governance

| Field | Value |
| --- | --- |
| Owner | Product Lead + TPM (Deepesh Kumar Gupta) |
| Status | `DISCOVERY` — measures defined; **numeric thresholds are open** (`DEC-005`) |
| Upstream source | Blueprint §5 (objectives), §17 (analytics, KPIs and decision governance) |
| Last reviewed | 2026-08-05 |

Navigation: [Charter](PRODUCT_CHARTER.md) · [Scope](PRODUCT_SCOPE.md) · [Analytics step](../08-steps/STEP-022-analytics-feedback-and-experimentation.md) · [Release readiness](../06-quality/RELEASE_READINESS_CHECKLIST.md) · [00-START-HERE](../00-START-HERE.md)

---

## 1. Governance rules

1. **Every KPI has an owner, a formula, a data lineage and a guardrail.** A metric without a guardrail is not approved for decision-making.
2. **A guardrail is not advisory.** If a guardrail breaches, the associated optimisation stops, regardless of the primary metric's movement.
3. **No KPI may be improved by reducing evidence visibility, choice diversity or accessibility.** This is a hard constraint on the metric system itself (blueprint §17).
4. **Engagement is not a success metric.** Time-in-product and session count are diagnostic only; JourneyLab measures decision quality, not attention.
5. Thresholds must be set from Phase 0/1 baselines, not asserted in advance. Where a threshold is unset, this document says so rather than inventing one.

---

## 2. Primary KPIs

### KPI-001 — Feasible scenario success
| Field | Value |
| --- | --- |
| Definition | Share of trip briefs producing **at least three valid, materially different** scenarios |
| Formula | `trips_with_3plus_distinct_feasible_scenarios / trips_with_confirmed_brief` |
| Grain | Trip | Owner | Product |
| Lineage | `EVT-003` scenario_set.generated → warehouse scenario model |
| **Guardrail** | **Zero hidden hard-constraint violations.** A scenario counted as valid must pass `REQ-CONS-004` |
| Threshold | **Unset** — baseline from Phase 1 pilot (`DEC-005`) |
| Steps | [STEP-012](../08-steps/STEP-012-scenario-optimisation-and-simulation.md) |

### KPI-002 — Plan feasibility quality
| Field | Value |
| --- | --- |
| Definition | Hard-constraint violation rate and stale-fact rate in delivered scenarios |
| Formula | `violating_scenarios / delivered_scenarios`; `facts_past_freshness_threshold / facts_used` |
| Owner | Engineering + Data |
| **Guardrail** | Target is **zero** violations in the release evaluation corpus; any non-zero result blocks release (`REQ-CONS-004`) |
| Threshold | Violations: 0 (blocking). Stale-fact rate: **unset** |
| Steps | [STEP-010](../08-steps/STEP-010-destination-evidence-assembly.md), [STEP-012](../08-steps/STEP-012-scenario-optimisation-and-simulation.md) |

### KPI-003 — Time to decision
| Field | Value |
| --- | --- |
| Definition | Median time from confirmed brief to selected scenario |
| Formula | `median(scenario.selected.occurred_at − trip_brief.confirmed.occurred_at)` |
| Owner | Product |
| **Guardrail** | Must not be improved by reducing evidence visibility or cutting choice below useful diversity. Paired with KPI-001 and KPI-004 in every review |
| Threshold | **Unset** — requires Phase 0 baseline of current manual workflow |
| Steps | [STEP-009](../08-steps/STEP-009-trip-brief-and-structured-constraints.md) → [STEP-013](../08-steps/STEP-013-visual-comparison.md) |

### KPI-004 — Scenario trust
| Field | Value |
| --- | --- |
| Definition | Share of users rating evidence and explanation sufficient **without external correction** |
| Formula | Survey response + `user_reported_incorrect_fact` events per trip |
| Owner | Design + Data |
| **Guardrail** | Reported inaccuracies and citation failures tracked **separately** and never netted against positive ratings |
| Threshold | Citation correctness ≥ **95%** for volatile facts (blueprint §16.191 — release gate). Trust rating: unset |
| Steps | [STEP-013](../08-steps/STEP-013-visual-comparison.md) |

### KPI-005 — Plan preservation *(Phase 3)*
| Field | Value |
| --- | --- |
| Definition | Percent of unaffected itinerary retained after a live replan |
| Formula | `preserved_nodes / nodes_before_replan` from `EVT-006` |
| Owner | Product |
| **Guardrail** | Revised plan must remain feasible **and** explicitly approved; a high preservation score on an unapproved change is invalid |
| Threshold | **Unset** | Steps | [STEP-019](../08-steps/STEP-019-controlled-replanning.md) |

### KPI-006 — Booking handoff
| Field | Value |
| --- | --- |
| Definition | Qualified selected items reaching a provider and returning as user-confirmed bookings |
| Formula | `confirmed_bookings / qualified_handoffs` |
| Owner | Product + Partnerships |
| **Guardrail** | Must not imply confirmed price or availability before provider confirmation (`REQ-EVID-003`) |
| Threshold | **Unset**; depends on `ASM-012` | Steps | [STEP-016](../08-steps/STEP-016-booking-handoff.md) |

### KPI-007 — Unit economics
| Field | Value |
| --- | --- |
| Definition | Model, data-provider and compute cost per **saved feasible trip** |
| Formula | `(llm_cost + provider_cost + compute_cost) / saved_feasible_trips` |
| Owner | Engineering + Finance |
| **Guardrail** | Quality, latency and diversity thresholds remain **fixed** during cost optimisation |
| Threshold | **Unset** — target contribution margin undefined (`RISK-003`, `EV-GAP-006`) |
| Steps | [STEP-022](../08-steps/STEP-022-analytics-feedback-and-experimentation.md) |

### KPI-008 — Planning quality *(Phase 3)*
| Field | Value |
| --- | --- |
| Definition | Post-trip completed-as-planned rate, adjusted for user choice and disruption |
| **Guardrail** | **Voluntary spontaneity is not product failure** and must be excluded from the denominator |
| Threshold | **Unset** | Steps | [STEP-020](../08-steps/STEP-020-post-trip-learning.md) |

### KPI-009 — Preference intelligence *(Phase 3)*
| Field | Value |
| --- | --- |
| Definition | Ranking acceptance lift, calibration, consented profile coverage, preference-reset success |
| **Guardrail** | No lift may be obtained from opaque profiling; all learning is from explicit signals with consent (`REQ-PRIV-003`) |
| Threshold | **Unset** | Steps | [STEP-020](../08-steps/STEP-020-post-trip-learning.md) |

---

## 3. Operational and quality SLIs

These are not product KPIs but gate release. Detail in [NON_FUNCTIONAL_REQUIREMENTS](../03-architecture/NON_FUNCTIONAL_REQUIREMENTS.md) and [OBSERVABILITY_ARCHITECTURE](../03-architecture/OBSERVABILITY_ARCHITECTURE.md).

| SLI | Target | Owner | Alert |
| --- | --- | --- | --- |
| Scenario generation p95 | ≤ 45 s (7-day trip) | Backend | `ALRT-SOLVER-001` |
| Interactive read p95 | ≤ 400 ms | Backend | `ALRT-API-001` |
| Citation correctness | ≥ 95% | AI/ML | `ALRT-AI-001` |
| Hard-constraint violations | 0 | Engineering | `ALRT-SOLVER-002` |
| Evidence freshness breach rate | Unset | Data | `ALRT-DATA-001` |
| Graph refresh lag after merge | ≤ 10 min | Platform | `ALRT-KG-001` |
| Deletion completion | 100% within policy window | Privacy | `ALRT-PRIV-001` |

---

## 4. Metric anti-patterns explicitly rejected

| Rejected metric | Why rejected |
| --- | --- |
| Session duration / time in app | Rewards confusion; JourneyLab's value is faster confident decisions |
| Number of scenarios generated | Rewards volume over materially different, feasible options |
| Notification open rate as a live-companion success metric | Rewards notification volume; KPI-005 measures accepted, feasible repair instead |
| AI usage rate | Rewards inserting the model where deterministic logic is correct (violates `CON-004`) |
| Aggregate NPS as a trust proxy | Hides citation failures; KPI-004 tracks reported inaccuracy separately |

---

## 5. Decision governance

- KPI review cadence, decision forum and escalation path: **undecided** (`DEC-006`).
- A negative result is recorded in [DECISION_LOG](../02-delivery/DECISION_LOG.md) as portfolio evidence, never discarded (portfolio standard §7.38).
- Stop conditions tied to metrics live in [RISK_REGISTER](../02-delivery/RISK_REGISTER.md): `RISK-002` (comparison not preferred), `RISK-003` (unit economics), `RISK-004` (constraint violations).
