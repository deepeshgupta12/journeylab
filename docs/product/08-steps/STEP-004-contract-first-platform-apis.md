---
step_id: STEP-004
title: Contract-first platform APIs
status: DISCOVERY
release: Phase 1
owners: []
dependencies: [STEP-002]
requirement_ids: [REQ-PLAT-005, REQ-PLAT-006, REQ-PLAT-007, REQ-PLAT-008]
api_ids: [API-001, API-002, API-003, API-004, API-005, API-006, API-007, API-008, API-009, API-010, API-011, API-012, API-013, API-014, API-015, API-016, API-017, API-018]
event_ids: [EVT-001, EVT-002, EVT-003, EVT-004, EVT-005, EVT-006, EVT-007, EVT-008]
data_ids: []
ai_ids: []
knowledge_graph_check: REQUIRED
last_updated: 2026-08-05
---

# STEP-004 — Contract-first platform APIs

> Status is authoritative in [MASTER_TRACKER](../02-delivery/MASTER_TRACKER.md).

## 1. Outcome
Stable resource, command, event and webhook contracts exist as machine-readable files; CI generates clients, validates examples and rejects accidental breaking changes.

## 2. Why this step exists
Nine steps consume these contracts. Defining them after implementations proliferate means every service invents its own error shape, pagination and idempotency semantics, and the compatibility guarantee in `REQ-PLAT-008` becomes unenforceable.

## 3. Scope
`contracts/openapi.yaml` for all 18 operations; `contracts/asyncapi.yaml` for all 8 events; shared JSON Schemas; generated TypeScript and Python clients; API composition with middleware and RFC 9457 problem responses; backward-compatibility and consumer contract tests.

## 4. Explicit exclusions
Business logic behind the endpoints belongs to [STEP-007](STEP-007-discovery-landing-and-destination-coverage.md) onward. Provider integration contracts are [STEP-005](STEP-005-source-integrations-and-ingestion.md).

## 5. Actors, permissions and data access
| Actor | Permission | Data accessed | Sensitivity |
| --- | --- | --- | --- |
| Product Architect | Contract authorship and approval | None | — |
| Backend | Implementation of the envelope | None | — |

Authorization semantics are *declared* here and enforced by `STEP-002` primitives.

## 6. Preconditions and dependencies
[STEP-002](STEP-002-identity-tenancy-and-authorization.md) exit — contracts embed the tenant/auth envelope.

## 7. Inputs and source systems
[API_CONTRACTS](../04-contracts/API_CONTRACTS.md), [EVENT_CONTRACTS](../04-contracts/EVENT_CONTRACTS.md), [ERROR_MODEL](../04-contracts/ERROR_MODEL.md), [AUTHORIZATION_MATRIX](../04-contracts/AUTHORIZATION_MATRIX.md); RFC 9457; OpenAPI 3.1; AsyncAPI.

## 8. Detailed normal workflow
1. Architect authors OpenAPI covering resources, commands, errors, pagination, auth and examples.
2. Architect authors AsyncAPI with an explicit delivery guarantee per event.
3. Architect extracts shared JSON Schemas for request, response, event and model-output shapes.
4. CI generates TypeScript and Python clients as build artifacts.
5. Backend composes the API with middleware: auth, tenant context, idempotency, ETag, correlation, problem details.
6. CI runs compatibility and consumer contract tests on every pull request.

## 9. Alternate, partial and failure workflows
| Condition | Behavior | User-visible result | Requirement |
| --- | --- | --- | --- |
| Breaking diff without version bump | **CI fails** | Merge blocked | REQ-PLAT-008 |
| Generated file hand-edited | **CI fails** | Merge blocked | REQ-PLAT-007 |
| Example fails schema validation | CI fails | Merge blocked | REQ-PLAT-005 |
| Event without a delivery guarantee | CI fails | Merge blocked | REQ-PLAT-006 |
| Deprecated operation without a sunset date | CI fails | Merge blocked | Contract policy |

## 10. State machine and lifecycle transitions
Contract lifecycle: `active → deprecated → dual-run → sunset announced → removed`. Removal is gated on **observed consumer traffic**, not on the date arriving.

## 11. Frontend implementation
Consumes `packages/contracts/src/generated/` (`PROPOSED`). No hand-written client code; no hand edits to generated files.

## 12. Backend implementation
`apps/api/src/main.py` (`PROPOSED`) — composition, middleware, route registration, problem responses. Route handlers are stubs returning `501` until their owning step implements them.

## 13. API, event and integration contracts
**This step produces them all.** `API-001` … `API-018`; `EVT-001` … `EVT-008`. All currently `PROPOSED` — no schema file exists.

## 14. Data model, migration and retention effects
No schema. Contracts declare data shapes; persistence arrives in [STEP-006](STEP-006-canonical-data-model-and-event-backbone.md).

## 15. AI, LLM, RAG, ML and data-science implementation
`NOT_APPLICABLE` as a capability. However, this step defines the **structured-output schemas** that `AI-001` must conform to, and the rule that model output fails closed on schema violation (`REQ-AI-002`). Reason: the contract boundary is where the deterministic guarantee is made enforceable.

## 16. Security, privacy, accessibility and responsible-AI controls
Auth envelope on every operation; 403/404 indistinguishability; idempotency keys on all commands; rate-limit declarations; sensitivity class recorded per operation; problem details that never leak another tenant's data or provider identities.

## 17. Observability, analytics and KPIs
Correlation ID propagation defined in the contract; route templates registered for RED metrics; contract test pass rate.

## 18. Files and modules expected to change
All `PROPOSED`: `contracts/openapi.yaml`, `contracts/asyncapi.yaml`, `contracts/jsonschema/`, `packages/contracts/src/generated/`, `apps/api/src/main.py`, `tests/contracts/`.

## 19. Knowledge-graph pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | `BLOCKED` for application code — static fallback |
| Queries to run | KG-Q-013 `api_impact` once contracts are indexed |
| Expected impact | Contracts become graph nodes linking code to consumers — this step is what makes `KG-Q-013` useful later |

## 20. Blast-radius assessment
Nine-step fan-in. Every subsequent contract change inherits [CONTRACT_CHANGE_POLICY](../04-contracts/CONTRACT_CHANGE_POLICY.md). Initial authorship has no consumers, so risk is low **now** and high for every change after.

## 21. Implementation task checklist — sub-steps
| Sub-step | Outcome |
| --- | --- |
| STEP-004.01 | Global conventions: errors, pagination, idempotency, ETags, correlation |
| STEP-004.02 | Trip, brief and scenario operations (API-001…009) |
| STEP-004.03 | Collaboration, booking, live, feedback operations (API-010…014) |
| STEP-004.04 | Privacy, admin, coverage, jobs operations (API-015…018) |
| STEP-004.05 | AsyncAPI events with delivery guarantees (EVT-001…008) |
| STEP-004.06 | Shared JSON Schemas incl. model-output schemas |
| STEP-004.07 | Client generation pipeline + no-hand-edit enforcement |
| STEP-004.08 | Compatibility and consumer contract tests |

## 22. Test and evaluation plan
`TST-PLAT-005` … `TST-PLAT-008`. Compatibility tests compare against the previous release; consumer-driven contract tests replay sanitized payloads.

## 23. Deployment, feature flag and migration plan
Contracts deploy with the API. Unimplemented operations return `501` behind a flag so the contract can ship before the behavior.

## 24. Rollback, compensation and recovery plan
Contract revert is a version bump. **A published contract with real consumers cannot be silently reverted** — that is itself a breaking change requiring the full policy.

## 25. Acceptance criteria
- [ ] All 18 operations defined in OpenAPI 3.1 with examples that validate (`REQ-PLAT-005`)
- [ ] All 8 events defined in AsyncAPI with explicit delivery guarantees (`REQ-PLAT-006`)
- [ ] Clients generated in CI; hand edits fail the build (`REQ-PLAT-007`)
- [ ] Breaking diff without version, migration guide, notice and sunset fails CI (`REQ-PLAT-008`)
- [ ] Every operation declares authorization consistent with the matrix
- [ ] Problem details conform to RFC 9457 with stable `type` URIs

## 26. Evidence required for completion
CI run showing generation and validation; a deliberately breaking change proven to fail; generated client diff; contract test results.

## 27. Open questions, risks and decisions
`DEC-009` event backbone affects delivery-guarantee wording. Whether SSE or WebSocket is used for progress is settled here (SSE proposed). Rate-limit values are unset pending capacity work.

## 28. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Sub-steps completed | 0 of 8 |
| Regression result | — |
| Verified by | — |
</content>
