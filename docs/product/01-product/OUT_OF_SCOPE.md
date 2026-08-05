# JourneyLab — Scope Boundaries, Phasing and Gating

| Field | Value |
| --- | --- |
| Owner | Product Lead (unassigned — `BLK-001`) |
| Status | `DISCOVERY` |
| **Scope position** | **Nothing is permanently out of scope.** Every capability is either in a release phase or gated on a named condition |
| Upstream source | Blueprint §23, reclassified per repository-owner direction (2026-08-05) |
| Last reviewed | 2026-08-05 |

Navigation: [Charter](PRODUCT_CHARTER.md) · [Scope](PRODUCT_SCOPE.md) · [Roadmap](../02-delivery/ROADMAP.md) · [Decisions](../02-delivery/DECISION_LOG.md) · [Master tracker](../02-delivery/MASTER_TRACKER.md) · [00-START-HERE](../00-START-HERE.md)

---

## 1. How scope is classified

The repository owner has directed that **no capability is excluded from the product**. This document therefore contains no "will never build" list. Every item is in one of three states:

| Class | Meaning | Where tracked |
| --- | --- | --- |
| **PHASED** | In the product; scheduled to a release phase; has a step file and a tracker row | [MASTER_TRACKER](../02-delivery/MASTER_TRACKER.md), status `DEFERRED` until its phase |
| **GATED** | In the product; cannot start until a named external condition is met (legal, contractual, safety, or evidence) | §3 below, with the condition and its owner |
| **UNDECIDED** | Direction not yet chosen; blocks planning until decided | [DECISION_LOG](../02-delivery/DECISION_LOG.md) |

**Why the distinction matters:** a phased item needs scheduling; a gated item needs someone to go and obtain something (a licence, an approval, a review). Treating a gated item as merely "later" is how programmes discover in month nine that they cannot ship.

---

## 2. PHASED — scheduled work

Each has a complete step file, so the gate is deliberate and reviewable (portfolio standard §7.31).

| Step | Capability | Phase | Gate that releases it |
| --- | --- | --- | --- |
| [STEP-014](../08-steps/STEP-014-interactive-what-if-editing.md) | Interactive what-if editing with incremental recompute | 2 | Phase 1 exit gates pass |
| [STEP-015](../08-steps/STEP-015-collaboration-and-decision.md) | Collaboration, invitations, votes, proposals | 2 | Phase 1 exit + anti-abuse controls (`REQ-SEC-008`) |
| [STEP-022](../08-steps/STEP-022-analytics-feedback-and-experimentation.md) | Experimentation and causal analysis | 2 | Exposure/outcome integrity proven (`REQ-OBS-006`) |
| [STEP-017](../08-steps/STEP-017-live-trip-activation-and-offline-pack.md) | Offline pack and live activation | 3 | Phase 2 exit + location safeguards (`RISK-006`) |
| [STEP-018](../08-steps/STEP-018-condition-monitoring.md) | Condition monitoring and impact matching | 3 | Provider event feeds contracted |
| [STEP-019](../08-steps/STEP-019-controlled-replanning.md) | Controlled partial replanning | 3 | Live pilot demonstrates safe adaptation |
| [STEP-020](../08-steps/STEP-020-post-trip-learning.md) | Preference learning from explicit feedback | 3 | Consent and reset controls verified |
| [STEP-028](../08-steps/STEP-028-advisor-workspace-and-commercial-scale.md) | Advisor workspace, white-label, commercial scale | 4 | Positive contribution margin + repeatable onboarding |

**Phased within otherwise-Phase-1 steps:**

| Element | Parent step | Phase |
| --- | --- | --- |
| Right-to-left layout implementation (readiness only in P1) | STEP-003 | 2 |
| Second destination pack with automated ingestion | STEP-005 | 2 |
| Kafka event streaming (managed queue acceptable at MVP) | STEP-006 | 2 |
| Neo4j-backed domain GraphRAG for end-user answers | STEP-026 | 2 |
| Tenant-managed encryption keys (enterprise tier) | STEP-023 | 4 |
| Multi-region deployment and residency configuration | STEP-027 | 4 |

---

## 3. GATED — in scope, blocked on a named condition

These are **not excluded**. Each names the condition, the owner and where the work lands once the condition is met. Several were listed as permanent exclusions in the source blueprint; they are reclassified here as gated.

| ID | Capability | Gating condition | Owner | Lands in |
| --- | --- | --- | --- | --- |
| GATE-001 | **Payment processing, ticket issuance, merchant of record** | Payment licensing, PCI scope assessment, settlement/refund/chargeback design, liability review | Commercial + Legal | New step (`STEP-029`) once `DEC-003` resolves |
| GATE-002 | **Booking APIs (write actions to providers)** | Liability, security and operational review (`REQ-BOOK-005`) | Product + Security | STEP-028, Phase 4 |
| GATE-003 | **Guarantees on visas, health, safety, accessibility, real-time availability** | Professional/legal sign-off per claim type and jurisdiction, plus a data source contractually warranting accuracy | Legal + Product | Requires a warranted data source; until then the product links evidence and states uncertainty |
| GATE-004 | **Autonomous changes to confirmed bookings or shared canonical plans** | User-trust evidence that auto-apply is wanted, plus per-change consent design. `EV-001` currently shows 6% full trust in AI decisions | Product | Revisit after Phase 3 live-pilot data |
| GATE-005 | **Global destination coverage** | Repeatable destination onboarding proven (Phase 4 exit gate) | Data | Phase 4 onward, region by region |
| GATE-006 | **Ingestion of any protected travel content or provider data** | Executed licence covering permitted use, cache duration and attribution (`CON-002`, `RISK-001`) | Data + Legal | STEP-005, per source |
| GATE-007 | **Advertising or personalization using accessibility, age, precise location or sensitive trip data** | Lawful basis, explicit consent design, and a privacy review concluding it is permissible | Privacy + Legal | Not scheduled; would require a new charter decision |
| GATE-008 | **Model training on customer trip content** | Explicit consent basis and a documented data-use design | Privacy + AI/ML | Requires a consent decision first |
| GATE-009 | **Corporate travel: policy compliance, expense integration, duty of care** | A named design partner and a buyer decision — this changes the buyer, not just the feature set | Product | Would follow a charter amendment |
| GATE-010 | **Multi-month / round-the-world itineraries** | `ASM-015` validated and solver scaling proven beyond the 3–7 day window | Product + Backend | After Phase 2 solver measurement |
| GATE-011 | **Native iOS/Android applications** | Evidence that the PWA cannot meet offline or notification needs | Frontend | Revisit at Phase 3 |
| GATE-012 | **Social feed, public itinerary sharing, user-generated content** | Moderation, safety and abuse design; interacts with `RISK-006` stalking risk | Product + Security | Not scheduled |

---

## 4. UNDECIDED — blocks classification

| ID | Open decision | Blocks |
| --- | --- | --- |
| DEC-002 | Phase 1 destination region | `STEP-005`, `STEP-010`, all evaluation corpora |
| DEC-003 | Business model: affiliate-only, subscription, hybrid | Whether `STEP-029` (billing) exists; `GATE-001` |
| DEC-004 | Identity provider | `STEP-002` |
| DEC-005 | Numeric KPI thresholds | Release gates |
| DEC-006 | KPI review cadence and forum | Governance |
| DEC-007 | Cloud provider, region, residency | `STEP-027`, `GATE-003` jurisdiction analysis |
| DEC-008 | Routing provider and wheelchair profile support | `STEP-005`, accessibility claims |
| DEC-009 | Event backbone: managed queue vs. Kafka | `STEP-006` |

---

## 5. What the MVP deliberately does *not include yet*

This is a statement about **sequencing**, not exclusion. Phase 1 ships: coverage landing, guest/account onboarding with consent, trip brief, evidence assembly, candidate generation, CP-SAT solving with Monte Carlo uncertainty, visual comparison, deep-link booking handoff, admin/curation, observability, privacy/deletion, knowledge graph and release automation.

Everything else in §2 and §3 arrives later or on a condition. Nothing is written off.

---

## 6. Definition of done for general availability

From blueprint §23, retained as the GA contract. Verified in [RELEASE_READINESS_CHECKLIST](../06-quality/RELEASE_READINESS_CHECKLIST.md).

1. One supported region has documented coverage, source rights, freshness and outage behavior.
2. All end-to-end steps from discovery through deletion are implemented **or explicitly gated by release phase**.
3. Scenario generation passes hard-constraint, diversity, citation, latency and cost thresholds.
4. Frontend passes WCAG 2.2 AA and completes critical tasks without a map or network connection where promised.
5. Security, privacy, threat model, backup/restore and incident playbooks reviewed and rehearsed.
6. API clients, runbooks, model cards, data contracts, code graph and architecture documentation current **at the release commit**.
7. Pilot users demonstrate repeatable value; support ownership and commercial terms defined.
