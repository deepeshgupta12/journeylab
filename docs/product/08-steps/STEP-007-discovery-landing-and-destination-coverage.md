---
step_id: STEP-007
title: Discovery landing and destination coverage
status: DISCOVERY
release: Phase 1
owners: []
dependencies: [STEP-003, STEP-006]
requirement_ids: [REQ-TRIP-001, REQ-TRIP-002, REQ-EVID-006]
api_ids: [API-017]
event_ids: []
data_ids: [DATA-006]
ai_ids: []
knowledge_graph_check: REQUIRED
last_updated: 2026-08-05
---

# STEP-007 — Discovery landing and destination coverage

> Status is authoritative in [MASTER_TRACKER](../02-delivery/MASTER_TRACKER.md).

## 1. Outcome
A visitor can tell what is supported, what data is used and what JourneyLab will not do **before signing in**, and an unsupported request is refused rather than partially simulated.

## 2. Why this step exists
The product's trust claim starts before the account. Setting expectations here prevents the worst failure mode: a user planning a trip into a region where evidence is too thin to be reliable, and receiving something that looks authoritative.

## 3. Scope
Public coverage and SEO pages; supported regions, freshness and documented limitations; privacy summary; sample comparisons; date and geography validation; waitlist or read-only inspiration mode when simulation is unsupported.

## 4. Explicit exclusions
Account creation and consent are [STEP-008](STEP-008-account-consent-and-traveler-profile.md). Provider health collection is [STEP-005](STEP-005-source-integrations-and-ingestion.md).

## 5. Actors, permissions and data access
| Actor | Permission | Data accessed | Sensitivity |
| --- | --- | --- | --- |
| Anonymous visitor | Public read | Coverage model only | Public |
| Marketing/content system | Publish content | None | — |

**No provider identities or quota details are ever exposed publicly.**

## 6. Preconditions and dependencies
[STEP-003](STEP-003-design-system-and-application-shell.md) shell and [STEP-006](STEP-006-canonical-data-model-and-event-backbone.md) coverage read model.

## 7. Inputs and source systems
Origin, broad destination interest, dates, device locale; coverage read model; provider health (`EVT-008`).

## 8. Detailed normal workflow
1. Visitor lands; page is server-rendered for speed and SEO.
2. Page shows supported regions, data freshness, limitations, sample comparisons and the privacy summary.
3. Visitor enters a destination and dates.
4. `API-017` validates geography and dates against current coverage and provider health.
5. On success, the visitor proceeds to a qualified start-planning action.

## 9. Alternate, partial and failure workflows
| Condition | Behavior | User-visible result | Requirement |
| --- | --- | --- | --- |
| Region unsupported | Refuse; show supported regions; offer waitlist | Honest scope statement | REQ-TRIP-002 |
| Dates outside window | Refuse with supported bounds | Clear boundary | REQ-TRIP-002 |
| Provider degraded | **Refuse rather than partially simulate**; disclose degradation | Region shown degraded | REQ-EVID-006 |
| Coverage service down | Static fallback listing regions with a staleness notice | Degraded but honest | REQ-EVID-006 |
| Waitlist offered | Inquiry preserved **only with consent** | Consent prompt | REQ-PRIV-002 |

## 10. State machine and lifecycle transitions
`visitor → coverage-checked → qualified → (start planning | waitlisted | declined)`.

## 11. Frontend implementation
`apps/web/src/app/(public)/coverage/page.tsx`, `apps/web/src/app/trips/new/page.tsx` (`PROPOSED`). Server-rendered; no map dependency; full keyboard and screen-reader paths.

## 12. Backend implementation
`services/destination/` coverage query and provider-health read (`PROPOSED`). Cached with a short TTL.

## 13. API, event and integration contracts
`API-017` `GET /v1/coverage` — public, unauthenticated, must not expose provider identities. Consumes `EVT-008`.

## 14. Data model, migration and retention effects
Reads `DATA-006` and the coverage read model. Waitlist inquiries are stored **only with consent** and carry a retention period.

## 15. AI, LLM, RAG, ML and data-science implementation
`NOT_APPLICABLE`. Reason: coverage validation is a deterministic rule over region and date bounds. A model here would introduce uncertainty into precisely the statement that must be reliable.

## 16. Security, privacy, accessibility and responsible-AI controls
Public page carries no tracking beyond typed, privacy-tiered analytics. Privacy summary is presented **before** any data collection. Consent required before storing an inquiry. WCAG 2.2 AA; no map required.

## 17. Observability, analytics and KPIs
`coverage_viewed`, `waitlist_joined`, refusal rate by reason. Refusal-by-degradation rate is a leading indicator for `RISK-001`.

## 18. Files and modules expected to change
All `PROPOSED` — see §11, §12.

## 19. Knowledge-graph pre-change analysis
| Field | Value | 
| --- | --- |
| Graph status | `BLOCKED` — static fallback |
| Queries to run | KG-Q-006 on the coverage read model |
| Expected impact | Public surface; low inbound coupling |

## 20. Blast-radius assessment
Low reach into other services, but **high customer criticality** — this is the first impression and the honesty gate. Detectability is good (public, monitored).

## 21. Implementation task checklist — sub-steps
| Sub-step | Outcome |
| --- | --- |
| STEP-007.01 | Coverage read model and `API-017` |
| STEP-007.02 | Public coverage/SEO page with limitations and privacy summary |
| STEP-007.03 | Date and geography validation with honest refusal states |
| STEP-007.04 | Waitlist / inspiration mode with consent |
| STEP-007.05 | Provider-degradation disclosure wiring |

## 22. Test and evaluation plan
`TST-TRIP-001`, `TST-TRIP-002`, `TST-EVID-006`, `TST-A11Y-001`. A resilience drill must prove that a degraded provider produces a refusal, not a partial simulation.

## 23. Deployment, feature flag and migration plan
Region availability controlled by flag so a region can be suspended without deployment.

## 24. Rollback, compensation and recovery plan
Static fallback content; region flag off. No data impact.

## 25. Acceptance criteria
- [ ] Supported regions, freshness, limitations and privacy summary visible pre-signup (`REQ-TRIP-001`)
- [ ] Out-of-coverage requests refused with an explanation and **no scenarios generated** (`REQ-TRIP-002`)
- [ ] Provider degradation disclosed, not masked by cache (`REQ-EVID-006`)
- [ ] Page completes all tasks by keyboard and screen reader

## 26. Evidence required for completion
Refusal-path test output; degradation drill record; accessibility audit; SEO/CWV measurement.

## 27. Open questions, risks and decisions
`DEC-002` region unknown, so no coverage content can be written yet. Waitlist retention period needs privacy-owner approval.

## 28. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Sub-steps completed | 0 of 5 |
| Regression result | — |
| Verified by | — |
</content>
