---
step_id: STEP-014
title: Interactive what-if editing
status: DEFERRED
release: Phase 2
owners: ["Deepesh Kumar Gupta"]
dependencies: [STEP-013]
requirement_ids: [REQ-CONS-010, REQ-CONS-011, REQ-A11Y-005]
api_ids: [API-009]
event_ids: []
data_ids: [DATA-011, DATA-012]
ai_ids: [AI-006]
knowledge_graph_check: REQUIRED
last_updated: 2026-08-05
---

# STEP-014 — Interactive what-if editing

> Status is authoritative in [MASTER_TRACKER](../02-delivery/MASTER_TRACKER.md). **`DEFERRED` to Phase 2** — gated on Phase 1 exit.

## 1. Outcome
When a traveler changes budget, pace, weather tolerance or an activity, only the affected portion recomputes; no unaffected day changes without an explanation, and every edit is reversible.

## 2. Why this step exists
Comparison shows what exists; editing lets a traveler steer. Without incremental recompute, every adjustment costs a full regeneration and the interaction stops feeling like a conversation with the plan.

## 3. Scope
Typed what-if edits; impact preview before applying; protected-item locking; incremental recompute of affected segments; score deltas; undo/redo history; merge/review state for conflicting edits.

## 4. Explicit exclusions
Live in-trip replanning is [STEP-019](STEP-019-controlled-replanning.md) — it operates under different constraints (current location, completed items).

## 5. Actors, permissions and data access
| Actor | Permission | Data accessed | Sensitivity |
| --- | --- | --- | --- |
| PER-001 traveler | Edit own scenario | Own scenario versions | PII |
| PER-002 collaborator | Propose edits (editor scope) | Scoped | PII |

## 6. Preconditions and dependencies
[STEP-013](STEP-013-visual-comparison.md); Phase 1 exit gates passed.

## 7. Inputs and source systems
Scenario version, typed edit command, dependency graph, protected-item flags, evidence pack.

## 8. Detailed normal workflow
1. Traveler adjusts a slider or numeric input, or swaps an activity.
2. System computes the **impact scope** and previews affected days plus estimated recompute time.
3. Traveler applies; protected items are locked.
4. Solver recomputes only affected segments.
5. New scenario version is created with score deltas and a change explanation.
6. Undo/redo history is retained; every change offers one-click revert.

## 9. Alternate, partial and failure workflows
| Condition | Behavior | User-visible result | Requirement |
| --- | --- | --- | --- |
| Edit touches a protected item | Rejected with `itinerary.item_protected`; explicit unlock required | Clear refusal | REQ-CONS-011 |
| Edit makes the plan infeasible | Minimal conflict set; previous version preserved | Actionable explanation | REQ-CONS-005 |
| Solver timeout | **Last valid version preserved** | No loss | REQ-CONS-010 |
| Concurrent collaborator edit | Merge/review state | Explicit resolution, no silent overwrite | REQ-CONS-010 |
| Preview times out | Apply is blocked rather than guessing | Honest refusal | — |

## 10. State machine and lifecycle transitions
`vN → preview → applying → vN+1` or `→ rejected (vN preserved)`. Versions are immutable; undo moves the pointer rather than mutating.

## 11. Frontend implementation
`apps/web/src/features/whatif/WhatIfPanel.tsx` (`PROPOSED`) — sliders **and** direct numeric input, impact preview, progressive job status via SSE with cancellation, before/after deltas, one-click revert. **Every drag interaction has a keyboard alternative** (`REQ-A11Y-005`).

## 12. Backend implementation
`services/scenarios/src/commands.py` edit command, dependency-graph traversal, incremental solve invocation (`PROPOSED`).

## 13. API, event and integration contracts
`API-009` `POST /v1/scenarios/{scenarioId}/edits` with `If-Match` required and an impact-preview token.

## 14. Data model, migration and retention effects
Writes new `DATA-011` ScenarioVersion rows; reads `DATA-012` protected/completed flags. Version history grows per trip and needs a retention policy.

## 15. AI, LLM, RAG, ML and data-science implementation
Reuses **`AI-006` CP-SAT** on a restricted subgraph. No LLM participates. The technical core is **dependency-graph traversal to determine the minimal affected set** — an over-broad set destroys the value proposition, an under-broad set produces an invalid plan.

## 16. Security, privacy, accessibility and responsible-AI controls
Protected items cannot be modified by any automated path. Optimistic concurrency prevents silent overwrite. Keyboard alternative to drag; minimum target sizes; changes announced to assistive technology.

## 17. Observability, analytics and KPIs
`whatif_previewed/applied/reverted`, recompute scope size, recompute latency, revert rate (a usability signal), merge-conflict frequency. Feeds `KPI-003`.

## 18. Files and modules expected to change
All `PROPOSED` — see §11, §12.

## 19. Knowledge-graph pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | `BLOCKED` — static fallback |
| Queries to run | KG-Q-006; KG-Q-004 (which edits caused a branch, what was preserved) |
| Expected impact | Shares the solver with `STEP-012`; a solver change affects both |

## 20. Blast-radius assessment
Shares the solver path with scenario generation, so changes here can regress `STEP-012`. Regression check R1 must include the full `STEP-012` suite.

## 21. Implementation task checklist — sub-steps
| Sub-step | Outcome |
| --- | --- |
| STEP-014.01 | Dependency graph and minimal affected-set computation |
| STEP-014.02 | Typed edit commands and validation |
| STEP-014.03 | Impact preview with estimated recompute time |
| STEP-014.04 | Protected-item locking |
| STEP-014.05 | Incremental solve and score deltas |
| STEP-014.06 | Undo/redo and one-click revert |
| STEP-014.07 | Merge/review state for concurrent edits |
| STEP-014.08 | Keyboard alternatives and accessibility |

## 22. Test and evaluation plan
`TST-CONS-010`, `TST-CONS-011`, `TST-A11Y-005`. A key test: assert that **no unaffected day changed**, comparing versions field by field.

## 23. Deployment, feature flag and migration plan
Behind a Phase 2 flag. Version-history growth requires a retention decision before enabling broadly.

## 24. Rollback, compensation and recovery plan
Flag off returns users to read-only comparison. Existing versions remain valid and viewable.

## 25. Acceptance criteria
- [ ] Only affected segments recompute; any other change carries an explanation (`REQ-CONS-010`)
- [ ] Protected and booked items are never modified by an edit (`REQ-CONS-011`)
- [ ] Every edit is reversible
- [ ] Impact preview shown before applying
- [ ] Drag interactions have keyboard alternatives (`REQ-A11Y-005`)

## 26. Evidence required for completion
Unaffected-day invariance test; protected-item rejection test; recompute scope measurement; accessibility audit.

## 27. Open questions, risks and decisions
Version-history retention is undecided. How "affected" is defined for weather-tolerance changes (which can touch every outdoor activity) needs design work — the naive answer recomputes everything.

## 28. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Sub-steps completed | 0 of 8 |
| Regression result | — |
| Verified by | — |
