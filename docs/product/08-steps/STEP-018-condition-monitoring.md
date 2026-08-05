---
step_id: STEP-018
title: Condition monitoring
status: DEFERRED
release: Phase 3
owners: []
dependencies: [STEP-017, STEP-006]
requirement_ids: [REQ-LIVE-003, REQ-LIVE-004, REQ-NFR-011]
api_ids: []
event_ids: [EVT-005]
data_ids: [DATA-014]
ai_ids: []
knowledge_graph_check: REQUIRED
last_updated: 2026-08-05
---

# STEP-018 — Condition monitoring

> Status is authoritative in [MASTER_TRACKER](../02-delivery/MASTER_TRACKER.md). **`DEFERRED` to Phase 3.**

## 1. Outcome
Material changes — closures, weather, transit disruption, booking changes — are matched to affected itinerary nodes, scored, deduplicated and surfaced according to the traveler's notification policy, **and never trigger an automatic plan change**.

## 2. Why this step exists
A live companion that notifies about everything is worse than one that notifies about nothing: travelers disable it, and then miss the one alert that mattered. Severity scoring and deduplication are the product, not the plumbing.

## 3. Scope
Provider event ingestion; matching events to itinerary nodes via dependency traversal; severity, confidence and time-to-impact scoring; duplicate suppression; notification eligibility per user policy.

## 4. Explicit exclusions
Repair generation is [STEP-019](STEP-019-controlled-replanning.md). Provider adapters are [STEP-005](STEP-005-source-integrations-and-ingestion.md).

## 5. Actors, permissions and data access
| Actor | Permission | Data accessed | Sensitivity |
| --- | --- | --- | --- |
| Provider adapters | Ingest | Provider events | Licensed |
| Event processor | Tenant-scoped match | Active itineraries | PII |
| PER-001 traveler | Receive notifications per policy | Own impacts | PII |

## 6. Preconditions and dependencies
[STEP-017](STEP-017-live-trip-activation-and-offline-pack.md) active trips; [STEP-006](STEP-006-canonical-data-model-and-event-backbone.md) event backbone.

## 7. Inputs and source systems
Closures, weather alerts, transit service alerts, booking updates, crowd updates; active itinerary graphs; user notification policy.

## 8. Detailed normal workflow
1. Provider event arrives via the connector framework.
2. Processor matches it to affected itinerary nodes, traversing `PRECEDES` dependencies.
3. Severity, confidence and time-to-impact are scored.
4. Duplicates are suppressed by source + subject + window.
5. `EVT-005` is emitted with affected scope and a recommended response window.
6. Notification is delivered only if user policy and quiet hours permit.

## 9. Alternate, partial and failure workflows
| Condition | Behavior | User-visible result | Requirement |
| --- | --- | --- | --- |
| **Unverified social report** | Recorded as low confidence; **never triggers an automatic change** | Optional informational notice | REQ-LIVE-004 |
| Providers disagree | Shown as uncertain with both sources | Honest ambiguity | REQ-EVID-002 |
| Duplicate events | Suppressed by dedup key | One notification | REQ-LIVE-003 |
| Quiet hours active | Deferred unless severity is critical | Respectful timing | REQ-LIVE-003 |
| Notification delivery fails | Retried; visible in the app regardless | No silent loss | — |
| Event storm | Rate-limited and aggregated; **`RB-LIVE-001`** | One summary, not fifty alerts | REQ-LIVE-003 |

## 10. State machine and lifecycle transitions
Impact: `detected → matched → scored → (suppressed | notified) → acknowledged → (repaired | expired)`.

## 11. Frontend implementation
`apps/web/src/app/trips/[id]/live/` notification center (`PROPOSED`) — severity, confidence, source and affected itinerary scope shown together, because severity without confidence is not actionable.

## 12. Backend implementation
`services/live/src/impact_matcher.py` (`PROPOSED`) — dependency traversal, scoring, deduplication, eligibility.

## 13. API, event and integration contracts
Emits `EVT-005` (stream, deduplicated). Consumes provider event feeds via `INT-001` … `INT-003`.

## 14. Data model, migration and retention effects
Writes `DATA-014` ImpactEvent with severity, confidence, evidence references and affected nodes. Retention 30 days.

## 15. AI, LLM, RAG, ML and data-science implementation
Severity scoring is **rule-based on measurable inputs** (time to impact, item protected status, alternatives available), not learned. Reason: a learned severity model would need labelled outcomes that do not exist at Phase 3, and its errors would be invisible. A confidence estimate on provider agreement is statistical, not generative.

## 16. Security, privacy, accessibility and responsible-AI controls
Provider events are untrusted input. **No unverified source may transition a plan** (`SC-CLAIM-01`). Notifications carry no sensitive detail in the preview text. Notification center is keyboard-navigable with severity conveyed by text.

## 17. Observability, analytics and KPIs
Match latency (p95 ≤ 60 s), false-positive rate, notification volume per trip, suppression rate, acknowledgement rate, delivery failures. Alert on notification storms.

## 18. Files and modules expected to change
All `PROPOSED` — see §11, §12.

## 19. Knowledge-graph pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | `BLOCKED` — static fallback |
| Queries to run | KG-Q-006; **KG-Q-001** (infeasibility from closure/delay) is the core product query |
| Expected impact | Depends directly on domain-graph dependency edges |

## 20. Blast-radius assessment
Over-notification degrades the product; under-notification harms travelers. Both failures are gradual and easy to miss without the volume and false-positive metrics defined here.

## 21. Implementation task checklist — sub-steps
| Sub-step | Outcome |
| --- | --- |
| STEP-018.01 | Provider event normalization into impact candidates |
| STEP-018.02 | Itinerary node matching via dependency traversal |
| STEP-018.03 | Severity, confidence and time-to-impact scoring |
| STEP-018.04 | Deduplication and suppression |
| STEP-018.05 | Notification eligibility, policy and quiet hours |
| STEP-018.06 | Notification center UI |
| STEP-018.07 | Storm rate-limiting and aggregation |

## 22. Test and evaluation plan
`TST-LIVE-003`, `TST-LIVE-004`, `TST-NFR-011`. A negative test must prove an unverified source cannot cause a plan transition. Storm simulation validates rate limiting.

## 23. Deployment, feature flag and migration plan
Phase 3 flag; per-source flags so a noisy feed can be silenced without disabling monitoring entirely.

## 24. Rollback, compensation and recovery plan
Notification suppression is an operational control (`RB-LIVE-001`). Disabling monitoring leaves the offline pack fully functional.

## 25. Acceptance criteria
- [ ] Events matched to affected nodes and deduplicated (`REQ-LIVE-003`)
- [ ] Unverified reports never trigger automatic plan changes (`REQ-LIVE-004`)
- [ ] Notifications are timely, deduplicated and traceable to evidence
- [ ] Closure and disruption freshness meets provider SLOs (`REQ-NFR-011`)
- [ ] Quiet hours and user policy respected

## 26. Evidence required for completion
Match latency measurement; false-positive analysis; storm simulation results; unverified-source negative test.

## 27. Open questions, risks and decisions
Provider event feeds are uncontracted (`EXT-001` … `EXT-003`). Notification burden threshold is a Phase 3 exit criterion but is currently unquantified (`DEC-005`).

## 28. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Sub-steps completed | 0 of 7 |
| Regression result | — |
| Verified by | — |
</content>
