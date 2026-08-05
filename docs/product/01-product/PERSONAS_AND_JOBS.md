# JourneyLab — Personas and Jobs to Be Done

| Field | Value |
| --- | --- |
| Owner | Product Lead (unassigned) |
| Status | `DISCOVERY` — personas derived from blueprint §5; none validated by interview |
| Upstream source | Blueprint §5 (Personas and jobs), §14 (privacy constraints) |
| Last reviewed | 2026-08-05 |

Navigation: [Charter](PRODUCT_CHARTER.md) · [Scope](PRODUCT_SCOPE.md) · [Authorization matrix](../04-contracts/AUTHORIZATION_MATRIX.md) · [00-START-HERE](../00-START-HERE.md)

---

## PER-001 — Primary traveler

**Job statement.** *When I am planning a 3–7 day trip with real constraints, I want to see several plans that actually work and understand what each costs me, so that I can commit to one without fearing I picked the fragile or overpriced option.*

| Dimension | Detail |
| --- | --- |
| Triggers | Fixed dates appear (leave approved, flight found); a group forms; a disruption occurs mid-trip |
| Inputs provided | Origin, destination, dates, party composition, budget ceiling, interests, pace tolerance, fixed commitments, exclusions, optional accessibility needs |
| Decisions owned | Which scenario becomes canonical; whether to accept a replan; what to book; what to share and with whom; what data to keep |
| Expected outcomes | A saved feasible scenario with visible trade-offs; deep links to book externally; (Phase 3) an offline live companion |
| Permissions | Owns own trips; invites collaborators; sets canonical scenario; controls profile, export and deletion |
| Sensitive data exposure | Accessibility/mobility needs, age of party members, precise location (Phase 3), travel documents. All classified sensitive; never used for advertising or unrelated personalization |
| Accessibility considerations | Must complete every MVP task with keyboard only and with a screen reader, **without a map**. Sunlight-readable and one-handed modes in live view. Reduced-motion honored |
| Failure / support needs | Must know when data is stale, a provider is down, or no feasible plan exists — and what to relax. Never a blank map or silent spinner |
| Scope steps | [STEP-007](../08-steps/STEP-007-discovery-landing-and-destination-coverage.md) → [STEP-020](../08-steps/STEP-020-post-trip-learning.md), [STEP-025](../08-steps/STEP-025-support-deletion-and-data-lifecycle.md) |

---

## PER-002 — Trip collaborator

**Job statement.** *When someone invites me to a trip, I want to add my constraints and register a preference without being able to break their bookings, so that the group decision reflects me but stays owned by the organiser.*

| Dimension | Detail |
| --- | --- |
| Triggers | Receives a secure invitation link or account invite |
| Inputs provided | Own hard constraints (dates unavailable, mobility, budget share), votes, comments, change proposals |
| Decisions owned | Own constraint declarations and votes only. **Cannot** select the canonical scenario or alter protected bookings |
| Expected outcomes | Their constraint is visibly represented in feasibility; conflicts are attributed without exposing their private details |
| Permissions | Invitation-scoped view / comment / propose. Expiring, revocable |
| Sensitive data exposure | Their own accessibility or budget constraints must be usable by the solver **without being displayed verbatim** to other collaborators (blueprint §6.9: "show conflicting hard constraints without revealing unnecessary sensitive details") |
| Accessibility considerations | Same WCAG 2.2 AA bar; invitation flows must be completable without the map |
| Failure / support needs | Expired or revoked links must fail closed without leaking trip content |
| Scope steps | [STEP-015](../08-steps/STEP-015-collaboration-and-decision.md), [STEP-009](../08-steps/STEP-009-trip-brief-and-structured-constraints.md) |

---

## PER-003 — Travel advisor *(Phase 4 — deferred)*

**Job statement.** *When a client briefs me, I want to generate and review scenarios and publish a branded recommendation with the evidence attached, so that I can defend the recommendation and hand it over cleanly.*

| Dimension | Detail |
| --- | --- |
| Triggers | Client engagement begins; client requests a revision |
| Inputs provided | Client brief on their behalf, agency preference defaults, branding |
| Decisions owned | Which scenarios to present; branded publication; handoff timing |
| Expected outcomes | Reproducible, evidence-backed recommendation; client handoff without data loss |
| Permissions | Organization workspace; delegated trip access with audit; **no** silent edit of a client-approved canonical plan |
| Sensitive data exposure | Acts on another person's sensitive constraints — requires explicit delegation record and audit trail |
| Accessibility considerations | Published client artifact must be accessible (PDF/ICS/CSV export path) |
| Failure / support needs | Must be able to prove who changed what, and when |
| Scope steps | [STEP-028](../08-steps/STEP-028-advisor-workspace-and-commercial-scale.md) — `DEFERRED` |

---

## PER-004 — Content / data curator *(internal)*

**Job statement.** *When destination evidence is wrong, stale or disputed, I want to correct it with an effective date and an audit trail, so that scenarios stop repeating the error without anyone editing a live plan by hand.*

| Dimension | Detail |
| --- | --- |
| Triggers | Source-health alert; user-reported incorrect fact; freshness threshold breach; conflicting providers |
| Inputs provided | Corrected fact value, effective period, evidence, reason |
| Decisions owned | Fact overrides within policy. **High-impact overrides require four-eyes approval** (blueprint §7.85) |
| Expected outcomes | Corrected canonical fact with provenance; regenerated scenarios where affected |
| Permissions | Internal least-privilege curation console; no access to traveler personal data |
| Sensitive data exposure | Should see destination facts only, not trip or traveler PII |
| Accessibility considerations | Internal console held to the same WCAG 2.2 AA standard |
| Failure / support needs | Must see which trips/scenarios an override will invalidate before applying it (graph impact query `KG-Q-003`) |
| Scope steps | [STEP-021](../08-steps/STEP-021-administration-and-curation-console.md), [STEP-010](../08-steps/STEP-010-destination-evidence-assembly.md) |

---

## PER-005 — Operations administrator *(internal)*

**Job statement.** *When a provider degrades, a model regresses or a user reports a bad plan, I want to diagnose one trip and degrade safely, so that I never have to grant myself unrestricted access to customer data to do my job.*

| Dimension | Detail |
| --- | --- |
| Triggers | Provider outage, quota exhaustion, solver saturation, citation-failure alert, privacy request, abuse report |
| Inputs provided | Correlation ID, trip ID, incident context |
| Decisions owned | Provider disable, model rollback, feature-flag change, notification suppression, incident severity |
| Expected outcomes | Tenant-safe diagnostic timeline; safe degradation without fabricated facts |
| Permissions | Audited internal administrative access. Reconstructing one trip must **not** require unrestricted tenant access (blueprint §9.137) |
| Sensitive data exposure | Diagnostic bundles carry source and version IDs, **not** raw sensitive payloads by default |
| Accessibility considerations | Admin surfaces meet the same AA bar |
| Failure / support needs | Runbook per failure class; rehearsed rollback; deletion-failure retry queue visibility |
| Scope steps | [STEP-021](../08-steps/STEP-021-administration-and-curation-console.md), [STEP-024](../08-steps/STEP-024-observability-sre-and-support-readiness.md), [STEP-025](../08-steps/STEP-025-support-deletion-and-data-lifecycle.md) |

---

## Persona → permission summary

Authoritative enforcement lives in [AUTHORIZATION_MATRIX](../04-contracts/AUTHORIZATION_MATRIX.md); this is the product-level summary.

| Capability | PER-001 Traveler | PER-002 Collaborator | PER-003 Advisor | PER-004 Curator | PER-005 Ops |
| --- | --- | --- | --- | --- | --- |
| Create trip / brief | ✅ own | ❌ | ✅ delegated | ❌ | ❌ |
| Generate scenarios | ✅ | ❌ | ✅ delegated | ❌ | ❌ |
| Propose edit | ✅ | ✅ proposal only | ✅ | ❌ | ❌ |
| Select canonical scenario | ✅ owner only | ❌ | ❌ (client approves) | ❌ | ❌ |
| Modify protected booking item | ✅ own | ❌ | ❌ | ❌ | ❌ |
| Override destination fact | ❌ | ❌ | ❌ | ✅ with audit + four-eyes for high impact | ❌ |
| Disable provider / roll back model | ❌ | ❌ | ❌ | ❌ | ✅ audited |
| Read raw traveler PII | own only | ❌ | delegated + audited | ❌ | ❌ by default |
| Delete own data | ✅ | ✅ own contributions | ✅ own workspace | ❌ | executes DSR, audited |

---

## Cross-persona accessibility commitments

Applies to all personas; verified in [ACCEPTANCE_TEST_CATALOG](../06-quality/ACCEPTANCE_TEST_CATALOG.md).

1. Every core task is completable by keyboard and by screen reader (`REQ-A11Y-001`).
2. Every visualization has a table/list equivalent and a CSV export (`REQ-A11Y-002`).
3. No core action requires the map (`REQ-A11Y-003`).
4. Status is never encoded by colour alone (`REQ-A11Y-004`).
5. Drag-and-drop always has a non-pointer alternative; touch targets meet minimum size (`REQ-A11Y-005`).
6. Streamed scenario updates restore focus and announce changes to assistive technology (`REQ-A11Y-006`).

---

## Anti-personas (explicitly not designed for in the target release)

| Not designed for | Why | Where recorded |
| --- | --- | --- |
| Corporate travel manager with policy compliance and expense integration | Requires policy engine, expense systems and duty-of-care obligations outside blueprint scope | [OUT_OF_SCOPE](OUT_OF_SCOPE.md) |
| Multi-month / round-the-world planner | 3–7 day window is the stated MVP bound (`ASM-015`) | [OUT_OF_SCOPE](OUT_OF_SCOPE.md) |
| Traveler needing visa, health or safety guarantees | Explicit product boundary; JourneyLab links evidence and never guarantees | [PRODUCT_CHARTER](PRODUCT_CHARTER.md) §6 |
| Advertiser or data broker | Prohibited use of sensitive trip data | [SECURITY_PRIVACY_RESPONSIBLE_AI](../03-architecture/SECURITY_PRIVACY_RESPONSIBLE_AI.md) |
