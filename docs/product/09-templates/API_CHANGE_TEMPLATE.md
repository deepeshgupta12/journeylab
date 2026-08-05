# API Change — Template

> For any change to a REST operation, event, JSON Schema, webhook payload, or the **semantics** of a field.
> Governed by [CONTRACT_CHANGE_POLICY](../04-contracts/CONTRACT_CHANGE_POLICY.md).

---

```markdown
# API Change — [Operation or event]

| Field | Value |
| --- | --- |
| Artifact | API-NNN / EVT-NNN / Schema |
| Sub-step | STEP-NNN.MM |
| Blast radius | BR-NNN |
| Author | |
| Date | |

## 1. Compatibility classification
- [ ] **Non-breaking (additive)** — new optional field, new endpoint, new event type
- [ ] **Potentially breaking** — new enum value on a branched field, tightened
      validation, changed default, new required header
- [ ] **Breaking** — removal, rename, type change, **semantic change**, changed
      error meaning, changed delivery guarantee, changed partition key

> **Semantic change is always breaking**, even when the name and type are
> unchanged. It passes every automated check and breaks every consumer.

**Classification rationale:**

## 2. Change detail
| Field | Before | After |

## 3. Known consumers
*From the code graph (`KG-Q-013` api_impact) plus generated-client usage —
not from memory.*

| Consumer | Type | Breaks? | Owner | Notified |
| --- | --- | --- | --- | --- |

**Unknown consumer coverage:**
*Required. State how confident we are that the list is complete, and why.
"None" is only valid with a current graph and verified coverage.*

## 4. Graph evidence
| Field | Value |
| Graph status | AVAILABLE / BLOCKED |
| Indexed commit | |
| Queries run | |
| Endpoints / clients / tests affected | |

## 5. Generated-client impact
- [ ] Clients regenerated and committed
- [ ] No hand edits to generated files
- [ ] Downstream repositories needing regeneration identified

## 6. Versioning
| Field | Value |
| Current version | |
| New version | |
| Both served? | |

## 7. Dual-run and deprecation *(breaking only)*
| Field | Value |
| Dual-run start | |
| Dual-run length | *(set by the slowest known consumer; min one release cycle)* |
| `Deprecation` header from | |
| `Sunset` date | |
| Traffic monitoring | *(how we confirm no consumer remains before removal)* |

## 8. Migration guide
*Concrete before/after request and response examples. Not prose.*

## 9. Tests
- [ ] Contract compatibility test updated
- [ ] Consumer-driven contract tests pass
- [ ] Examples validate against the schema
- [ ] Both versions tested during dual-run
- [ ] Error-path tests for new failure modes

## 10. Canary and rollout
| Field | Value |
| Flag | |
| Canary cohort | |
| Abort conditions | |

## 11. Rollback
*Including how **consumers** revert, not only how we revert.*

## 12. Documentation
- [ ] `contracts/openapi.yaml` / `asyncapi.yaml` updated (authoritative)
- [ ] [API_CONTRACTS](../04-contracts/API_CONTRACTS.md) / [EVENT_CONTRACTS](../04-contracts/EVENT_CONTRACTS.md)
- [ ] [CHANGELOG](../02-delivery/CHANGELOG.md) with classification
- [ ] Step file §13
- [ ] [REQUIREMENTS_TRACEABILITY](../01-product/REQUIREMENTS_TRACEABILITY.md) if artifacts changed
- [ ] Migration guide published

## 13. Approvals
| Role | Name | Date |
| API owner | | |
| Consumer representative(s) | | |
| Security *(if auth/data changes)* | | |
```

---

## Reminders

- A breaking change **ships alone**, unbundled, so its rollback is clean.
- Removal is gated on **observed consumer traffic**, not on the sunset date arriving.
- Emergency security fixes may compress the deprecation window, **never** the impact analysis.
- Commit and PR text must contain **no AI co-authorship attribution** (`ADR-006`).
</content>
