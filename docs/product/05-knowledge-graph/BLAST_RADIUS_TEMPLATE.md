# Blast Radius Assessment — Template

> Copy this file for every change. Store completed assessments in `docs/product/10-logs/blast-radius/BR-NNN-<slug>.md` and link from the sub-step file and the pull request.
> **An assessment with unknown dependency coverage may not be scored "low risk."**

---

```markdown
# BR-NNN — [Change title]

## Identification
| Field | Value |
| --- | --- |
| Change ID | BR-NNN |
| Title | |
| Requirement IDs | REQ-… |
| Scope step / sub-step | STEP-NNN / STEP-NNN.MM |
| Author | |
| Date | YYYY-MM-DD |

## Repository and graph state
| Field | Value |
| --- | --- |
| Repository | journeylab |
| Branch | |
| Target commit (HEAD) | |
| Graph indexed commit | |
| **Commits match?** | yes / no — *if no, refresh before proceeding* |
| Index timestamp | |
| Extractor / schema version | |
| Coverage % (first-party files) | |
| Known extraction gaps | |
| Graph status | `AVAILABLE` / `BLOCKED — static fallback applied` |

## Target nodes
| Node | Type | Source location | Owner |
| --- | --- | --- | --- |

## Reason for the change
*What outcome requires it, and what happens if it is not made.*

## Expected direct changes
| File / symbol | Change type | Notes |
| --- | --- | --- |

## Inbound dependencies (who calls / depends on the target)
| Dependent | Type | Hops | Confidence | Impact |
| --- | --- | --- | --- | --- |

## Outbound dependencies (what the target depends on)
| Dependency | Type | Confidence | Impact |
| --- | --- | --- | --- |

## Consumer and application impact
| Consumer | Surface | Breaking? | Notice required |
| --- | --- | --- | --- |

## API / event / schema compatibility
| Contract | Change class (additive / potentially breaking / breaking) | Version action | Migration guide |
| --- | --- | --- | --- |

## Data, migration and retention impact
| Table / dataset | Change | Migration phase (expand/migrate/contract) | Backward compatible? | Retention effect |
| --- | --- | --- | --- | --- |

## AI / model / prompt / retrieval impact
| Artifact | Change | Re-evaluation required | Rollback path |
| --- | --- | --- | --- |

## Security, privacy and compliance impact
| Concern | Affected? | Control | Data-flow check (KG-Q-014) |
| --- | --- | --- | --- |
| Authentication / authorization | | | |
| Tenant isolation | | | |
| Sensitive data classes | | | |
| Redaction / telemetry | | | |
| Deletion / export | | | |

## Deployment and infrastructure impact
| Component | Change | Flag | Canary plan |
| --- | --- | --- | --- |

## Observability and runbook impact
| Dashboard / alert / runbook | Change required | Owner |
| --- | --- | --- |

## Documentation impact
| Document | Update required |
| --- | --- |

## Unknown or low-confidence areas
> **Required section. "None" is only acceptable when the graph is current, coverage meets target, and every category above was explicitly enumerated.**

| Area | Why uncertain | How it was probed | Residual risk |
| --- | --- | --- | --- |

## Risk scoring
| Dimension | Score 1–5 | Rationale |
| --- | --- | --- |
| Likelihood of unintended effect | | |
| Severity if it occurs | | |
| Reach (users/tenants/services) | | |
| Detectability (would monitoring catch it?) | | |
| Reversibility | | |
| **Confidence in this analysis** | | |
| Customer criticality | | |

**Overall: LOW / MEDIUM / HIGH / CRITICAL**

*Scoring rule: overall risk may not be lower than the level implied by the confidence score. Low confidence with wide reach is HIGH, regardless of how small the diff looks.*

## Required owners and reviewers
| Role | Name | Approval | Date |
| --- | --- | --- | --- |

## Required tests and evaluations
| Test | Type | Status |
| --- | --- | --- |

## Migration and backward-compatibility plan

## Feature flag and canary plan

## Rollback and recovery plan
*Include how consumers revert, not only how we revert.*

## Pre-change graph evidence
```
Queries run:
Direct dependents: N   Indirect (3 hops): M
Unknown areas:
```

## Post-change graph evidence
```
Re-indexed at commit:
detect_changes() result:
Expected new nodes/edges:      confirmed?
Expected removed nodes/edges:  confirmed?
Unexpected consumers found:
New orphan / unowned nodes:
Untested requirement count:    before / after
```

## Regression cross-check (per sub-step)
| Check | Result |
| --- | --- |
| R1 full regression suite | |
| R2 contract compatibility | |
| R3 graph diff as expected | |
| R4 untested requirements not increased | |
| R5 orphan/unowned not increased | |
| R6 closed-bug regression tests pass | |
| R7 tenant isolation intact | |

## Final disposition
| Field | Value |
| --- | --- |
| Outcome | merged / reverted / deferred |
| Commit / PR | |
| Release | |
| Follow-up actions | |
| Step status change | |
```

---

## Scoring guidance

| Dimension | 1 | 5 |
| --- | --- | --- |
| Likelihood | Isolated pure function, fully covered | Widely called, weak coverage |
| Severity | Cosmetic | Data loss, wrong plan, privacy breach |
| Reach | One internal surface | All tenants |
| Detectability | Alert fires immediately | Silent until a user reports it |
| Reversibility | Flag off instantly | Irreversible data migration |
| **Confidence** | Graph current, coverage ≥95%, all categories enumerated | **Graph `BLOCKED`, static fallback only** |
| Customer criticality | Internal tooling | Core planning path |

**Anti-pattern this template exists to prevent:** a small diff, a stale graph, an empty "unknown areas" section, and a LOW score. If the graph is `BLOCKED`, confidence is 5 and the overall risk cannot be LOW.
</content>
