# Change Impact Record — Template

> Copy to `10-logs/blast-radius/BR-NNN-<slug>.md`. Completed **before** implementation begins (`REQ-KG-008`).
> For the full scoring table use [BLAST_RADIUS_TEMPLATE](../05-knowledge-graph/BLAST_RADIUS_TEMPLATE.md); this is the working short form for routine changes.

---

```markdown
# BR-NNN — [Change title]

| Field | Value |
| --- | --- |
| Sub-step | STEP-NNN.MM |
| Requirements | REQ-… |
| Author | |
| Date | |

## 1. Intent
*Target requirement, scope step and intended outcome.*

## 2. Graph state (protocol step 2)
| Field | Value |
| --- | --- |
| Repository / branch | journeylab / |
| HEAD commit | |
| Graph indexed commit | |
| **Match?** | yes / no — *if no, refresh before proceeding* |
| Index timestamp | |
| Extractor version | |
| Coverage % / known gaps | |
| Status | AVAILABLE / **BLOCKED — static fallback** |

## 3. Target nodes
| Node | Type | Source location | Owner |

## 4. Dependencies
**Inbound (≥3 hops):**
| Dependent | Hops | Confidence | Impact |

**Outbound:**
| Dependency | Confidence | Impact |

## 5. Impact by category
*Each category is either enumerated or explicitly "none found, confidence X".*

| Category | Affected | Confidence |
| --- | --- | --- |
| Requirements / scope steps | | |
| Owners / consumers | | |
| Frontend routes / components | | |
| Backend services / workflows / jobs | | |
| APIs / schemas / generated clients / webhooks | | |
| Events / producers / consumers | | |
| Tables / columns / migrations / caches | | |
| Datasets / features / models / prompts / retrievers / tools / evals | | |
| Tests / fixtures / contract suites | | |
| Services / deployments / infrastructure | | |
| Dashboards / alerts / runbooks | | |
| Documentation / deprecation commitments | | |

## 6. Data-flow check (security/privacy changes only)
*Required when touching auth, tenancy, redaction, retrieval inputs, prompts,
export or deletion. Record `pdg_query` / `trace` results.*

## 7. Classification
`direct` · `indirect` · `runtime-only` · `data/schema` · `contract/consumer` ·
`security/privacy` · `AI/model/evaluation` · `operational/deployment` ·
`documentation/process` · **`unknown`**

## 8. Risk
| Dimension | 1–5 | Rationale |
| Likelihood | | |
| Severity | | |
| Reach | | |
| Detectability | | |
| Reversibility | | |
| **Confidence** | | |
| Customer criticality | | |

**Overall: LOW / MEDIUM / HIGH / CRITICAL**

> Risk may not be scored below the level implied by confidence.
> Graph `BLOCKED` ⇒ confidence 5 ⇒ risk cannot be LOW.

## 9. Unknown or low-confidence areas
*Required. "None" only if the graph is current, coverage meets target and every
category above was explicitly enumerated.*

## 10. Required actions
| Action | Type | Owner |
| Tests | | |
| Migration | | |
| Compatibility | | |
| Rollout / flag | | |
| Monitoring | | |
| Rollback | | |

## 11. Approval
| Role | Name | Decision | Date |
*Required for HIGH, CRITICAL or materially uncertain impact. The author may
never approve their own change.*

## 12. Post-change verification
| Field | Value |
| Re-indexed at commit | |
| `detect_changes()` result | |
| Expected new/removed nodes confirmed | |
| **Unexpected consumers found** | |
| New orphan / unowned nodes | |
| Untested requirements before → after | |
| Regression R1–R7 | |

## 13. Disposition
| Field | Value |
| Outcome | merged / reverted / deferred |
| Commit / PR | |
| Follow-ups | |
```

---

## Anti-patterns this template exists to catch

| Anti-pattern | Why it is dangerous |
| --- | --- |
| Empty "unknown areas" on a stale graph | The most common way this protocol is defeated |
| LOW risk with low confidence | Confidence and risk are not independent |
| Written after implementation | Then it documents what was done, not what should have been considered |
| "No consumers" without checking generated clients and contract tests | Generated clients are exactly where breakage hides |
| Skipping the data-flow check on an auth change | Taint paths are not visible in a call graph alone |
