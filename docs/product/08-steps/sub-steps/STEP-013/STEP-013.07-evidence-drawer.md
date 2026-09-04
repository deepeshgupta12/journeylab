---
sub_step_id: STEP-013.07
parent_step: STEP-013
title: Evidence drawer with citations and conflicts
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-EVID-004, REQ-EVID-002]
blast_radius_id: TBD
depends_on: [STEP-013.06]
last_updated: 2026-09-04
---

# STEP-013.07 — Evidence drawer with citations and conflicts

## 1. Outcome
Any claim can be opened to show its sources, including the ones that disagree.

## 2. Scope and boundary
**In scope:** The evidence drawer; citation rendering; conflict display; licence attribution.

**Not in this sub-step:** Explanation generation (`.08`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-EVID-004, REQ-EVID-002 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | *(record at execution)* — run `npx gitnexus status` and confirm it matches HEAD |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | `impact` on each symbol to be modified, **each cross-checked against grep** — `RISK-016`: the graph under-reports dependants, reproduced twelve times |
| Migration present? | If this sub-step adds one, `RISK-017` applies: the graph holds one node per `.sql` file, so the blast radius comes from the migration and from **mutation against the deployed schema** |
| Unknown / low-confidence areas | How much evidence to show before it becomes unreadable. |
| Blast radius | **TBD** — assigned at execution. Pre-assigned numbers in STEP-005 and STEP-006 were wrong in every case, so this record does not invent one |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] Every claim opens to its supporting spans (`STEP-010.09`)
- [ ] **Conflicting sources are both shown** (`REQ-EVID-002`) — never one with the other hidden behind a control
- [ ] Source, observed time, effective window and confidence shown for each (`REQ-EVID-001`)
- [ ] Licence attribution rendered where required (`REQ-DATA-001`)
- [ ] **A claim with no citation cannot be displayed** — it is a bug, not a blank drawer

## 6. Contracts and schema changes
Consumes `Evidenced` and `Provenance`.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-EVID-004 | browser | Every claim opens to at least one citation |
| — | browser | **Conflicting sources are both visible without interaction** |
| — | unit | A claim with no citation is not rendered |
| — | browser | Attribution is present where the licence requires it |

**Mutation testing is required**, per the practice established from STEP-004.09
onward: seed a defect for each rule this sub-step claims and confirm a test fails.
A rule no mutant can break is a rule nothing is checking.

## 8. Telemetry, security and accessibility
Drawer open rate by claim type.

## 9. Documentation to update
- [ ] Sub-step completion record
- [ ] [IMPLEMENTATION_LOG](../../../10-logs/IMPLEMENTATION_LOG.md) · [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) · [BUG_REGISTER](../../../10-logs/BUG_REGISTER.md) if applicable
- [ ] Blast-radius record, post-change section
- [ ] Parent step §21 · [MASTER_TRACKER](../../../02-delivery/MASTER_TRACKER.md)

## 10. Regression cross-check (R1–R7)
| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression suite | | All prior sub-steps + every `VERIFIED` step |
| R2 contract compatibility | | No unintended breaking diff |
| R3 graph diff as expected | | `detect_changes()`; by inspection where a migration is involved |
| R4 untested requirements | | Not increased |
| R5 orphan/unowned nodes | | Not increased |
| R6 closed-bug regression tests | | All passing |
| R7 tenant isolation | | **Pass — non-negotiable** |

**Overall:** PASS / FAIL — a FAIL means this sub-step is not done.

## 11. Rollback
Revert the commit; claims render without their evidence — a `REQ-EVID-004` regression that removes the trust mechanism.

## 12. Acceptance criteria
- [ ] Every claim cites its spans
- [ ] Conflicts both visible
- [ ] Provenance complete per source
- [ ] No citation, no render

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Commit SHA | — |
| Pushed | — |
| Graph re-indexed at | — |
| `main` green and deployable | — |
| Mutation testing | — |
| Bugs found | — |
| Notes / surprises | **Hiding the disagreeing source behind a 'show more' is averaging by interaction design** — `REQ-EVID-002` says conflicting evidence stays visible, and a control the traveller does not click makes the conflict invisible just as effectively as a mean would. The pack retains both because STEP-010.05 was careful; the drawer is where that care is either honoured or undone. |
