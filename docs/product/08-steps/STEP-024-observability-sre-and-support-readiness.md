---
step_id: STEP-024
title: Observability, SRE and support readiness
status: DISCOVERY
release: Phase 1
owners: ["Deepesh Kumar Gupta"]
dependencies: [STEP-006, STEP-027]
requirement_ids: [REQ-OBS-001, REQ-OBS-002, REQ-OBS-003, REQ-OBS-004, REQ-AI-006]
api_ids: []
event_ids: []
data_ids: []
ai_ids: []
knowledge_graph_check: REQUIRED
last_updated: 2026-08-05
---

# STEP-024 — Observability, SRE and support readiness

> Status is authoritative in [MASTER_TRACKER](../02-delivery/MASTER_TRACKER.md).

## 1. Outcome
On-call can identify tenant impact and restore or degrade safely using rehearsed runbooks and current dashboards — including for **business-quality failures that leave every uptime metric green**.

## 2. Why this step exists
This product can fail while appearing healthy: uncited facts, stale evidence served as current, hard-constraint regressions. Conventional infrastructure monitoring would miss all three.

## 3. Scope
OpenTelemetry initialization and common attributes; dashboards for API, queue, data, model, retrieval, workflow and business SLIs; error-budget, freshness, saturation, cost and quality alerts; runbooks; tenant-safe diagnostics; fault injection and DR exercises.

## 4. Explicit exclusions
Product analytics is [STEP-022](STEP-022-analytics-feedback-and-experimentation.md); CI gates are [STEP-027](STEP-027-release-automation-and-controlled-rollout.md).

## 5. Actors, permissions and data access
| Actor | Permission | Data accessed | Sensitivity |
| --- | --- | --- | --- |
| PER-005 ops admin | Dashboards, alerts, diagnostics | **IDs and versions, not raw payloads** | Internal |
| SRE | Full operational access, audited | Infrastructure | Internal |
| Support | Single-trip diagnostic bundle | Tenant-safe timeline | Internal |

## 6. Preconditions and dependencies
[STEP-006](STEP-006-canonical-data-model-and-event-backbone.md) for event telemetry; [STEP-027](STEP-027-release-automation-and-controlled-rollout.md) for deployable units to observe.

## 7. Inputs and source systems
OTel semantic conventions 1.43 (**GenAI conventions version-pinned**), service instrumentation, SLO definitions.

## 8. Detailed normal workflow
1. Every service initialises OTel with common attributes and tenant-safe correlation IDs.
2. Traces span request → domain → worker → provider/model → result.
3. Metrics feed dashboards per [OBSERVABILITY_ARCHITECTURE](../03-architecture/OBSERVABILITY_ARCHITECTURE.md) §4.
4. Alerts fire with a runbook link and a named owner.
5. Support generates tenant-safe diagnostic bundles carrying IDs and versions only.
6. Fault injection and DR exercises validate the whole chain.

## 9. Alternate, partial and failure workflows
| Condition | Behavior | User-visible result | Requirement |
| --- | --- | --- | --- |
| Telemetry backend down | Application continues; telemetry buffered then dropped | No user impact | REQ-OBS-001 |
| Redaction failure | **Emission blocked rather than leaking** | Reduced observability | SC-REDACT-01 |
| Alert without a runbook | **CI/release gate fails** | Not shippable | REQ-OBS-004 |
| Support needs raw content | Requires time-boxed, audited elevation with justification | Deliberate friction | REQ-ADMIN-005 |
| Business SLI breach with green infra | SEV1/SEV2 raised on the quality signal | Correct prioritisation | REQ-OBS-003 |

## 10. State machine and lifecycle transitions
Alert: `firing → acknowledged → mitigating → resolved → retrospective`. Runbook: `written → rehearsed → updated by rehearsal`.

## 11. Frontend implementation
Frontend telemetry: Core Web Vitals, error boundaries, **accessibility failure counters**, user-reported incorrect facts. No sensitive data in payloads.

## 12. Backend implementation
`packages/observability/src/`, `observability/dashboards/`, `observability/alerts/`, `runbooks/`, `services/support/src/diagnostics.py`, `tests/resilience/` (all `PROPOSED`).

## 13. API, event and integration contracts
No public API. Consumes all domain events for business SLIs.

## 14. Data model, migration and retention effects
Telemetry retention per signal class. **Traces carry IDs and versions, never trip content, prompts, evidence prose or location.**

## 15. AI, LLM, RAG, ML and data-science implementation
Implements `REQ-AI-006` AI tracing: prompt version, model version, retrieval configuration, source pack, tool results, cost and latency in one trace with sensitive fields redacted. Feeds the MLflow production-trace-to-regression-dataset loop used by [AI_ML_EVALUATION](../06-quality/AI_ML_EVALUATION.md).

## 16. Security, privacy, accessibility and responsible-AI controls
`SC-REDACT-01` redaction at emission; `SC-AUDIT-01` audit separate from application logs; `SC-AUTHZ-02` support scoping. Dashboards are internal surfaces held to the same accessibility bar.

## 17. Observability, analytics and KPIs
Meta-observability: alert precision (false-positive rate), mean time to acknowledge, runbook rehearsal currency, dashboard freshness. Business SLIs per [SUCCESS_METRICS](../01-product/SUCCESS_METRICS.md) §3.

## 18. Files and modules expected to change
All `PROPOSED` — see §12.

## 19. Knowledge-graph pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | `BLOCKED` — static fallback |
| Queries to run | KG-Q-008 (alerts without runbooks; unowned services) |
| Expected impact | Runtime telemetry joins back into the graph as `OBSERVED_BY` edges |

## 20. Blast-radius assessment
Low direct user impact; **high incident-response impact**. Missing observability is invisible until an incident, at which point it is too late to add.

## 21. Implementation task checklist — sub-steps
| Sub-step | Outcome |
| --- | --- |
| STEP-024.01 | OTel initialization, common attributes, tenant-safe correlation |
| STEP-024.02 | End-to-end trip correlation trace |
| STEP-024.03 | Infrastructure and queue dashboards |
| STEP-024.04 | **Business-quality dashboards** (citations, constraints, freshness) |
| STEP-024.05 | AI cost/latency/quality telemetry |
| STEP-024.06 | Alerts with runbook links and owners |
| STEP-024.07 | Runbook authoring and first rehearsal |
| STEP-024.08 | Tenant-safe support diagnostics |
| STEP-024.09 | Fault injection and DR exercises |

## 22. Test and evaluation plan
`TST-OBS-001` … `TST-OBS-004`, `TST-AI-006`. Synthetic probes must prove business-quality alerts actually fire. Every runbook is rehearsed before GA — an unrehearsed runbook does not count.

## 23. Deployment, feature flag and migration plan
Telemetry deploys with each service. Sampling rates are configurable without deployment.

## 24. Rollback, compensation and recovery plan
Telemetry changes are low risk and independently revertible. Alert threshold changes are versioned so a noisy change can be reverted quickly.

## 25. Acceptance criteria
- [ ] Every request and job emits traces with tenant-safe correlation IDs (`REQ-OBS-001`)
- [ ] A trip is traceable end to end from brief to rendered result (`REQ-OBS-002`)
- [ ] Business-quality alerts exist for citation failure, hard-constraint regression and stale coverage (`REQ-OBS-003`)
- [ ] Every alert references a runbook with a named owner (`REQ-OBS-004`)
- [ ] AI traces carry prompt/model/retrieval/cost/latency with redaction (`REQ-AI-006`)
- [ ] Support reconstructs one trip without raw sensitive payloads

## 26. Evidence required for completion
Synthetic probe results per business alert; end-to-end trace demonstration; runbook rehearsal records; diagnostic bundle sample showing redaction; DR exercise record.

## 27. Open questions, risks and decisions
On-call rotation and support hours are **undecided** and required before GA. Telemetry backend not selected (`DEC-007`). GenAI OTel conventions must be version-pinned because they continue to evolve.

## 28. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Sub-steps completed | 0 of 9 |
| Regression result | — |
| Verified by | — |
