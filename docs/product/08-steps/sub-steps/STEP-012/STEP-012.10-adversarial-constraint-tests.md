---
sub_step_id: STEP-012.10
parent_step: STEP-012
title: Property-based adversarial constraint test suite
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-CONS-004, REQ-CONS-005]
blast_radius_id: TBD
depends_on: [STEP-012.09]
last_updated: 2026-09-04
---

# STEP-012.10 — Property-based adversarial constraint test suite

## 1. Outcome
The zero-violation promise is tested against briefs designed to break it, not against representative ones.

## 2. Scope and boundary
**In scope:** Property-based generation of adversarial briefs; the violation check; conflict-set minimality checking.

**Not in this sub-step:** Extraction evaluation (`STEP-009.08`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-CONS-004, REQ-CONS-005 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | *(record at execution)* — run `npx gitnexus status` and confirm it matches HEAD |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | `impact` on each symbol to be modified, **each cross-checked against grep** — `RISK-016`: the graph under-reports dependants, reproduced twelve times |
| Migration present? | If this sub-step adds one, `RISK-017` applies: the graph holds one node per `.sql` file, so the blast radius comes from the migration and from **mutation against the deployed schema** |
| Unknown / low-confidence areas | Generator coverage. A property test explores what its generator can produce, and the interesting briefs are the ones nobody thought to generate. |
| Blast radius | **TBD** — assigned at execution. Pre-assigned numbers in STEP-005 and STEP-006 were wrong in every case, so this record does not invent one |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] Property-based generation over constraint combinations, including contradictory ones
- [ ] **Every generated scenario checked for hard-constraint violations** — the `REQ-CONS-004` promise, tested adversarially
- [ ] Conflict-set minimality checked by construction: remove a member, confirm feasibility returns
- [ ] DST boundaries and seasonal windows included in generation (`STEP-006.02`'s hazard)
- [ ] Failing cases are captured as fixtures so they become permanent regressions

## 6. Contracts and schema changes
None.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-CONS-004 | property | **No generated brief produces a hard-constraint violation** |
| — | property | Every returned conflict set is minimal |
| — | property | Briefs spanning DST transitions are feasible-checked correctly |
| — | meta | A seeded solver bug is caught by the suite |

**Mutation testing is required**, per the practice established from STEP-004.09
onward: seed a defect for each rule this sub-step claims and confirm a test fails.
A rule no mutant can break is a rule nothing is checking.

## 8. Telemetry, security and accessibility
Offline.

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
Revert the commit; the zero-violation promise is tested only by example.

## 12. Acceptance criteria
- [ ] Adversarial generation over constraint combinations
- [ ] Zero violations across all generated cases
- [ ] Minimality checked by construction
- [ ] A seeded bug is caught

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
| Notes / surprises | **`REQ-CONS-004` promises zero hard-constraint violations and calls a breach an S1**, which is a promise no example-based suite can support. The meta-test matters as much as the properties: a generator that only produces satisfiable briefs will report perfect compliance forever — the same vacuous-pass shape as STEP-006.08's drift check, with a far worse consequence. |
