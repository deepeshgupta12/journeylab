# Sub-Step Template

> Copy to `08-steps/sub-steps/STEP-NNN/STEP-NNN.MM-<slug>.md`.
> One sub-step = one verifiable outcome = one commit + push.
> See [SUB_STEP_PROTOCOL](../02-delivery/SUB_STEP_PROTOCOL.md).

---

```markdown
---
sub_step_id: STEP-NNN.MM
parent_step: STEP-NNN
title: [Sub-step name]
status: NOT_STARTED
owners: []
requirement_ids: []
blast_radius_id: BR-NNN
depends_on: [STEP-NNN.MM-1]
last_updated: YYYY-MM-DD
---

# STEP-NNN.MM — [Sub-step name]

## 1. Outcome
*One sentence. What becomes verifiably true when this sub-step is done.*

## 2. Scope and boundary
**In scope:**
**Explicitly not in this sub-step** (and which sub-step owns it):

## 3. Requirements served
| Requirement | Acceptance criterion | Test ID |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | *(record at execution)* — `npx gitnexus status` must match HEAD. **Application code has been indexed since STEP-002.02**, so `BLOCKED` is a real finding to investigate, not an expected default. State the query you ran and its `epistemic` value. |
| HEAD commit | |
| Graph indexed commit | |
| Commits match? | |
| Queries run | KG-Q-006, KG-Q-007 |
| Direct dependents | |
| Indirect (3 hops) | |
| Unknown / low-confidence areas | |
| Blast radius | BR-NNN — risk, confidence |
| Approval required? | yes/no — approver |

## 5. Implementation plan
*Ordered, concrete tasks. Each independently reviewable.*
- [ ] …

## 6. Contracts and schema changes
| Artifact | Change | Compatibility | Version action |

## 7. Tests to add
| Test ID | Type | Asserts |

## 8. Telemetry, security and accessibility
| Concern | What this sub-step adds |

## 9. Documentation to update
- [ ] Sub-step completion record
- [ ] [IMPLEMENTATION_LOG](../10-logs/IMPLEMENTATION_LOG.md) entry
- [ ] [REGRESSION_LOG](../10-logs/REGRESSION_LOG.md) entry
- [ ] Blast-radius post-change section
- [ ] Parent step §21 checklist
- [ ] [MASTER_TRACKER](../02-delivery/MASTER_TRACKER.md)
- [ ] Contracts/architecture docs if changed

## 10. Regression cross-check (R1–R7)
| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression suite | | |
| R2 contract compatibility | | |
| R3 graph diff as expected | | |
| R4 untested requirements not increased | | |
| R5 orphan/unowned not increased | | |
| R6 closed-bug tests pass | | |
| R7 tenant isolation | | |

**Overall:** PASS / FAIL — *a FAIL means this sub-step is not done.*

## 11. Rollback
*How to revert this sub-step alone, leaving previous sub-steps intact.*

## 12. Acceptance criteria
- [ ] …

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | YYYY-MM-DD |
| Commit SHA | |
| Pushed | yes/no |
| Graph re-indexed at | |
| `main` green and deployable | |
| Bugs found | BUG-NNN |
| Enhancements logged | ENH-NNN |
| Notes / surprises | |
```

---

## Commit message for this sub-step

```
STEP-NNN.MM: <imperative summary>

- Implements: REQ-…
- Blast radius: BR-NNN (LOW|MEDIUM|HIGH|CRITICAL)
- Regression: R1-R7 pass
- Tests: TST-…
```

**No AI co-authorship attribution** in commits or PR descriptions (`ADR-006`).

---

## Sizing check before you start

- [ ] Produces a verifiable outcome, not "progress"
- [ ] Reviewable in one sitting
- [ ] Leaves `main` green and deployable
- [ ] Has its own acceptance criteria and rollback
- [ ] Touches one coherent concern

If any box is unchecked, split the sub-step.
