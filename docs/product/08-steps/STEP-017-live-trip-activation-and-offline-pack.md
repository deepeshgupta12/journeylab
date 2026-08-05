---
step_id: STEP-017
title: Live trip activation and offline pack
status: DEFERRED
release: Phase 3
owners: ["Deepesh Kumar Gupta"]
dependencies: [STEP-016]
requirement_ids: [REQ-LIVE-001, REQ-LIVE-002, REQ-PRIV-008, REQ-NFR-010]
api_ids: [API-012]
event_ids: []
data_ids: [DATA-012]
ai_ids: []
knowledge_graph_check: REQUIRED
last_updated: 2026-08-05
---

# STEP-017 — Live trip activation and offline pack

> Status is authoritative in [MASTER_TRACKER](../02-delivery/MASTER_TRACKER.md). **`DEFERRED` to Phase 3**, gated on Phase 2 exit and `RISK-006` safeguards.

## 1. Outcome
The selected scenario becomes a reliable mobile companion: critical itinerary information remains readable for at least 72 hours without network, and sync conflicts resolve visibly.

## 2. Why this step exists
Travelers use plans in exactly the conditions where connectivity fails — airports, transit, foreign networks. A planning tool that stops working on arrival has abandoned the user at the moment of use.

## 3. Scope
Offline pack download (itinerary, map metadata, ticket references, critical evidence); notification preferences, quiet hours and location permissions; today view with next action, buffers, transport and fallbacks; idempotent offline sync queue with visible conflict resolution.

## 4. Explicit exclusions
Event detection is [STEP-018](STEP-018-condition-monitoring.md); replanning is [STEP-019](STEP-019-controlled-replanning.md).

## 5. Actors, permissions and data access
| Actor | Permission | Data accessed | Sensitivity |
| --- | --- | --- | --- |
| PER-001 traveler | Activate own trip (**owner only**) | Own itinerary, tickets | **Sensitive** |
| PWA service worker | Local cache | Offline pack on device | **Sensitive** |

## 6. Preconditions and dependencies
[STEP-016](STEP-016-booking-handoff.md) canonical plan with confirmed bookings; `RISK-006` safeguards implemented.

## 7. Inputs and source systems
Approved scenario, confirmed bookings, device permissions, notification preferences.

## 8. Detailed normal workflow
1. Owner activates the trip via `API-012`.
2. System produces an offline manifest and readiness indicator.
3. Device downloads itinerary, map metadata, ticket references and critical evidence.
4. Traveler sets notification preferences, quiet hours and (optional) location permission.
5. Today view shows the next action, buffers, transport details, evidence and fallback activities.
6. Offline changes queue idempotently and sync on reconnection.

## 9. Alternate, partial and failure workflows
| Condition | Behavior | User-visible result | Requirement |
| --- | --- | --- | --- |
| Download incomplete | Readiness indicator shows exactly what is missing | Honest partial state | REQ-LIVE-001 |
| Offline edit | Queued idempotently | Applied on reconnect | REQ-LIVE-002 |
| Sync conflict | **Surfaced visibly; user resolves** — never silently overwritten | Explicit choice | REQ-LIVE-002 |
| Location permission denied | Full function without location | No degradation of core tasks | REQ-PRIV-008 |
| Device storage insufficient | Prioritise critical evidence; state what was dropped | Informed trade-off | REQ-LIVE-001 |
| Sensitive documents | **Require explicit opt-in and device protection** | Deliberate consent | REQ-SEC-010 |

## 10. State machine and lifecycle transitions
`selected → activating → active (online) ↔ active (offline) → completed → archived`. Offline queue: `queued → syncing → (applied | conflict)`.

## 11. Frontend implementation
`apps/web/src/app/trips/[id]/live/` (`PROPOSED`) — today view, offline status, sync queue, conflict recovery. **Low-motion, one-handed and sunlight-readable modes; never requires a map for core actions.**

## 12. Backend implementation
`services/live/` activation and manifest generation (`PROPOSED`).

## 13. API, event and integration contracts
`API-012` `POST /v1/trips/{tripId}:activate` (owner only), returning the offline manifest and readiness indicator.

## 14. Data model, migration and retention effects
Reads `DATA-012` ItineraryItem. Offline packs live on the device with retention tied to trip duration plus a short grace period; tokens are revoked on deletion or logout. **Precise location is not persisted** (`REQ-PRIV-008`).

## 15. AI, LLM, RAG, ML and data-science implementation
`NOT_APPLICABLE`. Reason: activation and sync are deterministic. Offline operation specifically **cannot** depend on a model, since no network means no inference — designing AI into this path would break the guarantee.

## 16. Security, privacy, accessibility and responsible-AI controls
Offline pack encrypted at rest on device. Sensitive documents require explicit opt-in plus device protection. **Location sharing defaults off**; location processed ephemerally. Tokens revocable remotely. Sunlight-readable and one-handed modes are accessibility requirements, not preferences.

## 17. Observability, analytics and KPIs
`live_activated`, offline readiness rate, sync conflict frequency, queue depth, notification opt-in rates. Runbook `RB-LIVE-001`.

## 18. Files and modules expected to change
All `PROPOSED` — see §11, §12.

## 19. Knowledge-graph pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | `BLOCKED` — static fallback |
| Queries to run | KG-Q-006; **KG-Q-014** for location and document paths |
| Expected impact | Introduces on-device data — a new data boundary |

## 20. Blast-radius assessment
Introduces the product's first **off-server data store**. Deletion must reach it (`REQ-PRIV-006`), and a defect leaves personal data on devices after account deletion — high severity, low detectability.

## 21. Implementation task checklist — sub-steps
| Sub-step | Outcome |
| --- | --- |
| STEP-017.01 | Offline manifest generation and readiness indicator |
| STEP-017.02 | Service worker caching with encryption |
| STEP-017.03 | Today view, next action, buffers, fallbacks |
| STEP-017.04 | Notification preferences and quiet hours |
| STEP-017.05 | Idempotent offline sync queue |
| STEP-017.06 | Visible conflict resolution |
| STEP-017.07 | Low-motion, one-handed, sunlight-readable modes |
| STEP-017.08 | Token revocation and offline deletion propagation |

## 22. Test and evaluation plan
`TST-LIVE-001`, `TST-LIVE-002`, `TST-PRIV-008`, `TST-NFR-010`. **72-hour offline test on supported mobile browsers is release-blocking.** Quarterly offline-sync conflict drill.

## 23. Deployment, feature flag and migration plan
Phase 3 flag. Manifest versioning allows the pack format to evolve without breaking installed devices.

## 24. Rollback, compensation and recovery plan
Flag off prevents new activations; existing packs continue to function offline by design. **Remote token revocation is the only lever over already-downloaded data** — which is why opt-in for sensitive documents matters.

## 25. Acceptance criteria
- [ ] Itinerary and critical evidence usable ≥72 h without network (`REQ-LIVE-001`, `REQ-NFR-010`)
- [ ] Offline changes queue idempotently; conflicts resolve visibly (`REQ-LIVE-002`)
- [ ] Precise location is not persisted unless explicitly saved (`REQ-PRIV-008`)
- [ ] Core actions complete without the map and without network
- [ ] Sensitive documents require explicit opt-in and device protection

## 26. Evidence required for completion
72-hour offline test on supported browsers; conflict drill record; deletion-reaches-device proof; accessibility audit of the live modes.

## 27. Open questions, risks and decisions
`RISK-006` — Phase 3 does not ship if location safeguards cannot be implemented. Device storage limits versus evidence completeness needs a product decision on what "critical" means.

## 28. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Sub-steps completed | 0 of 8 |
| Regression result | — |
| Verified by | — |
