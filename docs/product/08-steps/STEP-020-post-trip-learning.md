---
step_id: STEP-020
title: Post-trip learning
status: DEFERRED
release: Phase 3
owners: []
dependencies: [STEP-019]
requirement_ids: [REQ-TRIP-008, REQ-PRIV-003]
api_ids: [API-014]
event_ids: []
data_ids: [DATA-015, DATA-003]
ai_ids: [AI-009]
knowledge_graph_check: REQUIRED
last_updated: 2026-08-05
---

# STEP-020 — Post-trip learning

> Status is authoritative in [MASTER_TRACKER](../02-delivery/MASTER_TRACKER.md). **`DEFERRED` to Phase 3.**

## 1. Outcome
Recommendations improve from **explicit, inspectable** feedback. Every preference change is visible, attributable to a specific signal, and reversible.

## 2. Why this step exists
Personalization that users cannot see or correct is the profiling pattern this product explicitly rejects (`CON-003`). Doing it transparently is harder and is the differentiator.

## 3. Scope
Lightweight questions tied to specific decisions; distinguishing situational feedback from enduring preference; consented preference-vector updates with a visible diff; dismissal, correction and deletion of inferred learning; trip retrospective and quality labels.

## 4. Explicit exclusions
Ranking application is [STEP-011](STEP-011-candidate-generation.md); experimentation is [STEP-022](STEP-022-analytics-feedback-and-experimentation.md).

## 5. Actors, permissions and data access
| Actor | Permission | Data accessed | Sensitivity |
| --- | --- | --- | --- |
| PER-001 traveler | Give, correct, delete own feedback | Own trip + preferences | PII |
| PER-002 collaborator | Feedback on own experience | Own | PII |
| Preference service | Update with consent | Preference vector | **Sensitive** |

## 6. Preconditions and dependencies
[STEP-019](STEP-019-controlled-replanning.md); completed trip data.

## 7. Inputs and source systems
Completed activities, skips, edits, ratings, optional expense reconciliation, explicit consent.

## 8. Detailed normal workflow
1. After the trip, the system asks a few questions **tied to specific decisions**, not generic satisfaction.
2. Traveler answers; each response is labelled situational or enduring.
3. Only enduring, consented signals update the preference vector.
4. System shows exactly **what changed and why**.
5. Traveler can dismiss, correct or delete any inferred learning.
6. Retrospective and quality labels feed the evaluation datasets.

## 9. Alternate, partial and failure workflows
| Condition | Behavior | User-visible result | Requirement |
| --- | --- | --- | --- |
| No feedback given | **No negative labels created** — silence is not a signal | No change | REQ-TRIP-008 |
| Consent withheld | Feedback stored for the trip only; no profile update | Trip-level only | REQ-PRIV-002 |
| Traveler disagrees with a learned preference | Correction or deletion applied immediately | Restored behavior | REQ-TRIP-008 |
| Situational feedback | Excluded from the enduring profile | No over-generalisation | Blueprint §6.14 |
| Preference reset requested | Vector restored to a prior state | Verifiable rollback | REQ-TRIP-008 |

## 10. State machine and lifecycle transitions
`trip completed → feedback requested → (answered | ignored) → (situational | enduring) → profile vN+1 (consented)`. Profile versions are immutable.

## 11. Frontend implementation
`apps/web/src/features/feedback/`, `/settings/preferences` (`PROPOSED`) — decision-anchored questions, visible preference diff, per-item dismiss/correct/delete, reset control.

## 12. Backend implementation
`services/preference/`, `ml/training/preference_ranker.py`, `ml/features/trip_features.py` (`PROPOSED`).

## 13. API, event and integration contracts
`API-014` `POST /v1/trips/{tripId}/feedback` with a required consent scope.

## 14. Data model, migration and retention effects
Writes `DATA-015` Feedback with consent scope; updates `DATA-003` TravelerProfile as a new version. Deleted with the account; aggregates must meet de-identification thresholds and retain **no free-form sensitive text by default**.

## 15. AI, LLM, RAG, ML and data-science implementation
**`AI-009` preference learning.**
- Contextual ranking from **explicit** accept/reject/edit signals only.
- **No sensitive attribute may be inferred** (`REQ-PRIV-003`) — this is a hard boundary, not a tuning choice.
- Point-in-time correct features; time-based splits; leakage checks in CI.
- Must beat the deterministic baseline to ship; conservative exploration only.
- **Subgroup performance** measured across party composition and accessibility-constraint groups.
- Reset must fully restore prior behavior, verified by test.

## 16. Security, privacy, accessibility and responsible-AI controls
`SC-SENS-01` no inference of sensitive attributes; `SC-CONSENT-01` consent before any profile update; contestability — users can dismiss, correct or delete inferred learning. Feedback prompts are accessible and never modal-blocking.

## 17. Observability, analytics and KPIs
Feedback response rate (validates `ASM-013`), enduring-vs-situational ratio, preference change frequency, correction rate, **reset frequency** (a trust signal), ranking acceptance lift (`KPI-009`).

## 18. Files and modules expected to change
All `PROPOSED` — see §11, §12.

## 19. Knowledge-graph pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | `BLOCKED` — static fallback |
| Queries to run | KG-Q-006; **KG-Q-014** for sensitive-inference paths |
| Expected impact | Preference vector feeds candidate ranking — a change alters future recommendations for all trips |

## 20. Blast-radius assessment
A defect that infers a sensitive attribute is a **privacy harm that is difficult to detect and impossible to undo in the user's perception**. Static analysis proving no sensitive write path exists is mandatory, not optional.

## 21. Implementation task checklist — sub-steps
| Sub-step | Outcome |
| --- | --- |
| STEP-020.01 | Decision-anchored feedback prompts |
| STEP-020.02 | Situational vs. enduring classification |
| STEP-020.03 | Consented preference-vector update with visible diff |
| STEP-020.04 | Dismiss, correct, delete and reset controls |
| STEP-020.05 | `AI-009` ranker training with leakage checks |
| STEP-020.06 | Subgroup and calibration evaluation |
| STEP-020.07 | Trip retrospective and quality labels |

## 22. Test and evaluation plan
`TST-TRIP-008`, `TST-PRIV-003`. Leakage checks, subgroup performance, calibration, reset correctness. A static check must prove no code path writes a sensitive attribute from behavior.

## 23. Deployment, feature flag and migration plan
Phase 3 flag. Model promotion follows shadow → champion/challenger → gated rollout, rollable without an application deploy.

## 24. Rollback, compensation and recovery plan
Model rollback is independent of deployment. Preference versions allow per-user restoration. Disabling learning leaves the deterministic ranker fully functional.

## 25. Acceptance criteria
- [ ] Preference changes are shown, attributable and reversible (`REQ-TRIP-008`)
- [ ] No sensitive attribute is inferred from behavior (`REQ-PRIV-003`)
- [ ] Missing feedback creates no negative labels
- [ ] Situational feedback does not become an enduring preference
- [ ] Reset fully restores prior ranking behavior
- [ ] The ranker beats the deterministic baseline before promotion

## 26. Evidence required for completion
Leakage check results; subgroup performance report; reset correctness test; sensitive-inference static-check output; baseline comparison.

## 27. Open questions, risks and decisions
`ASM-013` — willingness to give feedback is unvalidated; without signal the ranker cannot be trained and this step delivers nothing. How much personalization is desirable at all is a product question with a privacy dimension.

## 28. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Sub-steps completed | 0 of 7 |
| Regression result | — |
| Verified by | — |
