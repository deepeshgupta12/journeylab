# JourneyLab — Event Contracts

| Field | Value |
| --- | --- |
| Owner | Backend + Data Architect (Deepesh Kumar Gupta) |
| Status | **All events `PROPOSED`** — no AsyncAPI file exists |
| Upstream source | Blueprint §11 (domain events), §9 (workflow and outbox) |
| Last reviewed | 2026-08-05 |

Navigation: [API contracts](API_CONTRACTS.md) · [Data contracts](DATA_CONTRACTS.md) · [Backend](../03-architecture/BACKEND_ARCHITECTURE.md) · [00-START-HERE](../00-START-HERE.md)

---

## 1. Envelope and conventions

Every event shares one envelope:

```json
{
  "event_id": "uuid",
  "event_type": "journey.scenario_set.generated.v1",
  "occurred_at": "RFC3339",
  "recorded_at": "RFC3339",
  "tenant_id": "org_…",
  "correlation_id": "…",
  "causation_id": "…",
  "actor": { "type": "user|service", "id": "…" },
  "schema_version": 1,
  "payload": {}
}
```

| Convention | Rule |
| --- | --- |
| Naming | `journey.<aggregate>.<past-tense-fact>.v<major>` |
| Versioning | Major version in the name; additive changes bump `schema_version` only |
| Publication | **Transactional outbox** — written in the same transaction as the state change |
| Consumers | Idempotent by `event_id`; replay must not duplicate effects |
| Ordering | Partitioned by `trip_id`; per-trip ordering guaranteed, cross-trip not |
| Payload contents | IDs, versions and classifications. **Never trip content, evidence prose, personal data or precise location** |
| Retention | Defined per event below |
| Dead letter | After capped exponential backoff; DLQ depth alerted |
| Discovery | AsyncAPI document beside the code (`contracts/asyncapi.yaml`) |

**The payload rule is a privacy control, not a size optimisation.** Events fan out to warehouses, graphs and consumers with varying retention; carrying personal data in them would make deletion (`REQ-PRIV-006`) effectively impossible.

---

## 2. Event register

### EVT-001 — `journey.trip_brief.confirmed.v1`
| Field | Value |
| --- | --- |
| Producer | `trip` module · **Trigger:** user confirms the structured brief (API-003) |
| Consumers | `evidence` (start pack build), `knowledge` (domain graph), `analytics` |
| Payload | `trip_id`, `brief_version`, constraint summary **counts by class** (hard/soft/inferred/unresolved), actor, occurred_at |
| Delivery | Outbox, at-least-once · **Order key** `trip_id` |
| Idempotency | By `event_id`; re-delivery must not start a second pack build |
| Privacy class | Internal — counts only, no constraint values |
| Retention | 90 days operational; aggregated indefinitely |
| Replay | Safe — triggers idempotent pack build |
| Step | STEP-009 |

### EVT-002 — `journey.evidence_pack.ready.v1`
| Field | Value |
| --- | --- |
| Producer | `evidence` · **Trigger:** pack assembly completes |
| Consumers | `scenarios`, `knowledge`, `observability` |
| Payload | `pack_id`, `trip_id`, coverage score, **freshness warnings**, source versions, blocked-option count |
| Delivery | Outbox, at-least-once |
| Privacy class | Internal |
| Retention | 90 days |
| Notes | Carries the coverage report reference, not the facts themselves |
| Step | STEP-010 |

### EVT-003 — `journey.scenario_set.generated.v1`
| Field | Value |
| --- | --- |
| Producer | `solver`/`scenarios` · **Trigger:** generation completes |
| Consumers | `ranking`, `knowledge`, `analytics`, `observability` |
| Payload | `trip_id`, scenario IDs, objective labels, solver version, model versions, **seed**, optimality gap, generation duration |
| Delivery | Outbox, at-least-once |
| Notes | The seed and versions make `REQ-CONS-006` reproducibility auditable from the event stream alone |
| Retention | 180 days |
| Step | STEP-012 |

### EVT-004 — `journey.scenario.selected.v1`
| Field | Value |
| --- | --- |
| Producer | `scenarios` · **Trigger:** owner selects the canonical scenario (API-008) |
| Consumers | `affiliate`, `live`, `analytics`, `knowledge` |
| Payload | `trip_id`, `scenario_id`, `scenario_version`, actor, decision context (objective chosen, alternatives considered) |
| Delivery | Outbox, **exactly-once effect** — consumers must guarantee a single canonical transition |
| Privacy class | Internal |
| Retention | Lifetime of the trip |
| Step | STEP-013, STEP-015 |

### EVT-005 — `journey.impact.detected.v1` *(Phase 3)*
| Field | Value |
| --- | --- |
| Producer | `live` · **Trigger:** provider event matched to itinerary nodes |
| Consumers | `notification`, `live` replan workflow, `observability` |
| Payload | event source, severity, **confidence**, affected node IDs, time to impact, evidence references |
| Delivery | Stream, **deduplicated** by source + subject + window |
| Notes | An unverified source may appear here but must never trigger an automatic plan change (`REQ-LIVE-004`) |
| Retention | 30 days |
| Step | STEP-018 |

### EVT-006 — `journey.replan.accepted.v1` *(Phase 3)*
| Field | Value |
| --- | --- |
| Producer | `live`/`scenarios` · **Trigger:** user accepts a repair |
| Consumers | `analytics`, `knowledge`, offline sync, collaborators |
| Payload | old/new `scenario_version`, **preserved percent**, deltas (cost/time/effort), actor |
| Delivery | Outbox, exactly-once effect |
| Retention | Lifetime of the trip |
| Step | STEP-019 |

### EVT-007 — `journey.privacy.deletion_completed.v1`
| Field | Value |
| --- | --- |
| Producer | `privacy` · **Trigger:** deletion traversal completes across all stores |
| Consumers | `observability`, audit |
| Payload | request ID, subject reference (pseudonymous), stores traversed, completion status, failures |
| Delivery | Outbox, exactly-once effect |
| Notes | The proof artifact for `REQ-PRIV-006`. Failure emits with status `failed` and enters the retry queue |
| Retention | Legally required audit minimum |
| Step | STEP-025 |

### EVT-008 — `journey.provider.health_changed.v1`
| Field | Value |
| --- | --- |
| Producer | `integrations` · **Trigger:** circuit breaker state change or quota threshold |
| Consumers | `destination` (coverage model), `observability`, admin UI |
| Payload | provider ID, previous/new state, reason, affected regions |
| Delivery | Stream, deduplicated |
| Notes | Drives the coverage refusal path in `REQ-TRIP-002` and the disclosure in `REQ-EVID-006` |
| Retention | 30 days |
| Step | STEP-005, STEP-021 |

---

## 3. Consumer obligations

1. **Idempotent by `event_id`.** Store processed IDs or make the effect naturally idempotent.
2. **Tolerate additive schema changes.** Unknown fields are ignored, never fatal.
3. **Never infer ordering across aggregates.** Only per-`trip_id` order is guaranteed.
4. **Handle replay explicitly.** A consumer that cannot be replayed must document why and provide a manual recovery path.
5. **No enrichment from the event alone.** Payloads carry IDs; consumers needing content must read it through an authorized API so tenancy is enforced.
6. **Dead-letter with context**, preserving the envelope for diagnosis.

---

## 4. Compatibility policy

| Change | Classification | Action |
| --- | --- | --- |
| Add optional field | Additive | Bump `schema_version`; no new event version |
| Add new event type | Additive | Register in AsyncAPI |
| Remove or rename a field | **Breaking** | New major event version; dual-publish through the deprecation window |
| Change field semantics | **Breaking** | New major version — silently changing meaning is the most damaging possible change |
| Change delivery guarantee | **Breaking** | Requires consumer notice and re-verification |
| Change partition key | **Breaking** | Ordering assumptions break; requires migration plan |

Full process in [CONTRACT_CHANGE_POLICY](CONTRACT_CHANGE_POLICY.md).

---

## 5. Status

`contracts/asyncapi.yaml` **does not exist**. All events above are specifications produced in `STEP-004` and implemented in `STEP-006`.
