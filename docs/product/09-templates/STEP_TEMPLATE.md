# Step Template

> Copy to `08-steps/STEP-NNN-<short-name>.md`. **All 28 sections are mandatory.** A section that genuinely does not apply is marked `NOT_APPLICABLE` with a reason, an owner and the condition that would make it applicable — it is never deleted.

---

```markdown
---
step_id: STEP-NNN
title: [Step name]
status: NOT_STARTED
release: [Phase 1 | Phase 2 | Phase 3 | Phase 4]
owners: []
dependencies: []
requirement_ids: []
api_ids: []
event_ids: []
data_ids: []
ai_ids: []
knowledge_graph_check: REQUIRED
last_updated: YYYY-MM-DD
---

# STEP-NNN — [Step name]

> Status is authoritative in [MASTER_TRACKER](../02-delivery/MASTER_TRACKER.md).
> The front-matter `status` is a mirror; if they disagree, the tracker wins.

## 1. Outcome
*The verifiable user or business outcome. Not "build X" — what becomes true.*

## 2. Why this step exists
*The problem it solves and what breaks without it.*

## 3. Scope
## 4. Explicit exclusions
*What a reader might reasonably expect here but which lives elsewhere, with the link.*

## 5. Actors, permissions and data access
| Actor | Permission | Data accessed | Sensitivity |

## 6. Preconditions and dependencies
## 7. Inputs and source systems

## 8. Detailed normal workflow
*Numbered. Each step states actor, action and system response.*

## 9. Alternate, partial and failure workflows
| Condition | Behavior | User-visible result | Requirement |

## 10. State machine and lifecycle transitions
## 11. Frontend implementation
## 12. Backend implementation
## 13. API, event and integration contracts
## 14. Data model, migration and retention effects
## 15. AI, LLM, RAG, ML and data-science implementation
*If no AI: state `NOT_APPLICABLE` and why deterministic logic is correct here.*

## 16. Security, privacy, accessibility and responsible-AI controls
## 17. Observability, analytics and KPIs
## 18. Files and modules expected to change
*Label every path `PROPOSED` unless verified against the codebase.*

## 19. Knowledge-graph pre-change analysis
| Field | Value |
| Graph status | AVAILABLE / BLOCKED |
| Indexed commit | |
| Queries to run | |
| Expected impact areas | |

## 20. Blast-radius assessment
*Link `BR-NNN`. Summarise risk and confidence. Low confidence ⇒ risk is not LOW.*

## 21. Implementation task checklist — sub-steps
| Sub-step | Outcome | Contract | Schema | Impl | Test | Telemetry | Security | Docs | KG refresh | Rollout |
| STEP-NNN.01 | | | | | | | | | | |

*Each sub-step gets a file in `08-steps/sub-steps/STEP-NNN/` and ends in a commit + push per
[SUB_STEP_PROTOCOL](../02-delivery/SUB_STEP_PROTOCOL.md).*

## 22. Test and evaluation plan
## 23. Deployment, feature flag and migration plan
## 24. Rollback, compensation and recovery plan
## 25. Acceptance criteria
*Binary and observable. Each maps to a requirement and a test ID.*

## 26. Evidence required for completion
| Evidence | Where recorded |

## 27. Open questions, risks and decisions
## 28. Completion record
| Field | Value |
| Completed date | |
| Sub-steps completed | |
| Commits / PR | |
| Regression result | |
| Post-change graph evidence | |
| Verified by | |
```

---

## Authoring rules

1. **No vague tasks.** "Implement backend" is not a task. "Add `POST /v1/trips` with idempotency and tenant scoping, returning 422 on out-of-coverage" is.
2. **Every requirement in `requirement_ids` appears in §25** with an acceptance criterion.
3. **Failure paths are first-class.** §9 is not optional — a step without failure handling is unfinished.
4. **Paths are `PROPOSED`** until verified against real code.
5. **§19 and §20 must be complete before any code is written** (`REQ-KG-008`).
6. **Sub-steps are created before implementation starts**, not discovered during it.
7. Security, privacy, accessibility and observability appear in every step — they are never deferred to a later step.
</content>
