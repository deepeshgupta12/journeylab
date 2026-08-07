---
sub_step_id: STEP-003.03
parent_step: STEP-003
title: Feedback primitives: dialog, notification, empty, error, skeleton
status: VERIFIED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-A11Y-001, REQ-A11Y-004]
blast_radius_id: BR-020
depends_on: [STEP-003.02]
last_updated: 2026-08-07
---

# STEP-003.03 — Feedback primitives: dialog, notification, empty, error, skeleton

## 1. Outcome
Every quality state defined in [FRONTEND_ARCHITECTURE](../../../03-architecture/FRONTEND_ARCHITECTURE.md) §4 has a reusable, accessible primitive, so features cannot invent inconsistent ones.

## 2. Scope and boundary
**In scope:** Dialog with focus trap and restoration; toast/notification with live-region semantics; empty, error, skeleton, stale-data and offline state components.

**Not in this sub-step:** Feature-specific empty states; the notification centre ([STEP-018](../../STEP-018-condition-monitoring.md)).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-A11Y-001, REQ-A11Y-004 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | ✅ **RUNNABLE** — the `BLOCKED` prediction is stale for the third consecutive sub-step; application code has been indexed since STEP-002.02 |
| HEAD / indexed commit | `b28bf15` / `b28bf15` — matched |
| Queries run | KG-Q-015 `detect_changes()`; KG-Q-006 once symbols exist |
| Unknown / low-confidence areas | Live-region politeness for streamed scenario updates — validate with a real screen reader, not only axe |
| Blast radius | [BR-020](../../../10-logs/blast-radius/BR-020-feedback-primitives.md) — **MEDIUM**; confidence 4/5, graph runnable |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [x] Trap, restoration and Escape — all three mutation-tested. Restoration guards against a trigger that has left the document, since focusing a detached node silently leaves focus on `body`
- [x] `politeness` is **required with no default** — the safe direction differs per message. Polite maps to `role="status"`, assertive to `role="alert"`. **Never auto-dismisses** (WCAG 2.2.1); both regions are mounted before any message exists
- [x] All nine states from FRONTEND_ARCHITECTURE §4, declared as **data** so "all nine" is a testable assertion rather than a counted list
- [x] Recoverable states accept an action slot. `UnauthorizedState` deliberately has none — retrying cannot grant permission, and offering it implies it might
- [x] `Progress` **requires** both `label` and `onCancel`, so a bare spinner cannot be constructed. Indeterminate work omits `aria-valuenow` rather than reporting a false 0%

## 6. Contracts and schema changes
Contracts are declared in [STEP-004](../../STEP-004-contract-first-platform-apis.md); this sub-step consumes them. Any change here follows [CONTRACT_CHANGE_POLICY](../../../04-contracts/CONTRACT_CHANGE_POLICY.md).

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-A11Y-001 | component | Focus trapped in dialog and restored on close |
| TST-A11Y-004 | component | States distinguishable without colour |

## 8. Telemetry, security and accessibility
Traces carry tenant-safe correlation IDs; no PII in telemetry. Any user-facing surface is keyboard and screen-reader complete (`REQ-A11Y-001`) and completable without the map (`REQ-A11Y-003`).

## 9. Documentation to update
- [x] Sub-step completion record
- [x] `IMPL-017` · regression entry · no new BUG (the inert focus trap was caught pre-commit and is recorded in IMPL-017)
- [x] `BR-020` post-change section
- [x] Parent step §21 · [MASTER_TRACKER](../../../02-delivery/MASTER_TRACKER.md)

## 10. Regression cross-check (R1–R7)
| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression suite | **PASS** | 335 Python + 41 web + 152 UI |
| R2 contract compatibility | **N/A** | No contracts yet (STEP-004) |
| R3 graph diff as expected | **PASS** | New `packages/ui/src/feedback/` |
| R4 untested requirements | **PASS** | Decreased |
| R5 orphan/unowned nodes | **PASS** | Catch-all owner covers `packages/ui/**` |
| R6 closed-bug regression tests | **PASS** | BUG-001…016 |
| R7 tenant isolation | **PASS — 12/12** | Untouched |

**Overall:** PASS / FAIL — a FAIL means this sub-step is not done.

## 11. Rollback
Revert this sub-step's commit; prior sub-steps stay intact and `main` stays deployable. Schema work uses expand/contract, so the expand phase is reversible.

## 12. Acceptance criteria
- [x] All nine — asserted against the list in FRONTEND_ARCHITECTURE §4, not counted by eye
- [x] Trap, restoration and Escape verified; 3/3 mutants killed
- [x] `subject` and `observedAt` are **required**, so the component cannot be rendered as a page-level banner at all

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | 2026-08-07 |
| Commit SHA | see git log |
| Pushed | Yes |
| Graph re-indexed at | post-commit |
| `main` green and deployable | Yes — `pnpm verify` and `pnpm ci:local` green |
| Bugs found | None shipped. The focus trap was **silently inert** on first write and caught pre-commit — see below |
| Tests | 45 added (152 in `packages/ui`); 6/6 mutants killed |
| Notes / surprises | The prediction was right and shaped the API: `StaleDataState` **requires** `subject` and `observedAt`, so it cannot be rendered as a global banner. Two other requirements got the same treatment — `Progress` cannot exist without a cancel path (`REQ-NFR-003`), and `InfeasibleState` throws on an empty conflict set (`REQ-CONS-005`). **Unpredicted:** the focus trap did nothing at all, because its visibility filter used `offsetParent !== null` — always null in jsdom, which computes no layout, and also null in real browsers for `position: fixed` elements, which a dialog usually is. A jsdom failure that turned out to be a genuine defect rather than an environment quirk |
| Carried gaps | Streamed-update politeness needs a real screen reader (`.08` / STEP-011); icon set (`.04`/`.05`); feature error boundaries (STEP-013) |
