---
sub_step_id: STEP-008.05
parent_step: STEP-008
title: Inspect, edit, export and delete for every attribute
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-PRIV-002, REQ-PRIV-006]
blast_radius_id: TBD
depends_on: [STEP-008.04]
last_updated: 2026-09-04
---

# STEP-008.05 — Inspect, edit, export and delete for every attribute

## 1. Outcome
A traveller can see everything held about them, correct it, take it away, and have it deleted from every store.

## 2. Scope and boundary
**In scope:** The subject-rights surface; export; **deletion traversal across primary, object, vector, graph, cache, export and token stores**.

**Not in this sub-step:** Trip lifecycle operations (`.06`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-PRIV-002, REQ-PRIV-006 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | *(record at execution)* — run `npx gitnexus status` and confirm it matches HEAD |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | `impact` on each symbol to be modified, **each cross-checked against grep** — `RISK-016`: the graph under-reports dependants, reproduced twelve times |
| Migration present? | If this sub-step adds one, `RISK-017` applies: the graph holds one node per `.sql` file, so the blast radius comes from the migration and from **mutation against the deployed schema** |
| Unknown / low-confidence areas | Which stores exist by the time this runs. Deletion must traverse them all, and the list grows with every step — so the traversal has to be derived rather than enumerated. |
| Blast radius | **TBD** — assigned at execution. Pre-assigned numbers in STEP-005 and STEP-006 were wrong in every case, so this record does not invent one |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] Inspect and edit surfaces for every stored attribute, including derived ones
- [ ] Export in a portable format, complete rather than curated
- [ ] **Deletion traverses every store**, with a proof artefact recording what was traversed
- [ ] The traversal list is **derived from the schema**, not hardcoded — a hardcoded list is stale the next time a table is added
- [ ] Deletion is a durable workflow with retries and manual recovery (`BACKEND_ARCHITECTURE` §4)

## 6. Contracts and schema changes
Implements the privacy request contracts (`PrivacyRequest`, `PrivacyStoreStatus`).

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-PRIV-006 | integration | **Deletion traversal proof covers every store that holds subject data** |
| — | integration | A newly added table with a subject reference is caught by the derived traversal |
| — | integration | Export contains every attribute the inspect surface shows |
| — | browser | The rights surface is keyboard and screen-reader complete |

**Mutation testing is required**, per the practice established from STEP-004.09
onward: seed a defect for each rule this sub-step claims and confirm a test fails.
A rule no mutant can break is a rule nothing is checking.

## 8. Telemetry, security and accessibility
A deletion request is itself personal data. The proof artefact records store names and counts, never content.

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
Revert the commit. **Deletions already performed are not reversible**, which is the point; the rollback removes the ability to request, not the effect of past requests.

## 12. Acceptance criteria
- [ ] Every attribute is inspectable, editable, exportable and deletable
- [ ] The traversal is derived from the schema, not a list
- [ ] A deletion proof artefact is produced
- [ ] The surface is accessible

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
| Notes / surprises | **A hardcoded store list is stale the day after it is written**, and this is the one place where staleness is a regulatory failure rather than an inconvenience. Every step from here adds tables; the traversal must find them by construction. The same lesson the R7 FORCE-RLS assertion learned in STEP-002.08 — derived, not listed — with a much worse failure mode. |
