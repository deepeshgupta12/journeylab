---
step_id: STEP-011
title: Candidate generation
status: DISCOVERY
release: Phase 1
owners: ["Deepesh Kumar Gupta"]
dependencies: [STEP-010]
requirement_ids: [REQ-CONS-003]
api_ids: []
event_ids: []
data_ids: [DATA-009]
ai_ids: [AI-005]
knowledge_graph_check: REQUIRED
last_updated: 2026-08-05
---

# STEP-011 — Candidate generation

> Status is authoritative in [MASTER_TRACKER](../02-delivery/MASTER_TRACKER.md).

## 1. Outcome
A diverse, ranked pool of eligible activities, routes and lodging anchors exists with explicit eligibility and exclusion reasons, and **no option violating a hard constraint can reach the solver**.

## 2. Why this step exists
Filtering after ranking is the classic ordering bug: a ranked list re-introduces an excluded option, and an inaccessible venue reaches a wheelchair user's itinerary. Separating hard filtering from ranking makes that structurally impossible.

## 3. Scope
Candidate generation across must-see, quiet, indoor, accessible and fallback categories; hard filters applied before ranking; exclusion reasons recorded; diversity preservation; limited-choice state for sparse packs.

## 4. Explicit exclusions
Scheduling feasibility is [STEP-012](STEP-012-scenario-optimisation-and-simulation.md) — this step decides *what is eligible*, not *what fits*.

## 5. Actors, permissions and data access
| Actor | Permission | Data accessed | Sensitivity |
| --- | --- | --- | --- |
| Recommendation service | Tenant-scoped read | Evidence pack, preference vector | Licensed + PII |

## 6. Preconditions and dependencies
[STEP-010](STEP-010-destination-evidence-assembly.md) frozen evidence pack.

## 7. Inputs and source systems
`TripBrief`, `EvidencePack`, preference vector, accessibility constraints.

## 8. Detailed normal workflow
1. Service generates candidates across all five categories from the frozen pack.
2. **Hard filters apply first** — accessibility, exclusions, budget ceiling, date validity.
3. Eligible candidates are ranked against the preference vector (`AI-005`).
4. Diversity is enforced so the pool is not near-duplicates.
5. Exclusion reasons are recorded for every rejected candidate.

## 9. Alternate, partial and failure workflows
| Condition | Behavior | User-visible result | Requirement |
| --- | --- | --- | --- |
| Sparse pack | Transparent limited-choice state; optional wider radius | Honest scarcity — **never fabricated candidates** | REQ-CONS-003 |
| All candidates filtered out | Return the filter reasons, not an empty screen | Actionable explanation | REQ-CONS-005 |
| Ranker unavailable | Deterministic popularity/distance ordering | Reduced personalization | REQ-AI-007 |
| Accessibility data missing | Candidate excluded and the **gap disclosed**, not assumed accessible | Explicit limitation | ASM-020 |

## 10. State machine and lifecycle transitions
`pack frozen → generated → filtered → ranked → diversified → pool available`.

## 11. Frontend implementation
No dedicated route. Exclusion reasons surface in the comparison evidence drawer ([STEP-013](STEP-013-visual-comparison.md)) and in the limited-choice state.

## 12. Backend implementation
`services/recommendation/src/candidates.py` (`PROPOSED`).

## 13. API, event and integration contracts
Internal only; consumed by the solver. No public API or event.

## 14. Data model, migration and retention effects
Writes `DATA-009` Candidate with ranking features and exclusion reasons, scoped to one generation run.

## 15. AI, LLM, RAG, ML and data-science implementation
**`AI-005` candidate ranking.** Non-AI baseline: popularity + distance heuristic. **Ranking runs strictly after deterministic hard filters and can never reintroduce an excluded option** (`REQ-CONS-003`). Diversity uses MMR-style constrained diversification. Evaluation: candidate recall against the destination evaluation set, and a negative test proving prohibited options never appear.

## 16. Security, privacy, accessibility and responsible-AI controls
Accessibility is a **hard filter**, not a ranking signal — demoting rather than excluding an inaccessible venue would be a safety failure. Preference vectors carry consent scope. Tenant-scoped reads only.

## 17. Observability, analytics and KPIs
Candidate recall, pool size distribution, exclusion reason histogram, diversity metric, limited-choice state frequency (a leading indicator of pack quality).

## 18. Files and modules expected to change
`services/recommendation/src/candidates.py` (`PROPOSED`).

## 19. Knowledge-graph pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | `BLOCKED` — static fallback |
| Queries to run | KG-Q-006 on the filter/rank boundary |
| Expected impact | Pool feeds the solver directly |

## 20. Blast-radius assessment
A filter-ordering defect is **high severity and low detectability** — the output looks plausible. Property-based tests with adversarial candidates are the only reliable guard.

## 21. Implementation task checklist — sub-steps
| Sub-step | Outcome |
| --- | --- |
| STEP-011.01 | Category generation across the five candidate classes |
| STEP-011.02 | Hard filter layer with recorded exclusion reasons |
| STEP-011.03 | Preference ranking (`AI-005`) with deterministic fallback |
| STEP-011.04 | Diversity enforcement |
| STEP-011.05 | Limited-choice state and wider-radius option |

## 22. Test and evaluation plan
`TST-CONS-003`. Property-based tests generate adversarial candidates that must never survive filtering. Recall measured against the destination evaluation set.

## 23. Deployment, feature flag and migration plan
Ranker behind a flag with the deterministic baseline always available.

## 24. Rollback, compensation and recovery plan
Disable the ranker flag; the deterministic ordering keeps the pool usable. Hard filters are never behind a flag.

## 25. Acceptance criteria
- [ ] Hard filters run before ranking; prohibited options never reach the solver (`REQ-CONS-003`)
- [ ] Every exclusion carries a reason
- [ ] Candidate recall meets the destination evaluation set
- [ ] Sparse packs produce a transparent limited-choice state, not fabricated options
- [ ] Missing accessibility data excludes rather than assumes

## 26. Evidence required for completion
Recall measurement; adversarial filter test results; diversity metric; exclusion-reason sample.

## 27. Open questions, risks and decisions
Diversity threshold is unset pending `DEC-005`. Wider-radius behavior needs a product decision on how far is still "this trip".

## 28. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Sub-steps completed | 0 of 5 |
| Regression result | — |
| Verified by | — |
