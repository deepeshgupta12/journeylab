---
sub_step_id: STEP-003.08
parent_step: STEP-003
title: Automated keyboard and axe checks in CI
status: NOT_STARTED
owners: []
requirement_ids: [REQ-A11Y-001]
blast_radius_id: BR-021
depends_on: [STEP-003.07]
last_updated: 2026-08-05
---

# STEP-003.08 — Automated keyboard and axe checks in CI

## 1. Outcome
Accessibility violations fail the build rather than surfacing in a later audit.

## 2. Scope and boundary
**In scope:** `apps/web/src/test/a11y.spec.ts`; axe over every component story and the shell; keyboard traversal tests; CI wiring.

**Not in this sub-step:** Manual screen-reader journeys (scheduled per release, they cannot be automated away).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-A11Y-001 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | **BLOCKED — static fallback** (no application symbols indexed yet) |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | KG-Q-015 `detect_changes()`; KG-Q-006 once symbols exist |
| Unknown / low-confidence areas | None material |
| Blast radius | BR-021 — scored at execution; **confidence capped while the graph is BLOCKED** |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] axe run across all component stories and the shell
- [ ] Keyboard traversal test asserting no focus traps outside dialogs
- [ ] **Build fails on any AA violation** — no warning-only mode
- [ ] Accessibility failure counter wired for production telemetry
- [ ] Document what automation cannot catch, so it is not mistaken for full coverage

## 6. Contracts and schema changes
Contracts are declared in [STEP-004](../../STEP-004-contract-first-platform-apis.md); this sub-step consumes them. Any change here follows [CONTRACT_CHANGE_POLICY](../../../04-contracts/CONTRACT_CHANGE_POLICY.md).

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-A11Y-001 | CI | Zero AA violations across stories and shell |
| — | meta | A seeded violation **fails** the build |

## 8. Telemetry, security and accessibility
Traces carry tenant-safe correlation IDs; no PII in telemetry. Any user-facing surface is keyboard and screen-reader complete (`REQ-A11Y-001`) and completable without the map (`REQ-A11Y-003`).

## 9. Documentation to update
- [ ] Sub-step completion record
- [ ] [IMPLEMENTATION_LOG](../../../10-logs/IMPLEMENTATION_LOG.md) · [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) · [BUG_REGISTER](../../../10-logs/BUG_REGISTER.md) if applicable
- [ ] `BR-021` post-change section
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
- [ ] axe runs in CI over all stories
- [ ] A seeded violation fails the build
- [ ] Keyboard traversal verified
- [ ] Limits of automation documented

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Commit SHA | — |
| Pushed | — |
| Graph re-indexed at | — |
| `main` green and deployable | — |
| Bugs found | — |
| Notes / surprises | Automated checks catch perhaps half of real accessibility defects; the documented limitation is what keeps the manual journeys scheduled instead of quietly dropped. |
