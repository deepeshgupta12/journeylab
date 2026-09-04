---
sub_step_id: STEP-009.03
parent_step: STEP-009
title: Structured constraint editor
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-CONS-001, REQ-A11Y-001]
blast_radius_id: TBD
depends_on: [STEP-009.02]
last_updated: 2026-09-04
---

# STEP-009.03 — Structured constraint editor

## 1. Outcome
A traveller can state and edit constraints directly, without prose and without a model.

## 2. Scope and boundary
**In scope:** The structured editor; class selection; validation feedback; the non-AI path through brief creation.

**Not in this sub-step:** Extraction (`.04`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-CONS-001, REQ-A11Y-001 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | *(record at execution)* — run `npx gitnexus status` and confirm it matches HEAD |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | `impact` on each symbol to be modified, **each cross-checked against grep** — `RISK-016`: the graph under-reports dependants, reproduced twelve times |
| Migration present? | If this sub-step adds one, `RISK-017` applies: the graph holds one node per `.sql` file, so the blast radius comes from the migration and from **mutation against the deployed schema** |
| Unknown / low-confidence areas | How much structure a traveller will tolerate before preferring prose. This surface must stand alone regardless — it is `REQ-AI-007`'s non-AI fallback. |
| Blast radius | **TBD** — assigned at execution. Pre-assigned numbers in STEP-005 and STEP-006 were wrong in every case, so this record does not invent one |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] Every constraint expressible without free text
- [ ] **Hard and soft chosen explicitly by the traveller**, not inferred from wording
- [ ] Validation feedback inline, announced to assistive technology
- [ ] This surface is complete on its own — the extraction path is an accelerator, not a prerequisite
- [ ] Keyboard-complete with visible focus

## 6. Contracts and schema changes
None changed.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-CONS-001 | e2e | **A complete brief is buildable with the editor alone**, no model involved |
| — | browser | Class selection is explicit and screen-reader labelled |
| — | axe | Zero violations, two device profiles |
| — | browser | Validation errors are announced |

**Mutation testing is required**, per the practice established from STEP-004.09
onward: seed a defect for each rule this sub-step claims and confirm a test fails.
A rule no mutant can break is a rule nothing is checking.

## 8. Telemetry, security and accessibility
No constraint content in telemetry.

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
Revert the commit. **This removes `REQ-AI-007`'s fallback**, so once `.04` ships this cannot be reverted independently.

## 12. Acceptance criteria
- [ ] A brief is completable without any model
- [ ] Hard/soft chosen explicitly
- [ ] Errors announced
- [ ] axe clean

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
| Notes / surprises | **This is the non-AI fallback `REQ-AI-007` requires for the extraction capability, and it is being built before the thing it falls back from.** That ordering is deliberate and worth protecting: built afterwards, it becomes a degraded copy of the model path rather than a first-class surface, and the fallback nobody uses is the fallback nobody notices breaking. |
