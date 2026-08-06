# JourneyLab — Security, Privacy and Responsible AI

| Field | Value |
| --- | --- |
| Owner | Security Architect + Privacy Owner (Deepesh Kumar Gupta) |
| Status | `DISCOVERY` — controls specified; none implemented or tested |
| Upstream source | Blueprint §14 (security, privacy, responsible AI), §16 (security testing) |
| Last reviewed | 2026-08-05 |

Navigation: [System context](SYSTEM_CONTEXT.md) · [Authorization matrix](../04-contracts/AUTHORIZATION_MATRIX.md) · [Security testing](../06-quality/SECURITY_TESTING.md) · [Retention & deletion](../07-operations/DATA_RETENTION_AND_DELETION.md) · [00-START-HERE](../00-START-HERE.md)

---

## 1. Control register

| ID | Control | Requirement | Verified by |
| --- | --- | --- | --- |
| SC-TEN-01 | Tenant ID on every row, event and cache key | REQ-SEC-001 | TST-SEC-001 |
| SC-TEN-02 | Row-level security + continuous cross-tenant isolation tests, incl. cache, jobs, exports, graph | REQ-SEC-002, REQ-KG-006 | TST-SEC-002 |
| SC-AUTH-01 | OIDC + passkeys; workload identity for services; no static long-lived keys | REQ-SEC-003 | TST-SEC-003 |
| SC-AUTHZ-01 | Server-side authorization on every operation | REQ-SEC-004 | TST-SEC-004 |
| SC-AUTHZ-02 | Support/advisor access is delegated, scoped and audited — never unrestricted | REQ-ADMIN-005, REQ-TRIP-009 | TST-ADMIN-005 |
| SC-EGRESS-01 | SSRF protection, egress allowlist, schema validation, rate limit, timeout on every connector **and model tool** | REQ-SEC-005 | TST-SEC-005 |
| SC-INJ-01 | Retrieved text, documents and MCP tool descriptions treated as untrusted data; instruction/data isolation; injection detectors | REQ-SEC-006, REQ-AI-009 | TST-SEC-006, TST-AI-009 |
| SC-DET-01 | Model output cannot mutate state without deterministic validation and user authorization | REQ-AI-001 | TST-AI-001 |
| SC-DET-02 | Structured output enforced; schema violation fails closed | REQ-AI-002 | TST-AI-002 |
| SC-TOOL-01 | Read-only tool allowlist; no booking writes in MVP | REQ-AI-005 | TST-AI-005 |
| SC-CLAIM-01 | No visa/health/legal/safety guarantees; unverified sources never transition a plan | REQ-AI-010, REQ-LIVE-004 | TST-AI-010 |
| SC-AUDIT-01 **✅ IMPLEMENTED (STEP-002.07)** | Immutable security and business audit events, stored separately from application logs. **Append-only enforced by privilege**: `journeylab_app` holds INSERT + SELECT only, so UPDATE/DELETE/TRUNCATE are refused by the database. Redaction applied at emission; a redaction failure blocks the write | REQ-SEC-007 | TST-SEC-007 |
| SC-REDACT-01 | Secret and PII detection/redaction for logs, telemetry, AI inputs and graph properties | REQ-AI-006, REQ-KG-007 | TST-SEC-007 |
| SC-SEG-01 | Booking references and travel documents segregated from the planning graph | REQ-SEC-010 | TST-SEC-010 |
| SC-ABUSE-01 | Expiring invitations, view logs, download controls, location sharing default off | REQ-SEC-008 | TST-SEC-008 |
| SC-SENS-01 | No inference of mobility/health/age/accessibility from behavior | REQ-PRIV-003 | TST-PRIV-003 |
| SC-SENS-02 | Sensitive classes never used for advertising or unrelated personalization | REQ-PRIV-004 | TST-PRIV-004 |
| SC-CONSENT-01 | Purpose-specific consent, independently revocable | REQ-PRIV-002 | TST-PRIV-002 |
| SC-MIN-01 | Data minimisation — guest planning without an account | REQ-PRIV-001 | TST-PRIV-001 |
| SC-DSR-01/02/03 | Export, deletion across all stores, monitored failure retry queue | REQ-PRIV-005…007 | TST-PRIV-005…007 |
| SC-LOC-01 | Precise location processed ephemerally, never persisted by default | REQ-PRIV-008 | TST-PRIV-008 |
| SC-RET-01 | Configurable retention; raw payloads minimally retained | REQ-TRIP-007, REQ-DATA-006 | TST-TRIP-007 |
| SC-LIC-01 | Licence terms, cache duration and attribution documented before ingestion | REQ-DATA-001 | TST-DATA-001 |
| SC-SUPPLY-01/02 | Lock files, SBOM, signed artifacts, dependency/container/IaC scanning | REQ-PLAT-002, REQ-SEC-009 | TST-SEC-009 |
| SC-GOV-01 | Every path has an owner | REQ-PLAT-003 | TST-PLAT-003 |
| SC-GOV-02 | Four-eyes approval for high-impact overrides and booking-API enablement | REQ-ADMIN-002, REQ-BOOK-005 | TST-ADMIN-002 |
| SC-CHANGE-01 | No change merges without a completed pre-change impact record | REQ-KG-008 | TST-KG-008 |

---

## 2. Threat model summary

Full threat model is produced in `STEP-023` (`security/threat-model.md`). Assets, boundaries and priority threats:

**Assets:** traveler identity and profile (incl. accessibility and age), trip itineraries and location, booking references and documents, licensed destination data, model prompts/configs, audit trail, tenant isolation itself.

| Threat | Vector | Mitigation | Risk |
| --- | --- | --- | --- |
| Stalking via shared itinerary | Share link forwarded or retained after revocation | Expiring invitations, view logs, revocation, location default off | `RISK-006` |
| Cross-tenant leakage | Cache key, job, export or graph traversal missing tenant scope | RLS + isolation tests across all paths | `RISK-010` |
| Prompt injection | Provider content or tool description carrying instructions | Untrusted-data handling, isolation, detectors, read-only tools | `RISK-009` |
| Data poisoning | Malicious or wrong provider data steering recommendations | Provenance, conflict surfacing, curator override with four-eyes, anomaly detection | `RISK-001` |
| Credential theft | Static provider keys | Workload identity, secret manager, rotation | — |
| SSRF via connector | Attacker-controlled URL in provider payload | Egress allowlist, URL validation | — |
| Model misuse | Model asked to authorise or book | Read-only tools; deterministic command validation | `SC-DET-01` |
| Privacy harm via inference | Deriving disability from behavior | Explicit declaration only; prohibition tested | `SC-SENS-01` |
| Supply-chain compromise | Dependency or build tampering | Lock files, SBOM, signing, protected branches, reviewed deploys | — |

Threat modelling runs **before beta and after material architecture changes**, including abuse cases, privacy harms, model misuse and data poisoning.

---

## 3. Privacy by design

| Principle | Implementation |
| --- | --- |
| Purpose limitation | Consent recorded per purpose; withdrawal of one purpose does not cascade |
| Minimisation | Guest planning without an account; profile attributes optional and inspectable |
| Sensitive-class handling | Accessibility, age, precise location treated as sensitive; never used for advertising or unrelated personalization |
| No inference | Sensitive attributes may only be set by explicit user declaration |
| Transparency | Data use, retention and limitations shown **before** signup (`REQ-TRIP-001`) |
| Control | Export, correction, consent withdrawal and deletion, with confirmation |
| Deletion integrity | Traverses transactional rows, objects, vector chunks, graph nodes, caches, exports and tokens — proven by test |
| Residency | Regional storage controls; residency posture is an open decision (`DEC-007`, `ASM-003`) |

**Data inventory** (`security/data-inventory.yml`, produced in `STEP-023`) records owner, purpose, sensitivity, residency, retention and legal basis for every source. A source without an inventory entry may not be ingested.

---

## 4. Responsible AI

| Commitment | Mechanism |
| --- | --- |
| Human decision boundary | The traveler selects the canonical plan and approves every consequential change. Named per capability in §2 of [AI architecture](AI_LLM_RAG_ML_ARCHITECTURE.md) |
| No autonomous consequential action | Model output cannot mutate trip state; booking writes are outside MVP |
| Grounded claims only | Claim-to-source spans; ungrounded claims removed before display |
| Honest uncertainty | Confidence bands, fragility, abstention when evidence is thin |
| No dark patterns | Estimated vs confirmed always distinct; guardrails prohibit optimising KPIs by hiding evidence |
| Contestability | Users can dismiss, correct or delete inferred learning; curators can correct facts with audit |
| Evaluation before release | Gold + adversarial sets, cost/latency budgets, safe fallback (`CON-005`) |
| Lineage | Prompt, model, retrieval config, source pack, cost and latency in one trace |
| Prohibited uses | Advertising on sensitive data; training on customer trip content without a consent basis (`EXC-011`) |

---

## 5. Compliance posture

**Not legal advice.** This documentation is not a substitute for legal, privacy, accessibility, security or domain-professional approval.

| Area | Position | Gap |
| --- | --- | --- |
| Data protection (GDPR-style rights) | Export, correction, withdrawal, deletion and purpose limitation are designed in | Applicable jurisdictions undetermined (`DEC-007`) |
| Accessibility | WCAG 2.2 AA as a release gate | Formal audit not yet commissioned |
| Provider licensing | Terms, cache duration and attribution required before ingestion | **No provider identified** (`EXT-001`, `RISK-001`) |
| Payment/PCI | Out of scope — no payment processing | Re-enters scope only at Phase 4 booking APIs |
| Records retention | Legally required audit metadata retained; exceptions documented | Statutory periods undetermined |

---

## 6. Incident-relevant security operations

- Immutable audit events separate from application logs, with redaction.
- Incident response, breach notification, backup restoration, DR and third-party outage playbooks **before production launch**.
- Annual penetration testing; SAST, DAST, dependency, container and IaC scanning in CI; authorization fuzzing and tenant-isolation tests continuously.
- Any confirmed cross-tenant exposure halts release immediately and triggers incident response.
