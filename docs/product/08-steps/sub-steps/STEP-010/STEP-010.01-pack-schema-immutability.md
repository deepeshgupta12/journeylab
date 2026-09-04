---
sub_step_id: STEP-010.01
parent_step: STEP-010
title: Evidence-pack schema, immutability and coverage report
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-EVID-001]
blast_radius_id: TBD
depends_on: [STEP-009.08]
last_updated: 2026-09-04
---

# STEP-010.01 — Evidence-pack schema, immutability and coverage report

## 1. Outcome
A pack is an immutable snapshot of the evidence a scenario was generated against, with an honest coverage report.

## 2. Scope and boundary
**In scope:** `evidence_packs` and `evidence_pack_facts` writes; the coverage report; immutability in practice.

**Not in this sub-step:** Retrieval (`.02`); conflict detection (`.05`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-EVID-001 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | *(record at execution)* — run `npx gitnexus status` and confirm it matches HEAD |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | `impact` on each symbol to be modified, **each cross-checked against grep** — `RISK-016`: the graph under-reports dependants, reproduced twelve times |
| Migration present? | If this sub-step adds one, `RISK-017` applies: the graph holds one node per `.sql` file, so the blast radius comes from the migration and from **mutation against the deployed schema** |
| Unknown / low-confidence areas | Pack size and retention. `STEP-006` §27 flags evidence-pack growth against the reproducibility window, and neither number exists. |
| Blast radius | **TBD** — assigned at execution. Pre-assigned numbers in STEP-005 and STEP-006 were wrong in every case, so this record does not invent one |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] A pack is written once; the table already refuses UPDATE (`STEP-006.01`)
- [ ] **The coverage report names what is missing**, not only what was found
- [ ] Facts are frozen into the pack by reference, so the pack and its facts cannot diverge
- [ ] Every fact in a pack carries source, observed time, effective window and licence (`REQ-EVID-001`)
- [ ] Pack build is a durable job with a handle, not a request-path operation

## 6. Contracts and schema changes
Writes `DATA-008`.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-EVID-001 | integration | Every fact in a pack carries complete provenance |
| — | integration | A pack cannot be updated after it is written |
| — | unit | **The coverage report names gaps** — a pack with holes says so |
| — | integration | A pack's facts cannot change after the pack is sealed |

**Mutation testing is required**, per the practice established from STEP-004.09
onward: seed a defect for each rule this sub-step claims and confirm a test fails.
A rule no mutant can break is a rule nothing is checking.

## 8. Telemetry, security and accessibility
Pack build progress carries IDs and counts.

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
Revert the commit; existing packs stay and remain citable by scenarios.

## 12. Acceptance criteria
- [ ] Packs are immutable in practice, not only in schema
- [ ] Coverage report names gaps
- [ ] Complete provenance on every fact
- [ ] Pack build is a durable job

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
| Notes / surprises | **The pack is the reproducibility freeze point**, so a coverage report that lists only what was found is the pack quietly claiming completeness. `REQ-EVID-001` requires source, observed time and confidence on every fact; the report must additionally say which facts were *sought and not found*, because a scenario built on a gap is different from one built on a fact. |
