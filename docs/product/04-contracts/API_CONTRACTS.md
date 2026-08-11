# JourneyLab — API Contracts

| Field | Value |
| --- | --- |
| Owner | Product Architect (Deepesh Kumar Gupta) |
| Status | **All operations `PROPOSED`** — no OpenAPI file exists; nothing implemented |
| Upstream source | Blueprint §11 (API and event contracts) |
| Authority | When `contracts/openapi.yaml` exists it becomes authoritative for schemas. This document explains contracts and **must not duplicate schema definitions** (`ADR-001`) |
| Last reviewed | 2026-08-05 |

Navigation: [Event contracts](EVENT_CONTRACTS.md) · [Error model](ERROR_MODEL.md) · [Authorization matrix](AUTHORIZATION_MATRIX.md) · [Change policy](CONTRACT_CHANGE_POLICY.md) · [00-START-HERE](../00-START-HERE.md)

---

## 1. Global conventions

| Convention | Rule |
| --- | --- |
| Style | REST, contract-first, OpenAPI 3.1. URI nouns; commands as `:verb` suffixes (`/scenarios:generate`) |
| Versioning | Explicit major version in the path (`/v1/`). Breaking change ⇒ new major version |
| Authentication | OIDC/OAuth 2.1 bearer tokens, short-lived. Passkeys supported at the identity provider |
| Authorization | Server-side per operation **and** per resource. Roles in [AUTHORIZATION_MATRIX](AUTHORIZATION_MATRIX.md) |
| Tenant context | Derived from the token, never from a client-supplied header or body field |
| Media types | `application/json`; `text/event-stream` for progress; `application/problem+json` for errors |
| Errors | RFC 9457 problem details with a stable `type` URI and deterministic error codes |
| Idempotency | `Idempotency-Key` **required** on every state-changing command; replay returns the original result |
| Pagination | Cursor-based (`cursor`, `limit`); offset pagination is not supported |
| Filtering/sorting | Explicit allowlisted fields only |
| Concurrency | `ETag` on mutable resources; `If-Match` required on replace and edit operations; mismatch ⇒ `409` |
| Correlation | `X-Correlation-Id` accepted and echoed; W3C trace context propagated |
| Rate limits | Published per operation class; `429` with `Retry-After` |
| Time & locale | RFC 3339 UTC timestamps with explicit IANA time zone where local time matters; ISO 4217 currency with minor units as integers |
| Numeric precision | Money as integer minor units — **never floating point** |
| Deprecation | `Deprecation` and `Sunset` headers; dual-run window per [CONTRACT_CHANGE_POLICY](CONTRACT_CHANGE_POLICY.md) |
| Webhooks | Signed, event ID + creation time, replayable, idempotent receivers |
| Generated clients | Build artifacts in `packages/contracts/src/generated/`; **never hand-edited** (`REQ-PLAT-007`) |

---

## 2. Operation register

Each operation carries the full contract fields required by the standard. All are `PROPOSED`.

### API-001 — `POST /v1/trips`
| Field | Value |
| --- | --- |
| Purpose | Create a trip and initial planning context |
| Step / persona | STEP-008 / PER-001 |
| Authorization | Authenticated user or valid guest session; creates ownership |
| Idempotency | `Idempotency-Key` required; replay returns the original trip |
| Request | `{ origin, destination_region, date_range, party, currency, locale }` |
| Responses | `201` trip resource with ETag · `400` validation · `409` idempotency conflict · `422` out of coverage |
| Errors | `coverage.unsupported_region`, `coverage.unsupported_dates`, `validation.invalid_party` |
| Rate limit | Per user, low |
| Audit | `trip.created` |
| Events | — |
| Data | Writes DATA-004; reads DATA-006 coverage |
| Sensitivity | PII |
| Tests | TST-TRIP-002/003/005 |
| Version | v1 `PROPOSED` |

### API-002 — `GET /v1/trips/{tripId}`
Read canonical trip, permissions and current version. Auth: trip member. Returns ETag. `403` non-member, `404` unknown (indistinguishable from unauthorized to prevent enumeration). Reads DATA-004/010. Tests: TST-SEC-002.

### API-003 — `PUT /v1/trips/{tripId}/brief`
| Field | Value |
| --- | --- |
| Purpose | Replace the validated structured brief |
| Step / persona | STEP-009 / PER-001, PER-002 (editor) |
| Authorization | owner/editor |
| Concurrency | **`If-Match` required** — brief version ETag |
| Request | Typed constraint document: hard/soft/inferred/unresolved arrays with units, priority, source |
| Responses | `200` new brief version · `409` version conflict · `422` unsatisfiable constraints with a minimal conflict set |
| Errors | `constraint.unsatisfiable`, `constraint.ambiguous_requires_clarification`, `concurrency.version_mismatch` |
| Audit | `brief.confirmed` |
| Events | EVT-001 |
| Data | Writes DATA-005 (immutable version) |
| Sensitivity | PII + sensitive (accessibility) |
| Tests | TST-CONS-001/002, TST-TRIP-004 |

### API-004 — `POST /v1/trips/{tripId}/evidence-packs`
Start evidence assembly; returns a **job handle within 500 ms**. Auth: owner/editor. `202` `{job_id, status, events_url}`. Emits EVT-002 on completion. Writes DATA-007/008. Errors: `coverage.provider_degraded`, `evidence.insufficient_coverage`. Tests: TST-EVID-001/005/006.

### API-005 — `POST /v1/trips/{tripId}/scenarios:generate`
| Field | Value |
| --- | --- |
| Purpose | Generate a diverse feasible scenario set |
| Step / persona | STEP-012 / PER-001 |
| Authorization | owner/editor |
| Idempotency | Required; `If-Match` on brief version |
| Request | `{ objectives[], scenario_count, evidence_pack_id, random_seed }` |
| Responses | `202` job handle · `409` brief changed · `422` infeasible with minimal conflict set |
| Errors | `solver.infeasible`, `solver.timeout`, `evidence.pack_stale` |
| Events | EVT-003 |
| Data | Writes DATA-010/011; reads DATA-008/009 |
| Tests | TST-CONS-004…008 |

**Example**

```http
POST /v1/trips/trp_01/scenarios:generate
Idempotency-Key: 8f2c...
If-Match: "brief-v3"
Content-Type: application/json

{ "objectives": ["balanced","low_cost","weather_resilient"],
  "scenario_count": 3, "evidence_pack_id": "ep_09", "random_seed": 4172 }
```
```http
202 Accepted
{ "job_id": "job_18", "status": "queued", "events_url": "/v1/jobs/job_18/events" }
```

### API-006 — `GET /v1/trips/{tripId}/scenarios`
List scenario summaries and comparison metrics. Auth: trip member. Cursor pagination. Reads DATA-010. Tests: TST-CONS-007.

### API-007 — `GET /v1/scenarios/{scenarioId}`
Read complete itinerary, evidence references and score components. Auth: trip member. **Every volatile value carries source, observed time, effective window and confidence** (`REQ-EVID-001`). Reads DATA-011/007. Tests: TST-EVID-001/004, TST-A11Y-002.

### API-008 — `POST /v1/scenarios/{scenarioId}:select`
Set the canonical plan after validation. Auth: **owner only**. Idempotent. `409` if another selection won; `422` if the scenario is stale or no longer feasible. Emits EVT-004. Tests: TST-COLL-003.

### API-009 — `POST /v1/scenarios/{scenarioId}/edits` *(Phase 2)*
Create a new version from a typed what-if edit. Auth: owner/editor. `If-Match` required. Request declares edit type and impact preview token. Protected items rejected with `itinerary.item_protected`. Tests: TST-CONS-010/011.

### API-010 — `POST /v1/trips/{tripId}/invitations` *(Phase 2)*
Invite a collaborator with scoped, **expiring** permissions. Auth: owner. Revocation supported. Emits EVT-004 on proposal activity. Tests: TST-TRIP-006, TST-COLL-001/002, TST-SEC-008.

### API-011 — `POST /v1/trips/{tripId}/booking-handoffs`
Create a provider deep link and attribution record. Auth: owner/editor. **Never accepts or returns payment credentials.** Response distinguishes `estimated` from `confirmed`. Errors: `affiliate.unavailable` (client shows copyable details). Writes DATA-013 (segregated). Tests: TST-BOOK-001…004, TST-SEC-010.

### API-012 — `POST /v1/trips/{tripId}:activate` *(Phase 3)*
Activate live monitoring and produce the offline manifest. Auth: owner. Returns offline pack manifest and readiness indicator. Tests: TST-LIVE-001/002.

### API-013 — `POST /v1/impacts/{impactId}/repairs:generate` *(Phase 3)*
Generate protected partial-replan alternatives. Auth: owner/editor. Response includes cost/time/effort deltas and preserved-plan percentage. **Acceptance is a separate explicit call** — generation never mutates the canonical plan. Emits EVT-006 on acceptance. Tests: TST-LIVE-005/006.

### API-014 — `POST /v1/trips/{tripId}/feedback` *(Phase 3)*
Record explicit outcome and preference feedback. Auth: trip member. Consent scope required; absence of feedback never creates a negative label. Writes DATA-015. Tests: TST-TRIP-008.

### API-015 — `POST /v1/privacy/requests`
Export, correction, consent withdrawal or deletion. Auth: data subject or authorized privacy operator. Returns a tracked request with completion confirmation. Failure enters a monitored retry queue. Tests: TST-PRIV-005/006/007.

### API-016 — `POST /v1/admin/evidence-overrides`
Curator fact override. Auth: curator; **four-eyes approval required for high-impact** overrides. Request requires reason, effective period and evidence. Response includes the impact preview of affected scenarios. Tests: TST-ADMIN-001/002/003.

### API-017 — `GET /v1/coverage`
Public. Returns supported regions, date bounds, freshness summary, provider health and documented limitations. **No authentication.** Must never expose provider identities or quota details. Tests: TST-TRIP-001/002, TST-EVID-006.

### API-018 — `GET /v1/jobs/{jobId}/events`
SSE stream of progress, warnings and terminal result. Auth: job owner. Supports cancellation via `DELETE /v1/jobs/{jobId}`. Heartbeats required so clients can distinguish a slow job from a dead connection. Tests: TST-A11Y-006, TST-NFR-003.

*(Knowledge-graph query API is also exposed as `API-018`-adjacent internal routes; see [GRAPH_QUERY_PLAYBOOK](../05-knowledge-graph/GRAPH_QUERY_PLAYBOOK.md). It is internal-only and permission-filtered.)*

---

## 3. Cross-cutting behaviors

| Behavior | Rule |
| --- | --- |
| Long operations | Job handle within 500 ms; progress via SSE; cancellable (`REQ-NFR-003`) |
| Not-found vs forbidden | Return the same status for unauthorized and unknown resources to prevent enumeration |
| Partial success | Never silently partial — a partial evidence pack returns a coverage report identifying what is missing |
| Estimates | Any price or availability field carries an explicit `is_estimate` flag; the API cannot express "confirmed" without provider confirmation (`REQ-EVID-003`) |
| Stale data | Responses carry per-field `observed_at` and staleness markers rather than a single response-level timestamp |
| Model output | No endpoint accepts model output as authoritative input; all mutations pass deterministic validation (`REQ-AI-001`) |

---

## 4. Contract status

| Artifact | Expected path | Status |
| --- | --- | --- |
| OpenAPI 3.1 | `contracts/openapi.yaml` | **Does not exist** |
| AsyncAPI | `contracts/asyncapi.yaml` | **Does not exist** |
| JSON Schema | `contracts/jsonschema/` | **Does not exist** |
| Generated TS client | `packages/contracts/src/generated/` | **Does not exist** |
| Contract tests | `tests/contracts/` | **Does not exist** |

Created in `STEP-004`. Until then every operation above is a specification, not an implementation, and must not be cited as an available API.
