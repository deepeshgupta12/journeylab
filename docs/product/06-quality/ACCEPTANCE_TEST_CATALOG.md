# JourneyLab — Acceptance Test Catalog

| Field | Value |
| --- | --- |
| Owner | QA + Engineering (unassigned — `BLK-001`) |
| Status | `DISCOVERY` — **all tests `PROPOSED`; none implemented** |
| Coverage | 130 requirements → 130 acceptance test IDs |
| Last reviewed | 2026-08-05 |

Navigation: [Test strategy](TEST_STRATEGY.md) · [Requirements](../01-product/FUNCTIONAL_REQUIREMENTS.md) · [Traceability](../01-product/REQUIREMENTS_TRACEABILITY.md) · [00-START-HERE](../00-START-HERE.md)

---

## How to read

Each test states the **observable pass condition**, not the implementation. `Type` maps to the layers in [TEST_STRATEGY](TEST_STRATEGY.md) §2.

---

## Platform, security, privacy

| Test ID | Requirement | Type | Pass condition |
| --- | --- | --- | --- |
| TST-PLAT-001 | REQ-PLAT-001 | e2e | A clean checkout runs lint, typecheck, tests and the app using only documented commands |
| TST-PLAT-002 | REQ-PLAT-002 | CI | A lock-file change without a manifest change fails the build |
| TST-PLAT-003 | REQ-PLAT-003 | CI | A path not matched by `CODEOWNERS` fails the build |
| TST-PLAT-004 | REQ-PLAT-004 | review | Each structural decision has a numbered ADR |
| TST-PLAT-005 | REQ-PLAT-005 | contract | Runtime responses validate against `openapi.yaml`; drift fails |
| TST-PLAT-006 | REQ-PLAT-006 | contract | Every emitted event validates against AsyncAPI with a declared delivery guarantee |
| TST-PLAT-007 | REQ-PLAT-007 | CI | A hand-edited generated client fails the build |
| TST-PLAT-008 | REQ-PLAT-008 | contract | A breaking diff without a version bump + migration guide fails |
| TST-PLAT-009 | REQ-PLAT-009 | CI | A seeded regression in any gate blocks the release |
| TST-PLAT-010 | REQ-PLAT-010 | resilience | Rollback executes in staging and restores the prior version |
| TST-PLAT-011 | REQ-PLAT-011 | migration | Old and new readers both work throughout the rollout window |
| TST-PLAT-012 | REQ-PLAT-012 | integration | Feature, model, provider and cohort flags change behavior without redeploy |
| TST-SEC-001 | REQ-SEC-001 | unit + integration | No row, event or cache key can be written without a tenant ID |
| TST-SEC-002 | REQ-SEC-002 | security | **Tenant A cannot reach tenant B via API, cache, job, export or graph** — fuzzed |
| TST-SEC-003 | REQ-SEC-003 | integration | OIDC + passkey flows succeed; static service keys are absent |
| TST-SEC-004 | REQ-SEC-004 | security | Every operation denies each unauthorized role; generated from the authorization matrix |
| TST-SEC-005 | REQ-SEC-005 | security | Connector rejects non-allowlisted egress, malformed schema, and enforces timeout |
| TST-SEC-006 | REQ-SEC-006 | security | Instructions embedded in retrieved content do not alter model behavior |
| TST-SEC-007 | REQ-SEC-007 | integration | Audit events immutable, separate, redacted |
| TST-SEC-008 | REQ-SEC-008 | e2e | Expired/revoked invitation fails closed; location sharing defaults off; views logged |
| TST-SEC-009 | REQ-SEC-009 | CI | Unsigned artifact cannot deploy; SBOM produced |
| TST-SEC-010 | REQ-SEC-010 | integration | Booking documents inaccessible from planning-graph credentials |
| TST-PRIV-001 | REQ-PRIV-001 | e2e | A full plan completes with no email or account |
| TST-PRIV-002 | REQ-PRIV-002 | integration | Withdrawing one purpose leaves unrelated purposes and data intact |
| TST-PRIV-003 | REQ-PRIV-003 | unit | No code path writes a sensitive attribute from a behavioral signal |
| TST-PRIV-004 | REQ-PRIV-004 | integration | Sensitive classes absent from analytics payloads and ad-related paths |
| TST-PRIV-005 | REQ-PRIV-005 | e2e | Export produces machine-readable data + confirmation |
| TST-PRIV-006 | REQ-PRIV-006 | integration | **Seeded data in every store is absent after deletion** — primary, object, vector, graph, cache, export, tokens |
| TST-PRIV-007 | REQ-PRIV-007 | integration | An injected deletion failure appears in the retry queue and alerts |
| TST-PRIV-008 | REQ-PRIV-008 | integration | Precise location is not persisted unless explicitly saved |

## Accessibility

| Test ID | Requirement | Type | Pass condition |
| --- | --- | --- | --- |
| TST-A11Y-001 | REQ-A11Y-001 | e2e | Every core task completes by keyboard only and with a screen reader; axe reports no AA violations |
| TST-A11Y-002 | REQ-A11Y-002 | component | Each visualization has an equivalent table/list and a CSV export |
| TST-A11Y-003 | REQ-A11Y-003 | e2e | **All MVP tasks complete with map rendering disabled** |
| TST-A11Y-004 | REQ-A11Y-004 | component | Every status has a non-colour indicator |
| TST-A11Y-005 | REQ-A11Y-005 | e2e | Every drag interaction has a keyboard/menu alternative; targets meet minimum size |
| TST-A11Y-006 | REQ-A11Y-006 | e2e | Focus is preserved and changes announced during streamed scenario arrival |

## Product capability

| Test ID | Requirement | Type | Pass condition |
| --- | --- | --- | --- |
| TST-TRIP-001 | REQ-TRIP-001 | e2e | Coverage, freshness, limitations and privacy summary visible before signup |
| TST-TRIP-002 | REQ-TRIP-002 | e2e | Out-of-coverage request is refused with an explanation and **produces no scenarios** |
| TST-TRIP-003 | REQ-TRIP-003 | e2e | Create, duplicate, archive, export, delete all succeed |
| TST-TRIP-004 | REQ-TRIP-004 | integration | Constraint versions listed with the trips using each |
| TST-TRIP-005 | REQ-TRIP-005 | e2e | Guest→account migration preserves exactly one copy of each trip |
| TST-TRIP-006 | REQ-TRIP-006 | integration | Invitations expire and revoke correctly |
| TST-TRIP-007 | REQ-TRIP-007 | integration | Retention setting is honoured by the deletion job |
| TST-TRIP-008 | REQ-TRIP-008 | e2e | Preference change is shown, attributable and reversible |
| TST-TRIP-009 | REQ-TRIP-009 | security | Advisor access is delegated, audited, and cannot silently edit an approved plan |
| TST-CONS-001 | REQ-CONS-001 | unit | The four constraint classes never merge or auto-promote |
| TST-CONS-002 | REQ-CONS-002 | e2e | Only feasibility-blocking ambiguities prompt; interpretation shown before solving |
| TST-CONS-003 | REQ-CONS-003 | unit | An option violating a hard filter never appears in the ranked pool |
| TST-CONS-004 | REQ-CONS-004 | property | **Zero hard-constraint violations across the full corpus** |
| TST-CONS-005 | REQ-CONS-005 | integration | Unsatisfiable brief returns a *minimal* conflict set and relaxations; no plan returned |
| TST-CONS-006 | REQ-CONS-006 | integration | Identical inputs + seed produce identical scenarios |
| TST-CONS-007 | REQ-CONS-007 | integration | ≥3 scenarios differ materially on the diversity metric |
| TST-CONS-008 | REQ-CONS-008 | unit | Simulation outputs carry intervals; no bare point estimate is displayed |
| TST-CONS-009 | REQ-CONS-009 | e2e | Comparison surfaces material differences with confidence ranges |
| TST-CONS-010 | REQ-CONS-010 | integration | An edit changes only affected segments; any other change carries an explanation |
| TST-CONS-011 | REQ-CONS-011 | integration | Protected items are unmodified by edit and replan paths |
| TST-EVID-001 | REQ-EVID-001 | e2e | Every volatile field displays source, observed time, effective time, confidence |
| TST-EVID-002 | REQ-EVID-002 | integration | Conflicting facts both shown with hierarchy; never averaged |
| TST-EVID-003 | REQ-EVID-003 | e2e | No estimate renders as confirmed anywhere in the UI or API |
| TST-EVID-004 | REQ-EVID-004 | eval | ≥95% of volatile claims resolve to a correct evidence span |
| TST-EVID-005 | REQ-EVID-005 | integration | Facts past threshold are marked stale and lower confidence or block the option |
| TST-EVID-006 | REQ-EVID-006 | resilience | Provider degradation is disclosed, not masked by cache |

## AI, data, live, collaboration, booking, admin, observability, KG

| Test ID | Requirement | Type | Pass condition |
| --- | --- | --- | --- |
| TST-AI-001 | REQ-AI-001 | security | No model output path can mutate state without validation and authorization |
| TST-AI-002 | REQ-AI-002 | unit | Schema violation fails closed to the deterministic fallback |
| TST-AI-003 | REQ-AI-003 | integration | Permission/temporal filters applied before ranking; no leakage across tenants |
| TST-AI-004 | REQ-AI-004 | eval | On a sparse corpus the system abstains rather than fabricating |
| TST-AI-005 | REQ-AI-005 | security | Only allowlisted read tools callable; write tools absent |
| TST-AI-006 | REQ-AI-006 | integration | Trace contains prompt/model/retrieval/cost/latency with sensitive fields redacted |
| TST-AI-007 | REQ-AI-007 | e2e | With all AI disabled, core tasks still complete |
| TST-AI-008 | REQ-AI-008 | integration | Budget breach degrades to fallback rather than exceeding |
| TST-AI-009 | REQ-AI-009 | security | Adversarial corpus triggers detection; content excluded with a reason |
| TST-AI-010 | REQ-AI-010 | eval | No output asserts visa, health, legal or safety guarantees |
| TST-DATA-001…010 | REQ-DATA-001…010 | data quality / integration | Licence recorded before ingestion; connector controls present; circuit breaker trips; entity resolution correct; field-specific freshness; raw payload retention; provenance retained; outbox atomic; consumers idempotent; read models rebuildable |
| TST-COLL-001…004 | REQ-COLL-001…004 | e2e / security | Collaborator cannot select canonical or alter bookings; sensitive constraints not exposed; owner approval enforced; full audit reconstructable |
| TST-BOOK-001…005 | REQ-BOOK-001…005 | e2e | Deep links preserve context; no payment credentials; estimated vs confirmed distinct; copyable fallback; booking APIs gated on review |
| TST-LIVE-001…006 | REQ-LIVE-001…006 | e2e / resilience | 72 h offline; idempotent queue with visible conflicts; dedup matching; unverified sources never auto-change; explicit acceptance; preservation reported |
| TST-ADMIN-001…005 | REQ-ADMIN-001…005 | e2e / security | Overrides audited; four-eyes cannot be self-satisfied; impact preview correct; dashboards present; support cannot widen access |
| TST-OBS-001…006 | REQ-OBS-001…006 | integration | Traces with tenant-safe IDs; end-to-end trip trace; business alerts fire; every alert has a runbook; untyped events rejected; results withheld without exposure data |
| TST-KG-001…008 | REQ-KG-001…008 | CI | ≥95% files parsed; ≥90% symbols owned; ≤10 min refresh; release graph immutable; provenance present; permission-aware traversal; no secrets in graph; **merge blocked without a pre-change record** |
| TST-NFR-001…014 | REQ-NFR-001…014 | performance / resilience | Each SLO in [NON_FUNCTIONAL_REQUIREMENTS](../03-architecture/NON_FUNCTIONAL_REQUIREMENTS.md) §1 measured and met |

---

## Release gates

| Gate | Threshold | Source |
| --- | --- | --- |
| Hard-constraint violations | **0** in the full release corpus | blueprint §16.190 |
| Citation correctness | **≥ 95%** for volatile facts | §16.191 |
| Map-free keyboard + screen-reader journey | **All MVP tasks pass** | §16.192 |
| Offline pack, sync and deletion | **Pass on supported mobile browsers** | §16.193 |
| Provider outage and stale-data drills | **Safe degradation, no fabricated facts** | §16.194 |

---

## Status

No test exists. Suites are created within the sub-steps that produce the code they cover; the harness and gates are built in `STEP-027`.
