---
sub_step_id: STEP-012.07
parent_step: STEP-012
title: Reproducibility: seed, config and version persistence
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-CONS-006]
blast_radius_id: TBD
depends_on: [STEP-012.06]
last_updated: 2026-09-04
---

# STEP-012.07 — Reproducibility: seed, config and version persistence

## 1. Outcome
Any delivered scenario can be regenerated exactly from what was stored with it.

## 2. Scope and boundary
**In scope:** Persisting seed, solver config, model versions and pack reference; the regeneration path.

**Not in this sub-step:** Export (`STEP-008.06`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-CONS-006 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | *(record at execution)* — run `npx gitnexus status` and confirm it matches HEAD |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | `impact` on each symbol to be modified, **each cross-checked against grep** — `RISK-016`: the graph under-reports dependants, reproduced twelve times |
| Migration present? | If this sub-step adds one, `RISK-017` applies: the graph holds one node per `.sql` file, so the blast radius comes from the migration and from **mutation against the deployed schema** |
| Unknown / low-confidence areas | Solver version pinning. CP-SAT output can differ across versions, so the version is part of the lineage rather than an environment detail. |
| Blast radius | **TBD** — assigned at execution. Pre-assigned numbers in STEP-005 and STEP-006 were wrong in every case, so this record does not invent one |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] All four lineage columns written — the schema already refuses a scenario without them
- [ ] **Solver and model versions recorded**, because the same seed on a different version is a different answer
- [ ] A regeneration command that reproduces a stored scenario and compares
- [ ] Reproduction is verified, not assumed — the same lesson as rebuild verification in `STEP-006.09`
- [ ] Lineage is exported with the trip

## 6. Contracts and schema changes
Writes `scenarios.model_versions`, already `NOT NULL`.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-CONS-006 | integration | **A stored scenario regenerates identically and the comparison is asserted** |
| — | unit | A missing lineage element makes the scenario unstorable |
| — | integration | A different solver version is detected rather than silently producing a different plan |
| — | integration | Exported lineage is sufficient to reproduce |

**Mutation testing is required**, per the practice established from STEP-004.09
onward: seed a defect for each rule this sub-step claims and confirm a test fails.
A rule no mutant can break is a rule nothing is checking.

## 8. Telemetry, security and accessibility
Reproduction attempts and mismatches — a mismatch is a serious signal.

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
Revert the commit; scenarios store lineage but nothing verifies it, so the reproducibility claim becomes untested.

## 12. Acceptance criteria
- [ ] All lineage persisted
- [ ] Regeneration verified by comparison
- [ ] Version differences detected
- [ ] Export carries enough to reproduce

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
| Notes / surprises | **`REQ-CONS-006` is claimed by the schema and proved only here.** `NOT NULL` columns guarantee the lineage was *recorded*, not that it is *sufficient* — and the gap between those is exactly where an unpinned solver version lives. STEP-006.09 learned the same thing about rebuild: finishing is not matching, and only a comparison distinguishes them. |
