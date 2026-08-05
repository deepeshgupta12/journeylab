# JourneyLab — Problem and Evidence

| Field | Value |
| --- | --- |
| Owner | Product Lead (unassigned) |
| Status | `DISCOVERY` |
| Upstream source | Blueprint §2 (Problem statement), §3 (Evidence and sources) |
| Last reviewed | 2026-08-05 |

Navigation: [Charter](PRODUCT_CHARTER.md) · [Personas](PERSONAS_AND_JOBS.md) · [Scope](PRODUCT_SCOPE.md) · [Assumptions](../02-delivery/ASSUMPTION_REGISTER.md) · [00-START-HERE](../00-START-HERE.md)

---

## 1. Problem statement

Travel planning is a **constrained decision problem** that most products present as a search or content-generation problem.

A traveler must jointly balance budget, travel time, opening hours, weather, crowding, group energy, mobility, transfers and personal priorities. Changing any one factor frequently invalidates several downstream choices. Yet most planners return a single polished itinerary without exposing feasibility, alternatives or uncertainty.

The result is **false confidence**. A traveler cannot easily tell whether a plan is fragile, exhausting, weather-dependent, or materially more expensive than an equally attractive alternative. Families and mixed-mobility groups pay an additional coordination cost because pace and accessibility are rarely first-class inputs.

The opportunity is not to generate more recommendations. It is to let people **understand the consequences of their choices, compare several valid futures, and retain the decision** — in a category where enthusiasm for AI is high but trust is low.

---

## 2. Affected personas

| Persona | How the problem presents | Reference |
| --- | --- | --- |
| Primary traveler | Reconciles 5–15 browser tabs, a map and a spreadsheet; cannot compare total cost/effort across candidate plans | [PERSONAS_AND_JOBS](PERSONAS_AND_JOBS.md) `PER-001` |
| Trip collaborator | Cannot see whose constraint caused a conflict or what trade-off restores feasibility | `PER-002` |
| Travel advisor | Rebuilds client itineraries manually when one booking shifts; no reproducible rationale to hand over | `PER-003` |
| Content/data curator | No systematic way to see which destination facts are stale, disputed or unsourced | `PER-004` |
| Operations administrator | No visibility into which provider degradation is producing bad plans | `PER-005` |

---

## 3. Consequences (blueprint §2)

| ID | Consequence | Product response | Scope step |
| --- | --- | --- | --- |
| CQ-001 | Excessive time reconciling maps, blogs, social posts, booking sites and spreadsheets | Single comparison surface with synchronized map, timeline, ledger, scorecard | [STEP-013](../08-steps/STEP-013-visual-comparison.md) |
| CQ-002 | Plans contain unrealistic transfers, closed venues, duplicated routes, budget overruns, no recovery margin | CP-SAT feasibility with opening hours, travel matrix, rest and buffers | [STEP-012](../08-steps/STEP-012-scenario-optimisation-and-simulation.md) |
| CQ-003 | A disruption forces a full itinerary rebuild instead of recalculating the affected subgraph | Dependency graph + partial replan with protected items | [STEP-019](../08-steps/STEP-019-controlled-replanning.md) |
| CQ-004 | Groups cannot see whose constraints caused a conflict or which trade-off restores feasibility | Minimal conflict sets + constraint attribution without exposing sensitive detail | [STEP-015](../08-steps/STEP-015-collaboration-and-decision.md) |
| CQ-005 | Uncited AI recommendations get re-fact-checked, erasing the time advantage | Claim-to-source spans, observed time, confidence, contradiction display | [STEP-010](../08-steps/STEP-010-destination-evidence-assembly.md) |

---

## 4. Current alternatives and why they fall short

| Alternative | What it does well | Documented gap JourneyLab targets | Evidence class |
| --- | --- | --- | --- |
| Manual research (maps + blogs + spreadsheets) | Full user control, zero trust problem | No feasibility check; no recomputation; high time cost | Blueprint §2 — **assertion**, to be measured in discovery |
| Single-itinerary AI planners | Fast, fluent output | One answer, no alternatives, no citations, no constraint proof | Blueprint §2 — **assertion** |
| OTA / booking-site planners | Live inventory and purchase | Optimised for conversion, not feasibility or comparison | **Assertion**, not independently sourced |
| Travel advisors (human) | Judgement, accountability | Cost, latency, non-reproducible rationale | **Assertion** |

> **Caveat.** No competitive teardown has been performed for this documentation set. Every row above is a product hypothesis until discovery (`ASM-010`) tests it. Do not cite this table as market research.

---

## 5. Quantified evidence

Sources below are reproduced from blueprint §3 with their **original scope and publisher**. Two are vendor-published and are therefore treated as directional, not as universal facts.

| ID | Source | Publisher & date | What it actually says | How JourneyLab uses it | Quality |
| --- | --- | --- | --- | --- | --- |
| `EV-001` | Global AI Sentiment Report | **Booking.com**, 23 July 2025 | Across >37,000 consumers: 89% want to use AI in future travel planning; **6% fully trust AI**; 12% comfortable with independent AI decisions | Justifies assistive, cited, user-controlled design and explicit approval before canonical plan changes | **Vendor-published.** Directional only. Commercial interest in AI-positive framing. |
| `EV-002` | 2025 Traveler Value Index | **Expedia Group**, 20 May 2025 | >60% used social media for inspiration; 58% expect to be more price conscious | Justifies fragmented-inspiration problem framing and transparent cost trade-offs | **Vendor-published.** Directional only. |
| `EV-003` | The evolving passenger journey | **IATA**, 2026 | Baggage, border control and transfers identified as weaker journey stages; rising expectation of seamless, digital, personalized travel | Justifies treating connection and transfer risk as explicit constraints | Industry body; methodology not reviewed here |
| `EV-004` | 2025 Global Passenger Survey | **IATA**, 2025 | >10,000 responses across 200 countries; strong demand for mobile, convenient, integrated experiences | Justifies mobile-first live companion (Phase 3) | Industry body; survey self-selection not assessed |

### 5.1 What the evidence does *not* establish

State this explicitly in any deck derived from this document:

- **No source measures willingness to pay** for scenario comparison.
- **No source measures whether comparison reduces planning time.** `EV-001`'s 89% is intent to use AI, not intent to compare scenarios.
- `EV-001`'s 6% full-trust figure supports *caution in autonomy*; it does not prove demand for JourneyLab's specific mechanism.
- No source covers mixed-mobility/accessibility coordination cost, which is a core differentiator claim.
- No source establishes destination-data licensing feasibility (`ASM-011`), the single largest delivery risk.

---

## 6. Discovery gaps that must close before architecture work

Per portfolio standard §7.30, discovery runs against these gaps *before* architecture is committed.

| Gap ID | Question | Method | Blocks | Assumption |
| --- | --- | --- | --- | --- |
| `EV-GAP-001` | Will target travelers choose scenario comparison over their current workflow? | 15+ moderated comparison tasks (Phase 0 exit gate) | Phase 1 start | `ASM-010` |
| `EV-GAP-002` | Can one destination pack be licensed/assembled lawfully with acceptable freshness? | Provider term review + coverage audit | Phase 1 start | `ASM-011` |
| `EV-GAP-003` | Do affiliate partners preserve itinerary context on deep link? | Partner technical review of 2–3 candidates | [STEP-016](../08-steps/STEP-016-booking-handoff.md) | `ASM-012` |
| `EV-GAP-004` | Will users disclose accessibility/mobility constraints to a planning product? | Sensitive-topic interview protocol with privacy review | [STEP-008](../08-steps/STEP-008-account-consent-and-traveler-profile.md) | `ASM-014` |
| `EV-GAP-005` | Is 3–7 days sufficient to show differentiated simulation? | Prototype scenario diversity measurement on golden packs | [STEP-012](../08-steps/STEP-012-scenario-optimisation-and-simulation.md) | `ASM-015` |
| `EV-GAP-006` | What is the realistic cost per saved feasible trip at target quality? | Cost model against prototype traces | `KPI-007` | `ASM-016` |

---

## 7. Evidence handling rules for this product

These rules bind the product itself, not just this document:

1. A vendor statistic is never rendered in the product UI as a neutral fact.
2. Every volatile fact shown to a user carries source, observed time, effective time and confidence ([REQ-EVID-001](FUNCTIONAL_REQUIREMENTS.md)).
3. Conflicting evidence stays visible with a source hierarchy; it is never silently averaged or resolved by the model.
4. Absence of evidence lowers scenario confidence or blocks the affected option — it never triggers generation from model memory ([AI architecture](../03-architecture/AI_LLM_RAG_ML_ARCHITECTURE.md) `AI-004`).
5. Negative discovery results are recorded in [DECISION_LOG](../02-delivery/DECISION_LOG.md) as portfolio evidence, not discarded.
