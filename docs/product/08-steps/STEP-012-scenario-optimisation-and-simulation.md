---
step_id: STEP-012
title: Scenario optimisation and simulation
status: DISCOVERY
release: Phase 1
owners: ["Deepesh Kumar Gupta"]
dependencies: [STEP-011]
requirement_ids: [REQ-CONS-004, REQ-CONS-005, REQ-CONS-006, REQ-CONS-007, REQ-CONS-008, REQ-A11Y-006, REQ-NFR-004]
api_ids: [API-005, API-006, API-018]
event_ids: [EVT-003]
data_ids: [DATA-010, DATA-011]
ai_ids: [AI-006, AI-007, AI-008]
knowledge_graph_check: REQUIRED
last_updated: 2026-08-05
---

# STEP-012 — Scenario optimisation and simulation

> Status is authoritative in [MASTER_TRACKER](../02-delivery/MASTER_TRACKER.md).

## 1. Outcome
Three to five feasible, materially different, reproducible scenarios exist with score breakdowns and calibrated uncertainty — **or** a minimal conflict set explaining why none is possible.

## 2. Why this step exists
This is the product. Everything before it prepares inputs; everything after presents outputs. `REQ-CONS-004` (zero hard-constraint violations) is the single promise the product cannot break.

## 3. Scope
CP-SAT scheduling with opening hours, durations, travel, rest, commitments and accessibility; named objectives (balanced, low cost, low effort, weather-resilient); Monte Carlo over price, duration, weather and disruption; confidence intervals and fragility; diversity ranking; minimal conflict extraction; reproducibility.

## 4. Explicit exclusions
Visual comparison is [STEP-013](STEP-013-visual-comparison.md); incremental re-solve is [STEP-014](STEP-014-interactive-what-if-editing.md).

## 5. Actors, permissions and data access
| Actor | Permission | Data accessed | Sensitivity |
| --- | --- | --- | --- |
| Solver worker | Tenant-scoped, isolated | Candidate pool, matrices, brief | PII + licensed |
| Simulation worker | Tenant-scoped | Distributions | Derived |
| PER-001 traveler | Own trip | Scenario results | PII |

## 6. Preconditions and dependencies
[STEP-011](STEP-011-candidate-generation.md) pool and the travel-time matrix.

## 7. Inputs and source systems
Candidate pool, time-dependent travel matrix, budget distributions, risk models, solver configuration, **random seed**.

## 8. Detailed normal workflow
1. `API-005` returns a job handle within 500 ms and streams progress over SSE.
2. Solver builds the CP-SAT model: hard constraints plus weighted soft objectives.
3. Solver produces one schedule per named objective.
4. Monte Carlo simulates price, duration, weather and disruption; intervals and fragility are computed.
5. Diversity ranker ensures the set differs materially, not cosmetically.
6. Scenario versions are persisted with full lineage; `EVT-003` is emitted with seed and versions.

## 9. Alternate, partial and failure workflows
| Condition | Behavior | User-visible result | Requirement |
| --- | --- | --- | --- |
| No feasible solution | **Minimal conflict set + suggested relaxations** | A product answer, not an error | REQ-CONS-005 |
| Solver timeout | Best-known feasible result with the optimality gap disclosed, or the last valid version | Honest partial result | REQ-NFR-004 |
| Latency pressure | Degrade in fixed order: samples → scenario count (never below 3) → optimality gap | Wider intervals, fewer options | REQ-NFR-004 |
| Pack stale | Reject with `evidence.pack_stale`; rebuild | Regeneration prompt | REQ-EVID-005 |
| User cancels | Job cancelled; partial results discarded cleanly | Immediate | REQ-NFR-003 |
| **Any hard-constraint violation** | **Scenario is never emitted; SEV1 alert** | Nothing invalid is shown | REQ-CONS-004 |

## 10. State machine and lifecycle transitions
`queued → solving → simulating → ranking → ready` · `→ infeasible (conflict set)` · `→ failed (retryable)`. Infeasible and failed are **distinct** — one is an answer, the other an outage.

## 11. Frontend implementation
`apps/web/src/features/generation/` (`PROPOSED`) — SSE progress with meaningful stages, cancel, warnings, and **focus restoration plus screen-reader announcement** when results arrive (`REQ-A11Y-006`). Never a silent spinner.

## 12. Backend implementation
`services/solver/src/cp_sat.py`, `services/simulation/src/monte_carlo.py`, `services/ranking/src/diverse_ranker.py`, `services/scenarios/src/commands.py` (`PROPOSED`). Workers have explicit CPU/memory budgets and deterministic seeds.

## 13. API, event and integration contracts
`API-005` generate, `API-006` list, `API-018` SSE. Emits `EVT-003` carrying scenario IDs, objective labels, solver and model versions, and the seed.

## 14. Data model, migration and retention effects
Writes `DATA-010` Scenario and `DATA-011` ScenarioVersion. **Creation requires brief version, evidence pack, solver config and seed** — all four, or the scenario cannot exist. Zero hard-constraint violations is a creation precondition, not a post-check.

## 15. AI, LLM, RAG, ML and data-science implementation
**`AI-006` CP-SAT (deterministic), `AI-007` Monte Carlo, `AI-008` diversity ranking. No LLM participates in feasibility** (`ADR-002`).
- CP-SAT: hard constraints and weighted soft objectives; minimal conflict extraction; property-based tests over adversarial constraint combinations.
- Monte Carlo: calibrated distributions; **never a point estimate presented as certain**; sensitivity analysis.
- Diversity: MMR/constrained diversification addressing `RISK-002`.
- Reproducibility: identical inputs + seed ⇒ identical output, verified by test.

## 16. Security, privacy, accessibility and responsible-AI controls
Solver workers are isolated with resource budgets so one job cannot starve the pool. Tenant-scoped inputs. Streamed updates preserve focus and announce changes. Scores are computed, never model-generated.

## 17. Observability, analytics and KPIs
Generation duration (p95 vs. 45 s), solver saturation, **infeasibility reasons**, conflict-set sizes, optimality gap, diversity metric, reproducibility check results. Alerts `ALRT-SOLVER-001`, `ALRT-SOLVER-002` (SEV1). `KPI-001`, `KPI-002`.

## 18. Files and modules expected to change
All `PROPOSED` — see §12.

## 19. Knowledge-graph pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | `BLOCKED` — static fallback |
| Queries to run | KG-Q-006; KG-Q-010 (unsatisfiable constraint sets) once the domain graph exists |
| Expected impact | Solver config changes invalidate stored reproducibility guarantees |

## 20. Blast-radius assessment
**Highest severity in the product.** A defect produces plans that fail in the real world. Reversibility is good (versions immutable) but the harm occurs before rollback. Every solver sub-step requires owner approval and property-based coverage.

## 21. Implementation task checklist — sub-steps
| Sub-step | Outcome |
| --- | --- |
| STEP-012.01 | CP-SAT hard-constraint model + minimal conflict extraction |
| STEP-012.02 | Soft objectives and named objective profiles |
| STEP-012.03 | Time-dependent travel matrix integration |
| STEP-012.04 | Monte Carlo with calibrated distributions and intervals |
| STEP-012.05 | Fragility and sensitivity computation |
| STEP-012.06 | Diversity ranking (`AI-008`) |
| STEP-012.07 | Reproducibility: seed, config and version persistence |
| STEP-012.08 | Job handle, SSE progress, cancellation |
| STEP-012.09 | Degradation ordering under latency pressure |
| STEP-012.10 | Property-based adversarial constraint test suite |

## 22. Test and evaluation plan
`TST-CONS-004` … `TST-CONS-008`, `TST-A11Y-006`, `TST-NFR-004`. **Zero hard-constraint violations across the entire release corpus is release-blocking.** Reproducibility asserted by repeat-run equality. Conflict-set minimality verified on known-infeasible briefs.

## 23. Deployment, feature flag and migration plan
Solver configuration is versioned and rollable independently of application deploys. Objective profiles behind flags.

## 24. Rollback, compensation and recovery plan
Revert solver configuration version. **Previously generated scenarios remain valid** because they store their own config and seed — this is the practical payoff of the reproducibility requirement.

## 25. Acceptance criteria
- [ ] Zero hard-constraint violations in the full corpus (`REQ-CONS-004`)
- [ ] Infeasibility returns a **minimal** conflict set and relaxations (`REQ-CONS-005`)
- [ ] Identical inputs + seed reproduce identical scenarios (`REQ-CONS-006`)
- [ ] ≥3 materially different scenarios with deterministic labels (`REQ-CONS-007`)
- [ ] Uncertainty reported as intervals with fragility (`REQ-CONS-008`)
- [ ] p95 ≤ 45 s for a seven-day trip, cancellable (`REQ-NFR-004`)
- [ ] Streamed results restore focus and announce to assistive technology (`REQ-A11Y-006`)

## 26. Evidence required for completion
Full-corpus violation report (must be zero); reproducibility test output; latency distribution; diversity measurement; conflict-set minimality proof; calibration report.

## 27. Open questions, risks and decisions
`ASM-022` solver latency unvalidated; `ASM-023` material diversity unproven (`RISK-002`); `RISK-012` latency budget. Simulation distributions cannot be calibrated until a destination pack exists (`DEC-002`).

## 28. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Sub-steps completed | 0 of 10 |
| Regression result | — |
| Verified by | — |
