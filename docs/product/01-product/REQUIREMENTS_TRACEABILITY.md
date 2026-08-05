# JourneyLab — Requirements Traceability Matrix

| Field | Value |
| --- | --- |
| Owner | TPM + Product Architect (unassigned — `BLK-001`) |
| Status | `DISCOVERY` — every requirement is linked; **no link is verified against code** (no implementation exists) |
| Upstream source | [FUNCTIONAL_REQUIREMENTS](FUNCTIONAL_REQUIREMENTS.md), [PRODUCT_SCOPE](PRODUCT_SCOPE.md), [API_CONTRACTS](../04-contracts/API_CONTRACTS.md) |
| Coverage | **130 / 130 requirements** linked to ≥1 scope step and ≥1 acceptance test |
| Last reviewed | 2026-08-05 |

Navigation: [Requirements](FUNCTIONAL_REQUIREMENTS.md) · [Scope](PRODUCT_SCOPE.md) · [Acceptance tests](../06-quality/ACCEPTANCE_TEST_CATALOG.md) · [Master tracker](../02-delivery/MASTER_TRACKER.md) · [00-START-HERE](../00-START-HERE.md)

---

## How to use and maintain this matrix

- **Rule:** no requirement may exist without a scope step **and** an acceptance test **and** a release disposition. A row failing this is a documentation defect and blocks release readiness.
- `PROPOSED` marks an artifact that does not exist yet. Since `CODEBASE_ROOT` is a documentation-only repository at the time of writing, **every frontend surface, backend service and test ID below is `PROPOSED`**. None has been verified against source.
- When code exists, the [knowledge-graph query](../05-knowledge-graph/GRAPH_QUERY_PLAYBOOK.md) `KG-Q-006` ("what requirement, API, data entity, model, alert and test depend on this symbol?") becomes the automated verification for this matrix, and `KG-Q-008` reports untested requirements.
- Legend for **Status**: `DISCOVERY` (defined, unbuilt) · `READY` · `IN_PROGRESS` · `VERIFIED` · `DEFERRED`.

---

## 1. Platform and foundation

| Requirement ID | Requirement (abbrev.) | Persona | Scope Step | Frontend Surface | Backend Service | API/Event | Data Entity | AI/ML | Security Control | Test ID | Release | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| REQ-PLAT-001 | Local dev from documented commands | Internal | STEP-001 | — | — | — | — | — | — | TST-PLAT-001 | P1 | DISCOVERY |
| REQ-PLAT-002 | Pinned lock files enforced in CI | Internal | STEP-001 | — | — | — | — | — | SC-SUPPLY-01 | TST-PLAT-002 | P1 | DISCOVERY |
| REQ-PLAT-003 | Every path has an owner | Internal | STEP-001 | — | — | — | — | — | SC-GOV-01 | TST-PLAT-003 | P1 | DISCOVERY |
| REQ-PLAT-004 | ADR per structural decision | Internal | STEP-001 | — | — | — | — | — | — | TST-PLAT-004 | P1 | DISCOVERY |
| REQ-PLAT-005 | OpenAPI 3.1 is the API source of truth | All | STEP-004 | — | `apps/api` | API-001…017 | — | — | — | TST-PLAT-005 | P1 | DISCOVERY |
| REQ-PLAT-006 | AsyncAPI defines all events | All | STEP-004 | — | `services/events` | EVT-001…008 | — | — | — | TST-PLAT-006 | P1 | DISCOVERY |
| REQ-PLAT-007 | Generated clients never hand-edited | Internal | STEP-004 | `packages/contracts` | — | all | — | — | — | TST-PLAT-007 | P1 | DISCOVERY |
| REQ-PLAT-008 | Breaking change requires version + migration | All | STEP-004, STEP-027 | — | — | all | — | — | — | TST-PLAT-008 | P1 | DISCOVERY |
| REQ-PLAT-009 | Release blocked by any gate regression | Internal | STEP-027 | — | CI | — | — | all | — | TST-PLAT-009 | P1 | DISCOVERY |
| REQ-PLAT-010 | Rollback exercised in staging | Internal | STEP-027 | — | CI | — | — | — | — | TST-PLAT-010 | P1 | DISCOVERY |
| REQ-PLAT-011 | Expand/migrate/contract migrations | Internal | STEP-027 | — | `db/` | — | all | — | — | TST-PLAT-011 | P1 | DISCOVERY |
| REQ-PLAT-012 | Runtime rollout control without deploy | PER-005 | STEP-021, STEP-027 | `/admin/flags` | `deploy/flags` | API-016 | — | AI-001…009 | SC-CHANGE-01 | TST-PLAT-012 | P1 | DISCOVERY |

## 2. Security

| Requirement ID | Requirement (abbrev.) | Persona | Scope Step | Frontend Surface | Backend Service | API/Event | Data Entity | AI/ML | Security Control | Test ID | Release | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| REQ-SEC-001 | Tenant ID on every row/event/cache key | All | STEP-002, STEP-006 | — | `identity`, `events` | all | DATA-001…016 | — | SC-TEN-01 | TST-SEC-001 | P1 | DISCOVERY |
| REQ-SEC-002 | No cross-tenant access by any path | All | STEP-002, STEP-026 | — | all | all | all | — | SC-TEN-02 | TST-SEC-002 | P1 | DISCOVERY |
| REQ-SEC-003 | OIDC + passkeys; workload identity | PER-001 | STEP-002 | `/auth/*` | `identity` | API-001 | DATA-002 | — | SC-AUTH-01 | TST-SEC-003 | P1 | DISCOVERY |
| REQ-SEC-004 | Server-side authorization on every op | All | STEP-002 | all | `apps/api` | all | all | — | SC-AUTHZ-01 | TST-SEC-004 | P1 | DISCOVERY |
| REQ-SEC-005 | SSRF, egress allowlist, timeouts on connectors | PER-005 | STEP-005, STEP-009 | — | `integrations`, `ai` | — | DATA-006 | AI-001…005 | SC-EGRESS-01 | TST-SEC-005 | P1 | DISCOVERY |
| REQ-SEC-006 | Retrieved content treated as untrusted data | PER-001 | STEP-010, STEP-009 | — | `retrieval`, `ai` | — | DATA-007 | AI-002, AI-009 | SC-INJ-01 | TST-SEC-006 | P1 | DISCOVERY |
| REQ-SEC-007 | Immutable audit separate from app logs | PER-005 | STEP-023, STEP-024 | — | `audit` | — | — | — | SC-AUDIT-01 | TST-SEC-007 | P1 | DISCOVERY |
| REQ-SEC-008 | Anti-stalking share controls | PER-001, PER-002 | STEP-015, STEP-017 | `/trips/[id]/share` | `collaboration` | API-010 | DATA-004 | — | SC-ABUSE-01 | TST-SEC-008 | P2 | DEFERRED |
| REQ-SEC-009 | SBOM + signed artifacts | Internal | STEP-027 | — | CI | — | — | — | SC-SUPPLY-02 | TST-SEC-009 | P1 | DISCOVERY |
| REQ-SEC-010 | Booking docs segregated from planning graph | PER-001 | STEP-016, STEP-023 | `/trips/[id]/booking` | `affiliate` | API-011 | DATA-013 | — | SC-SEG-01 | TST-SEC-010 | P1 | DISCOVERY |

## 3. Privacy and accessibility

| Requirement ID | Requirement (abbrev.) | Persona | Scope Step | Frontend Surface | Backend Service | API/Event | Data Entity | AI/ML | Security Control | Test ID | Release | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| REQ-PRIV-001 | Guest planning without account | PER-001 | STEP-008 | `/trips/new` | `identity` | API-001 | DATA-002 | — | SC-MIN-01 | TST-PRIV-001 | P1 | DISCOVERY |
| REQ-PRIV-002 | Purpose-specific consent, independently revocable | PER-001 | STEP-008 | `/settings/privacy` | `identity`, `privacy` | API-015 | DATA-003 | — | SC-CONSENT-01 | TST-PRIV-002 | P1 | DISCOVERY |
| REQ-PRIV-003 | No inference of sensitive attributes | PER-001 | STEP-008, STEP-020 | — | `preference` | — | DATA-003 | AI-009 | SC-SENS-01 | TST-PRIV-003 | P1 | DISCOVERY |
| REQ-PRIV-004 | Sensitive classes never used for ads | PER-001 | STEP-008, STEP-022 | — | `analytics` | — | DATA-003 | — | SC-SENS-02 | TST-PRIV-004 | P1 | DISCOVERY |
| REQ-PRIV-005 | Machine-readable export with confirmation | PER-001 | STEP-025 | `/settings/data` | `privacy` | API-015 | all | — | SC-DSR-01 | TST-PRIV-005 | P1 | DISCOVERY |
| REQ-PRIV-006 | Deletion across all stores incl. graph + vectors | PER-001 | STEP-025, STEP-026 | `/settings/data` | `privacy`, `knowledge` | API-015 | all | AI-002 | SC-DSR-02 | TST-PRIV-006 | P1 | DISCOVERY |
| REQ-PRIV-007 | Deletion failures visible in retry queue | PER-005 | STEP-025 | `/admin/privacy` | `privacy` | — | — | — | SC-DSR-03 | TST-PRIV-007 | P1 | DISCOVERY |
| REQ-PRIV-008 | Ephemeral precise location | PER-001 | STEP-017, STEP-019 | `/trips/[id]/live` | `live` | API-013 | — | — | SC-LOC-01 | TST-PRIV-008 | P3 | DEFERRED |
| REQ-A11Y-001 | Keyboard + screen-reader complete | All | STEP-003 + UI steps | all routes | — | — | — | — | — | TST-A11Y-001 | P1 | DISCOVERY |
| REQ-A11Y-002 | Table/list + CSV equivalent per visualization | PER-001 | STEP-013 | `/trips/[id]/compare` | — | API-007 | DATA-011 | — | — | TST-A11Y-002 | P1 | DISCOVERY |
| REQ-A11Y-003 | No core action requires the map | PER-001 | STEP-013, STEP-017 | `/trips/[id]/*` | — | — | — | — | — | TST-A11Y-003 | P1 | DISCOVERY |
| REQ-A11Y-004 | Status never colour-only | All | STEP-003 | `packages/ui` | — | — | — | — | — | TST-A11Y-004 | P1 | DISCOVERY |
| REQ-A11Y-005 | Non-pointer alternative to drag-and-drop | PER-001 | STEP-014 | `/trips/[id]/whatif` | — | API-009 | DATA-011 | — | — | TST-A11Y-005 | P2 | DEFERRED |
| REQ-A11Y-006 | Focus restore + SR announcements on stream | PER-001 | STEP-012, STEP-013 | `/trips/[id]/generate` | — | API-005 | — | — | — | TST-A11Y-006 | P1 | DISCOVERY |

## 4. Core product capability

| Requirement ID | Requirement (abbrev.) | Persona | Scope Step | Frontend Surface | Backend Service | API/Event | Data Entity | AI/ML | Security Control | Test ID | Release | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| REQ-TRIP-001 | Coverage + limitations shown pre-signup | PER-001 | STEP-007 | `/` , `/coverage` | `destination` | API-017 | DATA-006 | — | — | TST-TRIP-001 | P1 | DISCOVERY |
| REQ-TRIP-002 | Out-of-coverage refused, no partial sim | PER-001 | STEP-007 | `/trips/new` | `destination` | API-017 | — | — | — | TST-TRIP-002 | P1 | DISCOVERY |
| REQ-TRIP-003 | Create/duplicate/archive/export/delete trip | PER-001 | STEP-008, STEP-025 | `/trips` | `trip` | API-001…003 | DATA-004 | — | SC-DSR-01 | TST-TRIP-003 | P1 | DISCOVERY |
| REQ-TRIP-004 | Versioned constraints with usage view | PER-001 | STEP-008, STEP-009 | `/settings/profile` | `trip` | API-003 | DATA-003, DATA-005 | — | — | TST-TRIP-004 | P1 | DISCOVERY |
| REQ-TRIP-005 | Guest→account migration without duplication | PER-001 | STEP-008 | `/auth/upgrade` | `identity` | API-001 | DATA-002 | — | — | TST-TRIP-005 | P1 | DISCOVERY |
| REQ-TRIP-006 | Expiring, revocable, role-scoped invitations | PER-002 | STEP-015 | `/trips/[id]/share` | `collaboration` | API-010 | DATA-004 | — | SC-ABUSE-01 | TST-TRIP-006 | P2 | DEFERRED |
| REQ-TRIP-007 | User-configurable retention | PER-001 | STEP-025 | `/settings/data` | `privacy` | API-015 | DATA-004 | — | SC-RET-01 | TST-TRIP-007 | P1 | DISCOVERY |
| REQ-TRIP-008 | Preference changes shown, attributable, reversible | PER-001 | STEP-020 | `/settings/preferences` | `preference` | API-014 | DATA-003 | AI-009 | SC-SENS-01 | TST-TRIP-008 | P3 | DEFERRED |
| REQ-TRIP-009 | Advisor delegated + audited access | PER-003 | STEP-028 | `/org/*` | `identity` | API-001 | DATA-001 | — | SC-AUTHZ-02 | TST-TRIP-009 | P4 | DEFERRED |
| REQ-CONS-001 | Four constraint classes kept distinct | PER-001 | STEP-009 | `/trips/[id]/brief` | `trip` | API-003 | DATA-005 | AI-001 | — | TST-CONS-001 | P1 | DISCOVERY |
| REQ-CONS-002 | Only blocking clarifications; confirm interpretation | PER-001 | STEP-009 | `/trips/[id]/brief` | `ai` | API-003 | DATA-005 | AI-001 | — | TST-CONS-002 | P1 | DISCOVERY |
| REQ-CONS-003 | Hard filters before ranking | PER-001 | STEP-011 | — | `recommendation` | — | DATA-009 | AI-005 | — | TST-CONS-003 | P1 | DISCOVERY |
| REQ-CONS-004 | Zero hard-constraint violations | PER-001 | STEP-012 | — | `solver` | API-005 | DATA-010 | AI-006 | — | TST-CONS-004 | P1 | DISCOVERY |
| REQ-CONS-005 | Minimal conflict set on infeasibility | PER-001 | STEP-012 | `/trips/[id]/generate` | `solver` | API-005 | DATA-010 | AI-006 | — | TST-CONS-005 | P1 | DISCOVERY |
| REQ-CONS-006 | Reproducible from inputs + seed | Internal | STEP-012 | — | `solver`, `simulation` | EVT-003 | DATA-010 | AI-006, AI-007 | — | TST-CONS-006 | P1 | DISCOVERY |
| REQ-CONS-007 | ≥3 materially different labelled scenarios | PER-001 | STEP-012 | `/trips/[id]/compare` | `ranking` | API-006 | DATA-010 | AI-008 | — | TST-CONS-007 | P1 | DISCOVERY |
| REQ-CONS-008 | Confidence intervals, not point certainty | PER-001 | STEP-012 | `/trips/[id]/compare` | `simulation` | API-007 | DATA-011 | AI-007 | — | TST-CONS-008 | P1 | DISCOVERY |
| REQ-CONS-009 | Material differences + confidence ranges | PER-001 | STEP-013 | `/trips/[id]/compare` | — | API-007 | DATA-011 | AI-003 | — | TST-CONS-009 | P1 | DISCOVERY |
| REQ-CONS-010 | Recompute only affected segments | PER-001 | STEP-014 | `/trips/[id]/whatif` | `scenarios` | API-009 | DATA-011 | AI-006 | — | TST-CONS-010 | P2 | DEFERRED |
| REQ-CONS-011 | Protected elements locked | PER-001 | STEP-014, STEP-019 | `/trips/[id]/whatif` | `scenarios` | API-009 | DATA-012 | AI-006 | — | TST-CONS-011 | P2 | DEFERRED |
| REQ-EVID-001 | Source/observed/effective/confidence displayed | PER-001 | STEP-010, STEP-013 | evidence drawer | `evidence` | API-004 | DATA-007 | AI-002 | — | TST-EVID-001 | P1 | DISCOVERY |
| REQ-EVID-002 | Conflicts visible with hierarchy | PER-001 | STEP-010 | evidence drawer | `evidence` | API-004 | DATA-007 | AI-002 | — | TST-EVID-002 | P1 | DISCOVERY |
| REQ-EVID-003 | Estimate never shown as confirmed | PER-001 | STEP-010, STEP-016 | `/trips/[id]/booking` | `affiliate` | API-011 | DATA-013 | — | — | TST-EVID-003 | P1 | DISCOVERY |
| REQ-EVID-004 | Claim-to-source spans in prose | PER-001 | STEP-013 | `/trips/[id]/compare` | `retrieval` | API-007 | DATA-007 | AI-003 | — | TST-EVID-004 | P1 | DISCOVERY |
| REQ-EVID-005 | Stale facts lower confidence or block | PER-001 | STEP-010 | evidence drawer | `evidence` | EVT-002 | DATA-007 | AI-004 | — | TST-EVID-005 | P1 | DISCOVERY |
| REQ-EVID-006 | Provider degradation surfaced not masked | PER-001 | STEP-007, STEP-010 | `/coverage` | `destination` | API-017 | DATA-006 | — | — | TST-EVID-006 | P1 | DISCOVERY |

## 5. AI, data, live, collaboration, booking, admin, observability, KG

| Requirement ID | Requirement (abbrev.) | Persona | Scope Step | Frontend Surface | Backend Service | API/Event | Data Entity | AI/ML | Security Control | Test ID | Release | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| REQ-AI-001 | Model output cannot mutate state | All | STEP-009, STEP-013 | — | `ai` | all | all | AI-001…009 | SC-DET-01 | TST-AI-001 | P1 | DISCOVERY |
| REQ-AI-002 | Structured output, fail closed | Internal | STEP-009 | — | `ai` | — | DATA-005 | AI-001 | SC-DET-02 | TST-AI-002 | P1 | DISCOVERY |
| REQ-AI-003 | Permission/temporal filters before ranking | PER-001 | STEP-010 | — | `retrieval` | — | DATA-007 | AI-002 | SC-TEN-02 | TST-AI-003 | P1 | DISCOVERY |
| REQ-AI-004 | Abstain rather than backfill from memory | PER-001 | STEP-010 | evidence drawer | `retrieval` | — | DATA-008 | AI-004 | — | TST-AI-004 | P1 | DISCOVERY |
| REQ-AI-005 | Allowlisted read tools only | Internal | STEP-009, STEP-016 | — | `ai` | — | — | AI-001…005 | SC-TOOL-01 | TST-AI-005 | P1 | DISCOVERY |
| REQ-AI-006 | Single trace with cost/latency, redacted | Internal | STEP-009, STEP-024 | — | `ai` | — | — | all AI | SC-REDACT-01 | TST-AI-006 | P1 | DISCOVERY |
| REQ-AI-007 | Documented non-AI fallback per capability | PER-001 | all AI steps | — | `ai` | — | — | all AI | — | TST-AI-007 | P1 | DISCOVERY |
| REQ-AI-008 | Per-request cost/latency budget | Internal | STEP-009, STEP-010 | — | `ai` | — | — | all AI | — | TST-AI-008 | P1 | DISCOVERY |
| REQ-AI-009 | Injection detection on retrieved content | Internal | STEP-010 | — | `ai` | — | DATA-007 | AI-002 | SC-INJ-01 | TST-AI-009 | P1 | DISCOVERY |
| REQ-AI-010 | No visa/health/legal/safety guarantees | PER-001 | STEP-013 | `/trips/[id]/compare` | `ai` | — | — | AI-003 | SC-CLAIM-01 | TST-AI-010 | P1 | DISCOVERY |
| REQ-DATA-001 | Licence terms before ingestion | Internal | STEP-005 | — | `integrations` | — | DATA-006 | — | SC-LIC-01 | TST-DATA-001 | P1 | DISCOVERY |
| REQ-DATA-002 | Connector rotation/limits/checkpoint/backfill | Internal | STEP-005 | — | `integrations` | — | DATA-006 | — | SC-EGRESS-01 | TST-DATA-002 | P1 | DISCOVERY |
| REQ-DATA-003 | Circuit breaker, no unmarked stale data | PER-001 | STEP-005 | — | `integrations` | — | DATA-007 | — | — | TST-DATA-003 | P1 | DISCOVERY |
| REQ-DATA-004 | Canonical place entity resolution | Internal | STEP-005 | — | `ingestion` | — | DATA-006 | — | — | TST-DATA-004 | P1 | DISCOVERY |
| REQ-DATA-005 | Field-specific freshness policy | Internal | STEP-005, STEP-010 | — | `ingestion` | — | DATA-007 | — | — | TST-DATA-005 | P1 | DISCOVERY |
| REQ-DATA-006 | Raw payloads encrypted, minimally retained | Internal | STEP-005, STEP-025 | — | `ingestion` | — | — | — | SC-RET-01 | TST-DATA-006 | P1 | DISCOVERY |
| REQ-DATA-007 | Canonical records retain provenance + version | Internal | STEP-006 | — | `ingestion` | — | all | — | — | TST-DATA-007 | P1 | DISCOVERY |
| REQ-DATA-008 | Transactional outbox | Internal | STEP-006 | — | `events` | all EVT | — | — | — | TST-DATA-008 | P1 | DISCOVERY |
| REQ-DATA-009 | Idempotent consumers | Internal | STEP-006 | — | `events` | all EVT | — | — | — | TST-DATA-009 | P1 | DISCOVERY |
| REQ-DATA-010 | Read models rebuildable from events | Internal | STEP-006 | — | `events` | all EVT | — | — | — | TST-DATA-010 | P1 | DISCOVERY |
| REQ-COLL-001 | Collaborator cannot select canonical or alter bookings | PER-002 | STEP-015 | `/trips/[id]/collab` | `collaboration` | API-010 | DATA-004 | — | SC-AUTHZ-01 | TST-COLL-001 | P2 | DEFERRED |
| REQ-COLL-002 | Sensitive constraint usable but not exposed | PER-002 | STEP-015 | `/trips/[id]/collab` | `collaboration` | API-010 | DATA-003 | — | SC-SENS-01 | TST-COLL-002 | P2 | DEFERRED |
| REQ-COLL-003 | Owner approval for final selection | PER-001 | STEP-015 | `/trips/[id]/compare` | `scenarios` | API-008 | DATA-010 | — | SC-AUTHZ-01 | TST-COLL-003 | P2 | DEFERRED |
| REQ-COLL-004 | Full proposal/approval audit trail | PER-001 | STEP-015 | `/trips/[id]/collab` | `collaboration` | EVT-004 | DATA-004 | — | SC-AUDIT-01 | TST-COLL-004 | P2 | DEFERRED |
| REQ-BOOK-001 | Deep links preserve itinerary context | PER-001 | STEP-016 | `/trips/[id]/booking` | `affiliate` | API-011 | DATA-013 | — | — | TST-BOOK-001 | P1 | DISCOVERY |
| REQ-BOOK-002 | No payment credentials stored | PER-001 | STEP-016 | `/trips/[id]/booking` | `affiliate` | API-011 | DATA-013 | — | SC-SEG-01 | TST-BOOK-002 | P1 | DISCOVERY |
| REQ-BOOK-003 | Estimated vs confirmed visually distinct | PER-001 | STEP-016 | `/trips/[id]/booking` | `affiliate` | API-011 | DATA-013 | — | — | TST-BOOK-003 | P1 | DISCOVERY |
| REQ-BOOK-004 | Copyable fallback on affiliate failure | PER-001 | STEP-016 | `/trips/[id]/booking` | `affiliate` | API-011 | DATA-013 | — | — | TST-BOOK-004 | P1 | DISCOVERY |
| REQ-BOOK-005 | Booking APIs only after review | PER-001 | STEP-028 | — | `affiliate` | — | DATA-013 | — | SC-GOV-02 | TST-BOOK-005 | P4 | DEFERRED |
| REQ-LIVE-001 | ≥72 h offline usability | PER-001 | STEP-017 | `/trips/[id]/live` | `live` | API-012 | DATA-012 | — | SC-LOC-01 | TST-LIVE-001 | P3 | DEFERRED |
| REQ-LIVE-002 | Idempotent offline queue, visible conflicts | PER-001 | STEP-017 | `/trips/[id]/live` | `live` | API-012 | DATA-012 | — | — | TST-LIVE-002 | P3 | DEFERRED |
| REQ-LIVE-003 | Event→node matching with dedup | PER-001 | STEP-018 | `/trips/[id]/live` | `live` | EVT-005 | DATA-014 | — | — | TST-LIVE-003 | P3 | DEFERRED |
| REQ-LIVE-004 | Unverified reports never auto-change plans | PER-001 | STEP-018 | `/trips/[id]/live` | `live` | EVT-005 | DATA-014 | — | SC-CLAIM-01 | TST-LIVE-004 | P3 | DEFERRED |
| REQ-LIVE-005 | Replan requires explicit acceptance | PER-001 | STEP-019 | `/trips/[id]/live` | `live` | API-013 | DATA-011 | AI-006 | SC-DET-01 | TST-LIVE-005 | P3 | DEFERRED |
| REQ-LIVE-006 | Preserve protected items, report preservation | PER-001 | STEP-019 | `/trips/[id]/live` | `live` | EVT-006 | DATA-011 | AI-006 | — | TST-LIVE-006 | P3 | DEFERRED |
| REQ-ADMIN-001 | Overrides carry reason/period/evidence/actor | PER-004 | STEP-021 | `/admin/destinations` | `evidence` | API-016 | DATA-007 | — | SC-AUDIT-01 | TST-ADMIN-001 | P1 | DISCOVERY |
| REQ-ADMIN-002 | Four-eyes for high-impact overrides | PER-004 | STEP-021 | `/admin/destinations` | `evidence` | API-016 | DATA-007 | — | SC-GOV-02 | TST-ADMIN-002 | P1 | DISCOVERY |
| REQ-ADMIN-003 | Override preview lists invalidated scenarios | PER-004 | STEP-021, STEP-026 | `/admin/destinations` | `knowledge` | API-016 | DATA-010 | — | — | TST-ADMIN-003 | P1 | DISCOVERY |
| REQ-ADMIN-004 | Coverage + provider health dashboards | PER-005 | STEP-021 | `/admin/providers` | `destination` | API-017 | DATA-006 | — | — | TST-ADMIN-004 | P1 | DISCOVERY |
| REQ-ADMIN-005 | Single-trip diagnosis without tenant access | PER-005 | STEP-021, STEP-025 | `/admin/support` | `support` | — | all | — | SC-AUTHZ-02 | TST-ADMIN-005 | P1 | DISCOVERY |
| REQ-OBS-001 | OTel traces with tenant-safe correlation | Internal | STEP-024 | all | all | — | — | — | SC-REDACT-01 | TST-OBS-001 | P1 | DISCOVERY |
| REQ-OBS-002 | End-to-end trip trace | PER-005 | STEP-024 | — | all | — | — | all AI | — | TST-OBS-002 | P1 | DISCOVERY |
| REQ-OBS-003 | Business-quality alerts | PER-005 | STEP-024 | — | `observability` | — | — | AI-003 | — | TST-OBS-003 | P1 | DISCOVERY |
| REQ-OBS-004 | Every alert has a runbook + owner | PER-005 | STEP-024 | — | `observability` | — | — | — | — | TST-OBS-004 | P1 | DISCOVERY |
| REQ-OBS-005 | Typed events with privacy tier | Internal | STEP-022 | `packages/analytics` | `analytics` | — | — | — | SC-SENS-02 | TST-OBS-005 | P2 | DEFERRED |
| REQ-OBS-006 | No results without verified exposure data | Internal | STEP-022 | `/analytics` | `experiments` | — | — | — | — | TST-OBS-006 | P2 | DEFERRED |
| REQ-KG-001 | ≥95% first-party files parsed | Internal | STEP-026 | `/knowledge` | `knowledge` | API-018 | — | — | — | TST-KG-001 | P1 | DISCOVERY |
| REQ-KG-002 | ≥90% public symbols owned | Internal | STEP-026 | `/knowledge` | `knowledge` | API-018 | — | — | SC-GOV-01 | TST-KG-002 | P1 | DISCOVERY |
| REQ-KG-003 | Refresh ≤10 min after merge | Internal | STEP-026 | — | `knowledge` | — | — | — | — | TST-KG-003 | P1 | DISCOVERY |
| REQ-KG-004 | Immutable tagged release graphs | Internal | STEP-026, STEP-027 | — | `knowledge` | — | — | — | — | TST-KG-004 | P1 | DISCOVERY |
| REQ-KG-005 | Provenance on nodes and inferred edges | Internal | STEP-026 | `/knowledge` | `knowledge` | API-018 | — | — | — | TST-KG-005 | P1 | DISCOVERY |
| REQ-KG-006 | Permission-aware traversal | All | STEP-026 | `/knowledge` | `knowledge` | API-018 | all | — | SC-TEN-02 | TST-KG-006 | P1 | DISCOVERY |
| REQ-KG-007 | No secrets/payloads in graph or embeddings | Internal | STEP-026 | — | `knowledge` | — | — | AI-002 | SC-REDACT-01 | TST-KG-007 | P1 | DISCOVERY |
| REQ-KG-008 | No change merges without pre-change record | Internal | STEP-026, all | — | CI | — | — | — | SC-CHANGE-01 | TST-KG-008 | P1 | DISCOVERY |

## 6. Non-functional

| Requirement ID | Scope Step | Test ID | Release | Status |
| --- | --- | --- | --- | --- |
| REQ-NFR-001 … REQ-NFR-014 | STEP-024, STEP-027 and the step owning each surface | TST-NFR-001 … TST-NFR-014 | P1 / P3 / GA per [FUNCTIONAL_REQUIREMENTS](FUNCTIONAL_REQUIREMENTS.md) §REQ-NFR | DISCOVERY |

---

## 7. Reverse trace — every step has requirements

| Step | Requirements | Step | Requirements |
| --- | --- | --- | --- |
| STEP-001 | REQ-PLAT-001…004 | STEP-015 | REQ-COLL-001…004, REQ-TRIP-006, REQ-SEC-008 |
| STEP-002 | REQ-SEC-001…004, REQ-PLAT-012 | STEP-016 | REQ-BOOK-001…004, REQ-SEC-010, REQ-EVID-003 |
| STEP-003 | REQ-A11Y-001, 004 | STEP-017 | REQ-LIVE-001, 002, REQ-PRIV-008 |
| STEP-004 | REQ-PLAT-005…008 | STEP-018 | REQ-LIVE-003, 004 |
| STEP-005 | REQ-DATA-001…006, REQ-SEC-005 | STEP-019 | REQ-LIVE-005, 006, REQ-CONS-011 |
| STEP-006 | REQ-DATA-007…010, REQ-SEC-001 | STEP-020 | REQ-TRIP-008, REQ-PRIV-003 |
| STEP-007 | REQ-TRIP-001, 002, REQ-EVID-006 | STEP-021 | REQ-ADMIN-001…005, REQ-PLAT-012 |
| STEP-008 | REQ-PRIV-001…004, REQ-TRIP-003…005 | STEP-022 | REQ-OBS-005, 006, REQ-PRIV-004 |
| STEP-009 | REQ-CONS-001, 002, REQ-AI-001, 002, 005 | STEP-023 | REQ-SEC-006, 007, REQ-PRIV-* |
| STEP-010 | REQ-EVID-001…006, REQ-AI-003, 004, 009 | STEP-024 | REQ-OBS-001…004, REQ-AI-006 |
| STEP-011 | REQ-CONS-003 | STEP-025 | REQ-PRIV-005…007, REQ-TRIP-007, REQ-ADMIN-005 |
| STEP-012 | REQ-CONS-004…008, REQ-A11Y-006 | STEP-026 | REQ-KG-001…008 |
| STEP-013 | REQ-CONS-009, REQ-EVID-004, REQ-A11Y-002, 003, REQ-AI-010 | STEP-027 | REQ-PLAT-009…011, REQ-SEC-009 |
| STEP-014 | REQ-CONS-010, 011, REQ-A11Y-005 | STEP-028 | REQ-TRIP-009, REQ-BOOK-005 |

**Validation result:** 28/28 steps carry at least one requirement; 130/130 requirements carry at least one step, one test ID and a release disposition. No orphans.
