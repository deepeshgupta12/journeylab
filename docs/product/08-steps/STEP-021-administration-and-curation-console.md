---
step_id: STEP-021
title: Administration and curation console
status: DISCOVERY
release: Phase 1
owners: []
dependencies: [STEP-006, STEP-010]
requirement_ids: [REQ-ADMIN-001, REQ-ADMIN-002, REQ-ADMIN-003, REQ-ADMIN-004, REQ-ADMIN-005, REQ-PLAT-012]
api_ids: [API-016, API-017]
event_ids: [EVT-008]
data_ids: [DATA-007]
ai_ids: []
knowledge_graph_check: REQUIRED
last_updated: 2026-08-05
---

# STEP-021 — Administration and curation console

> Status is authoritative in [MASTER_TRACKER](../02-delivery/MASTER_TRACKER.md).

## 1. Outcome
Curators correct destination facts with effective dates, evidence and an audit trail — seeing which scenarios an override will invalidate **before** applying it — and operators control providers, models and rollout without a deployment.

## 2. Why this step exists
Destination data will be wrong sometimes. Without a governed correction path, the alternatives are editing production data by hand or shipping code for every bad opening time. Four-eyes approval exists because a single mistaken override can invalidate every trip in a region.

## 3. Scope
Coverage and provider health dashboards; fact correction with effective periods and four-eyes approval for high impact; override impact preview; model/prompt/solver/feature rollout controls; abuse, privacy, support and incident case management.

## 4. Explicit exclusions
Deletion execution is [STEP-025](STEP-025-support-deletion-and-data-lifecycle.md); dashboards and alerts are [STEP-024](STEP-024-observability-sre-and-support-readiness.md).

## 5. Actors, permissions and data access
| Actor | Permission | Data accessed | Sensitivity |
| --- | --- | --- | --- |
| PER-004 curator | Override facts (audited); **cannot approve own high-impact override** | Destination facts only — **no traveler PII** | Licensed |
| PER-005 ops admin | Provider disable, model rollback, flags (audited) | Provider metadata; no raw PII by default | — |

## 6. Preconditions and dependencies
[STEP-006](STEP-006-canonical-data-model-and-event-backbone.md) canonical facts; [STEP-010](STEP-010-destination-evidence-assembly.md) evidence packs.

## 7. Inputs and source systems
Corrected fact values, effective periods, evidence, reasons; provider health (`EVT-008`); flag configuration.

## 8. Detailed normal workflow
1. Curator identifies an incorrect fact from an alert or a user report.
2. Curator proposes an override with value, effective period, evidence and reason.
3. System computes and displays the **impact preview** — trips and scenarios affected.
4. If high impact, a **second curator** approves; the proposer cannot approve.
5. Override is applied with a full audit record.
6. Affected scenarios are flagged for regeneration.

## 9. Alternate, partial and failure workflows
| Condition | Behavior | User-visible result | Requirement |
| --- | --- | --- | --- |
| High-impact override without a second approver | **Blocked** | Pending approval | REQ-ADMIN-002 |
| Impact preview unavailable (graph down) | Override blocked for high-impact; low-impact proceeds with a warning | Explicit degradation | REQ-ADMIN-003 |
| Override conflicts with a fresh provider fact | Conflict shown; curator chooses with hierarchy recorded | Deliberate decision | REQ-EVID-002 |
| Provider disabled | Coverage updated; new trips refused for affected regions | Honest refusal | REQ-TRIP-002 |
| Support requests broader access | **No operation exists to grant it** | Request cannot be fulfilled by design | REQ-ADMIN-005 |

## 10. State machine and lifecycle transitions
Override: `proposed → previewed → (approved | rejected) → applied → (expired at effective_to)`. Provider: `enabled ↔ disabled`, audited both ways.

## 11. Frontend implementation
`apps/web/src/app/admin/{destinations,providers,support,flags}/` (`PROPOSED`) — coverage dashboard, override editor with preview, four-eyes approval queue, provider health, diagnostic timeline, flag controls. **Held to the same WCAG 2.2 AA bar as consumer surfaces.**

## 12. Backend implementation
`services/evidence/` override handling, `services/support/src/diagnostics.py`, flag service (`PROPOSED`).

## 13. API, event and integration contracts
`API-016` override with four-eyes enforcement; `API-017` coverage. Consumes `EVT-008`.

## 14. Data model, migration and retention effects
Writes override records against `DATA-007` with effective periods, evidence, actor and approver. Audit records are immutable and retained per policy.

## 15. AI, LLM, RAG, ML and data-science implementation
`NOT_APPLICABLE` for the override path itself. Reason: fact correction is a human judgement with accountability; a model-suggested correction applied without review would reintroduce exactly the unaccountable error the console exists to fix. The **impact preview** is a deterministic graph query, not a prediction.

## 16. Security, privacy, accessibility and responsible-AI controls
`SC-GOV-02` four-eyes; `SC-AUTHZ-02` support scoping; `SC-AUDIT-01` immutable audit. **Curators cannot access traveler PII** by any operation. Admin surfaces meet the full accessibility bar.

## 17. Observability, analytics and KPIs
Override volume and approval latency, provider disable frequency, override-triggered regeneration count, support bundle usage, flag change audit. Alert `ALRT-DATA-001`.

## 18. Files and modules expected to change
All `PROPOSED` — see §11, §12.

## 19. Knowledge-graph pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | `BLOCKED` — static fallback |
| Queries to run | KG-Q-006; **KG-Q-005** (override blast radius) is the feature itself |
| Expected impact | The impact preview depends directly on the domain graph |

## 20. Blast-radius assessment
An override touches every scenario referencing the fact. **This is the one product feature whose blast radius is itself a user-facing feature** — which is why the preview is a requirement rather than a nicety.

## 21. Implementation task checklist — sub-steps
| Sub-step | Outcome |
| --- | --- |
| STEP-021.01 | Coverage and provider health dashboards |
| STEP-021.02 | Override proposal with effective period and evidence |
| STEP-021.03 | Impact preview (`KG-Q-005`) |
| STEP-021.04 | Four-eyes approval workflow |
| STEP-021.05 | Audit trail and regeneration flagging |
| STEP-021.06 | Provider disable and model rollback controls |
| STEP-021.07 | Feature/cohort flag controls |
| STEP-021.08 | Tenant-safe support diagnostic timeline |

## 22. Test and evaluation plan
`TST-ADMIN-001` … `TST-ADMIN-005`, `TST-PLAT-012`. A negative test must prove a curator cannot approve their own high-impact override, and that no operation exposes traveler PII to a curator.

## 23. Deployment, feature flag and migration plan
Admin console behind a role gate. Override capability can be disabled independently if abused.

## 24. Rollback, compensation and recovery plan
Overrides carry effective periods and can be expired or reversed, with the reversal itself audited. Provider and model controls are the rollback mechanism for other steps.

## 25. Acceptance criteria
- [ ] Every override records reason, effective period, evidence and actor (`REQ-ADMIN-001`)
- [ ] High-impact overrides require a **different** second approver (`REQ-ADMIN-002`)
- [ ] Impact preview lists affected trips and scenarios before applying (`REQ-ADMIN-003`)
- [ ] Coverage and provider health dashboards exist (`REQ-ADMIN-004`)
- [ ] Support can reconstruct one trip without unrestricted tenant access (`REQ-ADMIN-005`)
- [ ] Flags change model, provider and feature behavior without deployment (`REQ-PLAT-012`)

## 26. Evidence required for completion
Four-eyes negative test; impact preview accuracy check; curator PII isolation test; support scoping test; audit record sample.

## 27. Open questions, risks and decisions
What constitutes "high impact" needs a numeric threshold (affected trips or scenarios) — currently undefined. Curator staffing model is unknown; four-eyes requires at least two curators to exist.

## 28. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Sub-steps completed | 0 of 8 |
| Regression result | — |
| Verified by | — |
</content>
