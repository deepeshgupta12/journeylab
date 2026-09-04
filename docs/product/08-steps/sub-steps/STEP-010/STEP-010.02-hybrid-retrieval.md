---
sub_step_id: STEP-010.02
parent_step: STEP-010
title: Hybrid retrieval with pre-ranking filters
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-AI-003, REQ-EVID-001]
blast_radius_id: TBD
depends_on: [STEP-010.01]
last_updated: 2026-09-04
---

# STEP-010.02 — Hybrid retrieval with pre-ranking filters

## 1. Outcome
Relevant evidence is retrieved, with hard filters applied before ranking rather than after.

## 2. Scope and boundary
**In scope:** Hybrid keyword and vector retrieval; **pre-ranking filters**; tenant-scoped indexes.

**Not in this sub-step:** Temporal filtering (`.03`); conflict detection (`.05`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-AI-003, REQ-EVID-001 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | *(record at execution)* — run `npx gitnexus status` and confirm it matches HEAD |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | `impact` on each symbol to be modified, **each cross-checked against grep** — `RISK-016`: the graph under-reports dependants, reproduced twelve times |
| Migration present? | If this sub-step adds one, `RISK-017` applies: the graph holds one node per `.sql` file, so the blast radius comes from the migration and from **mutation against the deployed schema** |
| Unknown / low-confidence areas | **Embeddings are disabled** (`REQ-KG-007`) until a documented scan proves no secret or customer payload can enter them. That scan has not happened, so the vector half of hybrid retrieval is blocked. |
| Blast radius | **TBD** — assigned at execution. Pre-assigned numbers in STEP-005 and STEP-006 were wrong in every case, so this record does not invent one |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] Keyword retrieval first, which works without the blocked vector path
- [ ] **Hard filters applied before ranking** — `TST-CONS-003`'s hazard is a filter bypassed by ranking
- [ ] Vector index tenant-scoped by construction; an untenanted index leaks by design
- [ ] Retrieval is reproducible: same pack inputs, same results
- [ ] The embeddings scan is a precondition, recorded as blocking rather than assumed done

## 6. Contracts and schema changes
None changed.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-CONS-003 | integration | **A hard filter cannot be bypassed by ranking** — adversarial candidates |
| — | security | Vector search is tenant-scoped; the pending R7 vector closes here |
| — | integration | Retrieval is reproducible across runs |
| — | unit | Retrieval works with the vector path disabled |

**Mutation testing is required**, per the practice established from STEP-004.09
onward: seed a defect for each rule this sub-step claims and confirm a test fails.
A rule no mutant can break is a rule nothing is checking.

## 8. Telemetry, security and accessibility
Query text is trip content; not logged.

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
Revert the commit; pack assembly has no retrieval and the step is inert.

## 12. Acceptance criteria
- [ ] Hard filters precede ranking
- [ ] Vector index is tenant-scoped
- [ ] Retrieval is reproducible
- [ ] Degrades to keyword-only

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
| Notes / surprises | **`REQ-KG-007` blocks embeddings until a scan proves no secret or payload can enter them, and that scan has not been done.** Building the vector path first and scanning later is the natural order and the wrong one — an embedding is a store `REQ-PRIV-006` deletion must traverse, and one nobody thinks of as a store. `test_pending_vector_is_still_absent[vector store]` fires the moment an index appears. |
