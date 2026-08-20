---
step_id: STEP-006
title: Canonical data model and event backbone
status: IN_PROGRESS
release: Phase 1
owners: ["Deepesh Kumar Gupta"]
dependencies: [STEP-005]
requirement_ids: [REQ-DATA-007, REQ-DATA-008, REQ-DATA-009, REQ-DATA-010, REQ-SEC-001]
api_ids: []
event_ids: [EVT-001, EVT-002, EVT-003, EVT-004, EVT-005, EVT-006, EVT-007, EVT-008]
data_ids: [DATA-001, DATA-002, DATA-003, DATA-004, DATA-005, DATA-006, DATA-007, DATA-008, DATA-009, DATA-010, DATA-011, DATA-012, DATA-013, DATA-014, DATA-015, DATA-016]
ai_ids: []
knowledge_graph_check: REQUIRED
last_updated: 2026-08-05
---

# STEP-006 — Canonical data model and event backbone

> Status is authoritative in [MASTER_TRACKER](../02-delivery/MASTER_TRACKER.md).

## 1. Outcome
Inputs are normalized into versioned canonical entities retaining source, observed time, effective time and schema version. Domain events publish through a transactional outbox and can rebuild read models.

## 2. Why this step exists
Eight steps depend on canonical entities. The temporal model (observed vs. effective vs. recorded time) must be right here — a system that confuses "when we learned it" with "when it is true" produces confidently wrong itineraries, and that error is nearly invisible in testing.

## 3. Scope
Core transactional schema with constraints, indexes and row-level security; domain entities and invariants independent of transport; repository interfaces and unit-of-work boundaries; provider→canonical normalizers; transactional outbox with idempotency and replay; executable data-quality expectations.

## 4. Explicit exclusions
Provider fetching is [STEP-005](STEP-005-source-integrations-and-ingestion.md); evidence-pack assembly is [STEP-010](STEP-010-destination-evidence-assembly.md); warehouse modelling is [STEP-022](STEP-022-analytics-feedback-and-experimentation.md).

## 5. Actors, permissions and data access
| Actor | Permission | Data accessed | Sensitivity |
| --- | --- | --- | --- |
| Domain services | Repository access within tenant context | All canonical entities | PII + licensed |
| Outbox publisher | Read outbox, write offsets | Event envelopes (IDs only) | Internal |

## 6. Preconditions and dependencies
[STEP-005](STEP-005-source-integrations-and-ingestion.md) exit — normalizers require real provider payload shapes. **`DEC-009`** (event backbone) affects publisher implementation.

## 7. Inputs and source systems
Provider payloads from `STEP-005`; [DATA_CONTRACTS](../04-contracts/DATA_CONTRACTS.md); [EVENT_CONTRACTS](../04-contracts/EVENT_CONTRACTS.md).

## 8. Detailed normal workflow
1. Normalizer maps a validated provider payload to canonical entity shapes.
2. Repository writes the entity **and** its outbox row in one transaction.
3. Entity retains source, `observed_at`, effective window, `recorded_at` and schema version.
4. Outbox publisher relays the event with at-least-once delivery.
5. Consumers process idempotently by `event_id`.
6. Data-quality expectations run against the batch.
7. Read models are projected and remain rebuildable from the log.

## 9. Alternate, partial and failure workflows
| Condition | Behavior | User-visible result | Requirement |
| --- | --- | --- | --- |
| Transaction fails | Entity and event both roll back — **no phantom events** | Retry | REQ-DATA-008 |
| Publisher down | Outbox accumulates; alert on lag; replay on recovery | Delayed downstream | REQ-NFR-005 |
| Duplicate delivery | Consumer idempotency prevents duplicate effect | None | REQ-DATA-009 |
| Schema version mismatch | Reject, never coerce | Ingestion halted | REQ-DATA-007 |
| Quality expectation fails | Batch quarantined, alert raised | Facts excluded from planning | Data quality |
| Read model corrupt | Rebuild from the event log | Temporary staleness | REQ-DATA-010 |

## 10. State machine and lifecycle transitions
Entity: `draft → active → superseded → tombstoned → deleted`. Outbox row: `pending → published → acknowledged → archived`; `failed → dead-letter` after the retry cap.

## 11. Frontend implementation
`NOT_APPLICABLE`. Reason: this step delivers no user-facing surface. Read models it produces are consumed by later UI steps.

## 12. Backend implementation
`db/migrations/010_domain.sql`, `apps/api/src/domain/models.py`, `apps/api/src/domain/repositories.py`, `services/ingestion/src/normalizers/`, `services/events/src/outbox.py`, `data/quality/domain_expectations.yml` (all `PROPOSED`).

## 13. API, event and integration contracts
Implements delivery for all eight events (`EVT-001` … `EVT-008`) defined in `STEP-004`. No new public API.

## 14. Data model, migration and retention effects
Creates all sixteen entities (`DATA-001` … `DATA-016`) with constraints, indexes and RLS. **Immutability is enforced at the schema level** for `TripBrief`, `EvidencePack` and `ScenarioVersion` — an in-place update must be impossible, not merely discouraged, because reproducibility depends on it.

## 15. AI, LLM, RAG, ML and data-science implementation
`NOT_APPLICABLE`. Reason: canonical modelling and event delivery are deterministic infrastructure. Introducing model inference into normalization would make the canonical layer non-reproducible and break `REQ-CONS-006`.

## 16. Security, privacy, accessibility and responsible-AI controls
`SC-TEN-01` tenant ID on every row, event and cache key. RLS on all tenant-scoped tables. Event payloads carry IDs and classifications only — **never trip content, evidence prose or personal data**, which is what makes deletion tractable later. Booking references are written to a segregated store.

## 17. Observability, analytics and KPIs
Outbox lag, DLQ depth, event throughput, quality-expectation pass rate, entity counts by source. Alert `ALRT-QUEUE-001`; runbook `RB-QUEUE-001`.

## 18. Files and modules expected to change
All `PROPOSED` — see §12.

## 19. Knowledge-graph pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | `BLOCKED` for application code — static fallback |
| Queries to run | KG-Q-006; migrations become `Table`/`Migration` nodes |
| Expected impact | Schema changes here affect every service that reads these tables |

## 20. Blast-radius assessment
Eight-step fan-out and a schema foundation. Migration errors are **low reversibility** — a destructive migration cannot be undone by reverting code. Every schema sub-step requires expand/contract and owner approval.

## 21. Implementation task checklist — sub-steps
| Sub-step | Outcome |
| --- | --- |
| STEP-006.01 | Core schema, constraints, indexes, RLS | — ✅ **VERIFIED** 2026-08-18 (BR-050, IMPL-049; raises RISK-017)
| STEP-006.02 | Temporal model: observed/effective/recorded across all fact tables | — ✅ **VERIFIED** 2026-08-20 (BR-051, IMPL-050)
| STEP-006.03 | Domain entities and invariants |
| STEP-006.04 | Repositories and unit-of-work boundaries |
| STEP-006.05 | Provider→canonical normalizers |
| STEP-006.06 | Transactional outbox publisher with idempotency |
| STEP-006.07 | Consumer idempotency and replay |
| STEP-006.08 | Data-quality expectations and quarantine |
| STEP-006.09 | Read-model projection and rebuild proof |

## 22. Test and evaluation plan
`TST-DATA-007` … `TST-DATA-010`, `TST-SEC-001`. **Property-based tests over the temporal model** — including DST transitions and seasonal effective windows — are mandatory, since this is the defect class most likely to reach production unnoticed.

## 23. Deployment, feature flag and migration plan
Expand/migrate/contract. Outbox publisher deploys before producers so no event is written without a relay. `DEC-009` determines whether the publisher targets a managed queue or Kafka; the AsyncAPI contract is identical either way.

## 24. Rollback, compensation and recovery plan
Expand-phase migrations revert cleanly. **Contract-phase migrations do not** — they run only after the rollout window closes and the code graph confirms no reader remains. Read models rebuild from the log; the log itself is the recovery boundary.

## 25. Acceptance criteria
- [ ] Canonical records retain source, observed time, effective time, schema version (`REQ-DATA-007`)
- [ ] Events publish via transactional outbox in the same transaction (`REQ-DATA-008`)
- [ ] Replaying an event produces no duplicate effect (`REQ-DATA-009`)
- [ ] Read models rebuild from the event log (`REQ-DATA-010`)
- [ ] Every row, event and cache key carries a tenant ID (`REQ-SEC-001`)
- [ ] Immutable entities cannot be updated in place

## 26. Evidence required for completion
Migration rehearsal timing; outbox atomicity test; replay test output; read-model rebuild proof; temporal property-test results.

## 27. Open questions, risks and decisions
`DEC-009` event backbone. Retention defaults per entity need the privacy owner's approval. Evidence-pack storage growth needs a lifecycle policy that does not break the reproducibility window.

## 28. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Sub-steps completed | 0 of 9 |
| Regression result | — |
| Verified by | — |
