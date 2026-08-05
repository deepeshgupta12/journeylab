---
step_id: STEP-010
title: Destination evidence assembly
status: DISCOVERY
release: Phase 1
owners: []
dependencies: [STEP-006, STEP-009]
requirement_ids: [REQ-EVID-001, REQ-EVID-002, REQ-EVID-003, REQ-EVID-005, REQ-EVID-006, REQ-AI-003, REQ-AI-004, REQ-AI-009]
api_ids: [API-004]
event_ids: [EVT-002]
data_ids: [DATA-007, DATA-008]
ai_ids: [AI-002, AI-004]
knowledge_graph_check: REQUIRED
last_updated: 2026-08-05
---

# STEP-010 — Destination evidence assembly

> Status is authoritative in [MASTER_TRACKER](../02-delivery/MASTER_TRACKER.md).

## 1. Outcome
An immutable, time-aware evidence pack exists for the requested window, in which **every fact the solver will use is source-addressable and governed by freshness policy**, with conflicts and coverage gaps explicit.

## 2. Why this step exists
This is the reproducibility anchor (`ADR-004`) and the trust mechanism. Solvers never query live providers; they consume a frozen pack. Without that freeze, no scenario can be reproduced and no explanation can be audited.

## 3. Scope
Retrieval of places, hours, closures, price ranges, transit, weather, crowd signals and accessibility evidence for the trip window; deduplication with provenance; conflict flagging; freshness enforcement; coverage report; immutable pack versioning.

## 4. Explicit exclusions
Provider fetching is [STEP-005](STEP-005-source-integrations-and-ingestion.md); candidate eligibility is [STEP-011](STEP-011-candidate-generation.md); citation rendering is [STEP-013](STEP-013-visual-comparison.md).

## 5. Actors, permissions and data access
| Actor | Permission | Data accessed | Sensitivity |
| --- | --- | --- | --- |
| Retrieval service | Tenant-scoped read | Canonical facts | Licensed |
| PER-004 curator | Override with audit | Destination facts only | Licensed |
| PER-001 traveler | Read own pack's coverage report | Coverage summary | Internal |

## 6. Preconditions and dependencies
[STEP-006](STEP-006-canonical-data-model-and-event-backbone.md) canonical facts and [STEP-009](STEP-009-trip-brief-and-structured-constraints.md) confirmed brief.

## 7. Inputs and source systems
Confirmed `TripBrief`; canonical `EvidenceFact` store; destination graph; cached facts; freshness policy; provider health.

## 8. Detailed normal workflow
1. `API-004` starts assembly and returns a **job handle within 500 ms**.
2. Hybrid retrieval (`AI-002`) gathers candidate facts — lexical for names and codes, dense for intent.
3. **Geospatial, temporal, tenant and access filters are applied before ranking.**
4. Facts are deduplicated into canonical claims retaining effective time, observed time, source and confidence.
5. Conflicts are flagged rather than resolved; a source hierarchy is recorded.
6. Freshness policy marks stale facts by field class.
7. Coverage report records what could and could not be established.
8. Pack is frozen as an immutable version; `EVT-002` is emitted.

## 9. Alternate, partial and failure workflows
| Condition | Behavior | User-visible result | Requirement |
| --- | --- | --- | --- |
| Provider failure | Bounded cached data **only when clearly marked** | Staleness at point of use | REQ-EVID-006 |
| Missing critical facts | Lower scenario confidence or **block affected options** | Explicit gap statement | REQ-EVID-005 |
| Sources conflict | Both retained with hierarchy; **never averaged** | Conflict shown | REQ-EVID-002 |
| Coverage/agreement low | `AI-004` corrective retrieval; then uncertainty or a blocking question | Honest abstention | REQ-AI-004 |
| Effective window misses trip dates | Fact excluded; counted as a coverage gap | Gap disclosed | Temporal model |
| Injection detected in retrieved content | Content dropped, alert raised, exclusion reason recorded | Fact excluded | REQ-AI-009 |

## 10. State machine and lifecycle transitions
`requested → retrieving → resolving → scored → frozen (immutable)` or `→ insufficient`. A frozen pack referenced by a scenario **cannot be mutated or deleted** while that scenario exists.

## 11. Frontend implementation
`apps/web/src/features/generation/` progress and warnings; `apps/web/src/features/evidence/` source drawer showing source, observed time, effective window, confidence and conflicts (`PROPOSED`). Citations open in a drawer rather than navigating the user away.

## 12. Backend implementation
`services/evidence/src/builder.py`, `services/retrieval/src/{ingest,hybrid,citations,corrective}.py` (`PROPOSED`).

## 13. API, event and integration contracts
`API-004` start assembly (job handle), `API-018` SSE progress. Emits `EVT-002` with coverage and freshness warnings.

## 14. Data model, migration and retention effects
Writes `DATA-007` EvidenceFact references and `DATA-008` EvidencePack (immutable, with coverage report). Pack retention must respect provider licence terms while preserving the reproducibility window — a genuine tension recorded as `ASM-019`.

## 15. AI, LLM, RAG, ML and data-science implementation
**`AI-002` hybrid temporal retrieval** and **`AI-004` corrective retrieval / abstention**.
- **Non-AI baseline:** structured provider queries by place ID and date.
- **Filters before ranking**, never after — a post-filter can leak across tenants and silently drop the best in-scope result.
- **Abstention is a success behavior**: low coverage or low agreement returns uncertainty or a blocking question, never model-memory backfill (`REQ-AI-004`).
- Retrieved text is **untrusted data**; injection detectors run before content enters any model context.
- Evaluation: place/entity recall, temporal-filter correctness (**100%**), permission-filter correctness (**100%**), contradiction detection, abstention precision/recall.

## 16. Security, privacy, accessibility and responsible-AI controls
`SC-INJ-01` untrusted content handling; `SC-EGRESS-01` on retrieval tools; `SC-LIC-01` licence labels carried on every fact; tenant filters during traversal. Evidence drawer is keyboard-navigable with conflicts announced.

## 17. Observability, analytics and KPIs
Pack build duration, coverage score distribution, stale-fact rate, conflict rate, abstention rate, retrieval recall, AI cost per pack. Alerts `ALRT-DATA-001`, `ALRT-AI-001`.

## 18. Files and modules expected to change
All `PROPOSED` — see §11, §12.

## 19. Knowledge-graph pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | `BLOCKED` — static fallback |
| Queries to run | KG-Q-006; KG-Q-003 (expiring facts) once the domain graph exists |
| Expected impact | Packs feed candidates, solver, explanation and citations |

## 20. Blast-radius assessment
**Highest-consequence data step.** A freshness or temporal-filter defect produces plans that are wrong in ways users cannot detect. Detectability depends entirely on the age-at-use and conflict metrics defined here.

## 21. Implementation task checklist — sub-steps
| Sub-step | Outcome |
| --- | --- |
| STEP-010.01 | Pack schema, immutability and coverage report |
| STEP-010.02 | Hybrid retrieval with pre-ranking filters |
| STEP-010.03 | Temporal filtering on effective windows |
| STEP-010.04 | Deduplication with provenance retention |
| STEP-010.05 | Conflict detection and source hierarchy |
| STEP-010.06 | Freshness enforcement by field class |
| STEP-010.07 | `AI-004` corrective retrieval and abstention |
| STEP-010.08 | Injection detection on retrieved content |
| STEP-010.09 | Citation span assembly |
| STEP-010.10 | Retrieval and abstention evaluation sets |

## 22. Test and evaluation plan
`TST-EVID-001` … `TST-EVID-006`, `TST-AI-003`, `TST-AI-004`, `TST-AI-009`. Clock-controlled tests for staleness; adversarial corpora for injection and contradiction; sparse-evidence corpus for abstention.

## 23. Deployment, feature flag and migration plan
Retrieval strategy behind a flag to allow lexical-only fallback. Index updates are incremental and rollback-able without an application deploy.

## 24. Rollback, compensation and recovery plan
Revert to a previous retrieval configuration or index version. **Frozen packs are never rewritten** — a corrected pack is a new version, and affected scenarios are regenerated rather than silently updated.

## 25. Acceptance criteria
- [ ] Every solver-visible fact is source-addressable with observed and effective time and confidence (`REQ-EVID-001`)
- [ ] Conflicts remain visible with a hierarchy; nothing is averaged (`REQ-EVID-002`)
- [ ] No estimate is presented as confirmed (`REQ-EVID-003`)
- [ ] Stale facts lower confidence or block affected options (`REQ-EVID-005`)
- [ ] Provider degradation is disclosed, not masked (`REQ-EVID-006`)
- [ ] Permission and temporal filters apply before ranking (`REQ-AI-003`)
- [ ] Low coverage produces abstention, never fabrication (`REQ-AI-004`)
- [ ] Injection attempts in retrieved content are detected and excluded (`REQ-AI-009`)

## 26. Evidence required for completion
Retrieval evaluation report; temporal-filter correctness proof; abstention precision/recall; injection detection results; pack immutability test; provider outage drill.

## 27. Open questions, risks and decisions
`RISK-001` — no provider identified. `ASM-019` cache rights vs. reproducibility is an unresolved architectural tension. Crowd-signal privacy (`ASM-021`) may remove the "quieter" dimension entirely.

## 28. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Sub-steps completed | 0 of 10 |
| Regression result | — |
| Verified by | — |
</content>
