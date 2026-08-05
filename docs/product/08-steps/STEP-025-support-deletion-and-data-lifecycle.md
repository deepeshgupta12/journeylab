---
step_id: STEP-025
title: Support, deletion and data lifecycle
status: DISCOVERY
release: Phase 1
owners: ["Deepesh Kumar Gupta"]
dependencies: [STEP-023, STEP-026]
requirement_ids: [REQ-PRIV-005, REQ-PRIV-006, REQ-PRIV-007, REQ-TRIP-007, REQ-ADMIN-005]
api_ids: [API-015]
event_ids: [EVT-007]
data_ids: []
ai_ids: []
knowledge_graph_check: REQUIRED
last_updated: 2026-08-05
---

# STEP-025 — Support, deletion and data lifecycle

> Status is authoritative in [MASTER_TRACKER](../02-delivery/MASTER_TRACKER.md).

## 1. Outcome
A user receives confirmation of export or deletion, and **automated tests prove data removal across primary, cache, vector, graph, object, export and token stores**. Support resolves cases without unrestricted tenant access.

## 2. Why this step exists
Deletion that removes the database row but leaves an embedding, a graph node or a cached export has not deleted anything meaningful — it has only made the data harder to find. This step closes the lifecycle, including product and destination retirement.

## 3. Scope
Tenant-safe diagnostic bundles; export, correction, consent withdrawal and deletion; deletion traversal across every derived store with proof; monitored retry queue; retention enforcement; legally required audit exceptions; retirement procedures.

## 4. Explicit exclusions
Control design is [STEP-023](STEP-023-security-privacy-and-compliance-controls.md); consent capture UI is [STEP-008](STEP-008-account-consent-and-traveler-profile.md).

## 5. Actors, permissions and data access
| Actor | Permission | Data accessed | Sensitivity |
| --- | --- | --- | --- |
| PER-001 traveler | Export, correct, withdraw, delete own | Own data | PII |
| Privacy operator | Execute DSRs, audited | Subject data under authority | **Sensitive** |
| PER-005 ops admin | Single-trip diagnostics | IDs and versions, no raw payloads | Internal |

## 6. Preconditions and dependencies
[STEP-023](STEP-023-security-privacy-and-compliance-controls.md) controls; **[STEP-026](STEP-026-knowledge-graph-platform.md)** — deletion must traverse graph nodes, so the graph must exist to be traversed.

## 7. Inputs and source systems
Correlation ID, trip state, support request or deletion instruction; retention policy; legal-hold status.

## 8. Detailed normal workflow
1. User requests export, correction, withdrawal or deletion via `API-015`.
2. Request is tracked with a status the user can see.
3. A durable workflow traverses every store: transactional rows → object storage → vector chunks → graph nodes → caches → exports → notification and offline tokens.
4. Each store confirms completion.
5. `EVT-007` is emitted and the user receives confirmation.
6. Only legally required audit metadata is retained, with the exception documented.

## 9. Alternate, partial and failure workflows
| Condition | Behavior | User-visible result | Requirement |
| --- | --- | --- | --- |
| A store fails to confirm | **Monitored retry queue visible to the privacy owner** — never silently dropped | Status remains "in progress" | REQ-PRIV-007 |
| Legal hold active | Deletion suspended; **hold recorded, time-boxed and reviewed** | User informed of the hold | Retention policy |
| Shared trip, collaborator deletes | Their contributions removed/pseudonymised; owner's trip survives | Trip intact | REQ-PRIV-006 |
| Evidence pack referenced by a live scenario | Pack released only when the trip is deleted | No dangling reference | ADR-004 |
| Restore crosses a deletion event | **Deletions re-applied after restore** and recorded | Data does not reappear | Backup/DR |
| Support requests wider access | No operation exists to grant it | Request unfulfillable by design | REQ-ADMIN-005 |

## 10. State machine and lifecycle transitions
DSR: `received → in progress → (completed → EVT-007) | (failed → retry queue → completed)`. Trip: `active → archived → deleted`. Destination pack: `active → deprecated → retired`.

## 11. Frontend implementation
`apps/web/src/app/settings/data/` (`PROPOSED`) — export, retention controls, delete account with clear consequences, request status. Phase 3 adds a warning that deletion removes the offline pack and live monitoring.

## 12. Backend implementation
`services/privacy/src/requests.py` (durable workflow), `services/support/src/diagnostics.py` (`PROPOSED`).

## 13. API, event and integration contracts
`API-015` privacy requests. Emits `EVT-007` deletion completed — **the proof artifact for `REQ-PRIV-006`**, emitted with `failed` status when incomplete.

## 14. Data model, migration and retention effects
Enforces retention across every entity. Deletion propagates to embeddings, graph nodes, caches, exports and offline-token revocation. Consent records and audit events are the **only two documented exceptions**.

## 15. AI, LLM, RAG, ML and data-science implementation
`NOT_APPLICABLE` as a capability, but this step **constrains AI**: vector embeddings derived from deleted data must be removed, and evaluation datasets built from production traces must not retain deleted subjects' content. Reason: retrieval indexes are the store most often forgotten in deletion design.

## 16. Security, privacy, accessibility and responsible-AI controls
`SC-DSR-01/02/03`, `SC-RET-01`, `SC-AUTHZ-02`. Diagnostic bundles carry source and version IDs, **not raw sensitive payloads by default**. Deletion and export flows are keyboard and screen-reader complete — a privacy right that is inaccessible is not exercisable.

## 17. Observability, analytics and KPIs
DSR turnaround, deletion completion rate, retry-queue depth and age, per-store confirmation latency, support bundle usage. Alert `ALRT-PRIV-001`; runbook `RB-PRIV-001`.

## 18. Files and modules expected to change
All `PROPOSED` — see §11, §12.

## 19. Knowledge-graph pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | `BLOCKED` — static fallback |
| Queries to run | KG-Q-006; **KG-Q-014** to enumerate every store touched by a subject's data |
| Expected impact | Deletion must reach every derived store the graph knows about — the graph is how completeness is verified |

## 20. Blast-radius assessment
**Highest compliance severity.** An incomplete deletion is a breach that is invisible until audited. Detectability depends entirely on the traversal proof test, which must seed data into every store before deleting.

## 21. Implementation task checklist — sub-steps
| Sub-step | Outcome |
| --- | --- |
| STEP-025.01 | DSR request tracking and user-visible status |
| STEP-025.02 | Export in a machine-readable format with confirmation |
| STEP-025.03 | Correction and consent-withdrawal flows |
| STEP-025.04 | Deletion traversal workflow across all stores |
| STEP-025.05 | Vector and graph deletion propagation |
| STEP-025.06 | Token revocation (notification + offline) |
| STEP-025.07 | Monitored retry queue with privacy-owner visibility |
| STEP-025.08 | Retention enforcement jobs |
| STEP-025.09 | Tenant-safe support diagnostics |
| STEP-025.10 | **Traversal proof test** seeding every store |
| STEP-025.11 | Retirement procedures (trip, destination pack, product) |

## 22. Test and evaluation plan
`TST-PRIV-005` … `TST-PRIV-007`, `TST-TRIP-007`, `TST-ADMIN-005`. **The deletion proof is release-blocking**: seed data into primary, object, vector, graph, cache, export and token stores; delete; assert absence in all seven.

## 23. Deployment, feature flag and migration plan
Deletion workflow is not flaggable off — a flag that disables deletion creates a compliance gap. Retention jobs deploy with configurable schedules.

## 24. Rollback, compensation and recovery plan
**Deletion is irreversible by design**; the safeguards are confirmation, legal hold and the retry queue rather than undo. A restore crossing a deletion must re-apply it.

## 25. Acceptance criteria
- [ ] Machine-readable export with confirmation (`REQ-PRIV-005`)
- [ ] Deletion proven across primary, object, vector, graph, cache, export and token stores (`REQ-PRIV-006`)
- [ ] Failures enter a monitored retry queue visible to the privacy owner (`REQ-PRIV-007`)
- [ ] Retention is user-configurable within policy and enforced (`REQ-TRIP-007`)
- [ ] Support reconstructs one trip without unrestricted tenant access (`REQ-ADMIN-005`)
- [ ] Only documented, legally required exceptions survive deletion

## 26. Evidence required for completion
Traversal proof test output for all seven stores; DSR rehearsal record; retry-queue behavior under injected failure; diagnostic bundle sample; retention job verification.

## 27. Open questions, risks and decisions
**No legal review performed** — statutory retention periods and jurisdictions unknown (`DEC-007`). Warehouse deletion strategy (row-level vs. re-aggregation) undecided. Legal-hold process undefined.

## 28. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Sub-steps completed | 0 of 11 |
| Regression result | — |
| Verified by | — |
