---
step_id: STEP-009
title: Trip brief and structured constraints
status: DISCOVERY
release: Phase 1
owners: []
dependencies: [STEP-008, STEP-004]
requirement_ids: [REQ-CONS-001, REQ-CONS-002, REQ-AI-001, REQ-AI-002, REQ-AI-005, REQ-AI-008, REQ-TRIP-004]
api_ids: [API-003]
event_ids: [EVT-001]
data_ids: [DATA-005]
ai_ids: [AI-001]
knowledge_graph_check: REQUIRED
last_updated: 2026-08-05
---

# STEP-009 — Trip brief and structured constraints

> Status is authoritative in [MASTER_TRACKER](../02-delivery/MASTER_TRACKER.md).

## 1. Outcome
Natural-language intent and form input become an auditable typed planning specification, where every item is classified hard, soft, inferred or unresolved, and the user confirms the interpretation before any solving occurs.

## 2. Why this step exists
Everything downstream is only as correct as the brief. A misclassified hard constraint produces a plan that is infeasible in reality while appearing valid — the exact false-confidence failure the product exists to eliminate.

## 3. Scope
Natural-language entry; LLM extraction into a JSON Schema-validated constraint document; four-class classification; blocking-only clarification; structured constraint editor with units, priority and source; interpretation confirmation; immutable brief versioning.

## 4. Explicit exclusions
Evidence retrieval is [STEP-010](STEP-010-destination-evidence-assembly.md); feasibility solving is [STEP-012](STEP-012-scenario-optimisation-and-simulation.md). This step determines *what is asked for*, never *what is possible*.

## 5. Actors, permissions and data access
| Actor | Permission | Data accessed | Sensitivity |
| --- | --- | --- | --- |
| PER-001 traveler | Create/edit own brief | Own constraints | **Sensitive** |
| PER-002 collaborator | Contribute constraints (editor scope) | Own constraints | **Sensitive** |
| Intent service | Parse only | Redacted text | Sensitive |

## 6. Preconditions and dependencies
[STEP-008](STEP-008-account-consent-and-traveler-profile.md) profile, [STEP-004](STEP-004-contract-first-platform-apis.md) contracts.

## 7. Inputs and source systems
Origin, destinations, dates, travelers, budget, interests, pace, commitments, exclusions; traveler profile constraints; `EXT-006` LLM provider via the model gateway.

## 8. Detailed normal workflow
1. Traveler enters intent as free text, form input, or both.
2. `AI-001` extracts a typed draft against a JSON Schema, with per-field class and confidence.
3. Deterministic validators check dates, currencies, units, party composition and coverage.
4. System classifies each item hard / soft / inferred / unresolved.
5. **Only feasibility-blocking ambiguities** raise a clarification question.
6. System displays the full interpretation, labelling every inferred field.
7. Traveler edits and confirms; an immutable `TripBrief` version is written and `EVT-001` emitted.

## 9. Alternate, partial and failure workflows
| Condition | Behavior | User-visible result | Requirement |
| --- | --- | --- | --- |
| Ambiguous currency/age/date/mobility | Blocking clarification with the specific question | Targeted prompt | REQ-CONS-002 |
| Non-blocking ambiguity | Marked `unresolved`; workflow continues | Visible flag, no interruption | REQ-CONS-002 |
| Constraints impossible before search | Reject with a minimal conflict set **before** solving | Early, cheap feedback | REQ-CONS-005 |
| Schema violation from the model | **Fail closed** to the structured form | Form entry; no malformed brief | REQ-AI-002 |
| LLM unavailable or over budget | Structured form path | Fully functional | REQ-AI-007 |
| Injection attempt in user text | Treated as data; never as instruction | Ignored | REQ-SEC-006 |

## 10. State machine and lifecycle transitions
`draft → parsed → clarifying → interpreted → confirmed (immutable vN)`. A change after confirmation creates `vN+1`; it never mutates `vN`, because existing scenarios reference it.

## 11. Frontend implementation
`apps/web/src/features/brief/` (`PROPOSED`) — progressive natural-language entry, constraint editor with units/priority/source, inline blocking clarifications, autosave with visible status, version history, undo, conflict resolution. Class is conveyed by **text and icon, not colour**.

## 12. Backend implementation
`services/ai/src/orchestrator.py`, `services/ai/src/prompts/`, `services/ai/src/guardrails.py`, brief validation and versioning in `apps/api/src/trips/` (`PROPOSED`).

## 13. API, event and integration contracts
`API-003` `PUT /v1/trips/{tripId}/brief` with **`If-Match` required**. Emits `EVT-001`. `INT-006` LLM provider via gateway.

## 14. Data model, migration and retention effects
Writes `DATA-005` TripBrief as an immutable version with four separate class collections. Retained with the trip; deleted with it.

## 15. AI, LLM, RAG, ML and data-science implementation
**`AI-001` TripBrief extraction.**
- **Non-AI baseline:** structured forms — fully functional and the permanent fallback.
- **Deterministic validators own** typing, dates, currency, units and coverage. A field the validator rejects is never accepted from the model.
- **Human approval required:** the user confirms the interpretation before solving.
- **Budget:** per-request cost and latency; degrade to the form rather than exceed.
- **Prohibited:** the model may not classify a constraint as *soft* if the user's phrasing is imperative — misclassification toward soft is the dangerous direction and is asymmetrically penalised in evaluation.
- **Evaluation:** field-level precision/recall, unit/date accuracy, hard/soft misclassification rate, blocking-ambiguity recall across locales.

## 16. Security, privacy, accessibility and responsible-AI controls
`SC-DET-01` model output cannot mutate state without validation and user authorization. `SC-DET-02` structured output fails closed. `SC-TOOL-01` read-only tools. `SC-REDACT-01` sensitive fields redacted before leaving the gateway. Inline clarifications are announced to assistive technology and do not steal focus.

## 17. Observability, analytics and KPIs
Extraction accuracy, clarification rate, edit-after-interpretation rate (a proxy for extraction quality), time from entry to confirmed brief (`KPI-003` start point), AI cost per brief.

## 18. Files and modules expected to change
All `PROPOSED` — see §11, §12.

## 19. Knowledge-graph pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | `BLOCKED` — static fallback |
| Queries to run | KG-Q-006; KG-Q-014 for prompt input paths |
| Expected impact | Brief version is consumed by evidence, candidates, solver — a schema change ripples through the whole chain |

## 20. Blast-radius assessment
High severity (wrong constraints produce wrong plans), moderate detectability (the edit-after-interpretation metric surfaces it), good reversibility (versions are immutable).

## 21. Implementation task checklist — sub-steps
| Sub-step | Outcome |
| --- | --- |
| STEP-009.01 | Brief schema and immutable versioning |
| STEP-009.02 | Deterministic validators (dates, currency, units, coverage) |
| STEP-009.03 | Structured constraint editor UI |
| STEP-009.04 | `AI-001` extraction via gateway with structured output |
| STEP-009.05 | Four-class classification and inferred-field labelling |
| STEP-009.06 | Blocking-only clarification flow |
| STEP-009.07 | Interpretation confirmation and `EVT-001` |
| STEP-009.08 | Extraction evaluation set and guardrails |

## 22. Test and evaluation plan
`TST-CONS-001`, `TST-CONS-002`, `TST-AI-001`, `TST-AI-002`, `TST-AI-005`, `TST-AI-008`, `TST-TRIP-004`. Gold extraction set spanning locales, currencies, date formats and accessibility phrasings; adversarial set for injection and ambiguity.

## 23. Deployment, feature flag and migration plan
Natural-language entry behind a flag; the form path is always available. Prompt versions roll out independently of application deploys.

## 24. Rollback, compensation and recovery plan
Disable the NL flag to fall back to forms with no loss of capability. Prompt rollback is independent of deployment. Existing brief versions are unaffected by either.

## 25. Acceptance criteria
- [ ] Four constraint classes represented separately, never auto-promoted (`REQ-CONS-001`)
- [ ] Only blocking ambiguities prompt; interpretation shown before solving (`REQ-CONS-002`)
- [ ] User can edit the structured brief and understand every inferred field
- [ ] Model output cannot write brief state without validation and confirmation (`REQ-AI-001`)
- [ ] Schema violation fails closed to the form (`REQ-AI-002`)
- [ ] Only allowlisted read tools are exposed (`REQ-AI-005`)
- [ ] Cost/latency budget enforced with degradation (`REQ-AI-008`)

## 26. Evidence required for completion
Extraction evaluation report by locale; misclassification analysis; clarification-rate measurement; fallback-path e2e run; AI trace sample with redaction verified.

## 27. Open questions, risks and decisions
`ASM-024` — extraction precision across locales is unvalidated; if it fails, conversational entry drops from MVP and forms remain. Locale coverage for Phase 1 is undecided pending `DEC-002`.

## 28. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Sub-steps completed | 0 of 8 |
| Regression result | — |
| Verified by | — |
</content>
