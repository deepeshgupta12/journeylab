---
sub_step_id: STEP-003.02
parent_step: STEP-003
title: Form and input primitives with validation states
status: VERIFIED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-A11Y-001]
blast_radius_id: BR-019
depends_on: [STEP-003.01]
last_updated: 2026-08-06
---

# STEP-003.02 — Form and input primitives with validation states

## 1. Outcome
Accessible inputs, selects, checkboxes and field groups exist with error, warning, disabled and busy states, each announced correctly to assistive technology.

## 2. Scope and boundary
**In scope:** Text, number, date, select, checkbox, radio and fieldset primitives; label/description/error association; inline validation.

**Not in this sub-step:** Product forms — the trip brief editor is [STEP-009](../../STEP-009-trip-brief-and-structured-constraints.md).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-A11Y-001 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | ✅ **RUNNABLE** — the `BLOCKED` prediction is stale; application code has been indexed since STEP-002.02 |
| HEAD / indexed commit | `0e3ea40` / `0e3ea40` — matched |
| Queries run | KG-Q-015 `detect_changes()`; KG-Q-006 once symbols exist |
| Unknown / low-confidence areas | ICU message loading strategy interacts with server components — resolve before STEP-003.07 |
| Blast radius | [BR-019](../../../10-logs/blast-radius/BR-019-form-primitives.md) — **MEDIUM**; confidence 4/5, graph runnable |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [x] Association centralised in `Field`, so it cannot be forgotten on the fourteenth form. `aria-describedby` points at description **and** error; `aria-invalid` is absent rather than `false` when valid
- [x] `aria-live="polite"`, never `role="alert"` — assertive interrupts a user mid-sentence. The region is **always rendered**, because one inserted when content arrives is frequently never announced. Focus theft is asserted directly
- [x] Separators derived from `Intl.NumberFormat`. `parseFloat("1.234,56")` returns 1.234 — wrong by three orders of magnitude, silently. Ambiguous input is **refused**, not guessed
- [x] Returns a `CalendarDate`, **never a `Date`**. Converting to an instant requires an explicit IANA zone with no default; DST boundaries verified
- [x] Kept distinct and separately tested. `disabled` leaves the tab order and can make the field unreadable to screen readers; `readOnly` stays focusable and readable

## 6. Contracts and schema changes
Contracts are declared in [STEP-004](../../STEP-004-contract-first-platform-apis.md); this sub-step consumes them. Any change here follows [CONTRACT_CHANGE_POLICY](../../../04-contracts/CONTRACT_CHANGE_POLICY.md).

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-A11Y-001 | component | Every primitive is keyboard and screen-reader complete |
| — | component | Errors are announced without focus theft |

## 8. Telemetry, security and accessibility
Traces carry tenant-safe correlation IDs; no PII in telemetry. Any user-facing surface is keyboard and screen-reader complete (`REQ-A11Y-001`) and completable without the map (`REQ-A11Y-003`).

## 9. Documentation to update
- [x] Sub-step completion record
- [x] `IMPL-016` · regression entry · **`BUG-016`** (flaky workflow guard)
- [x] `BR-019` post-change section
- [x] Parent step §21 · [MASTER_TRACKER](../../../02-delivery/MASTER_TRACKER.md)

## 10. Regression cross-check (R1–R7)
| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression suite | **PASS** | 335 Python + 41 web + 107 UI |
| R2 contract compatibility | **N/A** | No contracts yet (STEP-004) |
| R3 graph diff as expected | **PASS** | New `packages/ui/src/form/`; guard fix for BUG-016 |
| R4 untested requirements | **PASS** | Decreased |
| R5 orphan/unowned nodes | **PASS** | Catch-all owner covers `packages/ui/**` |
| R6 closed-bug regression tests | **PASS** | BUG-001…015 |
| R7 tenant isolation | **PASS — 12/12** | Untouched |

**Overall:** PASS / FAIL — a FAIL means this sub-step is not done.

## 11. Rollback
Revert this sub-step's commit; prior sub-steps stay intact and `main` stays deployable. Schema work uses expand/contract, so the expand phase is reversible.

## 12. Acceptance criteria
- [x] Zero AA violations on all six primitives — and **axe itself proven able to fail** first, since otherwise "zero violations" is indistinguishable from axe not running
- [x] Announced politely and associated programmatically; mutation-tested both ways
- [x] Verified across en-GB, de-DE and fr-FR, and across four time zones including a DST boundary

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | 2026-08-06 |
| Commit SHA | see git log |
| Pushed | Yes |
| Graph re-indexed at | post-commit |
| `main` green and deployable | Yes — `pnpm verify` and `pnpm ci:local` green |
| Bugs found | **`BUG-016`** — the workflow guard fetched pyyaml at run time, so a transient network failure was reported as "workflow YAML does not parse". Flaky, which is worse than failing |
| Tests | 39 added (107 in `packages/ui`); 5/5 mutants killed |
| Notes / surprises | The prediction was right and drove the design: `DateInput` returns a `CalendarDate`, never a `Date`, and conversion demands an explicit IANA zone. **Unpredicted:** Biome's a11y rules caught two standards errors I had written — `aria-required` on `input[type=date]` (no ARIA role) and then on a `fieldset` (`role="group"` does not support it). The fix was to stop reaching for ARIA: the native `required` attribute already maps to the same property. Also, a mutant appeared to survive because my harness replaced a string inside a **docstring** rather than the JSX — the third time a mutation harness has misled me |
| Carried gaps | ICU message loading vs server components (before `.07`); real-browser and assistive-technology verification (`.08`) |
