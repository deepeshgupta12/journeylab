---
sub_step_id: STEP-003.05
parent_step: STEP-003
title: Application frame, providers and global error boundary
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-A11Y-001, REQ-NFR-013]
blast_radius_id: BR-018
depends_on: [STEP-003.04]
last_updated: 2026-08-05
---

# STEP-003.05 — Application frame, providers and global error boundary

## 1. Outcome
The app frame renders with providers, metadata, skip links and a global error boundary, so a feature failure degrades one region instead of blanking the page.

## 2. Scope and boundary
**In scope:** `apps/web/src/app/layout.tsx`; query/session/i18n providers; skip-to-content; global and feature error boundaries; metadata.

**Not in this sub-step:** Navigation (`.06`); route-level pages.

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-A11Y-001, REQ-NFR-013 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | **BLOCKED — static fallback** (no application symbols indexed yet) |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | KG-Q-015 `detect_changes()`; KG-Q-006 once symbols exist |
| Unknown / low-confidence areas | Provider composition order affects streaming behaviour in the App Router — document the rationale |
| Blast radius | BR-018 — scored at execution; **confidence capped while the graph is BLOCKED** |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] Root layout with providers composed in a documented order
- [ ] **Skip-to-content link** as the first focusable element
- [ ] Global error boundary with a recovery path
- [ ] Reusable feature error boundary
- [ ] Document language and direction attributes set from locale

## 6. Contracts and schema changes
Contracts are declared in [STEP-004](../../STEP-004-contract-first-platform-apis.md); this sub-step consumes them. Any change here follows [CONTRACT_CHANGE_POLICY](../../../04-contracts/CONTRACT_CHANGE_POLICY.md).

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-A11Y-001 | e2e | Skip link works; landmarks present |
| — | component | A throwing child is contained by its feature boundary |

## 8. Telemetry, security and accessibility
Traces carry tenant-safe correlation IDs; no PII in telemetry. Any user-facing surface is keyboard and screen-reader complete (`REQ-A11Y-001`) and completable without the map (`REQ-A11Y-003`).

## 9. Documentation to update
- [ ] Sub-step completion record
- [ ] [IMPLEMENTATION_LOG](../../../10-logs/IMPLEMENTATION_LOG.md) · [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) · [BUG_REGISTER](../../../10-logs/BUG_REGISTER.md) if applicable
- [ ] `BR-018` post-change section
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
- [ ] Skip link present and functional
- [ ] Landmark regions correct
- [ ] A feature failure does not remove surrounding content
- [ ] CWV budgets met on the empty shell

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Commit SHA | — |
| Pushed | — |
| Graph re-indexed at | — |
| `main` green and deployable | — |
| Bugs found | — |
| Notes / surprises | Feature error boundaries are a product requirement here: blueprint §8.114 requires a map or chart failure not to remove itinerary text. |
