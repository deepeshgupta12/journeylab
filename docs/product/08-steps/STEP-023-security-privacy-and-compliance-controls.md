---
step_id: STEP-023
title: Security, privacy and compliance controls
status: DISCOVERY
release: Phase 1
owners: ["Deepesh Kumar Gupta"]
dependencies: [STEP-002]
requirement_ids: [REQ-SEC-006, REQ-SEC-007, REQ-SEC-009, REQ-SEC-010, REQ-PRIV-002, REQ-PRIV-003, REQ-PRIV-004]
api_ids: []
event_ids: []
data_ids: []
ai_ids: []
knowledge_graph_check: REQUIRED
last_updated: 2026-08-05
---

# STEP-023 — Security, privacy and compliance controls

> Status is authoritative in [MASTER_TRACKER](../02-delivery/MASTER_TRACKER.md).

## 1. Outcome
Security and privacy exist as **testable product behavior**, not documentation: threat-model actions are closed or explicitly accepted, and data-subject requests and tenant deletion are rehearsed and auditable.

## 2. Why this step exists
Portfolio standard §7.34 requires the first end-to-end path to include permissions, failure states and deletion. Controls added after launch are controls that were absent when the data arrived.

## 3. Scope
Threat model with abuse cases, privacy harms, model misuse and data poisoning; living data inventory; secret and PII redaction library; DSR workflows; infrastructure policy-as-code; security test suites.

## 4. Explicit exclusions
Authentication and tenancy primitives are [STEP-002](STEP-002-identity-tenancy-and-authorization.md); deletion **execution** across stores is [STEP-025](STEP-025-support-deletion-and-data-lifecycle.md).

## 5. Actors, permissions and data access
| Actor | Permission | Data accessed | Sensitivity |
| --- | --- | --- | --- |
| Security Architect | Threat model, policy authorship | Design artifacts | Internal |
| Privacy Owner | Data inventory, DSR oversight | Metadata, not content | Internal |
| Privacy operator | Execute DSRs (audited) | Subject data under authority | **Sensitive** |

## 6. Preconditions and dependencies
[STEP-002](STEP-002-identity-tenancy-and-authorization.md).

## 7. Inputs and source systems
Architecture documents; data classifications; provider licences; [SECURITY_PRIVACY_RESPONSIBLE_AI](../03-architecture/SECURITY_PRIVACY_RESPONSIBLE_AI.md) control register.

## 8. Detailed normal workflow
1. Security Architect produces the threat model covering assets, trust boundaries and abuse cases.
2. Privacy Owner produces the data inventory: owner, purpose, sensitivity, residency, retention, legal basis per source.
3. Engineering implements the redaction library used by logs, telemetry, AI inputs and graph properties.
4. Engineering implements DSR workflows: export, correction, consent withdrawal, deletion.
5. Infrastructure policies are codified (network, admission, artifact, IAM).
6. Security test suites run continuously in CI.

## 9. Alternate, partial and failure workflows
| Condition | Behavior | User-visible result | Requirement |
| --- | --- | --- | --- |
| Source without an inventory entry | **Ingestion refused** | Source unavailable | REQ-DATA-001 |
| Redaction fails | Telemetry emission blocked rather than leaking | Reduced observability, no leak | SC-REDACT-01 |
| Threat-model action open at release | Blocked, or explicitly accepted with an owner and date | Release gate | Release readiness |
| Policy violation in IaC | Merge blocked | Build failure | REQ-SEC-009 |
| DSR cannot complete | Monitored retry queue; privacy owner notified | Tracked, never silent | REQ-PRIV-007 |

## 10. State machine and lifecycle transitions
Threat-model action: `identified → mitigated | accepted (owner, date) → reviewed`. DSR: `received → in progress → (completed | failed → retry queue)`.

## 11. Frontend implementation
Consent management and data controls surfaces are built in [STEP-008](STEP-008-account-consent-and-traveler-profile.md); this step supplies the redaction library used by client telemetry.

## 12. Backend implementation
`security/threat-model.md`, `security/data-inventory.yml`, `packages/security/src/redaction.ts`, `services/privacy/src/requests.py`, `infra/policies/`, `tests/security/` (all `PROPOSED`).

## 13. API, event and integration contracts
Supports `API-015` privacy requests. Emits `EVT-007` deletion completed (implemented in `STEP-025`).

## 14. Data model, migration and retention effects
Defines classification and retention for every data class. No new entities; constrains all of them.

## 15. AI, LLM, RAG, ML and data-science implementation
Covers **model-specific threats**: prompt injection, model misuse, data poisoning, and the prohibition on training with customer trip content without a consent basis. Reason for inclusion: these are security controls on AI, not AI capabilities — the model itself is not used here.

## 16. Security, privacy, accessibility and responsible-AI controls
This step **is** the control layer: `SC-INJ-01`, `SC-AUDIT-01`, `SC-REDACT-01`, `SC-SEG-01`, `SC-SENS-01`, `SC-SENS-02`, `SC-CONSENT-01`, `SC-SUPPLY-01/02`. Threat modelling runs before beta and after material architecture changes.

## 17. Observability, analytics and KPIs
Scan findings by severity, threat-model action closure rate, DSR turnaround and failure rate, redaction failure count, policy violation rate. Alert `ALRT-PRIV-001`.

## 18. Files and modules expected to change
All `PROPOSED` — see §12.

## 19. Knowledge-graph pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | `BLOCKED` — static fallback |
| Queries to run | **KG-Q-014 taint/data-flow is the primary tool** for verifying redaction and isolation |
| Expected impact | Controls constrain every service |

## 20. Blast-radius assessment
Cross-cutting. A redaction defect leaks data from every service simultaneously. Low detectability without dedicated tests, which is why `tests/security/` is in scope here rather than deferred.

## 21. Implementation task checklist — sub-steps
| Sub-step | Outcome |
| --- | --- |
| STEP-023.01 | Threat model with abuse cases and model threats |
| STEP-023.02 | Data inventory with legal basis per source |
| STEP-023.03 | Redaction library for logs, telemetry, AI inputs, graph |
| STEP-023.04 | DSR workflows: export, correction, withdrawal, deletion |
| STEP-023.05 | Infrastructure policy-as-code |
| STEP-023.06 | Security test suites (authorization, injection, isolation, egress, deletion) |
| STEP-023.07 | Supply-chain controls: SBOM, signing, scanning |

## 22. Test and evaluation plan
`TST-SEC-006`, `TST-SEC-007`, `TST-SEC-009`, `TST-SEC-010`, `TST-PRIV-002` … `TST-PRIV-004`. Authorization fuzzing and tenant-isolation tests run continuously; **R7 runs at every sub-step across the whole programme**.

## 23. Deployment, feature flag and migration plan
Policies deploy with infrastructure. Redaction is not flaggable — it is always on, because a flag that disables redaction is a leak waiting for a misconfiguration.

## 24. Rollback, compensation and recovery plan
Policy rollback widens access and is therefore forward-only in production: fix the policy rather than removing it. **A data exposure cannot be rolled back.**

## 25. Acceptance criteria
- [ ] Threat-model actions closed or explicitly accepted with an owner (`REQ-SEC-006`)
- [ ] Audit events immutable, separate from application logs, redacted (`REQ-SEC-007`)
- [ ] SBOM generated; unsigned artifacts cannot deploy (`REQ-SEC-009`)
- [ ] Booking documents segregated from the planning graph (`REQ-SEC-010`)
- [ ] Consent is per purpose and independently revocable (`REQ-PRIV-002`)
- [ ] No sensitive attribute inferred from behavior (`REQ-PRIV-003`)
- [ ] Sensitive classes never used for advertising (`REQ-PRIV-004`)
- [ ] DSR workflows rehearsed and auditable

## 26. Evidence required for completion
Threat model with sign-off; data inventory; redaction test results; DSR rehearsal record; policy violation test; SBOM and signing evidence.

## 27. Open questions, risks and decisions
`DEC-007` residency determines applicable obligations. **No legal review has been performed** — retention periods in the policy are relative, not legally validated. Penetration testing is unscheduled.

## 28. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Sub-steps completed | 0 of 7 |
| Regression result | — |
| Verified by | — |
