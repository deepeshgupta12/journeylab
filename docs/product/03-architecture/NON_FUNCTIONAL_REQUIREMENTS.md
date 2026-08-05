# JourneyLab — Non-Functional Requirements and SLOs

| Field | Value |
| --- | --- |
| Owner | Product Architect + SRE (unassigned — `BLK-001`) |
| Status | `DISCOVERY` — targets defined; none measured |
| Upstream source | Blueprint §15 (NFRs and SLOs) |
| Last reviewed | 2026-08-05 |

Navigation: [Technical architecture](TECHNICAL_ARCHITECTURE.md) · [Observability](OBSERVABILITY_ARCHITECTURE.md) · [Performance testing](../06-quality/PERFORMANCE_AND_RESILIENCE_TESTING.md) · [00-START-HERE](../00-START-HERE.md)

---

## 1. Service level objectives

| ID | Dimension | Target | Measurement | Applies from |
| --- | --- | --- | --- | --- |
| REQ-NFR-001 | Availability | 99.9% monthly for customer-facing APIs | Successful requests / total, excluding client errors | GA |
| REQ-NFR-002 | Interactive read latency | p95 ≤ 400 ms **excluding third-party provider time** | Server-side histogram per route template | Phase 1 |
| REQ-NFR-003 | Long operation acknowledgement | Job handle returned within 500 ms; progress streamed | API timing + SSE first-byte | Phase 1 |
| REQ-NFR-004 | Scenario generation | p95 ≤ 45 s for a seven-day covered-region trip; cancellable | Job duration histogram | Phase 1 |
| REQ-NFR-005 | Event delivery | At-least-once with idempotent consumers; dead-letter handling | Outbox lag, DLQ depth | Phase 1 |
| REQ-NFR-010 | Offline usability | Itinerary + critical evidence usable ≥ 72 h without network | Device test suite | Phase 3 |
| REQ-NFR-011 | Freshness | Closure/disruption facts meet provider-specific minute-level SLOs | Age-at-use distribution per field | Phase 3 |
| REQ-NFR-012 | Geospatial accuracy | Coordinates, time zones, routing profiles validated against golden sets; **no itinerary item with an unresolved location** | Golden-set validation in CI | Phase 1 |
| REQ-NFR-014 | Unit economics | Cost per saved feasible trip within budget with quality/latency/diversity fixed | Cost per trip from traces | Phase 1 |

**Error budget:** 99.9% monthly ⇒ ~43 minutes of downtime. Budget burn > 50% in a rolling week freezes feature rollout until the burn rate recovers.

**Explicit exclusion:** third-party provider latency is excluded from `REQ-NFR-002` but **tracked separately** — a provider that is reliably slow is a product problem even if it is not an API-latency problem.

---

## 2. Scalability and reliability

| Dimension | Requirement |
| --- | --- |
| Statelessness | All request-serving services horizontally scalable and stateless |
| Partitioning | High-volume events partitioned by tenant and domain key (`trip_id`) |
| Back-pressure | Mandatory; queue saturation degrades gracefully rather than dropping silently |
| Idempotency | All commands and consumers idempotent |
| Replay | Events replayable from checkpoints; read models rebuildable |
| Retries | Capped exponential backoff with jitter; dead-letter after the cap |
| Isolation | Solver and ML workers have explicit CPU/memory budgets so one job cannot starve the pool |
| Graceful degradation | Provider, model or map failure reduces capability with disclosure; it never fabricates |

---

## 3. Security, privacy, accessibility, i18n

| ID | Requirement |
| --- | --- |
| REQ-NFR-006 | TLS in transit; encryption at rest with managed keys; tenant-managed keys at enterprise tier (Phase 4) |
| REQ-SEC-* | OIDC/OAuth 2.1, short-lived tokens, least privilege, tenant isolation, secret rotation, supply-chain controls, audit trails |
| REQ-PRIV-* | Purpose limitation, minimisation, configurable retention, export/deletion, PII classification, regional controls |
| Accessibility | WCAG 2.2 AA; keyboard-complete; SR semantics; non-colour cues; reduced motion; minimum target sizes; accessible data visualisations |
| REQ-NFR-007 | UTF-8 end to end, ICU messages, locale-aware dates/numbers/currency, time-zone and DST correctness |
| REQ-NFR-008 | Right-to-left readiness (implementation Phase 2) |

**Time-zone correctness is a functional risk, not a formatting concern.** An itinerary crossing a DST transition or a time-zone boundary must compute travel and opening-hour feasibility in the correct local time, or the plan is wrong.

---

## 4. Observability and maintainability

| Dimension | Requirement |
| --- | --- |
| Tracing | OTel traces, metrics and structured logs with tenant-safe correlation IDs |
| Coverage | Model, retrieval, tool, queue and data-pipeline telemetry |
| Business SLIs | Citation correctness, hard-constraint violations, evidence freshness, solver saturation |
| Maintainability | Contract-first APIs, strict typing, ADRs, enforced dependency boundaries, automated documentation, incrementally refreshed code graph |
| Documentation currency | Docs current at the release commit (GA gate) |

---

## 5. Performance budgets (frontend)

| ID | Metric | Budget |
| --- | --- | --- |
| REQ-NFR-013 | LCP (public routes) | ≤ 2.5 s, mid-tier mobile on 4G |
| REQ-NFR-013 | INP | ≤ 200 ms, including during scenario streaming |
| REQ-NFR-013 | CLS | ≤ 0.1 |
| REQ-NFR-013 | Bundle | Map and chart libraries lazy-loaded; budget fixed at implementation |

---

## 6. Capacity assumptions

**All figures below are placeholders**, not forecasts. No user or volume projection exists (`ASM-002`). They are recorded so load tests have a starting shape and must be replaced with real projections before Phase 1 exit.

| Dimension | Placeholder | Basis |
| --- | --- | --- |
| Concurrent generations | To be determined | Drives solver worker pool sizing |
| Evidence pack size | To be determined | Drives storage and pack build latency |
| Trips per active user | To be determined | Drives retention and storage growth |
| Provider call volume | To be determined | Drives quota negotiation (`EXT-001`) |

Publishing invented capacity numbers would produce a false infrastructure plan; the gap is recorded instead.

---

## 7. Conflicts between NFRs

Real tension exists and is resolved by explicit precedence, not by wishful thinking:

| Tension | Resolution |
| --- | --- |
| Scenario latency (`REQ-NFR-004`) vs. scenario quality/diversity | **Quality wins.** Reduce the number of scenarios or extend the documented budget; never ship a scenario with unverified constraints |
| Cost (`REQ-NFR-014`) vs. citation correctness | **Correctness wins.** Guardrail: quality thresholds stay fixed during cost optimisation |
| Freshness (`REQ-NFR-011`) vs. provider quota | Degrade to marked-stale data and block options requiring fresh facts; never present stale data as current |
| Offline availability vs. privacy | Sensitive documents require explicit opt-in and device protection |
| Availability vs. tenant isolation | **Isolation wins.** A confirmed cross-tenant exposure halts release |
