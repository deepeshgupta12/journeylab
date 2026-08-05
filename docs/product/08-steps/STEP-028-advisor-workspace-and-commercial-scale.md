---
step_id: STEP-028
title: Advisor workspace and commercial scale
status: DEFERRED
release: Phase 4
owners: []
dependencies: [STEP-020]
requirement_ids: [REQ-TRIP-009, REQ-BOOK-005]
api_ids: [API-001, API-011]
event_ids: []
data_ids: [DATA-001]
ai_ids: []
knowledge_graph_check: REQUIRED
last_updated: 2026-08-05
---

# STEP-028 — Advisor workspace and commercial scale

> Status is authoritative in [MASTER_TRACKER](../02-delivery/MASTER_TRACKER.md). **`DEFERRED` to Phase 4**, gated on Phase 3 exit.

## 1. Outcome
Travel advisors operate in an organization workspace with delegated, audited client access and can publish a branded, evidence-backed recommendation. Destination onboarding is repeatable and partner economics are positive.

## 2. Why this step exists
The advisor is the product's second buyer and the path to sustainable economics. It is deliberately last because it multiplies every earlier requirement — a defect in tenancy, audit or evidence becomes a professional liability issue once someone advises a client using it.

## 3. Scope
Organization workspace; delegated trip access with audit; branded client publication and handoff; provider portfolio expansion; affiliate reconciliation at scale; regional infrastructure; advanced personalisation. **Selective booking APIs only after liability, security and operational review** (`GATE-002`).

## 4. Explicit exclusions
Payment processing and merchant-of-record remain gated (`GATE-001`) pending licensing and liability work.

## 5. Actors, permissions and data access
| Actor | Permission | Data accessed | Sensitivity |
| --- | --- | --- | --- |
| PER-003 advisor | Delegated client trip access, **audited** | Client PII under delegation | **Sensitive** |
| Client (PER-001) | Owns the plan; approves | Own trip | PII |
| Org admin | Manage members and branding | Org metadata | Internal |

## 6. Preconditions and dependencies
Phase 3 exit: safe adaptation, plan preservation and acceptable notification burden demonstrated.

## 7. Inputs and source systems
Client briefs entered on their behalf, agency preference defaults, branding assets, expanded provider portfolio.

## 8. Detailed normal workflow
1. Organization is provisioned with members and branding.
2. Client grants delegation; the delegation record is explicit and time-bounded.
3. Advisor creates or reviews scenarios on the client's behalf — every access audited.
4. Advisor publishes a branded recommendation with evidence attached.
5. Client reviews and approves; the canonical plan remains the **client's** decision.
6. Handoff transfers ownership cleanly without data loss.

## 9. Alternate, partial and failure workflows
| Condition | Behavior | User-visible result | Requirement |
| --- | --- | --- | --- |
| Advisor attempts to edit an approved canonical plan | **Blocked** — proposal only | Client retains control | REQ-TRIP-009 |
| Delegation expires or is revoked | Access ends immediately; audit retained | Fail closed | REQ-SEC-008 |
| Client disputes a recommendation | Full audit reconstructs who changed what and when | Defensible record | REQ-COLL-004 |
| Branded export requested | Accessible PDF/ICS/CSV with evidence | Usable artifact | REQ-A11Y-002 |
| Booking API requested | **Blocked pending review** (`GATE-002`) | Deep links only | REQ-BOOK-005 |

## 10. State machine and lifecycle transitions
Delegation: `requested → granted → active → (expired | revoked)`. Client plan: `advisor draft → client review → client approved → handed off`.

## 11. Frontend implementation
`apps/web/src/app/org/*` (`PROPOSED`) — workspace, client list, delegation management, branding, publication and export. Published client artifacts must be accessible.

## 12. Backend implementation
Organization provisioning extensions in `services/identity/`, publication and handoff in `services/collaboration/`, affiliate reconciliation at scale in `services/affiliate/` (`PROPOSED`).

## 13. API, event and integration contracts
Extends `API-001` with organization scoping and `API-011` with reconciliation at scale. Expanded provider contracts under [INTEGRATION_CONTRACTS](../04-contracts/INTEGRATION_CONTRACTS.md).

## 14. Data model, migration and retention effects
Extends `DATA-001` Organization as the B2B tenant boundary; adds delegation records with expiry. **Client data retention is governed by the client, not the advisor** — a distinction that must be explicit in the data model, not merely in policy.

## 15. AI, LLM, RAG, ML and data-science implementation
Advanced personalisation reuses `AI-009` with **agency-level defaults kept separate from individual client preferences** — an advisor's house style must never silently become a client's inferred preference. No new AI capability is introduced.

## 16. Security, privacy, accessibility and responsible-AI controls
`SC-AUTHZ-02` delegated, audited access. Advisor acts on another person's sensitive constraints, requiring an explicit delegation record. Tenant-managed encryption keys become available at this tier. Published artifacts meet the accessibility bar.

## 17. Observability, analytics and KPIs
Advisor activation, client approval rate, delegation audit completeness, destination onboarding time (the Phase 4 exit measure), partner conversion, contribution margin.

## 18. Files and modules expected to change
All `PROPOSED` — see §11, §12.

## 19. Knowledge-graph pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | `BLOCKED` — static fallback |
| Queries to run | KG-Q-006; **KG-Q-014** for delegated-access paths |
| Expected impact | Introduces a second tenancy dimension (org over user) affecting every authorization path |

## 20. Blast-radius assessment
**Re-opens the tenancy model.** Organization-scoped delegation over user-owned data is a materially different authorization shape from Phase 1, and every earlier isolation guarantee must be re-verified under it. R7 must be re-run across the whole suite.

## 21. Implementation task checklist — sub-steps
| Sub-step | Outcome |
| --- | --- |
| STEP-028.01 | Organization workspace and membership |
| STEP-028.02 | Delegation records with expiry and audit |
| STEP-028.03 | Advisor-authored scenarios with client approval gate |
| STEP-028.04 | Branding and client publication |
| STEP-028.05 | Accessible export and clean handoff |
| STEP-028.06 | Provider portfolio expansion |
| STEP-028.07 | Affiliate reconciliation at scale |
| STEP-028.08 | Regional infrastructure and residency |
| STEP-028.09 | Tenant-managed keys |

## 22. Test and evaluation plan
`TST-TRIP-009`, `TST-BOOK-005`, plus **full re-run of `TST-SEC-002` under organization-scoped delegation**. Audit reconstruction must be demonstrated end to end.

## 23. Deployment, feature flag and migration plan
Phase 4 flag per organization. Regional deployment follows `DEC-007`.

## 24. Rollback, compensation and recovery plan
Flag off per organization. Delegation revocation is immediate. Published client artifacts already delivered cannot be recalled — a reason publication requires explicit client approval first.

## 25. Acceptance criteria
- [ ] Advisor access is delegated, audited and cannot silently edit an approved canonical plan (`REQ-TRIP-009`)
- [ ] Booking APIs remain disabled until liability, security and operational review completes (`REQ-BOOK-005`)
- [ ] Full audit reconstructs who proposed, approved and changed every material choice
- [ ] Destination onboarding is repeatable and measured
- [ ] Cross-tenant isolation holds under organization-scoped delegation

## 26. Evidence required for completion
Delegation audit demonstration; re-run isolation test results; onboarding time measurement; contribution margin analysis; accessibility audit of published artifacts.

## 27. Open questions, risks and decisions
Advisor buyer has had **no discovery** (`PER-003` unvalidated). Liability model for advice given through the product is undefined. `DEC-003` business model determines whether this step is licensing, commission or subscription.

## 28. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Sub-steps completed | 0 of 9 |
| Regression result | — |
| Verified by | — |
</content>
