---
sub_step_id: STEP-003.07
parent_step: STEP-003
title: Locale, time zone, currency and DST handling
status: VERIFIED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-NFR-007, REQ-NFR-008]
blast_radius_id: BR-024
depends_on: [STEP-003.06]
last_updated: 2026-08-10
---

# STEP-003.07 — Locale, time zone, currency and DST handling

## 1. Outcome
Dates, numbers, currencies and time zones render correctly per locale, **including across DST transitions**, with right-to-left-ready structure.

## 2. Scope and boundary
**In scope:** `apps/web/src/lib/i18n.ts`; ICU message loading; locale-aware formatters; IANA time-zone handling; RTL-ready layout primitives.

**Not in this sub-step:** RTL *implementation* (Phase 2); translation content.

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-NFR-007, REQ-NFR-008 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | ✅ **NOT BLOCKED** — `npx gitnexus status` up to date; three impact queries returned `epistemic: exact` |
| HEAD / indexed commit | `bb943f9` / `bb943f9` — matched |
| Queries run | `impact(startOfDayUtc)`, `impact(documentLocale)`, `impact(packages/ui/src/index.ts)`, `detect_changes()` |
| Unknown / low-confidence areas | **Resolved.** Formatting runs **server-side with an explicit locale and IANA zone**, both required arguments, nothing ambient — see `BR-024` and `packages/ui/src/i18n/datetime.ts`. Separately: the graph does not follow `workspace:*` aliases, so cross-package reach is unverified (`BR-024` §3) |
| Blast radius | **[BR-024](../../../10-logs/blast-radius/BR-024-i18n-locale-timezone-money.md) — MEDIUM, confidence HIGH.** The record predicted `BR-020`; that number was already taken by STEP-003.03 |
| Approval required? | **No** — MEDIUM with high confidence |

## 5. Implementation plan
- [x] ICU message loading with a documented fallback locale — `packages/ui/src/i18n/messages.ts`; catalogues are plain data resolved synchronously, and a missing key returns the key rather than a blank
- [x] Locale-aware date, number and currency formatters — `datetime.ts`, `money.ts`
- [x] **Money as integer minor units** — never floating point; the exponent is looked up, not assumed to be 2
- [x] IANA time-zone-aware date handling with explicit DST tests — spring-forward, fall-back, southern hemisphere, half-hour offset, and a non-existent wall-clock time
- [x] Logical CSS properties throughout so RTL is a configuration change — plus `tests/guards/logical-css.sh`, which fails the build on a physical directional property

## 6. Contracts and schema changes
Contracts are declared in [STEP-004](../../STEP-004-contract-first-platform-apis.md); this sub-step consumes them. Any change here follows [CONTRACT_CHANGE_POLICY](../../../04-contracts/CONTRACT_CHANGE_POLICY.md).

## 7. Tests to add
| Test | Type | Asserts | Status |
| --- | --- | --- | --- |
| TST-NFR-007 | unit | Dates, numbers and currency correct across the locale matrix | ✅ en-GB, en-US, de-DE, ja-JP, fr-FR, ar-EG |
| — | unit | **A date range spanning a DST transition computes the correct duration** | ✅ 7 real hours across 8 wall-clock hours, both directions |
| TST-NFR-008 | component | Layout does not break under an RTL locale | ✅ structure + axe; real-browser layout binds at STEP-003.08 |
| TST-SEC-006 | unit | `Accept-Language` cannot reach the module loader | ✅ 9 hostile headers; no specifier is constructed |

36 new tests: 17 in `packages/ui/src/i18n/i18n.test.tsx`, 19 in `apps/web/src/lib/i18n.test.ts`. Totals: 256 UI, 61 web.

## 8. Telemetry, security and accessibility
Traces carry tenant-safe correlation IDs; no PII in telemetry. Any user-facing surface is keyboard and screen-reader complete (`REQ-A11Y-001`) and completable without the map (`REQ-A11Y-003`).

## 9. Documentation to update
- [ ] Sub-step completion record
- [ ] [IMPLEMENTATION_LOG](../../../10-logs/IMPLEMENTATION_LOG.md) · [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) · [BUG_REGISTER](../../../10-logs/BUG_REGISTER.md) if applicable
- [ ] `BR-020` post-change section
- [ ] Parent step §21 · [MASTER_TRACKER](../../../02-delivery/MASTER_TRACKER.md)

## 10. Regression cross-check (R1–R7)
| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression suite | **PASS** | 335 Python + 61 web + 256 UI; green under 5 host time zones |
| R2 contract compatibility | **N/A** | No contracts yet; 25 exports added, none removed |
| R3 graph diff as expected | **PASS** | 3 touched symbols, all in `layout.tsx`; 0 affected processes |
| R4 untested requirements | **PASS** | REQ-NFR-007/008 newly covered |
| R5 orphan/unowned nodes | **PASS** | Catch-all owner covers the new paths |
| R6 closed-bug regression tests | **PASS** | BUG-001…016 pass; meta-suite 39/39 |
| R7 tenant isolation | **PASS — 12/12** | Untouched by construction |

**Overall:** **PASS**. Full detail in [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md).

## 11. Rollback
Revert this sub-step's commit; prior sub-steps stay intact and `main` stays deployable. Schema work uses expand/contract, so the expand phase is reversible.

## 12. Acceptance criteria
- [x] Locale matrix renders correctly — one instant across six locales and five zones
- [x] DST-spanning ranges compute correct durations — 7 hours where wall-clock arithmetic says 8
- [x] Currency handled as integer minor units — floats rejected, not rounded; exponent per currency
- [x] Missing locale falls back without crashing — and a missing *catalogue* fails at load rather than serving raw keys
- [x] RTL structure does not break layout — structure and axe; **real-browser layout is unmet and binds at STEP-003.08**

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | 2026-08-10 |
| Commit SHA | *(this commit)* |
| Pushed | ✅ |
| Graph re-indexed at | post-commit |
| `main` green and deployable | ✅ — **and it was not before this sub-step**; see BUG-017 |
| Bugs found | **BUG-017** — the production build had been broken since before `bb943f9`, and nothing ran it |
| Notes / surprises | DST correctness is a feasibility concern, not formatting: an itinerary crossing a transition computes wrong travel windows, which STEP-012 will then present as a valid plan. **Confirmed in the implementation** — the useful work was making `hoursInDay` return 23/24/25 rather than assuming 24.<br><br>Three tests passed for the wrong reason and one of my own comments was false; all four surfaced through mutation testing and none would have surfaced from a green run. See IMPL-021.<br><br>TypeScript making an argument required is worthless at a package boundary: `Intl` treats `timeZone: undefined` as the system zone, so the missing-zone failure was silent rather than an exception. `assertZone` closes it at runtime. |
