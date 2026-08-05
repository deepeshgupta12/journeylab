---
step_id: STEP-022
title: Analytics, feedback and experimentation
status: DEFERRED
release: Phase 2
owners: []
dependencies: [STEP-006, STEP-013]
requirement_ids: [REQ-OBS-005, REQ-OBS-006, REQ-PRIV-004]
api_ids: []
event_ids: []
data_ids: [DATA-015]
ai_ids: []
knowledge_graph_check: REQUIRED
last_updated: 2026-08-05
---

# STEP-022 — Analytics, feedback and experimentation

> Status is authoritative in [MASTER_TRACKER](../02-delivery/MASTER_TRACKER.md). **`DEFERRED` to Phase 2.**

## 1. Outcome
Product usage and real outcomes drive prioritisation and model learning. Every KPI has an owner, formula, lineage and guardrail, and no experiment surfaces results without verified exposure and outcome data.

## 2. Why this step exists
The blueprint requires causal evaluation of whether comparison and replanning improve **outcomes, not merely engagement**. Without exposure integrity, an experiment produces a confident number that means nothing.

## 3. Scope
Typed product-event taxonomy with privacy tiers; server-side validation, deduplication and enrichment; warehouse models for activation, funnel, quality, retention, cost and outcomes; deterministic cohort assignment with exposure logging; frequentist/Bayesian/causal analysis; role-aware analytics views.

## 4. Explicit exclusions
Operational telemetry is [STEP-024](STEP-024-observability-sre-and-support-readiness.md); preference learning is [STEP-020](STEP-020-post-trip-learning.md).

## 5. Actors, permissions and data access
| Actor | Permission | Data accessed | Sensitivity |
| --- | --- | --- | --- |
| PER-005 ops admin | Role-aware analytics views | Aggregates | Internal |
| Product/Data | Warehouse query | De-identified aggregates | Internal |
| Analytics collector | Ingest typed events | Event payloads | Internal |

## 6. Preconditions and dependencies
[STEP-006](STEP-006-canonical-data-model-and-event-backbone.md) event backbone; [STEP-013](STEP-013-visual-comparison.md) real usage surfaces.

## 7. Inputs and source systems
Typed frontend events, domain events, cost traces, feedback records.

## 8. Detailed normal workflow
1. Frontend emits typed events carrying a privacy tier.
2. Collector validates against the taxonomy, deduplicates and enriches server-side.
3. Warehouse models compute activation, funnel, quality, retention, cost and outcome metrics.
4. Experiments assign cohorts deterministically and log exposure.
5. Analysis runs only where exposure and outcome data are both verified.
6. Results are presented with guardrails adjacent to primary metrics.

## 9. Alternate, partial and failure workflows
| Condition | Behavior | User-visible result | Requirement |
| --- | --- | --- | --- |
| Untyped event received | **Rejected server-side** | Not recorded | REQ-OBS-005 |
| Exposure data missing | **Results withheld** | Experiment inconclusive, stated as such | REQ-OBS-006 |
| Sensitive class in payload | Rejected and alerted | Not recorded | REQ-PRIV-004 |
| Duplicate events | Deduplicated | Accurate counts | REQ-DATA-009 |
| Guardrail breached | Optimisation stops regardless of primary metric | Explicit halt | Metric governance |

## 10. State machine and lifecycle transitions
Experiment: `designed → assigned → exposed → collecting → (analysable | inconclusive) → decided`. An experiment cannot skip `exposed`.

## 11. Frontend implementation
`packages/analytics/src/events.ts` typed taxonomy; `apps/web/src/app/analytics/` role-aware views (`PROPOSED`). Charts carry table equivalents.

## 12. Backend implementation
`services/analytics/src/collector.py`, `services/experiments/src/{assignment,analysis}.py`, `warehouse/models/` (`PROPOSED`).

## 13. API, event and integration contracts
Internal collector endpoint; consumes all domain events. No public API.

## 14. Data model, migration and retention effects
Reads `DATA-015` Feedback. Warehouse aggregates must meet **de-identification thresholds and retain no free-form sensitive text by default**. Deletion must reach warehouse rows or trigger re-aggregation.

## 15. AI, LLM, RAG, ML and data-science implementation
Statistical, not generative. **Causal claims require randomized or quasi-experimental designs with stated identification assumptions.** An observed correlation between comparison usage and satisfaction is never reported as an effect. Engagement improvement is explicitly not an outcome improvement.

## 16. Security, privacy, accessibility and responsible-AI controls
`SC-SENS-02` sensitive classes never used for advertising or unrelated personalization, and never present in analytics payloads. Privacy tiers enforced at ingestion. Analytics views are role-aware and accessible.

## 17. Observability, analytics and KPIs
Event validation rejection rate, exposure coverage, experiment power, KPI freshness, cost attribution accuracy. Feeds `KPI-001` … `KPI-009`.

## 18. Files and modules expected to change
All `PROPOSED` — see §11, §12.

## 19. Knowledge-graph pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | `BLOCKED` — static fallback |
| Queries to run | KG-Q-006; KG-Q-009 (lineage from metric to source) |
| Expected impact | Warehouse models depend on event schemas — a schema change breaks metrics silently |

## 20. Blast-radius assessment
Low user-facing severity, **high decision severity**: a broken metric leads to wrong product decisions that are discovered months later. Lineage and freshness checks are the guard.

## 21. Implementation task checklist — sub-steps
| Sub-step | Outcome |
| --- | --- |
| STEP-022.01 | Typed event taxonomy with privacy tiers |
| STEP-022.02 | Server-side validation, dedup, enrichment |
| STEP-022.03 | Warehouse models with documented lineage |
| STEP-022.04 | Deterministic cohort assignment |
| STEP-022.05 | Exposure logging and integrity gate |
| STEP-022.06 | Analysis with stated identification assumptions |
| STEP-022.07 | Role-aware analytics views with guardrails displayed |

## 22. Test and evaluation plan
`TST-OBS-005`, `TST-OBS-006`, `TST-PRIV-004`. A negative test must prove results are withheld without exposure data, and that a sensitive class in a payload is rejected.

## 23. Deployment, feature flag and migration plan
Phase 2 flag. Event schema changes follow the contract change policy — consumers include warehouse models.

## 24. Rollback, compensation and recovery plan
Warehouse models rebuild from the event log. A bad metric definition is corrected and recomputed; **decisions already made on it are re-examined**, which is why definition changes are logged.

## 25. Acceptance criteria
- [ ] Events are typed with privacy tiers; untyped events rejected (`REQ-OBS-005`)
- [ ] Experiments cannot surface results without verified exposure and outcome data (`REQ-OBS-006`)
- [ ] Sensitive classes never appear in analytics payloads (`REQ-PRIV-004`)
- [ ] Every KPI has an owner, formula, lineage and guardrail
- [ ] Guardrails are displayed adjacent to their primary metric

## 26. Evidence required for completion
Rejection test results; exposure integrity test; KPI lineage documentation; de-identification threshold analysis.

## 27. Open questions, risks and decisions
`DEC-005` thresholds and `DEC-006` review cadence. Whether the warehouse is a separate system or PostgreSQL read models at MVP scale is undecided.

## 28. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Sub-steps completed | 0 of 7 |
| Regression result | — |
| Verified by | — |
