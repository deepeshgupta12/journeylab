# JourneyLab — Out of Scope and Deferred Work

| Field | Value |
| --- | --- |
| Owner | Product Lead (unassigned — `BLK-001`) |
| Status | `DISCOVERY` |
| Upstream source | Blueprint §23 (Out of scope and definition of done), §21 (roadmap phases) |
| Last reviewed | 2026-08-05 |

Navigation: [Charter](PRODUCT_CHARTER.md) · [Scope](PRODUCT_SCOPE.md) · [Roadmap](../02-delivery/ROADMAP.md) · [Master tracker](../02-delivery/MASTER_TRACKER.md) · [00-START-HERE](../00-START-HERE.md)

---

## 1. The distinction this document enforces

There are three different things people call "out of scope", and conflating them causes silent scope loss:

| Class | Meaning | Where tracked |
| --- | --- | --- |
| **EXCLUDED** | Will not be built in the first release; a deliberate product boundary | This document §2 |
| **DEFERRED** | In the product, gated to a later phase; has a complete step file and a tracker row | [MASTER_TRACKER](../02-delivery/MASTER_TRACKER.md) with status `DEFERRED` |
| **UNDECIDED** | Not yet chosen; blocks work until resolved | [DECISION_LOG](../02-delivery/DECISION_LOG.md) |

Portfolio standard §7.31 requires later scope to be **deliberately gated, not accidentally omitted**. Every deferred item below therefore points to a real step file.

---

## 2. EXCLUDED from the first release

| ID | Excluded capability | Reason | Would become in scope when |
| --- | --- | --- | --- |
| EXC-001 | Airline ticket issuance, payment processing, merchant-of-record responsibility | Requires licensing, PCI scope, settlement, refunds and liability JourneyLab does not carry | Phase 4 only after liability, security and operational review (`REQ-BOOK-005`) |
| EXC-002 | Guarantees about visas, health, safety, accessibility or real-time availability | JourneyLab links authoritative evidence and surfaces uncertainty; guarantees imply a duty of care it cannot discharge | Never within current product definition |
| EXC-003 | Global destination coverage | Coverage is deliberately narrow so source quality, routing and adaptation are measurable | Repeatable destination onboarding proven (Phase 4 exit gate) |
| EXC-004 | Autonomous changes to confirmed bookings or shared canonical plans | Violates the user-control principle; `EV-001` shows only 6% fully trust AI decisions | Never without explicit per-change user approval |
| EXC-005 | Advertising based on accessibility, age, precise location or sensitive trip data | Prohibited use of sensitive classes (`REQ-PRIV-004`) | Never |
| EXC-006 | Unlicensed ingestion of protected travel content or provider data | Legal and contractual exposure (`CON-002`) | Never |
| EXC-007 | Corporate travel policy compliance, expense integration, duty-of-care reporting | Different buyer, different obligations; would change the product definition | Requires a new charter, not a phase |
| EXC-008 | Multi-month or round-the-world itineraries | 3–7 day window is the stated MVP bound (`ASM-015`); complexity is unbounded beyond it | After `ASM-015` validated and solver scaling proven |
| EXC-009 | Native iOS/Android applications | Responsive PWA is the documented delivery vehicle | Requires evidence that PWA cannot meet offline/notification needs |
| EXC-010 | Real-time inventory or price guarantees from providers | Prices are estimates unless a contracted provider returns them with a timestamp and terms | Contracted provider integration only |
| EXC-011 | Model training on customer trip content | No documented consent basis or business need | Requires explicit consent design and a new decision record |
| EXC-012 | Social feed, public itinerary sharing or user-generated content moderation | Not part of the decision-system product definition; creates safety and moderation obligations | Requires a new charter |

---

## 3. DEFERRED to a later phase (in the product, gated)

Each has a full step file so the gate is reviewable, per portfolio standard §7.31.

| Step | Capability | Phase | Gate that releases it |
| --- | --- | --- | --- |
| [STEP-014](../08-steps/STEP-014-interactive-what-if-editing.md) | Interactive what-if editing with incremental recompute | 2 | Phase 1 exit: feasibility, citation, latency, usability, unit-cost gates pass |
| [STEP-015](../08-steps/STEP-015-collaboration-and-decision.md) | Collaboration, invitations, votes, proposals | 2 | Phase 1 exit + anti-abuse controls (`REQ-SEC-008`) implemented |
| [STEP-022](../08-steps/STEP-022-analytics-feedback-and-experimentation.md) | Experimentation and causal analysis | 2 | Exposure/outcome integrity proven (`REQ-OBS-006`) |
| [STEP-017](../08-steps/STEP-017-live-trip-activation-and-offline-pack.md) | Offline pack and live activation | 3 | Phase 2 exit + privacy safeguards for location (`RISK-006`) |
| [STEP-018](../08-steps/STEP-018-condition-monitoring.md) | Condition monitoring and impact matching | 3 | Provider event feeds contracted and health-monitored |
| [STEP-019](../08-steps/STEP-019-controlled-replanning.md) | Controlled partial replanning | 3 | Live pilot demonstrates safe adaptation |
| [STEP-020](../08-steps/STEP-020-post-trip-learning.md) | Preference learning from explicit feedback | 3 | Consent and reset controls verified (`REQ-TRIP-008`) |
| [STEP-028](../08-steps/STEP-028-advisor-workspace-and-commercial-scale.md) | Advisor workspace, white-label, commercial scale | 4 | Positive contribution margin + repeatable destination onboarding |

**Deferred within otherwise-Phase-1 steps:**

| Deferred element | Parent step | Phase |
| --- | --- | --- |
| Right-to-left layout implementation (readiness only in P1) | STEP-003 | 2 |
| Second destination pack with automated ingestion | STEP-005 | 2 |
| Tenant-managed encryption keys (enterprise tier) | STEP-023 | 4 |
| Kafka event streaming (managed queue acceptable in MVP) | STEP-006 | 2 |
| Neo4j-backed domain GraphRAG for end-user answers | STEP-026 | 2 |
| Multi-region deployment and residency configuration | STEP-027 | 4 |

---

## 4. UNDECIDED — blocks scope classification

These cannot be classified as excluded or deferred until decided. Full detail in [DECISION_LOG](../02-delivery/DECISION_LOG.md).

| ID | Open decision | Blocks |
| --- | --- | --- |
| DEC-002 | Which destination region is Phase 1 | `STEP-005`, `STEP-010`, all evaluation corpora |
| DEC-003 | Subscription / freemium boundary, or affiliate-only | Whether a billing step (`STEP-029`) must exist at all |
| DEC-004 | Identity provider selection | `STEP-002` |
| DEC-005 | Numeric KPI thresholds | [SUCCESS_METRICS](SUCCESS_METRICS.md), release gates |
| DEC-006 | KPI review cadence and decision forum | Governance |
| DEC-007 | Cloud provider, region and residency posture | [DEPLOYMENT_ARCHITECTURE](../03-architecture/DEPLOYMENT_ARCHITECTURE.md) |
| DEC-008 | Routing provider (affects wheelchair profile availability) | `STEP-005`, `REQ-A11Y` coverage in routing |

---

## 5. Definition of done for general availability

Reproduced from blueprint §23 as the GA contract. Verified in [RELEASE_READINESS_CHECKLIST](../06-quality/RELEASE_READINESS_CHECKLIST.md).

1. One supported region has documented coverage, source rights, freshness and outage behavior.
2. All end-to-end steps from discovery through deletion are implemented **or explicitly gated by release phase**.
3. Scenario generation passes hard-constraint, diversity, citation, latency and cost thresholds.
4. Frontend passes WCAG 2.2 AA and completes critical tasks without a map or network connection where promised.
5. Security, privacy, threat model, backup/restore and incident playbooks are reviewed and rehearsed.
6. API clients, runbooks, model cards, data contracts, code graph and architecture documentation are current **at the release commit**.
7. Pilot users demonstrate repeatable value; support ownership and commercial terms are defined.
</content>
