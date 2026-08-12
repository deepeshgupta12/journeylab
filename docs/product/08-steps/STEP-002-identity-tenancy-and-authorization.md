---
step_id: STEP-002
title: Identity, tenancy and authorization
status: DISCOVERY
release: Phase 1
owners: ["Deepesh Kumar Gupta"]
dependencies: [STEP-001]
requirement_ids: [REQ-SEC-001, REQ-SEC-002, REQ-SEC-003, REQ-SEC-004, REQ-PLAT-012]
api_ids: [API-001]
event_ids: []
data_ids: [DATA-001, DATA-002]
ai_ids: []
knowledge_graph_check: REQUIRED
last_updated: 2026-08-05
---

# STEP-002 — Identity, tenancy and authorization

> Status is authoritative in [MASTER_TRACKER](../02-delivery/MASTER_TRACKER.md).

## 1. Outcome
Every request, job and event carries tenant and actor context. Unauthorized and cross-tenant operations fail deterministically and are audited.

## 2. Why this step exists
Twelve downstream steps depend on these primitives. Tenancy retrofitted after data exists is the classic source of leakage: a cache key or background job written before tenancy is enforced will silently cross tenants forever.

## 3. Scope
Session and token handling; tenant-context resolution at the API boundary; role and attribute policy definitions; user/org/membership/invitation/service-account provisioning; row-level security; continuous cross-tenant isolation tests; runtime flag control primitives.

## 4. Explicit exclusions
Collaborator invitation UX is [STEP-015](STEP-015-collaboration-and-decision.md); consent capture is [STEP-008](STEP-008-account-consent-and-traveler-profile.md); the advisor organization workspace is [STEP-028](STEP-028-advisor-workspace-and-commercial-scale.md).

## 5. Actors, permissions and data access
| Actor | Permission | Data accessed | Sensitivity |
| --- | --- | --- | --- |
| PER-001 traveler | Own identity | Own profile | PII |
| PER-002 collaborator | Invitation-scoped | Scoped trip data | PII |
| PER-005 ops admin | Audited admin | No raw PII by default | — |
| Service identity | Workload identity, narrow capability | Scoped | — |

## 6. Preconditions and dependencies
[STEP-001](STEP-001-foundation-and-repository-governance.md) exit. **Blocked on `DEC-004`** (identity provider undecided).

## 7. Inputs and source systems
OIDC provider (`EXT-007`, unselected); [AUTHORIZATION_MATRIX](../04-contracts/AUTHORIZATION_MATRIX.md); persona permission summary.

## 8. Detailed normal workflow
1. User authenticates via OIDC (passkey where supported); IdP returns tokens.
2. API boundary resolves actor and tenant **from the token**, never from a header or body.
3. Policy engine evaluates role capability plus resource relationship.
4. Database enforces row-level security using the tenant context.
5. Every emitted event and cache key carries the tenant ID.
6. Every authorization decision on a sensitive operation writes an audit event.

## 9. Alternate, partial and failure workflows
| Condition | Behavior | User-visible result | Requirement |
| --- | --- | --- | --- |
| IdP unavailable | **Fail closed** — never an anonymous authorized session | Sign-in unavailable | REQ-SEC-003 |
| Missing tenant context | Reject at the boundary | 401/403 | REQ-SEC-001 |
| Cross-tenant attempt | Deny, audit, **SEV1 alert** | 403 identical to 404 | REQ-SEC-002 |
| Unauthorized resource | 403 with the same shape as 404 | No enumeration possible | REQ-SEC-004 |
| Token expired | Refresh; then re-authenticate | Transparent or prompted | — |

## 10. State machine and lifecycle transitions
`anonymous → guest session → authenticated → (org member) → revoked/deleted`. Guest→authenticated migration must not duplicate trips ([STEP-008](STEP-008-account-consent-and-traveler-profile.md)).

## 11. Frontend implementation
`apps/web/src/auth/session.ts` (`PROPOSED`) — browser session, token refresh, server-side identity helpers. Role-aware rendering is presentation only; the server is the control.

## 12. Backend implementation
`apps/api/src/auth/dependencies.py`, `packages/authz/src/policy.ts`, `services/identity/src/provisioning.py`, `db/migrations/001_identity_tenancy.sql` (all `PROPOSED`).

## 13. API, event and integration contracts
`API-001` carries the auth envelope. `INT-006` identity provider contract. No domain events emitted at this step.

## 14. Data model, migration and retention effects
`DATA-001` Organization, `DATA-002` User, memberships, roles, service identities. Row-level security policies. Migration `001` is the foundation every later migration assumes.

## 15. AI, LLM, RAG, ML and data-science implementation
`NOT_APPLICABLE`. Authorization is a security boundary and must be deterministic and auditable (`CON-004`). Reason for exclusion: no model output may participate in an access decision.

## 16. Security, privacy, accessibility and responsible-AI controls
`SC-TEN-01`, `SC-TEN-02`, `SC-AUTH-01`, `SC-AUTHZ-01`. Data minimisation — guest sessions require no email. Auth flows are keyboard and screen-reader complete with announced errors.

## 17. Observability, analytics and KPIs
Auth success/failure rate; cross-tenant denial count (`ALRT-SEC-001`); token refresh failures; audit event volume. No PII in telemetry.

## 18. Files and modules expected to change
All `PROPOSED` — see §11, §12, plus `tests/security/test_tenant_isolation.py`.

## 19. Knowledge-graph pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | `BLOCKED` for application code — static fallback |
| Queries to run | KG-Q-006, KG-Q-014 (**data-flow check mandatory** — this is an auth change) |
| Expected impact | Foundational; every later module depends on it |

## 20. Blast-radius assessment
**HIGH by construction** — 12-step fan-in and a security boundary. Every sub-step here requires the `KG-Q-014` data-flow check and owner approval.

## 21. Implementation task checklist — sub-steps
| Sub-step | Outcome |
| --- | --- |
| STEP-002.01 | Identity schema and RLS migration |
| STEP-002.02 | Tenant-context resolution at the API boundary |
| STEP-002.03 | Role/attribute policy definitions from the authorization matrix |
| STEP-002.04 | Provisioning (users, orgs, memberships, service accounts) |
| STEP-002.05 | Browser session and token refresh |
| STEP-002.06 | Cross-tenant isolation test suite (`TST-SEC-002`) |
| STEP-002.07 | Audit event emission and runtime flag primitives |
| STEP-002.08 | Server-side session store and revocation — ✅ **VERIFIED** 2026-08-12 (BR-036, IMPL-033, BUG-022, ENH-002). Added after `.07`: the revocation carry from `.05` was dropped |

*Sub-step files created at step start per [SUB_STEP_PROTOCOL](../02-delivery/SUB_STEP_PROTOCOL.md) §9.*

## 22. Test and evaluation plan
`TST-SEC-001` … `TST-SEC-004`, `TST-PLAT-012`. Authorization tests are **generated from the matrix** so a matrix change without a test change fails CI. Isolation tests become regression check **R7**, run at every sub-step thereafter.

## 23. Deployment, feature flag and migration plan
IdP behind a flag to allow provider substitution. RLS policies applied via expand/contract so no window exists where rows are unprotected.

## 24. Rollback, compensation and recovery plan
Policy changes are revertible via flag. **RLS rollback requires care** — removing a policy widens access, so rollback is forward-only in production: fix the policy rather than dropping it.

## 25. Acceptance criteria
- [ ] Every row, event and cache key carries a tenant ID (`REQ-SEC-001`)
- [ ] Tenant A cannot reach tenant B via API, cache, job, export or graph (`REQ-SEC-002`)
- [ ] OIDC + passkey flows work; no static service keys exist (`REQ-SEC-003`)
- [ ] Every operation enforces server-side authorization (`REQ-SEC-004`)
- [ ] 403 and 404 are indistinguishable
- [ ] Flags change behavior without redeploy (`REQ-PLAT-012`)

## 26. Evidence required for completion
Isolation test run output; authorization matrix coverage report; audit event sample with redaction verified; `KG-Q-014` data-flow evidence.

## 27. Open questions, risks and decisions
`DEC-004` identity provider — **blocking**. `RISK-010` cross-tenant exposure. Guest-session security model needs explicit design: a guest session is a bearer capability and must expire.

## 28. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Sub-steps completed | 0 of 7 |
| Regression result | — |
| Verified by | — |
