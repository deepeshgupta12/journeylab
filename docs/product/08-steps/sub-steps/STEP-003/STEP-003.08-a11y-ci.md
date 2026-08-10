---
sub_step_id: STEP-003.08
parent_step: STEP-003
title: Automated keyboard and axe checks in CI
status: VERIFIED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-A11Y-001]
blast_radius_id: BR-025
depends_on: [STEP-003.07]
last_updated: 2026-08-10
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
| Graph status | ✅ **NOT BLOCKED** — `npx gitnexus status` up to date; queries returned `epistemic: exact` |
| HEAD / indexed commit | `1d67ffc` / `1d67ffc` — matched |
| Queries run | `impact(RootLayout)`, `impact(SkipLink)`, `detect_changes()` |
| Unknown / low-confidence areas | **One found, and it is material.** `impact(SkipLink)` returns 0 impacted against 8 real references: the graph records `CALLS` edges from function calls, and a React component used only as JSX is never called. Component-level impact analysis is unreliable until STEP-026 — see `BR-025` §3 |
| Blast radius | **[BR-025](../../../10-logs/blast-radius/BR-025-accessibility-ci.md) — MEDIUM, confidence HIGH.** The record predicted `BR-021`; that number was already taken by STEP-003.04 |
| Approval required? | **No** — MEDIUM with high confidence |

## 5. Implementation plan
- [x] axe run across all component stories and the shell — a gated gallery at `/dev/gallery` provides the stories (there is no Storybook); scanned LTR, RTL, dialog-open and drawer-open, in two device profiles
- [x] Keyboard traversal test asserting no focus traps outside dialogs — 400-tab walk that must return to the first control, plus the inverse assertion that a dialog **does** trap and releases on Escape
- [x] **Build fails on any AA violation** — `pnpm a11y` is the last step of `pnpm verify`; `retries: 0`, because a retry policy on an accessibility gate is a way of not fixing accessibility
- [x] Accessibility failure counter wired for production telemetry — `packages/ui/src/a11y/counter.ts`; counts what only a real session reveals, and emits no identifying payload
- [x] Document what automation cannot catch — [ACCESSIBILITY_AUTOMATION_LIMITS](../../../06-quality/ACCESSIBILITY_AUTOMATION_LIMITS.md)

## 6. Contracts and schema changes
Contracts are declared in [STEP-004](../../STEP-004-contract-first-platform-apis.md); this sub-step consumes them. Any change here follows [CONTRACT_CHANGE_POLICY](../../../04-contracts/CONTRACT_CHANGE_POLICY.md).

## 7. Tests to add
| Test | Type | Asserts | Status |
| --- | --- | --- | --- |
| TST-A11Y-001 | CI | Zero AA violations across stories and shell | ✅ 5 surfaces × 2 device profiles |
| — | meta | A seeded violation **fails** the build | ✅ a missing `alt` is injected and `image-alt` must be reported — a permanent test, not a one-off |
| — | CI | No focus trap outside dialogs; dialogs do trap | ✅ |
| — | CI | Targets ≥ 24×24; nav ≥ 44×44; no reflow overflow at 320px | ✅ |
| — | CI | forced-colors, RTL, LCP, CLS, interaction latency | ✅ |
| — | guard | The gallery 404s without its flag | ✅ `tests/guards/gallery-gate.sh`, meta-tested |
| — | unit | The runtime counter emits no identifying payload | ✅ 11 tests |

40 browser tests (20 × Desktop Chrome and Pixel 7) and 11 counter tests. Totals: 267 UI, 61 web, 40 browser.

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
| R1 full regression suite | **PASS** | 335 Python + 61 web + 267 UI + 40 browser |
| R2 contract compatibility | **N/A** | 7 exports and one CSS entry point added; nothing removed |
| R3 graph diff as expected | **PASS, with a caveat** | Scope as expected; but the graph cannot trace JSX usage at all — see §4 |
| R4 untested requirements | **PASS — materially improved** | Six carried criteria closed, plus the STEP-002.05 carry |
| R5 orphan/unowned nodes | **PASS** | Catch-all owner covers the new paths |
| R6 closed-bug regression tests | **PASS** | BUG-001…017 pass; meta-suite 43/43 |
| R7 tenant isolation | **PASS — 12/12** | Untouched |

**Overall:** **PASS**. Full detail in [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md).

## 11. Rollback
Revert this sub-step's commit; prior sub-steps stay intact and `main` stays deployable. Schema work uses expand/contract, so the expand phase is reversible.

## 12. Acceptance criteria
- [x] axe runs in CI over all stories — and in `pnpm verify`, so it is not CI-only
- [x] A seeded violation fails the build — asserted permanently, not demonstrated once
- [x] Keyboard traversal verified — in a real browser, including the dialog exception
- [x] Limits of automation documented — [ACCESSIBILITY_AUTOMATION_LIMITS](../../../06-quality/ACCESSIBILITY_AUTOMATION_LIMITS.md), which states the honest coverage figure of a third to a half

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | 2026-08-10 |
| Commit SHA | *(this commit)* |
| Pushed | ✅ |
| Graph re-indexed at | post-commit |
| `main` green and deployable | ✅ |
| Bugs found | **BUG-018** — the documented `tokens:build` command had never worked. Seven product defects found by the first browser run, all fixed in this sub-step rather than logged as bugs, since they were discovered and closed before any commit |
| Notes / surprises | The prediction was right, and understated: *"Automated checks catch perhaps half of real accessibility defects; the documented limitation is what keeps the manual journeys scheduled instead of quietly dropped."*<br><br>**The larger finding was that half of nothing had been measured at all.** 28 of the design system's 40 class names had no CSS. Checkboxes rendered 13×13. Every geometric assertion in seven sub-steps of jsdom tests was vacuous, and nothing in those suites could have said so — jsdom has no layout engine.<br><br>`forced-colors` and `prefers-contrast` had shared one media query since STEP-003.01. They are different signals: one asks for more contrast, the other announces a palette the user has already chosen. Overriding the second is both presumptuous and ineffective.<br><br>A fix I made introduced a regression that the next run caught within minutes: the gallery's own link styling outranked the nav's and halved its touch targets. A gallery must never restyle its specimens, or it measures itself. |
