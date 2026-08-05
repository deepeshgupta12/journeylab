---
sub_step_id: STEP-003.06
parent_step: STEP-003
title: Role-aware desktop and mobile navigation
status: NOT_STARTED
owners: []
requirement_ids: [REQ-A11Y-001, REQ-SEC-004]
blast_radius_id: BR-019
depends_on: [STEP-003.05]
last_updated: 2026-08-05
---

# STEP-003.06 — Role-aware desktop and mobile navigation

## 1. Outcome
Navigation renders by role on desktop and mobile, keyboard-complete, with the clear caveat that **rendering is presentation only and the server is the control**.

## 2. Scope and boundary
**In scope:** `apps/web/src/components/navigation/`; role-aware menu construction; mobile drawer; current-page indication.

**Not in this sub-step:** Server-side authorization ([STEP-002](../../STEP-002-identity-tenancy-and-authorization.md)); admin console navigation ([STEP-021](../../STEP-021-administration-and-curation-console.md)).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-A11Y-001, REQ-SEC-004 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | **BLOCKED — static fallback** (no application symbols indexed yet) |
| HEAD / indexed commit | *(record at execution)* |
| Queries run | KG-Q-015 `detect_changes()`; KG-Q-006 once symbols exist |
| Unknown / low-confidence areas | None material |
| Blast radius | BR-019 — scored at execution; **confidence capped while the graph is BLOCKED** |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [ ] Desktop navigation with landmark and current-page semantics
- [ ] Mobile drawer with focus trap and restoration
- [ ] Role-aware item visibility driven by session claims
- [ ] **Comment asserting that hiding an item is not an authorization control**
- [ ] Touch targets meeting minimum size

## 6. Contracts and schema changes
Contracts are declared in [STEP-004](../../STEP-004-contract-first-platform-apis.md); this sub-step consumes them. Any change here follows [CONTRACT_CHANGE_POLICY](../../../04-contracts/CONTRACT_CHANGE_POLICY.md).

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-A11Y-001 | e2e | Navigation fully keyboard-operable; current page announced |
| TST-SEC-004 | security | Hidden routes remain **server-denied** when requested directly |

## 8. Telemetry, security and accessibility
Traces carry tenant-safe correlation IDs; no PII in telemetry. Any user-facing surface is keyboard and screen-reader complete (`REQ-A11Y-001`) and completable without the map (`REQ-A11Y-003`).

## 9. Documentation to update
- [ ] Sub-step completion record
- [ ] [IMPLEMENTATION_LOG](../../../10-logs/IMPLEMENTATION_LOG.md) · [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) · [BUG_REGISTER](../../../10-logs/BUG_REGISTER.md) if applicable
- [ ] `BR-019` post-change section
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
- [ ] Keyboard and screen-reader complete on both breakpoints
- [ ] Role-aware rendering matches the authorization matrix
- [ ] Directly requesting a hidden route is denied server-side

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Commit SHA | — |
| Pushed | — |
| Graph re-indexed at | — |
| `main` green and deployable | — |
| Bugs found | — |
| Notes / surprises | The security test matters more than the rendering: a hidden nav item with an open endpoint is a vulnerability, not a UI bug. |
