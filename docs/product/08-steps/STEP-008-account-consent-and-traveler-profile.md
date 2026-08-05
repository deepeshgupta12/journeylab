---
step_id: STEP-008
title: Account, consent and traveler profile
status: DISCOVERY
release: Phase 1
owners: []
dependencies: [STEP-002, STEP-007]
requirement_ids: [REQ-PRIV-001, REQ-PRIV-002, REQ-PRIV-003, REQ-PRIV-004, REQ-TRIP-003, REQ-TRIP-004, REQ-TRIP-005]
api_ids: [API-001, API-002, API-003, API-015]
event_ids: []
data_ids: [DATA-002, DATA-003, DATA-004, DATA-016]
ai_ids: []
knowledge_graph_check: REQUIRED
last_updated: 2026-08-05
---

# STEP-008 — Account, consent and traveler profile

> Status is authoritative in [MASTER_TRACKER](../02-delivery/MASTER_TRACKER.md).

## 1. Outcome
A traveler can complete planning with minimal data — including as a guest with no email — and can inspect or remove every stored profile attribute.

## 2. Why this step exists
Accessibility and mobility constraints are first-class planning inputs, and they are also among the most sensitive data the product touches. How they are collected determines whether users provide them at all (`ASM-014`) and whether the product is trustworthy.

## 3. Scope
Account creation and privacy-preserving guest sessions; guest→account migration; versioned traveler profile separating **hard accessibility needs from soft preferences**; purpose-specific consent records; skip/edit/export/delete for every attribute; trip lifecycle operations.

## 4. Explicit exclusions
Trip brief capture is [STEP-009](STEP-009-trip-brief-and-structured-constraints.md); deletion execution across all stores is [STEP-025](STEP-025-support-deletion-and-data-lifecycle.md); collaborator invitations are [STEP-015](STEP-015-collaboration-and-decision.md).

## 5. Actors, permissions and data access
| Actor | Permission | Data accessed | Sensitivity |
| --- | --- | --- | --- |
| PER-001 traveler | Own profile and trips | Own PII + accessibility | **Sensitive** |
| PER-002 collaborator | Own contributions | Own constraints | **Sensitive** |
| Identity service | Provisioning | Identity records | PII |

## 6. Preconditions and dependencies
[STEP-002](STEP-002-identity-tenancy-and-authorization.md) and [STEP-007](STEP-007-discovery-landing-and-destination-coverage.md).

## 7. Inputs and source systems
Identity, locale, currency, time zone, consent choices, optional accessibility preferences.

## 8. Detailed normal workflow
1. Qualified visitor chooses guest session or account.
2. System creates the session/account with the minimum viable data.
3. User optionally declares accessibility needs — presented **separately** from soft preferences, with a clear explanation of why they are asked and how they are used.
4. User grants purpose-specific consent; each purpose is independently recorded.
5. Profile is written as a new version; prior versions are retained with their trip linkage.
6. User can inspect, edit, export or delete any attribute at any time.

## 9. Alternate, partial and failure workflows
| Condition | Behavior | User-visible result | Requirement |
| --- | --- | --- | --- |
| Onboarding interrupted | Resume from last saved state | No data loss | Blueprint §6.2 |
| User skips all optional data | Planning proceeds with reduced personalization | Fully functional | REQ-PRIV-001 |
| Consent withdrawn for one purpose | Only that purpose stops; unrelated data untouched | Granular control | REQ-PRIV-002 |
| Guest→account migration | Trips transfer **without duplication** | One copy of each trip | REQ-TRIP-005 |
| Guest session expires | Trip recoverable only via the session token; clearly warned in advance | Explicit risk notice | — |

## 10. State machine and lifecycle transitions
`anonymous → guest → registered → (deleted)`. Profile: `v1 → v2 → …`, each immutable and linked to the trips that used it.

## 11. Frontend implementation
`apps/web/src/app/auth/*`, `/settings/profile`, `/settings/privacy`, `/settings/data`, `apps/web/src/features/onboarding/` (`PROPOSED`). Sensitive fields are visually and structurally separated, optional, and never pre-filled from inference.

## 12. Backend implementation
`services/identity/src/provisioning.py`, `apps/api/src/trips/routes.py`, consent recording in `services/privacy/` (`PROPOSED`).

## 13. API, event and integration contracts
`API-001` create trip, `API-002` read, `API-003` brief/profile, `API-015` privacy requests. `INT-007` identity provider.

## 14. Data model, migration and retention effects
Writes `DATA-002` User, `DATA-003` TravelerProfile (versioned), `DATA-004` Trip, `DATA-016` ConsentRecord. Retention is user-configurable within policy; consent records may survive deletion **only where legally required**, documented as an exception.

## 15. AI, LLM, RAG, ML and data-science implementation
`NOT_APPLICABLE`, and deliberately so. **No sensitive attribute may be inferred** from behavior (`REQ-PRIV-003`) — accessibility, mobility, health and age are set by explicit declaration only. This is the one place where *not* using AI is the product requirement.

## 16. Security, privacy, accessibility and responsible-AI controls
`SC-MIN-01` minimisation, `SC-CONSENT-01` purpose-specific consent, `SC-SENS-01` no inference, `SC-SENS-02` no advertising use. Sensitive fields encrypted with narrower access. Onboarding is keyboard and screen-reader complete — the accessibility questionnaire itself must be accessible, which is easy to overlook.

## 17. Observability, analytics and KPIs
Onboarding completion, skip rate per field, consent grant/withdrawal rates, guest→account conversion. **Accessibility-field completion rate is the direct measurement of `ASM-014`.** No sensitive values in telemetry.

## 18. Files and modules expected to change
All `PROPOSED` — see §11, §12.

## 19. Knowledge-graph pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | `BLOCKED` — static fallback |
| Queries to run | KG-Q-006; **KG-Q-014 mandatory** (sensitive data paths) |
| Expected impact | Profile versions consumed by brief, solver and preference learning |

## 20. Blast-radius assessment
Handles the product's most sensitive data. Severity of a defect is high (privacy harm); reversibility is poor once data is over-collected. Every sub-step requires the data-flow check.

## 21. Implementation task checklist — sub-steps
| Sub-step | Outcome |
| --- | --- |
| STEP-008.01 | Guest session with no-email planning path |
| STEP-008.02 | Account creation and guest→account migration without duplication |
| STEP-008.03 | Versioned profile with hard/soft separation |
| STEP-008.04 | Purpose-specific consent records with independent withdrawal |
| STEP-008.05 | Inspect/edit/export/delete for every attribute |
| STEP-008.06 | Trip lifecycle: create, duplicate, archive, export, delete |
| STEP-008.07 | Accessibility of the sensitive-data collection flow |

## 22. Test and evaluation plan
`TST-PRIV-001` … `TST-PRIV-005`, `TST-TRIP-003` … `TST-TRIP-005`, `TST-A11Y-001`. A static check must prove no code path writes a sensitive attribute from a behavioral signal.

## 23. Deployment, feature flag and migration plan
Guest mode behind a flag. Profile schema uses expand/contract; new optional attributes never break existing versions.

## 24. Rollback, compensation and recovery plan
Profile versions are immutable, so rollback means pointing at the prior version. **Over-collected data cannot be un-collected** — it must be deleted, which is why collection is gated on consent rather than corrected afterwards.

## 25. Acceptance criteria
- [ ] Planning completes with no email or account (`REQ-PRIV-001`)
- [ ] Consent is per purpose and independently revocable (`REQ-PRIV-002`)
- [ ] No sensitive attribute is inferred from behavior (`REQ-PRIV-003`)
- [ ] Sensitive classes are never used for advertising or unrelated personalization (`REQ-PRIV-004`)
- [ ] Every stored attribute is inspectable and removable
- [ ] Guest→account migration produces exactly one copy of each trip (`REQ-TRIP-005`)
- [ ] Trip create/duplicate/archive/export/delete all work (`REQ-TRIP-003`)

## 26. Evidence required for completion
Guest-path e2e run; consent matrix test; inference static-check result; migration test; accessibility audit of the sensitive-data flow.

## 27. Open questions, risks and decisions
`ASM-014` — willingness to disclose accessibility needs is unvalidated and is a core differentiator dependency. Guest-session lifetime and recovery semantics need a decision. `DEC-004` identity provider.

## 28. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Sub-steps completed | 0 of 7 |
| Regression result | — |
| Verified by | — |
</content>
