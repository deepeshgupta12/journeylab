# JourneyLab — Product Charter

| Field | Value |
| --- | --- |
| Product name | JourneyLab |
| Product slug | `journeylab` |
| Domain | Travel (consumer planning + in-trip decision support) |
| Target release | **MVP (Phase 1)** — three-to-seven-day scenario generation for one supported region |
| Source blueprint | `01_JourneyLab_Product_and_Technical_Blueprint.pdf` (v1.0, 5 August 2026), `00_AI_Product_Portfolio_Index.pdf` (v1.0) |
| Documentation owner | Product Lead (unassigned — see [ASSUMPTION_REGISTER](../02-delivery/ASSUMPTION_REGISTER.md) `ASM-001`) |
| Status | `DISCOVERY` — charter derived from blueprint; discovery assumptions remain untested |
| Last reviewed | 2026-08-05 |

Navigation: [00-START-HERE](../00-START-HERE.md) · [Problem & evidence](PROBLEM_AND_EVIDENCE.md) · [Personas](PERSONAS_AND_JOBS.md) · [Scope](PRODUCT_SCOPE.md) · [Requirements](FUNCTIONAL_REQUIREMENTS.md) · [Roadmap](../02-delivery/ROADMAP.md)

---

## 1. Product definition

JourneyLab is a consumer-facing planning and in-trip decision platform. It builds a **versioned digital representation of a proposed journey** — travelers, preferences, constraints, places, bookings, routes, budgets, risks and evidence — then generates and compares **multiple feasible scenarios**, allows controlled edits, and recalculates only the affected portion of the plan when conditions or preferences change.

It is a **simulation and decision system**, not a single-answer itinerary chatbot. The distinguishing product claim is: *a traveler can see several valid futures, understand why each is feasible, and keep control of the decision.*

**Source:** blueprint §1 (Product definition), §4 (Solution). Classification: **confirmed product decision** (from blueprint), pending discovery validation of buyer willingness (§2 of this file).

---

## 2. Value proposition

| Audience | Value claim | Evidence class |
| --- | --- | --- |
| Primary traveler | Compare 3–5 feasible trips in one surface instead of reconciling maps, blogs, booking tabs and spreadsheets | Assumption requiring validation — see [PROBLEM_AND_EVIDENCE](PROBLEM_AND_EVIDENCE.md) `EV-GAP-001` |
| Primary traveler | Every volatile fact (hours, price range, closure, transit) carries source, observed time and confidence, so the plan does not need re-verification | Source-supported direction (Booking.com AI sentiment: 89% want AI in planning, 6% fully trust it) |
| Mixed-mobility / family groups | Accessibility and pace are first-class hard constraints, not filters applied after the fact | Blueprint §2; **assumption** on willingness to disclose accessibility needs (`ASM-014`) |
| In-trip traveler | A disruption repairs the affected subgraph instead of forcing an itinerary rebuild | Blueprint §6.13; deferred to Phase 3 |
| Travel advisor (later) | Produce and publish a branded, evidence-backed recommendation for a client | Phase 4 — deferred, see [ROADMAP](../02-delivery/ROADMAP.md) |

---

## 3. Target buyer and user

- **MVP user and payer are the same person:** the primary traveler planning a 3–7 day trip into a supported region.
- **Later buyer:** travel advisors and agencies (organization workspace, delegated trip access, client handoff) — Phase 4.
- **Not a buyer in any documented phase:** airlines, OTAs or hotels purchasing distribution. JourneyLab is not merchant of record.

See [PERSONAS_AND_JOBS](PERSONAS_AND_JOBS.md) for the five documented personas and their permissions.

---

## 4. Desired outcomes and how they are measured

| Outcome | Measure | Owner | Detail |
| --- | --- | --- | --- |
| Reduce planning effort | Median time to first saved feasible scenario; external-tab count; task completion | Product | [SUCCESS_METRICS](SUCCESS_METRICS.md) `KPI-001` |
| Improve plan feasibility | Hard-constraint violation rate (target: zero in release corpus); stale-fact rate | Engineering + Data | `KPI-002` |
| Make trade-offs understandable | Comparison completion; explanation usefulness; edit-to-save conversion | Design | `KPI-003` |
| Support live adaptation | Time to accepted replan; percent of plan preserved; notification action rate | Product (Phase 3) | `KPI-004` |
| Build preference intelligence | Ranking acceptance lift; calibration; consented profile coverage; preference-reset success | AI/ML | `KPI-005` |

---

## 5. Business model

**Status: PROPOSAL REQUIRING APPROVAL.** The blueprint states affiliate deep links and (Phase 4) advisor white-label, but does not state pricing, commission terms or a subscription tier.

| Element | Documented position | Classification |
| --- | --- | --- |
| Affiliate deep-link attribution on booking handoff | In MVP scope, no payment processing | Confirmed (blueprint §6.10) |
| Consumer subscription / freemium boundary | **Not specified in the blueprint** | Open decision `DEC-003` in [DECISION_LOG](../02-delivery/DECISION_LOG.md) |
| Advisor white-label licensing | Phase 4 | Deferred |
| Booking APIs / merchant of record | Explicitly out of scope for first release; Phase 4 only after liability, security and operational review | Confirmed exclusion — [OUT_OF_SCOPE](OUT_OF_SCOPE.md) |
| Advertising | Prohibited on accessibility, age, precise-location or sensitive trip data | Confirmed constraint |

Unit economics are tracked as `KPI-007` (model, data-provider and compute cost per saved feasible trip) with the guardrail that quality, latency and diversity thresholds stay fixed during cost optimisation.

---

## 6. Product boundaries (confirmed)

1. JourneyLab **recommends and simulates**. The MVP does not issue tickets, hold inventory or act as merchant of record.
2. Prices and availability are **estimates** unless returned by a contracted provider with an observation timestamp and explicit terms. An estimate is never rendered as a confirmed price.
3. The LLM interprets language and explains trade-offs. **Deterministic solvers own** time, route, budget and hard-constraint validity.
4. No immigration, medical, legal or safety guarantees. JourneyLab links authoritative evidence and surfaces uncertainty.
5. The initial destination pack is deliberately narrow so source quality, routing and live adaptation are measurable before geographic expansion.

These five boundaries are release gates, not aspirations — each maps to a requirement and a test in [REQUIREMENTS_TRACEABILITY](REQUIREMENTS_TRACEABILITY.md).

---

## 7. Constraints

| ID | Constraint | Type | Consequence for delivery |
| --- | --- | --- | --- |
| CON-001 | WCAG 2.2 AA, keyboard-complete, screen-reader complete; every visualization has a table/list equivalent | Accessibility (portfolio standard §4.22) | Blocks GA; enforced in [STEP-003](../08-steps/STEP-003-design-system-and-application-shell.md) and every UI step |
| CON-002 | Destination/provider data may only be cached and used per licence terms; attribution and deletion honored | Legal / commercial | Blocks Phase 1 exit if terms unobtainable — stop condition `RISK-001` |
| CON-003 | Accessibility, age and precise-location data are sensitive; no advertising or unrelated personalization | Privacy | Enforced in [SECURITY_PRIVACY_RESPONSIBLE_AI](../03-architecture/SECURITY_PRIVACY_RESPONSIBLE_AI.md) |
| CON-004 | Deterministic validation owns money, capacity, eligibility, compatibility, permissions and workflow state | Architecture (portfolio standard §4.20) | Model output cannot mutate trip state — [AI architecture](../03-architecture/AI_LLM_RAG_ML_ARCHITECTURE.md) |
| CON-005 | Every AI feature ships with gold/adversarial evals, lineage, cost/latency budget, safe fallback and a named human decision boundary | Responsible AI | Release gate in [AI_ML_EVALUATION](../06-quality/AI_ML_EVALUATION.md) |
| CON-006 | No code change before the knowledge-graph pre-change and blast-radius protocol passes | Engineering governance | [CHANGE_IMPACT_PROTOCOL](../05-knowledge-graph/CHANGE_IMPACT_PROTOCOL.md) |
| CON-007 | Technology baseline is current as of August 2026 and must be revalidated before implementation; it is not a licence for continuous version churn | Technical | [TECHNICAL_ARCHITECTURE](../03-architecture/TECHNICAL_ARCHITECTURE.md) |
| CON-008 | Team size, budget, deadline and deployment region are **not specified** | Programme | Recorded as `ASM-002`, `ASM-003`; blocks capacity planning in [COST_AND_CAPACITY_MANAGEMENT](../07-operations/COST_AND_CAPACITY_MANAGEMENT.md) |

---

## 8. Assumptions carried from the blueprint

All five blueprint discovery assumptions are reproduced verbatim-in-substance and tracked as testable items in [ASSUMPTION_REGISTER](../02-delivery/ASSUMPTION_REGISTER.md):

- `ASM-010` Travelers will compare scenarios when comparison beats manual tabs/spreadsheets.
- `ASM-011` A destination pack (places, hours, transit, weather, price ranges) can be licensed or lawfully assembled.
- `ASM-012` Deep-link affiliate partners preserve enough itinerary context to avoid restarting the purchase journey.
- `ASM-013` Users give preference feedback if it visibly improves recommendations.
- `ASM-015` A 3–7 day window is large enough to demonstrate differentiated simulation without unbounded complexity.

None of these are treated as facts anywhere in this documentation set.

---

## 9. Stakeholders and decision rights

| Role | Decision rights | Consulted on | Status |
| --- | --- | --- | --- |
| Product Lead | Scope, release phase boundary, KPI definitions, stop conditions | Everything | Deepesh Kumar Gupta |
| Product Architect | Service boundaries, contract conventions, ADR approval | Roadmap sequencing | Deepesh Kumar Gupta |
| Staff Engineer (Backend) | Backend implementation, migration and rollout plans | Contracts, SLOs | Deepesh Kumar Gupta |
| Frontend Lead | Route inventory, state ownership, accessibility conformance | Design system | Deepesh Kumar Gupta |
| AI/ML Architect | Model class selection, eval gates, fallback behavior | Cost budgets | Deepesh Kumar Gupta |
| Security Architect | Threat model sign-off, authorization matrix, egress policy | Provider onboarding | Deepesh Kumar Gupta |
| Data Architect | Canonical entities, freshness policy, retention/deletion | Licence compliance | Deepesh Kumar Gupta |
| Privacy Owner | Consent model, deletion verification, DSR handling | Sensitive-data classes | Deepesh Kumar Gupta |
| TPM | Master tracker, dependency and critical path, release readiness | All gates | Deepesh Kumar Gupta |

**`BLK-001` CLOSED (2026-08-05, `ADR-010`).** Deepesh Kumar Gupta (`@deepeshgupta12`) is the named owner for all roles until the team grows. **Recorded consequence:** a single owner cannot satisfy four-eyes approval (`REQ-ADMIN-002`, `SC-GOV-02`) — that control is structurally unsatisfiable and must be resolved before `STEP-021` ships.

---

## 10. What would make us stop

Stop conditions are contractual, not rhetorical. Full detail in [RISK_REGISTER](../02-delivery/RISK_REGISTER.md).

- Critical destination facts cannot meet accuracy/freshness or permitted-use requirements (`RISK-001`).
- Users do not prefer scenario comparison to existing manual or single-itinerary tools (`RISK-002`).
- Quality-preserving unit economics cannot reach target contribution margin (`RISK-003`).
- Hard-constraint violations persist above the release threshold (`RISK-004`).
- Partners cannot provide a reliable handoff or attribution path (`RISK-005`).
- Live-companion privacy safeguards cannot be implemented (`RISK-006`).

---

## 11. Related documents

- [PROBLEM_AND_EVIDENCE](PROBLEM_AND_EVIDENCE.md) — why this problem, with source quality caveats
- [PRODUCT_SCOPE](PRODUCT_SCOPE.md) — 28 lifecycle steps from pre-signup to retirement
- [SUCCESS_METRICS](SUCCESS_METRICS.md) — KPI definitions and guardrails
- [OUT_OF_SCOPE](OUT_OF_SCOPE.md) — explicit exclusions and deferrals
- [MASTER_TRACKER](../02-delivery/MASTER_TRACKER.md) — the only source of delivery status
