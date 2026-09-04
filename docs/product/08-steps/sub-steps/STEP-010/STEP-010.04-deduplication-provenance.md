---
sub_step_id: STEP-010.04
parent_step: STEP-010
title: Deduplication with provenance retention
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-EVID-001, REQ-EVID-002]
blast_radius_id: TBD
depends_on: [STEP-010.03]
last_updated: 2026-09-04
---

# STEP-010.04 — Deduplication with provenance retention

## 1. Outcome
Duplicate facts collapse for display while every source is retained.

## 2. Scope and boundary
**In scope:** Fact deduplication; provenance retention across merged facts.

**Not in this sub-step:** Conflict detection (`.05`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-EVID-001, REQ-EVID-002 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | *(record at execution)* — run `npx gitnexus status` and confirm it matches HEAD |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | `impact` on each symbol to be modified, **each cross-checked against grep** — `RISK-016`: the graph under-reports dependants, reproduced twelve times |
| Migration present? | If this sub-step adds one, `RISK-017` applies: the graph holds one node per `.sql` file, so the blast radius comes from the migration and from **mutation against the deployed schema** |
| Unknown / low-confidence areas | When two facts are the same fact rather than two sources agreeing. The distinction matters: agreement is evidence, duplication is noise. |
| Blast radius | **TBD** — assigned at execution. Pre-assigned numbers in STEP-005 and STEP-006 were wrong in every case, so this record does not invent one |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] Deduplicate for **display**, never in storage — the pack keeps every source
- [ ] Merged facts retain all contributing provenance records
- [ ] Agreement across independent sources raises confidence and is visible as such
- [ ] **Nothing is averaged** (`REQ-EVID-002`)
- [ ] Deduplication is reproducible from the pack

## 6. Contracts and schema changes
None changed.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-EVID-001 | integration | Every contributing source survives deduplication |
| — | unit | **No value is averaged across sources** |
| — | integration | Agreement between independent sources is distinguishable from a single source repeated |
| — | integration | Deduplication is reproducible |

**Mutation testing is required**, per the practice established from STEP-004.09
onward: seed a defect for each rule this sub-step claims and confirm a test fails.
A rule no mutant can break is a rule nothing is checking.

## 8. Telemetry, security and accessibility
Counts only.

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
Revert the commit; packs contain duplicates, which is noisy rather than wrong.

## 12. Acceptance criteria
- [ ] All provenance retained
- [ ] Nothing averaged
- [ ] Agreement is visible
- [ ] Reproducible

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
| Notes / surprises | **Two sources agreeing and one source counted twice look identical after a naive dedupe**, and they mean opposite things about confidence. The provider identifier graph from STEP-005.07 is what distinguishes them — the same `is_identity` question, one layer up, and the same failure if a coarse identifier is treated as identity. |
