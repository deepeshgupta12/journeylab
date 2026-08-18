---
step_id: STEP-005
title: Source integrations and ingestion
status: BLOCKED
release: Phase 1
owners: ["Deepesh Kumar Gupta"]
dependencies: [STEP-004]
requirement_ids: [REQ-DATA-001, REQ-DATA-002, REQ-DATA-003, REQ-DATA-004, REQ-DATA-005, REQ-DATA-006, REQ-SEC-005]
api_ids: []
event_ids: [EVT-008]
data_ids: [DATA-006, DATA-007]
ai_ids: []
knowledge_graph_check: REQUIRED
last_updated: 2026-08-05
---

# STEP-005 — Source integrations and ingestion

> Status is authoritative in [MASTER_TRACKER](../02-delivery/MASTER_TRACKER.md). **This step is on the critical path and currently `BLOCKED`.**

## 1. Outcome
Every product input arrives with consent, provenance, replay capability and source reconciliation. Each connector has credential handling, rate limits, checkpoint state, schema validation, backfill, circuit breaking and deletion behavior.

## 2. Why this step exists
Without an evidence pack there is no solver input and no product. This step is simultaneously the highest-value and highest-risk work in Phase 1 — `RISK-001` (exposure 20) lives here.

## 3. Scope
Provider adapters for places/hours/accessibility, weather, transit and affiliate; canonical entity resolution; field-specific freshness policy; sanitized provider fixtures; provider health events.

## 4. Explicit exclusions
Evidence-pack assembly is [STEP-010](STEP-010-destination-evidence-assembly.md); canonical persistence and the event backbone are [STEP-006](STEP-006-canonical-data-model-and-event-backbone.md).

## 5. Actors, permissions and data access
| Actor | Permission | Data accessed | Sensitivity |
| --- | --- | --- | --- |
| Ingestion service | Workload identity, per-provider credentials | Provider payloads | Licensed |
| PER-004 curator | Read source health | Destination facts only | Licensed |
| PER-005 ops admin | Disable provider, audited | Provider metadata | — |

**No traveler PII is touched by this step.**

## 6. Preconditions and dependencies
[STEP-004](STEP-004-contract-first-platform-apis.md) exit. **Blocked on `DEC-002`** (region), **`DEC-008`** (routing provider) and **`EV-GAP-002`** (licence viability).

## 7. Inputs and source systems
`EXT-001` places, `EXT-002` weather, `EXT-003` transit, `EXT-004` routing, `EXT-005` affiliate, `EXT-009` crowd signals — **all unidentified**. Contracts specified in [INTEGRATION_CONTRACTS](../04-contracts/INTEGRATION_CONTRACTS.md).

## 8. Detailed normal workflow
1. Scheduler triggers a connector run with a stored cursor.
2. Connector authenticates with rotated credentials via allowlisted egress.
3. Connector fetches within its rate limit and quota budget.
4. Raw payload is encrypted and stored with short retention.
5. Payload is validated against its registered schema.
6. Normalizer maps to canonical shapes; entity resolution deduplicates places.
7. Freshness policy stamps observed and effective times per field class.
8. Reconciliation compares ingested totals against source totals.
9. Checkpoint advances; provider health is published as `EVT-008`.

## 9. Alternate, partial and failure workflows
| Condition | Behavior | User-visible result | Requirement |
| --- | --- | --- | --- |
| Provider timeout | Capped backoff, then circuit break | Region marked degraded | REQ-DATA-003 |
| Schema drift | **Reject and alert; never coerce** | Ingestion halted for that source | REQ-DATA-002 |
| Quota exhausted | Degrade to cached data **marked stale**; block options needing fresh facts | Staleness disclosed | REQ-EVID-005 |
| Reconciliation mismatch | Backfill from checkpoint | None if resolved | REQ-DATA-002 |
| Licence absent | **Ingestion refused** | Source unavailable | REQ-DATA-001 |
| Individual-level crowd data offered | **Rejected outright** | Preference withdrawn | ASM-021 |

## 10. State machine and lifecycle transitions
Per provider: `configured → authenticated → healthy → degraded → circuit-open → recovering → healthy`. Transitions emit `EVT-008` and drive the coverage model.

## 11. Frontend implementation
None directly. Provider health surfaces in `/admin/providers` ([STEP-021](STEP-021-administration-and-curation-console.md)) and in public coverage ([STEP-007](STEP-007-discovery-landing-and-destination-coverage.md)).

## 12. Backend implementation
`services/integrations/src/{places,weather,transit,affiliate}/`, `services/ingestion/src/entity_resolution.py`, `services/ingestion/src/freshness.py`, `tests/fixtures/providers/` (all `PROPOSED`).

## 13. API, event and integration contracts
`INT-001` … `INT-005`, `INT-009`. Emits `EVT-008` provider health. No public API surface.

## 14. Data model, migration and retention effects
Writes `DATA-006` Place and `DATA-007` EvidenceFact. Raw payloads encrypted with short retention (`REQ-DATA-006`). Cache keys include provider licence terms so licence-limited data cannot be over-retained.

## 15. AI, LLM, RAG, ML and data-science implementation
`NOT_APPLICABLE` for the ingestion path itself — normalization and freshness are deterministic. **Entity resolution may use similarity scoring**, but a match below the confidence threshold goes to a human review queue rather than being auto-merged; merging two distinct venues silently would produce wrong itineraries.

## 16. Security, privacy, accessibility and responsible-AI controls
`SC-EGRESS-01` SSRF protection, egress allowlist, schema validation, rate limits, timeouts. `SC-LIC-01` licence recorded before ingestion. Credentials in a managed secret store with rotation. **Provider content is untrusted input** and never executed as instructions (`SC-INJ-01`).

## 17. Observability, analytics and KPIs
Per-provider latency, error rate, quota consumption, circuit state, reconciliation delta, freshness age-at-use. Alerts `ALRT-PROV-001`, `ALRT-DATA-001`. Runbooks `RB-PROV-001`, `RB-DATA-002`.

## 18. Files and modules expected to change
All `PROPOSED` — see §12.

## 19. Knowledge-graph pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | `BLOCKED` for application code — static fallback |
| Queries to run | KG-Q-006; KG-Q-014 for credential and egress paths |
| Expected impact | Canonical entities feed every downstream step |

## 20. Blast-radius assessment
Eight-step fan-out. A defect in entity resolution or freshness propagates silently into every scenario. Detectability is **poor** without reconciliation and age-at-use metrics — which is why they are in scope here rather than deferred.

## 21. Implementation task checklist — sub-steps
| Sub-step | Outcome |
| --- | --- |
| STEP-005.01 | Connector framework: credentials, egress allowlist, rate limit, timeout, circuit breaker  — ✅ **VERIFIED** 2026-08-13 (BR-038, IMPL-035)
| STEP-005.02 | Places/hours/accessibility adapter + fixtures | — ✅ **VERIFIED** 2026-08-13 (BR-041, IMPL-038)
| STEP-005.03 | Weather adapter with confidence/ensemble spread | — ✅ **VERIFIED** 2026-08-14 (BR-042, IMPL-039)
| STEP-005.04 | Transit adapter with time-zone normalization | — ✅ **VERIFIED** 2026-08-17 (BR-043, IMPL-040)
| STEP-005.05 | Routing adapter with explicit profile declaration | — ✅ **VERIFIED** 2026-08-17 (BR-044, IMPL-041)
| STEP-005.06 | Affiliate adapter: deep links + signed callbacks | — ✅ **VERIFIED** 2026-08-18 (BR-045, IMPL-044)
| STEP-005.07 | Entity resolution and provider identifier graph | — ✅ **VERIFIED** 2026-08-18 (BR-046, IMPL-045; closes BUG-027)
| STEP-005.08 | Field-specific freshness policy | — ✅ **VERIFIED** 2026-08-18 (BR-047, IMPL-046)
| STEP-005.09 | Reconciliation, backfill and checkpointing | — ✅ **VERIFIED** 2026-08-18 (BR-048, IMPL-047)
| STEP-005.10 | Provider health events and admin surface wiring | — ✅ **VERIFIED** 2026-08-18 (BR-049, IMPL-048)

## 22. Test and evaluation plan
`TST-DATA-001` … `TST-DATA-006`, `TST-SEC-005`, `TST-EVID-006`. Resilience drills for outage, quota exhaustion and schema drift are **release-blocking** (`RB-PROV-001`).

## 23. Deployment, feature flag and migration plan
Each provider behind its own flag so a failing source can be disabled without deployment. Backfills run as resumable jobs with progress checkpoints.

## 24. Rollback, compensation and recovery plan
Disable the provider flag; canonical facts from that source are marked stale and options requiring them are blocked. Re-ingestion is idempotent from the last checkpoint.

## 25. Acceptance criteria
- [ ] Every source has a licence record before ingestion is enabled (`REQ-DATA-001`)
- [ ] Every connector implements all eleven framework capabilities (`REQ-DATA-002`)
- [x] Provider failure trips a circuit breaker; no unmarked stale data is served (`REQ-DATA-003`) — STEP-005.01, STEP-005.10
- [x] Places deduplicate into canonical entities with a provider identifier graph (`REQ-DATA-004`) — STEP-005.07
- [x] Freshness policy is field-specific (`REQ-DATA-005`) — STEP-005.08
- [ ] Raw payloads encrypted and minimally retained (`REQ-DATA-006`)
- [ ] Egress allowlist, SSRF protection and timeouts enforced (`REQ-SEC-005`)

## 26. Evidence required for completion
Licence records; connector capability matrix; outage/quota/drift drill results; reconciliation report; entity-resolution precision sample.

## 27. Open questions, risks and decisions
**`RISK-001` (exposure 20)** — no provider identified; cache rights unproven (`ASM-019`); wheelchair routing data quality unknown (`ASM-020`); crowd-signal privacy unresolved (`ASM-021`). `DEC-002` and `DEC-008` blocking.

## 28. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Sub-steps completed | 0 of 10 |
| Regression result | — |
| Verified by | — |
