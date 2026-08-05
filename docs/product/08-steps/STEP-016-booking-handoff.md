---
step_id: STEP-016
title: Booking handoff
status: DISCOVERY
release: Phase 1
owners: []
dependencies: [STEP-013, STEP-005]
requirement_ids: [REQ-BOOK-001, REQ-BOOK-002, REQ-BOOK-003, REQ-BOOK-004, REQ-SEC-010, REQ-EVID-003]
api_ids: [API-011]
event_ids: []
data_ids: [DATA-013]
ai_ids: []
knowledge_graph_check: REQUIRED
last_updated: 2026-08-05
---

# STEP-016 — Booking handoff

> Status is authoritative in [MASTER_TRACKER](../02-delivery/MASTER_TRACKER.md).

## 1. Outcome
A traveler moves from planning to third-party purchase with itinerary context preserved, and **no estimated price or availability is ever presented as confirmed**.

## 2. Why this step exists
This is where the product's honesty commitment is most commercially tempting to break. It is also the seam where users abandon (`ASM-017`), so it must be smooth without becoming misleading.

## 3. Scope
Deep-link generation with dates, party size and product identifiers where permitted; handoff and return attribution; reconciliation of user-confirmed bookings into protected itinerary items; estimated vs. confirmed distinction; copyable fallback details.

## 4. Explicit exclusions
Payment processing, ticket issuance and merchant-of-record are **gated** (`GATE-001`). Booking write APIs are `GATE-002`, Phase 4.

## 5. Actors, permissions and data access
| Actor | Permission | Data accessed | Sensitivity |
| --- | --- | --- | --- |
| PER-001 traveler | Create handoff, confirm booking | Own itinerary | PII |
| PER-002 collaborator | Create handoff (editor) | Scoped | PII |
| Affiliate service | Generate links, receive signed callbacks | Booking metadata | **Sensitive** |

## 6. Preconditions and dependencies
[STEP-013](STEP-013-visual-comparison.md) selected scenario; [STEP-005](STEP-005-source-integrations-and-ingestion.md) affiliate adapter. **`ASM-012`** unvalidated.

## 7. Inputs and source systems
Selected itinerary items, traveler-approved parameters, provider capabilities, `EXT-005` affiliate partners.

## 8. Detailed normal workflow
1. Traveler chooses an item to book.
2. System generates a deep link preserving dates, party size and product identifiers where the provider permits.
3. Handoff and attribution are recorded — **no payment credentials, ever**.
4. Traveler completes purchase externally.
5. Traveler confirms the booking, or forwards a confirmation.
6. System reconciles it into a **protected** itinerary item, visually distinct from estimates.

## 9. Alternate, partial and failure workflows
| Condition | Behavior | User-visible result | Requirement |
| --- | --- | --- | --- |
| Affiliate unreachable | **Copyable booking details** fallback | Traveler can still book manually | REQ-BOOK-004 |
| Availability changed | Re-search with a clear delta | Honest change statement | REQ-BOOK-001 |
| Provider drops parameters | Record the degradation; warn the traveler | Expectation set | ASM-012 |
| Attribution callback unsigned | **Discarded, not best-effort processed** | None | INT-005 |
| Booking confirmed then cancelled | Item returns to estimated state with history | Explicit reversal | REQ-BOOK-003 |

## 10. State machine and lifecycle transitions
Item: `estimated → handoff issued → (confirmed → protected) | (abandoned → estimated)`. **Protected items cannot be modified by automated paths** thereafter.

## 11. Frontend implementation
`apps/web/src/features/booking/` (`PROPOSED`) — handoff list, **estimate and confirmed badges distinguished by text and icon, not colour**, copyable details, reconciliation flow.

## 12. Backend implementation
`services/affiliate/src/handoff.py` (`PROPOSED`) — link generation, attribution records, signed-webhook receipt, reconciliation.

## 13. API, event and integration contracts
`API-011` create handoff and attribution record. `INT-005` affiliate: outbound deep link, inbound **signed** webhook with replay-window enforcement and idempotent receipt.

## 14. Data model, migration and retention effects
Writes `DATA-013` BookingReference in a **segregated store** with narrower access and shorter retention. Payment credentials are structurally excluded — no column exists for them.

## 15. AI, LLM, RAG, ML and data-science implementation
`NOT_APPLICABLE`. Reason: link generation, attribution and reconciliation are deterministic and commercially consequential. Model involvement would add non-determinism to a money-adjacent path, violating `CON-004`.

## 16. Security, privacy, accessibility and responsible-AI controls
`SC-SEG-01` booking documents segregated from the planning graph. `SC-EGRESS-01` on affiliate calls. Webhook signature verified **before** parsing. Estimated/confirmed distinction is conveyed accessibly. Payment credentials never stored or transmitted (`REQ-BOOK-002`).

## 17. Observability, analytics and KPIs
`handoff_clicked`, `booking_confirmed`, handoff→confirmation conversion (`KPI-006`), parameter-preservation rate, affiliate error rate, reconciliation delta. Runbook `RB-PROV-002`.

## 18. Files and modules expected to change
All `PROPOSED` — see §11, §12.

## 19. Knowledge-graph pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | `BLOCKED` — static fallback |
| Queries to run | KG-Q-006; **KG-Q-014** for the booking-document boundary |
| Expected impact | Touches the segregated store — isolation must be verified |

## 20. Blast-radius assessment
Commercially sensitive and privacy-sensitive. A defect that leaks booking documents into the planning graph breaches `REQ-SEC-010` and is hard to reverse. Attribution loss is revenue loss but recoverable via reconciliation.

## 21. Implementation task checklist — sub-steps
| Sub-step | Outcome |
| --- | --- |
| STEP-016.01 | Segregated booking store with narrower access |
| STEP-016.02 | Deep-link generation with parameter preservation |
| STEP-016.03 | Attribution recording |
| STEP-016.04 | Signed webhook receipt with replay-window enforcement |
| STEP-016.05 | Reconciliation into protected itinerary items |
| STEP-016.06 | Estimated vs. confirmed UI distinction |
| STEP-016.07 | Copyable-details fallback |

## 22. Test and evaluation plan
`TST-BOOK-001` … `TST-BOOK-004`, `TST-SEC-010`, `TST-EVID-003`. A negative test must prove **no code path can write a payment credential**. An affiliate-outage drill must prove the fallback works.

## 23. Deployment, feature flag and migration plan
Per-partner flags. Attribution reconciliation runs as a scheduled job with a manual replay path.

## 24. Rollback, compensation and recovery plan
Disable a partner flag; copyable details remain. Attribution gaps are reconciled from partner statements after recovery.

## 25. Acceptance criteria
- [ ] Deep links preserve dates, party size and product identifiers where permitted (`REQ-BOOK-001`)
- [ ] No payment credential is ever stored or transmitted (`REQ-BOOK-002`)
- [ ] Estimated and confirmed items are visually and structurally distinct (`REQ-BOOK-003`)
- [ ] Affiliate failure offers copyable details (`REQ-BOOK-004`)
- [ ] Booking documents are segregated from the planning graph (`REQ-SEC-010`)
- [ ] No price is described as final without provider confirmation (`REQ-EVID-003`)

## 26. Evidence required for completion
Payment-credential negative test; segregation isolation test; affiliate outage drill; parameter-preservation measurement per partner.

## 27. Open questions, risks and decisions
`ASM-012` — no partner has been technically reviewed. `RISK-005` stop condition applies. `DEC-003` business model affects whether attribution is the revenue mechanism at all.

## 28. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Sub-steps completed | 0 of 7 |
| Regression result | — |
| Verified by | — |
