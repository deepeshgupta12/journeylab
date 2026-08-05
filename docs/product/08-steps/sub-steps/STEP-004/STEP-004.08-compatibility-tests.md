---
sub_step_id: STEP-004.08
parent_step: STEP-004
title: Backward-compatibility and consumer contract tests
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-PLAT-008]
blast_radius_id: BR-029
depends_on: [STEP-004.07]
last_updated: 2026-08-05
---

# STEP-004.08 — Backward-compatibility and consumer contract tests

## 1. Outcome
A breaking contract change fails CI unless it carries a new major version, migration guide, consumer notice and sunset date.

## 2. Scope and boundary
**In scope:** `tests/contracts/`; OpenAPI/AsyncAPI diff against the previous release; consumer-driven contract tests; deprecation metadata checks.

**Not in this sub-step:** Provider integration contract tests ([STEP-005](../../STEP-005-source-integrations-and-ingestion.md)).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-PLAT-008 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | **BLOCKED — static fallback** (no application symbols indexed yet) |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | KG-Q-015 `detect_changes()`; KG-Q-006 once symbols exist |
| Unknown / low-confidence areas | Automated diff cannot detect semantic change; documented as a known limit in CONTRACT_CHANGE_POLICY |
| Blast radius | BR-029 — scored at execution; **confidence capped while the graph is BLOCKED** |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] Diff current contracts against the last released version
- [ ] Classify diffs: additive / potentially breaking / breaking
- [ ] **Breaking diff without a version bump fails the build**
- [ ] Deprecated operation without a `Sunset` date fails the build
- [ ] Consumer-driven contract test harness
- [ ] **Meta-test: a seeded breaking change must fail CI**

## 6. Contracts and schema changes
Contracts are declared in [STEP-004](../../STEP-004-contract-first-platform-apis.md); this sub-step consumes them. Any change follows [CONTRACT_CHANGE_POLICY](../../../04-contracts/CONTRACT_CHANGE_POLICY.md).

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-PLAT-008 | CI | Breaking change without version + migration guide fails |
| — | meta | A seeded breaking change is actually caught |

## 8. Telemetry, security and accessibility
Traces carry tenant-safe correlation IDs; no PII in telemetry. Any user-facing surface is keyboard and screen-reader complete (`REQ-A11Y-001`) and completable without the map (`REQ-A11Y-003`).

## 9. Documentation to update
- [ ] Sub-step completion record
- [ ] [IMPLEMENTATION_LOG](../../../10-logs/IMPLEMENTATION_LOG.md) · [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) · [BUG_REGISTER](../../../10-logs/BUG_REGISTER.md) if applicable
- [ ] `BR-029` post-change section
- [ ] Parent step §21 · [MASTER_TRACKER](../../../02-delivery/MASTER_TRACKER.md)

## 10. Regression cross-check (R1–R7)
| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression suite | | All prior sub-steps + every `VERIFIED` step |
| R2 contract compatibility | | No unintended breaking diff |
| R3 graph diff as expected | | `detect_changes()` |
| R4 untested requirements | | Not increased |
| R5 orphan/unowned nodes | | Not increased |
| R6 closed-bug regression tests | | All passing |
| R7 tenant isolation | | **Pass — non-negotiable** |

**Overall:** PASS / FAIL — a FAIL means this sub-step is not done.

## 11. Rollback
Revert this sub-step's commit; prior sub-steps stay intact and `main` stays deployable. Schema work uses expand/contract, so the expand phase is reversible.

## 12. Acceptance criteria
- [ ] Compatibility diff runs on every PR
- [ ] Breaking change blocked without the full policy
- [ ] Seeded breaking change proven to fail
- [ ] Deprecation metadata enforced

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Commit SHA | — |
| Pushed | — |
| Graph re-indexed at | — |
| `main` green and deployable | — |
| Bugs found | — |
| Notes / surprises | Semantic changes — same name, same type, different meaning — pass every automated diff. The policy names them breaking; only review catches them. |
