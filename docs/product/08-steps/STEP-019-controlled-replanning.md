---
step_id: STEP-019
title: Controlled replanning
status: DEFERRED
release: Phase 3
owners: ["Deepesh Kumar Gupta"]
dependencies: [STEP-018, STEP-012]
requirement_ids: [REQ-LIVE-005, REQ-LIVE-006, REQ-CONS-011, REQ-PRIV-008]
api_ids: [API-013]
event_ids: [EVT-006]
data_ids: [DATA-011, DATA-012]
ai_ids: [AI-006]
knowledge_graph_check: REQUIRED
last_updated: 2026-08-05
---

# STEP-019 — Controlled replanning

> Status is authoritative in [MASTER_TRACKER](../02-delivery/MASTER_TRACKER.md). **`DEFERRED` to Phase 3.**

## 1. Outcome
A disrupted plan is repaired by recomputing only the affected subgraph, protecting completed and booked items, and **only after the traveler explicitly accepts** the change.

## 2. Why this step exists
Blueprint consequence `CQ-003`: a disruption forces travelers to rebuild the whole itinerary. Partial replanning is the payoff of the dependency-graph model, and `KPI-005` (plan preservation) measures whether it works.

## 3. Scope
Freezing completed and protected items; repair option generation with cost, time and effort deltas; explicit acceptance; offline pack and collaborator updates; escalation when no safe repair exists.

## 4. Explicit exclusions
Event detection is [STEP-018](STEP-018-condition-monitoring.md); pre-trip editing is [STEP-014](STEP-014-interactive-what-if-editing.md).

## 5. Actors, permissions and data access
| Actor | Permission | Data accessed | Sensitivity |
| --- | --- | --- | --- |
| PER-001 traveler | Generate and **accept** repairs (owner) | Own itinerary, ephemeral location | **Sensitive** |
| PER-002 collaborator | Generate repairs (editor); cannot accept | Scoped | PII |
| Replanning service | Tenant-scoped solve | Remaining plan | PII |

## 6. Preconditions and dependencies
[STEP-018](STEP-018-condition-monitoring.md) impact event; [STEP-012](STEP-012-scenario-optimisation-and-simulation.md) solver.

## 7. Inputs and source systems
Impact event, current location (**ephemeral, optional**), remaining plan, preferences, protected-item flags, refreshed evidence for the affected area.

## 8. Detailed normal workflow
1. Impact event triggers a durable impact-assessment workflow.
2. System freezes completed and protected items.
3. Solver recomputes only the affected subgraph.
4. Repair options are generated with cost, time and effort deltas and preserved-plan percentage.
5. Traveler reviews and **explicitly accepts** one, or consciously keeps the original.
6. On acceptance, a new scenario version is created, `EVT-006` emitted, offline pack and collaborators updated.

## 9. Alternate, partial and failure workflows
| Condition | Behavior | User-visible result | Requirement |
| --- | --- | --- | --- |
| No safe repair exists | **Clear escalation with nearby information sources** | Honest help, not a bad plan | Blueprint §6.13 |
| Traveler declines all repairs | Original preserved as a conscious decision | No forced change | REQ-LIVE-005 |
| Offline at time of impact | Repair queued; presented on reconnect | No silent change | REQ-LIVE-002 |
| Protected item would need changing | Excluded from repair; stated explicitly | Traveler decides manually | REQ-CONS-011 |
| Location unavailable | Repair computed from the last known itinerary node | Reduced precision, still useful | REQ-PRIV-008 |
| Solver timeout | Best-known repair or none; original preserved | Never an unvalidated plan | REQ-CONS-004 |

## 10. State machine and lifecycle transitions
`impact detected → assessing → repairs offered → (accepted → vN+1 | declined → vN preserved | escalated)`.

## 11. Frontend implementation
`apps/web/src/app/trips/[id]/live/` repair options (`PROPOSED`) — deltas, preserved-plan percentage, explicit accept action. **Acceptance is never a default or a timeout.**

## 12. Backend implementation
`services/live/` replanning orchestration via a Temporal durable workflow; solver invocation on the affected subgraph (`PROPOSED`).

## 13. API, event and integration contracts
`API-013` `POST /v1/impacts/{impactId}/repairs:generate` — **generation never mutates the canonical plan**; acceptance is a separate explicit call. Emits `EVT-006` with old/new version, preserved percent and deltas.

## 14. Data model, migration and retention effects
Writes `DATA-011` ScenarioVersion; reads `DATA-012` protected/completed flags. **Location is used transiently and not retained beyond the stated purpose** (`REQ-PRIV-008`).

## 15. AI, LLM, RAG, ML and data-science implementation
Reuses **`AI-006` CP-SAT** on the affected subgraph with completed and protected items as fixed constraints. No LLM participates in repair feasibility. Preserved-plan percentage is computed, not estimated.

## 16. Security, privacy, accessibility and responsible-AI controls
**Explicit acceptance is the responsible-AI boundary of this product** — `EV-001` shows only 6% of travelers fully trust autonomous AI decisions, and this is where autonomy would be most tempting. Location is ephemeral. Repair options are keyboard-accessible and readable one-handed in the live view.

## 17. Observability, analytics and KPIs
Time to repair proposal, feasible repair rate, **preserved-plan percentage (`KPI-005`)**, acceptance rate, escalation rate. Guardrail: a high preservation score on an unapproved change is invalid.

## 18. Files and modules expected to change
All `PROPOSED` — see §11, §12.

## 19. Knowledge-graph pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | `BLOCKED` — static fallback |
| Queries to run | KG-Q-006; **KG-Q-001** and **KG-Q-004** (what preserved, what branched) |
| Expected impact | Shares the solver with `STEP-012` and `STEP-014` |

## 20. Blast-radius assessment
Shares the solver path with two other steps; R1 must include both suites. Highest-stakes context: the traveler is mid-trip, so a wrong repair has immediate real-world consequences.

## 21. Implementation task checklist — sub-steps
| Sub-step | Outcome |
| --- | --- |
| STEP-019.01 | Durable impact-assessment workflow |
| STEP-019.02 | Freezing completed and protected items |
| STEP-019.03 | Affected-subgraph solve |
| STEP-019.04 | Repair option generation with deltas and preserved percentage |
| STEP-019.05 | Explicit acceptance flow (no defaults, no timeouts) |
| STEP-019.06 | Offline pack and collaborator update on acceptance |
| STEP-019.07 | Escalation path when no safe repair exists |

## 22. Test and evaluation plan
`TST-LIVE-005`, `TST-LIVE-006`, `TST-CONS-011`, `TST-PRIV-008`. A negative test must prove no path applies a repair without explicit acceptance. Preserved-plan percentage verified against a known-disruption corpus.

## 23. Deployment, feature flag and migration plan
Phase 3 flag. Repair generation can be enabled independently of notification delivery.

## 24. Rollback, compensation and recovery plan
Flag off leaves monitoring and the offline pack intact — travelers are informed but repairs are manual. Accepted repairs are versions and can be reverted to the prior version.

## 25. Acceptance criteria
- [ ] Replan requires explicit user acceptance (`REQ-LIVE-005`)
- [ ] Completed and protected items are preserved; preservation percentage reported (`REQ-LIVE-006`)
- [ ] Protected items are never modified (`REQ-CONS-011`)
- [ ] Location is not retained beyond the stated purpose (`REQ-PRIV-008`)
- [ ] No safe repair produces a clear escalation, not a poor plan

## 26. Evidence required for completion
Acceptance-required negative test; preserved-percentage measurement; escalation-path test; location-retention proof; disruption-corpus results.

## 27. Open questions, risks and decisions
Phase 3 exit thresholds for replan time and preservation are unset (`DEC-005`). What "nearby information sources" means when no repair exists needs a product decision — it is the difference between helpful and abandoning.

## 28. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Sub-steps completed | 0 of 7 |
| Regression result | — |
| Verified by | — |
