---
step_id: STEP-013
title: Visual comparison
status: DISCOVERY
release: Phase 1
owners: []
dependencies: [STEP-012, STEP-003]
requirement_ids: [REQ-CONS-009, REQ-EVID-004, REQ-A11Y-002, REQ-A11Y-003, REQ-AI-010]
api_ids: [API-006, API-007, API-008]
event_ids: [EVT-004]
data_ids: [DATA-011]
ai_ids: [AI-003]
knowledge_graph_check: REQUIRED
last_updated: 2026-08-05
---

# STEP-013 — Visual comparison

> Status is authoritative in [MASTER_TRACKER](../02-delivery/MASTER_TRACKER.md).

## 1. Outcome
A traveler understands the **material** differences between scenarios — cost, pace, crowds, risk, fragility — and selects one, using a map or using no map at all, by mouse, keyboard or screen reader.

## 2. Why this step exists
Generating comparable futures is worthless if the comparison is unreadable. This is where the product's value becomes visible, and where `REQ-A11Y-003` (nothing requires the map) is proven rather than claimed.

## 3. Scope
Synchronized map, day timeline, budget ledger and scorecard; material-difference highlighting with confidence ranges; evidence drawer with citations; accessible table equivalent and CSV export; scenario selection.

## 4. Explicit exclusions
Editing is [STEP-014](STEP-014-interactive-what-if-editing.md); collaboration is [STEP-015](STEP-015-collaboration-and-decision.md); booking is [STEP-016](STEP-016-booking-handoff.md).

## 5. Actors, permissions and data access
| Actor | Permission | Data accessed | Sensitivity |
| --- | --- | --- | --- |
| PER-001 traveler | Read all, **select canonical (owner only)** | Own scenarios | PII |
| PER-002 collaborator | Read, comment | Scoped scenarios | PII |

## 6. Preconditions and dependencies
[STEP-012](STEP-012-scenario-optimisation-and-simulation.md) scenario set and [STEP-003](STEP-003-design-system-and-application-shell.md) primitives.

## 7. Inputs and source systems
Scenario versions with score components, map layers, timeline data, budget ledger, evidence references and explanations.

## 8. Detailed normal workflow
1. Traveler opens comparison; two to five scenarios load progressively.
2. Map, timeline, ledger and scorecard **share one selection state**, addressable by URL.
3. Only material differences are highlighted, with confidence ranges shown.
4. `AI-003` explains trade-offs, with every volatile claim linked to an evidence span.
5. Traveler opens the evidence drawer to inspect source, observed time and conflicts.
6. Traveler selects a scenario; `API-008` sets the canonical plan and emits `EVT-004`.

## 9. Alternate, partial and failure workflows
| Condition | Behavior | User-visible result | Requirement |
| --- | --- | --- | --- |
| Map fails | Feature error boundary; **list/table comparison retains full function** | No capability lost | REQ-A11Y-003 |
| Chart fails | Table equivalent renders | Data still readable | REQ-A11Y-002 |
| Large scenario set | Progressive rendering with progress | No blank screen | Blueprint §8.113 |
| Stale evidence | Marked **at the point of use**, not only globally | Per-field staleness | REQ-EVID-005 |
| Explanation ungrounded | Claim removed before display; scores unchanged | Shorter prose | REQ-EVID-004 |
| Selection conflicts with another actor | 409; refetch and re-confirm | Explicit resolution | — |

## 10. State machine and lifecycle transitions
`scenarios ready → comparing → (selected canonical | request edit | request more evidence)`. Selection is owner-only and reversible until booking handoff.

## 11. Frontend implementation
`apps/web/src/features/compare/ScenarioCompare.tsx`, `features/map/ScenarioMap.tsx`, `features/timeline/DayTimeline.tsx`, `features/evidence/` (`PROPOSED`). MapLibre with clustering and route layers; ECharts/D3 for uncertainty ranges and budget waterfalls; **every visualization has a table equivalent and CSV export**; sticky difference controls; URL-addressable comparison state.

## 12. Backend implementation
`services/ranking/` comparison metrics, `services/retrieval/src/citations.py`, `services/scenarios/src/commands.py` selection (`PROPOSED`).

## 13. API, event and integration contracts
`API-006` list with metrics, `API-007` full scenario with evidence and score components, `API-008` select (owner only). Emits `EVT-004`. `INT-008` map tiles.

## 14. Data model, migration and retention effects
Reads `DATA-011`; writes the canonical pointer on `DATA-004`. No new entities.

## 15. AI, LLM, RAG, ML and data-science implementation
**`AI-003` trade-off explanation.** Non-AI baseline: templated deltas computed from score components — fully functional. **The explanation may never alter a score, price or feasibility verdict**; it describes solver output. Every volatile claim resolves to an evidence span or is removed before display. **Prohibited:** visa, health, legal or safety assertions (`REQ-AI-010`). Evaluation: groundedness, citation correctness ≥95%, trade-off completeness, calibrated uncertainty, prohibited-claim count of zero.

## 16. Security, privacy, accessibility and responsible-AI controls
**This step carries the heaviest accessibility load:** full parity without the map, table equivalents, CSV export, non-colour status, focus preservation during progressive render. Citations open in a drawer rather than navigating away. No sensitive collaborator constraint is displayed verbatim.

## 17. Observability, analytics and KPIs
`comparison_viewed`, `scenario_selected`, time-to-decision (`KPI-003` end point), comparison completion, explanation usefulness, citation failures reported by users (tracked **separately** from satisfaction), map/chart error rate.

## 18. Files and modules expected to change
All `PROPOSED` — see §11, §12.

## 19. Knowledge-graph pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | `BLOCKED` — static fallback |
| Queries to run | KG-Q-006; KG-Q-002 ("why this over that") once the domain graph exists |
| Expected impact | Consumes scenario shape — a score-component change breaks the scorecard |

## 20. Blast-radius assessment
High customer criticality, high detectability (visible), good reversibility. The subtle risk is an explanation that is technically grounded yet misleading — automated groundedness metrics will not catch it, which is why human review is scheduled per prompt change.

## 21. Implementation task checklist — sub-steps
| Sub-step | Outcome |
| --- | --- |
| STEP-013.01 | Accessible scenario table + CSV export (**built first**, so the map is never load-bearing) |
| STEP-013.02 | Day timeline with buffers |
| STEP-013.03 | Budget ledger and scorecard with score components |
| STEP-013.04 | MapLibre layers, clustering, list fallback |
| STEP-013.05 | Synchronized selection state, URL-addressable |
| STEP-013.06 | Material-difference detection and confidence ranges |
| STEP-013.07 | Evidence drawer with citations and conflicts |
| STEP-013.08 | `AI-003` explanation with claim-to-span validation |
| STEP-013.09 | Scenario selection and `EVT-004` |
| STEP-013.10 | Progressive rendering, error boundaries, focus management |

## 22. Test and evaluation plan
`TST-CONS-009`, `TST-EVID-004`, `TST-A11Y-002`, `TST-A11Y-003`, `TST-AI-010`. **The map-free journey is release-blocking.** Citation correctness ≥95% measured on a claim-to-span dataset.

## 23. Deployment, feature flag and migration plan
Explanation behind a flag; templated deltas always available. Map behind a flag so tile-provider issues degrade rather than break.

## 24. Rollback, compensation and recovery plan
Disable explanation or map flags; comparison remains fully functional in both cases by design.

## 25. Acceptance criteria
- [ ] Only material differences highlighted, with confidence ranges (`REQ-CONS-009`)
- [ ] Every volatile claim links to an evidence span (`REQ-EVID-004`)
- [ ] Every visualization has a table equivalent and CSV export (`REQ-A11Y-002`)
- [ ] **All comparison and selection tasks complete with the map disabled** (`REQ-A11Y-003`)
- [ ] No visa/health/legal/safety guarantees in any explanation (`REQ-AI-010`)
- [ ] Keyboard and screen-reader users complete the same comparison

## 26. Evidence required for completion
Map-disabled e2e run; screen-reader journey recording; citation correctness report; groundedness evaluation; human review of explanation quality.

## 27. Open questions, risks and decisions
`RISK-002` — if scenarios do not feel materially different, this surface cannot rescue them. Which score components are user-visible needs a design decision. Explanation length vs. completeness is an open trade-off.

## 28. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Sub-steps completed | 0 of 10 |
| Regression result | — |
| Verified by | — |
</content>
