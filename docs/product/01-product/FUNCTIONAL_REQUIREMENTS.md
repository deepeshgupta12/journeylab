# JourneyLab — Functional Requirements

| Field | Value |
| --- | --- |
| Owner | Product Lead + Product Architect (Deepesh Kumar Gupta) |
| Status | `DISCOVERY` — requirements derived from blueprint; none accepted by a named owner |
| Upstream source | Blueprint §7 (Functional requirements), §8 (Frontend), §9 (Backend), §13 (AI/ML), §14 (Security), §15 (NFR) |
| Requirement count | **130** across 16 domains |
| Last reviewed | 2026-08-05 |

Navigation: [Scope](PRODUCT_SCOPE.md) · [Traceability](REQUIREMENTS_TRACEABILITY.md) · [Acceptance tests](../06-quality/ACCEPTANCE_TEST_CATALOG.md) · [NFRs](../03-architecture/NON_FUNCTIONAL_REQUIREMENTS.md) · [00-START-HERE](../00-START-HERE.md)

---

## How to read this document

- Every requirement is **atomic and testable**. A requirement that cannot fail a test is not a requirement — it is a principle, and belongs in [PRODUCT_CHARTER](PRODUCT_CHARTER.md).
- `Release` uses the phase boundary from [PRODUCT_SCOPE](PRODUCT_SCOPE.md) §3. `P1` = target MVP.
- `Test` links to the acceptance test ID in [ACCEPTANCE_TEST_CATALOG](../06-quality/ACCEPTANCE_TEST_CATALOG.md).
- Requirements phrased with **must not** are prohibitions and are tested by negative/adversarial cases, not by absence of a positive case.

**Classification key:** `[C]` confirmed product decision · `[S]` source-supported · `[A]` assumption requiring validation · `[P]` proposal requiring approval.

---

## REQ-PLAT — Platform, contracts and release

| ID | Requirement | Steps | Test | Release | Class |
| --- | --- | --- | --- | --- | --- |
| REQ-PLAT-001 | A new engineer must run lint, type-check, unit tests and the application locally using only commands documented in `README.md`. | STEP-001 | TST-PLAT-001 | P1 | [C] |
| REQ-PLAT-002 | All dependencies must be pinned by lock file; CI must reject a change that alters a lock file without an accompanying manifest change. | STEP-001 | TST-PLAT-002 | P1 | [C] |
| REQ-PLAT-003 | Every directory in the repository must resolve to an owner via `CODEOWNERS`; CI must reject unowned paths. | STEP-001 | TST-PLAT-003 | P1 | [C] |
| REQ-PLAT-004 | The repository must contain an architecture decision record for every accepted structural decision, numbered `ADR-NNN`. | STEP-001 | TST-PLAT-004 | P1 | [C] |
| REQ-PLAT-005 | All external and command APIs must be defined in OpenAPI 3.1 stored beside the code; runtime behavior must be generated from or validated against it. | STEP-004 | TST-PLAT-005 | P1 | [C] |
| REQ-PLAT-006 | All domain events must be defined in AsyncAPI with an explicit delivery guarantee per event. | STEP-004 | TST-PLAT-006 | P1 | [C] |
| REQ-PLAT-007 | Generated clients must be build artifacts; CI must fail if a generated client file is modified by hand. | STEP-004 | TST-PLAT-007 | P1 | [C] |
| REQ-PLAT-008 | A backward-incompatible contract change must fail CI unless it carries a new major version, migration guide, consumer notice and deprecation date. | STEP-004, STEP-027 | TST-PLAT-008 | P1 | [C] |
| REQ-PLAT-009 | A release must be blocked by regression in contracts, security, accessibility, data quality, model performance or business guardrails. | STEP-027 | TST-PLAT-009 | P1 | [C] |
| REQ-PLAT-010 | Every deployable unit must have an automated rollback path exercised in staging before it may ship to production. | STEP-027 | TST-PLAT-010 | P1 | [C] |
| REQ-PLAT-011 | Database migrations must follow expand/migrate/contract and remain backward compatible for the full rollout window. | STEP-027 | TST-PLAT-011 | P1 | [C] |
| REQ-PLAT-012 | Feature, model, provider and cohort rollout must be controllable without a code deployment. | STEP-021, STEP-027 | TST-PLAT-012 | P1 | [C] |

## REQ-SEC — Security

| ID | Requirement | Steps | Test | Release | Class |
| --- | --- | --- | --- | --- | --- |
| REQ-SEC-001 | Every persisted row, emitted event and cache key must carry an organization/tenant identifier. | STEP-002, STEP-006 | TST-SEC-001 | P1 | [C] |
| REQ-SEC-002 | A request authenticated for tenant A must never read, write or enumerate tenant B data, including via cache, job, export or graph traversal. | STEP-002, STEP-026 | TST-SEC-002 | P1 | [C] |
| REQ-SEC-003 | People must authenticate via OIDC with passkey support; service identities must use workload identity, never static long-lived keys. | STEP-002 | TST-SEC-003 | P1 | [C] |
| REQ-SEC-004 | Authorization must be enforced server-side on every operation; client-side role checks are presentation only and must never be the sole control. | STEP-002 | TST-SEC-004 | P1 | [C] |
| REQ-SEC-005 | Every external connector and model tool must apply SSRF protection, an egress allowlist, schema validation, a rate limit and a timeout. | STEP-005, STEP-009 | TST-SEC-005 | P1 | [C] |
| REQ-SEC-006 | Retrieved text, documents, provider payloads and MCP tool descriptions must be treated as untrusted data and must never be executed as instructions. | STEP-010, STEP-009 | TST-SEC-006 | P1 | [C] |
| REQ-SEC-007 | Security and business audit events must be stored immutably and separately from application logs, with secrets and sensitive payloads redacted. | STEP-023, STEP-024 | TST-SEC-007 | P1 | [C] |
| REQ-SEC-008 | Trip sharing must default to no location sharing, use expiring invitations, log views and support immediate revocation. | STEP-015, STEP-017 | TST-SEC-008 | P2 | [C] |
| REQ-SEC-009 | Builds must produce an SBOM and signed artifacts; unsigned artifacts must not deploy. | STEP-027 | TST-SEC-009 | P1 | [C] |
| REQ-SEC-010 | Booking references and uploaded travel documents must be stored separately from the planning graph with narrower access and shorter retention. | STEP-016, STEP-023 | TST-SEC-010 | P1 | [C] |

## REQ-PRIV — Privacy and data lifecycle

| ID | Requirement | Steps | Test | Release | Class |
| --- | --- | --- | --- | --- | --- |
| REQ-PRIV-001 | A traveler must be able to complete planning as a guest without providing an email address or account. | STEP-008 | TST-PRIV-001 | P1 | [C] |
| REQ-PRIV-002 | Consent must be recorded per purpose; withdrawing one purpose must not withdraw unrelated purposes or delete unrelated data. | STEP-008 | TST-PRIV-002 | P1 | [C] |
| REQ-PRIV-003 | The system must not infer mobility, health, age or accessibility attributes from behavioral signals; such attributes may only be set by explicit user declaration. | STEP-008, STEP-020 | TST-PRIV-003 | P1 | [C] |
| REQ-PRIV-004 | Accessibility, age and precise-location data must never be used for advertising or unrelated personalization. | STEP-008, STEP-022 | TST-PRIV-004 | P1 | [C] |
| REQ-PRIV-005 | A user must be able to export all their data in a machine-readable format and receive confirmation of completion. | STEP-025 | TST-PRIV-005 | P1 | [C] |
| REQ-PRIV-006 | Deletion must propagate to transactional rows, object storage, vector chunks, graph nodes, caches, exports and notification/offline tokens, proven by automated test. | STEP-025, STEP-026 | TST-PRIV-006 | P1 | [C] |
| REQ-PRIV-007 | A deletion failure must enter a monitored retry queue visible to the privacy owner and must not be silently dropped. | STEP-025 | TST-PRIV-007 | P1 | [C] |
| REQ-PRIV-008 | Precise location must be processed ephemerally and must not be persisted unless the traveler explicitly saves it. | STEP-017, STEP-019 | TST-PRIV-008 | P3 | [C] |

## REQ-A11Y — Accessibility

| ID | Requirement | Steps | Test | Release | Class |
| --- | --- | --- | --- | --- | --- |
| REQ-A11Y-001 | Every core task must be completable using keyboard only and using a screen reader, to WCAG 2.2 AA. | STEP-003 + all UI steps | TST-A11Y-001 | P1 | [C] |
| REQ-A11Y-002 | Every visualization must have an equivalent accessible table or list and a downloadable CSV. | STEP-013 | TST-A11Y-002 | P1 | [C] |
| REQ-A11Y-003 | No core action may require the map; all MVP tasks must complete with map rendering disabled. | STEP-013, STEP-017 | TST-A11Y-003 | P1 | [C] |
| REQ-A11Y-004 | Status must never be conveyed by colour alone. | STEP-003 | TST-A11Y-004 | P1 | [C] |
| REQ-A11Y-005 | Drag-and-drop must have a non-pointer alternative; interactive targets must meet minimum size. | STEP-014 | TST-A11Y-005 | P2 | [C] |
| REQ-A11Y-006 | Streamed updates must restore focus predictably and announce scenario changes to assistive technology. | STEP-012, STEP-013 | TST-A11Y-006 | P1 | [C] |

## REQ-TRIP — Trip and profile management

| ID | Requirement | Steps | Test | Release | Class |
| --- | --- | --- | --- | --- | --- |
| REQ-TRIP-001 | A visitor must see supported regions, data freshness, limitations and the privacy summary before creating an account. | STEP-007 | TST-TRIP-001 | P1 | [C] |
| REQ-TRIP-002 | A trip request outside current coverage must be refused with an explanation and must not produce a partial simulation. | STEP-007 | TST-TRIP-002 | P1 | [C] |
| REQ-TRIP-003 | Users must be able to create, duplicate, archive, export and delete a trip. | STEP-008, STEP-025 | TST-TRIP-003 | P1 | [C] |
| REQ-TRIP-004 | Traveler constraints must be versioned, and the system must show which trips use each version. | STEP-008, STEP-009 | TST-TRIP-004 | P1 | [C] |
| REQ-TRIP-005 | A guest session must migrate to an account without duplicating trips. | STEP-008 | TST-TRIP-005 | P1 | [C] |
| REQ-TRIP-006 | Collaborator invitations must be role-scoped, expiring and revocable. | STEP-015 | TST-TRIP-006 | P2 | [C] |
| REQ-TRIP-007 | Trip data retention must be user-configurable within policy bounds. | STEP-025 | TST-TRIP-007 | P1 | [C] |
| REQ-TRIP-008 | Preference-profile changes must be shown to the user, be attributable to a specific signal, and be reversible. | STEP-020 | TST-TRIP-008 | P3 | [C] |
| REQ-TRIP-009 | An advisor must operate in an organization workspace with delegated, audited trip access and must not silently edit a client-approved canonical plan. | STEP-028 | TST-TRIP-009 | P4 | [C] |

## REQ-CONS — Constraint and scenario engine

| ID | Requirement | Steps | Test | Release | Class |
| --- | --- | --- | --- | --- | --- |
| REQ-CONS-001 | Constraints must be represented in four distinct classes — hard, soft, inferred, unresolved — and never silently promoted between classes. | STEP-009 | TST-CONS-001 | P1 | [C] |
| REQ-CONS-002 | The system must ask only blocking clarification questions and must display the resulting interpretation for user confirmation before solving. | STEP-009 | TST-CONS-002 | P1 | [C] |
| REQ-CONS-003 | Hard filters must be applied before ranking; an option violating a hard constraint must never reach the solver or the user. | STEP-011 | TST-CONS-003 | P1 | [C] |
| REQ-CONS-004 | A generated scenario must contain zero hard-constraint violations. | STEP-012 | TST-CONS-004 | P1 | [C] |
| REQ-CONS-005 | When no feasible solution exists, the system must return a minimal conflict set and suggested relaxations, and must not present an infeasible plan as complete. | STEP-012 | TST-CONS-005 | P1 | [C] |
| REQ-CONS-006 | A scenario run must be reproducible from stored inputs, solver configuration, model versions and random seed. | STEP-012 | TST-CONS-006 | P1 | [C] |
| REQ-CONS-007 | A scenario set must contain at least three materially different scenarios with deterministic objective labels and published score definitions. | STEP-012 | TST-CONS-007 | P1 | [C] |
| REQ-CONS-008 | Stochastic simulation must report confidence intervals and fragility, never a single point estimate presented as certain. | STEP-012 | TST-CONS-008 | P1 | [C] |
| REQ-CONS-009 | Comparison must highlight only material differences and must show confidence ranges. | STEP-013 | TST-CONS-009 | P1 | [C] |
| REQ-CONS-010 | An edit must recompute only affected segments; no unaffected day may change without an explanation. | STEP-014 | TST-CONS-010 | P2 | [C] |
| REQ-CONS-011 | Booked or user-protected elements must be locked during edits and replanning. | STEP-014, STEP-019 | TST-CONS-011 | P2 | [C] |

## REQ-EVID — Evidence and trust

| ID | Requirement | Steps | Test | Release | Class |
| --- | --- | --- | --- | --- | --- |
| REQ-EVID-001 | Every volatile fact displayed must carry source, observed time, effective time and confidence. | STEP-010, STEP-013 | TST-EVID-001 | P1 | [C] |
| REQ-EVID-002 | Conflicting evidence must remain visible with a source hierarchy and must not be averaged or silently resolved. | STEP-010 | TST-EVID-002 | P1 | [C] |
| REQ-EVID-003 | An estimate must never be rendered as a confirmed price or confirmed availability. | STEP-010, STEP-016 | TST-EVID-003 | P1 | [C] |
| REQ-EVID-004 | Every volatile planning claim in generated prose must link to an evidence fact and a source span. | STEP-013 | TST-EVID-004 | P1 | [C] |
| REQ-EVID-005 | A fact outside its freshness threshold must be marked stale and must lower scenario confidence or block the affected option. | STEP-010 | TST-EVID-005 | P1 | [C] |
| REQ-EVID-006 | Provider degradation must be surfaced to the user rather than masked by cached data presented as current. | STEP-007, STEP-010 | TST-EVID-006 | P1 | [C] |

## REQ-AI — AI, LLM and RAG behavior

| ID | Requirement | Steps | Test | Release | Class |
| --- | --- | --- | --- | --- | --- |
| REQ-AI-001 | Model output must never mutate trip, scenario, booking or consent state without deterministic command validation and user authorization. | STEP-009, STEP-013 | TST-AI-001 | P1 | [C] |
| REQ-AI-002 | All LLM calls must use structured JSON Schema output and must fail closed on schema violation. | STEP-009 | TST-AI-002 | P1 | [C] |
| REQ-AI-003 | Retrieval must apply tenant, permission, geospatial and temporal filters before ranking. | STEP-010 | TST-AI-003 | P1 | [C] |
| REQ-AI-004 | When evidence coverage or agreement is low, the system must return an uncertainty statement or a blocking question and must not fill gaps from model memory. | STEP-010 | TST-AI-004 | P1 | [C] |
| REQ-AI-005 | Only allowlisted read tools may be exposed to the planning model; booking write actions are outside the MVP. | STEP-009, STEP-016 | TST-AI-005 | P1 | [C] |
| REQ-AI-006 | Every AI request must record prompt version, model version, retrieval configuration, source pack, tool results, cost and latency in one trace with sensitive fields redacted. | STEP-009, STEP-024 | TST-AI-006 | P1 | [C] |
| REQ-AI-007 | Every AI capability must have a documented non-AI fallback that keeps the core task completable. | All AI steps | TST-AI-007 | P1 | [C] |
| REQ-AI-008 | Each AI capability must enforce a per-request cost and latency budget and degrade rather than exceed it. | STEP-009, STEP-010 | TST-AI-008 | P1 | [C] |
| REQ-AI-009 | Prompt-injection detection must run on retrieved content and tool descriptions before they enter a model context. | STEP-010 | TST-AI-009 | P1 | [C] |
| REQ-AI-010 | Explanations must not assert visa, health, legal or safety guarantees. | STEP-013 | TST-AI-010 | P1 | [C] |

## REQ-DATA — Ingestion and canonical data

| ID | Requirement | Steps | Test | Release | Class |
| --- | --- | --- | --- | --- | --- |
| REQ-DATA-001 | Every provider source must have documented licence terms, permitted cache duration and attribution obligations before ingestion is enabled. | STEP-005 | TST-DATA-001 | P1 | [C] |
| REQ-DATA-002 | Every connector must implement credential rotation, rate limiting, checkpointing, schema validation and backfill. | STEP-005 | TST-DATA-002 | P1 | [C] |
| REQ-DATA-003 | Provider failure must trip a circuit breaker and must not silently degrade to unmarked stale data. | STEP-005 | TST-DATA-003 | P1 | [C] |
| REQ-DATA-004 | Place entities must be deduplicated into a canonical entity with a provider identifier graph. | STEP-005 | TST-DATA-004 | P1 | [C] |
| REQ-DATA-005 | Freshness policy must be field-specific; hours and disruptions must expire faster than descriptive content. | STEP-005, STEP-010 | TST-DATA-005 | P1 | [C] |
| REQ-DATA-006 | Raw provider payloads must be encrypted and retained only as long as reconciliation and dispute handling require. | STEP-005, STEP-025 | TST-DATA-006 | P1 | [C] |
| REQ-DATA-007 | Canonical records must retain source, observed time, effective time and schema version. | STEP-006 | TST-DATA-007 | P1 | [C] |
| REQ-DATA-008 | Domain events must be published via a transactional outbox in the same transaction as the state change. | STEP-006 | TST-DATA-008 | P1 | [C] |
| REQ-DATA-009 | Event consumers must be idempotent; replaying an event must not duplicate an effect. | STEP-006 | TST-DATA-009 | P1 | [C] |
| REQ-DATA-010 | Read models must be rebuildable from the event log. | STEP-006 | TST-DATA-010 | P1 | [C] |

## REQ-COLL / REQ-BOOK / REQ-LIVE / REQ-ADMIN

| ID | Requirement | Steps | Test | Release | Class |
| --- | --- | --- | --- | --- | --- |
| REQ-COLL-001 | A collaborator must be able to contribute constraints and votes but must not select the canonical scenario or alter protected bookings. | STEP-015 | TST-COLL-001 | P2 | [C] |
| REQ-COLL-002 | A collaborator's sensitive constraint must be usable by the solver without being displayed verbatim to other collaborators. | STEP-015 | TST-COLL-002 | P2 | [C] |
| REQ-COLL-003 | Final scenario selection must require explicit owner approval. | STEP-015 | TST-COLL-003 | P2 | [C] |
| REQ-COLL-004 | The owner must be able to reconstruct who proposed, approved and changed every material choice. | STEP-015 | TST-COLL-004 | P2 | [C] |
| REQ-BOOK-001 | Deep links must preserve dates, party size and product identifiers where the provider permits. | STEP-016 | TST-BOOK-001 | P1 | [A] |
| REQ-BOOK-002 | Payment credentials must never be stored or transmitted by JourneyLab. | STEP-016 | TST-BOOK-002 | P1 | [C] |
| REQ-BOOK-003 | Estimated and user-confirmed items must be visually and structurally distinct. | STEP-016 | TST-BOOK-003 | P1 | [C] |
| REQ-BOOK-004 | Affiliate failure must offer copyable booking details as a fallback path. | STEP-016 | TST-BOOK-004 | P1 | [C] |
| REQ-BOOK-005 | Booking APIs may only be enabled after documented liability, security and operational review. | STEP-028 | TST-BOOK-005 | P4 | [C] |
| REQ-LIVE-001 | The selected itinerary and critical evidence must remain usable for at least 72 hours without network. | STEP-017 | TST-LIVE-001 | P3 | [C] |
| REQ-LIVE-002 | Offline changes must queue idempotently and resolve conflicts visibly. | STEP-017 | TST-LIVE-002 | P3 | [C] |
| REQ-LIVE-003 | Live events must be matched to affected itinerary nodes and deduplicated before notification. | STEP-018 | TST-LIVE-003 | P3 | [C] |
| REQ-LIVE-004 | Unverified social reports must never trigger an automatic plan change. | STEP-018 | TST-LIVE-004 | P3 | [C] |
| REQ-LIVE-005 | A replan must require explicit user acceptance before the canonical plan changes. | STEP-019 | TST-LIVE-005 | P3 | [C] |
| REQ-LIVE-006 | A replan must preserve completed and protected items and report the preserved-plan percentage. | STEP-019 | TST-LIVE-006 | P3 | [C] |
| REQ-ADMIN-001 | Curator overrides must record reason, effective period, evidence and actor in an audit trail. | STEP-021 | TST-ADMIN-001 | P1 | [C] |
| REQ-ADMIN-002 | High-impact fact overrides must require four-eyes approval. | STEP-021 | TST-ADMIN-002 | P1 | [C] |
| REQ-ADMIN-003 | An override preview must list the scenarios and trips it will invalidate before it is applied. | STEP-021, STEP-026 | TST-ADMIN-003 | P1 | [C] |
| REQ-ADMIN-004 | Operators must have destination coverage and provider health dashboards. | STEP-021 | TST-ADMIN-004 | P1 | [C] |
| REQ-ADMIN-005 | Support must reconstruct a single trip without unrestricted tenant access. | STEP-021, STEP-025 | TST-ADMIN-005 | P1 | [C] |

## REQ-OBS — Observability and analytics

| ID | Requirement | Steps | Test | Release | Class |
| --- | --- | --- | --- | --- | --- |
| REQ-OBS-001 | Every request and job must emit OpenTelemetry traces with a tenant-safe correlation ID. | STEP-024 | TST-OBS-001 | P1 | [C] |
| REQ-OBS-002 | A trip must be traceable end to end from brief through evidence, solver, model and UI result. | STEP-024 | TST-OBS-002 | P1 | [C] |
| REQ-OBS-003 | Business-quality alerts must exist for citation failure, hard-constraint regression and stale destination coverage. | STEP-024 | TST-OBS-003 | P1 | [C] |
| REQ-OBS-004 | Every alert must reference a runbook with a named owner. | STEP-024 | TST-OBS-004 | P1 | [C] |
| REQ-OBS-005 | Product analytics events must be typed and carry a privacy tier; untyped events must be rejected server-side. | STEP-022 | TST-OBS-005 | P2 | [C] |
| REQ-OBS-006 | An experiment must not surface results without verified exposure and outcome data. | STEP-022 | TST-OBS-006 | P2 | [C] |

## REQ-KG — Knowledge graph

| ID | Requirement | Steps | Test | Release | Class |
| --- | --- | --- | --- | --- | --- |
| REQ-KG-001 | The codebase graph must index at least 95% of first-party source files, with exclusions explicit and visible. | STEP-026 | TST-KG-001 | P1 | [C] |
| REQ-KG-002 | At least 90% of public symbols must link to an owner or parent module. | STEP-026 | TST-KG-002 | P1 | [C] |
| REQ-KG-003 | The default-branch graph must refresh within ten minutes of merge. | STEP-026 | TST-KG-003 | P1 | [C] |
| REQ-KG-004 | Release graphs must be immutable and tagged. | STEP-026, STEP-027 | TST-KG-004 | P1 | [C] |
| REQ-KG-005 | Every node and inferred edge must store extractor version, source location, commit and confidence. | STEP-026 | TST-KG-005 | P1 | [C] |
| REQ-KG-006 | Graph traversal must enforce repository, tenant and data-source authorization; a graph answer must never reveal a path the caller cannot inspect at source. | STEP-026 | TST-KG-006 | P1 | [C] |
| REQ-KG-007 | Secrets, customer payloads and restricted code must never enter graph properties or embeddings. | STEP-026 | TST-KG-007 | P1 | [C] |
| REQ-KG-008 | No code, schema, API, event, model, prompt or infrastructure change may merge without a completed pre-change impact record. | STEP-026, all | TST-KG-008 | P1 | [C] |

## REQ-NFR — Non-functional (summary)

Full specification and measurement method in [NON_FUNCTIONAL_REQUIREMENTS](../03-architecture/NON_FUNCTIONAL_REQUIREMENTS.md).

| ID | Requirement | Test | Release |
| --- | --- | --- | --- |
| REQ-NFR-001 | 99.9% monthly availability for customer-facing APIs at GA. | TST-NFR-001 | GA |
| REQ-NFR-002 | Interactive reads p95 ≤ 400 ms excluding third-party provider time. | TST-NFR-002 | P1 |
| REQ-NFR-003 | Long-running work returns a job handle within 500 ms and streams progress. | TST-NFR-003 | P1 |
| REQ-NFR-004 | Scenario generation p95 ≤ 45 s for a seven-day covered-region trip, cancellable. | TST-NFR-004 | P1 |
| REQ-NFR-005 | At-least-once event delivery with idempotent consumers and dead-letter handling. | TST-NFR-005 | P1 |
| REQ-NFR-006 | Encryption in transit (modern TLS) and at rest (managed keys). | TST-NFR-006 | P1 |
| REQ-NFR-007 | UTF-8 end to end, ICU messages, locale-aware dates/numbers/currency, correct time zones and DST. | TST-NFR-007 | P1 |
| REQ-NFR-008 | Right-to-left layout readiness. | TST-NFR-008 | P2 |
| REQ-NFR-009 | Horizontal stateless services with back-pressure, idempotency and replay. | TST-NFR-009 | P1 |
| REQ-NFR-010 | Offline itinerary usable ≥72 h; queued changes encrypted and conflict-safe. | TST-NFR-010 | P3 |
| REQ-NFR-011 | Closure and disruption facts meet provider-specific minute-level freshness SLOs. | TST-NFR-011 | P3 |
| REQ-NFR-012 | Coordinates, time zones and routing profiles validated against destination golden sets; no itinerary item may use an unresolved location. | TST-NFR-012 | P1 |
| REQ-NFR-013 | Frontend meets defined Core Web Vitals and bundle budgets. | TST-NFR-013 | P1 |
| REQ-NFR-014 | Cost per saved feasible trip must stay within budget without relaxing quality, latency or diversity thresholds. | TST-NFR-014 | P1 |

---

## Requirements that are deliberately *not* stated here

To prevent false precision, these are **open** and tracked in [ASSUMPTION_REGISTER](../02-delivery/ASSUMPTION_REGISTER.md) / [DECISION_LOG](../02-delivery/DECISION_LOG.md), not written as requirements:

- Concrete numeric targets for time-to-decision, trust score and preserved-plan percentage (`DEC-005`) — the blueprint names the measures but no thresholds.
- Subscription/pricing behavior (`DEC-003`).
- Named destination region for Phase 1 (`DEC-002`).
- Data residency and regional deployment obligations (`ASM-003`).
- Specific provider identities and their contractual freshness SLAs (`ASM-011`).
