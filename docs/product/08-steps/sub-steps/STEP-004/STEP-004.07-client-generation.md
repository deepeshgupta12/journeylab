---
sub_step_id: STEP-004.07
parent_step: STEP-004
title: Client generation pipeline and no-hand-edit enforcement
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-PLAT-007]
blast_radius_id: BR-028
depends_on: [STEP-004.06]
last_updated: 2026-08-05
---

# STEP-004.07 — Client generation pipeline and no-hand-edit enforcement

## 1. Outcome
TypeScript and Python clients are generated in CI as build artifacts, and hand-editing one fails the build.

## 2. Scope and boundary
**In scope:** Generation scripts; `packages/contracts/src/generated/`; CI drift detection; generated-path exclusion from the knowledge graph.

**Not in this sub-step:** Client usage in features.

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-PLAT-007 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | **BLOCKED — static fallback** (no application symbols indexed yet) |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | KG-Q-015 `detect_changes()`; KG-Q-006 once symbols exist |
| Unknown / low-confidence areas | None material |
| Blast radius | BR-028 — scored at execution; **confidence capped while the graph is BLOCKED** |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] Generate TypeScript and Python clients from OpenAPI
- [ ] Commit generated output with a clear 'do not edit' header
- [ ] **CI regenerates and fails on any diff** — catches both hand edits and stale clients
- [ ] Exclude generated paths from graph indexing so coverage is not inflated
- [ ] Document the regeneration command in the README

## 6. Contracts and schema changes
Contracts are declared in [STEP-004](../../STEP-004-contract-first-platform-apis.md); this sub-step consumes them. Any change follows [CONTRACT_CHANGE_POLICY](../../../04-contracts/CONTRACT_CHANGE_POLICY.md).

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-PLAT-007 | CI | A hand-edited generated file fails the build |
| — | CI | A contract change without regeneration fails the build |

## 8. Telemetry, security and accessibility
Traces carry tenant-safe correlation IDs; no PII in telemetry. Any user-facing surface is keyboard and screen-reader complete (`REQ-A11Y-001`) and completable without the map (`REQ-A11Y-003`).

## 9. Documentation to update
- [ ] Sub-step completion record
- [ ] [IMPLEMENTATION_LOG](../../../10-logs/IMPLEMENTATION_LOG.md) · [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) · [BUG_REGISTER](../../../10-logs/BUG_REGISTER.md) if applicable
- [ ] `BR-028` post-change section
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
- [ ] Clients generated for both languages
- [ ] Hand edit fails the build
- [ ] Stale client fails the build
- [ ] Generated paths excluded from graph coverage

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Commit SHA | — |
| Pushed | — |
| Graph re-indexed at | — |
| `main` green and deployable | — |
| Bugs found | — |
| Notes / surprises | Failing on stale clients matters as much as failing on hand edits — a stale client is how a contract change silently reaches production half-applied. |
