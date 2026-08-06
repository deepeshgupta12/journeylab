---
sub_step_id: STEP-003.01
parent_step: STEP-003
title: Design tokens including high-contrast and reduced-motion
status: VERIFIED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-A11Y-004, REQ-NFR-013]
blast_radius_id: BR-018
depends_on: [STEP-002.07]
last_updated: 2026-08-06
---

# STEP-003.01 — Design tokens including high-contrast and reduced-motion

## 1. Outcome
Colour, typography, spacing, elevation and motion tokens exist, with high-contrast and reduced-motion variants, so no component invents its own values.

## 2. Scope and boundary
**In scope:** `packages/ui/src/tokens.css`; light/dark, high-contrast and reduced-motion token sets; contrast ratios verified against WCAG 2.2 AA.

**Not in this sub-step:** Components themselves (`.02`–`.04`); product-specific chart palettes ([STEP-013](../../STEP-013-visual-comparison.md)).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-A11Y-004, REQ-NFR-013 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | ✅ **RUNNABLE** — the prediction of `BLOCKED` is stale; application code has been indexed since STEP-002.02 |
| HEAD / indexed commit | `9f5ff36` / `9f5ff36` — matched |
| Queries run | KG-Q-015 `detect_changes()`; KG-Q-006 once symbols exist |
| Unknown / low-confidence areas | Whether the chart library honours token-driven theming — verify before committing to it in STEP-013 |
| Blast radius | [BR-018](../../../10-logs/blast-radius/BR-018-design-tokens.md) — **MEDIUM**; confidence 4/5, graph runnable |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [x] Colour tokens with **computed** AA verification — every declared foreground/background pairing has its ratio calculated from the token values on each test run
- [x] Typography, spacing and elevation. Font sizes are **rem, never px** — a px size ignores the browser font-size setting low-vision users rely on (WCAG 1.4.4)
- [x] Motion tokens; reduced motion sets every duration to **exactly 0ms**, plus an `!important` catch-all for components that hard-code their own
- [x] High contrast as a **distinct AAA palette**, not dark mode intensified — a test asserts it differs from the dark palette. Honours `forced-colors` as well as `prefers-contrast`
- [x] Status tokens carry **both** an icon and a text label. An icon with no accessible name is invisible to a screen reader; text alone is easy to miss when scanning

## 6. Contracts and schema changes
Contracts are declared in [STEP-004](../../STEP-004-contract-first-platform-apis.md); this sub-step consumes them. Any change here follows [CONTRACT_CHANGE_POLICY](../../../04-contracts/CONTRACT_CHANGE_POLICY.md).

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-A11Y-004 | component | Every status token has a non-colour counterpart |
| — | unit | All foreground/background pairs meet AA contrast |

## 8. Telemetry, security and accessibility
Traces carry tenant-safe correlation IDs; no PII in telemetry. Any user-facing surface is keyboard and screen-reader complete (`REQ-A11Y-001`) and completable without the map (`REQ-A11Y-003`).

## 9. Documentation to update
- [x] Sub-step completion record
- [x] `IMPL-015` · regression entry · no new BUG (the self-repairing test was caught pre-commit and is recorded in IMPL-015)
- [x] `BR-018` post-change section
- [x] Parent step §21 · [MASTER_TRACKER](../../../02-delivery/MASTER_TRACKER.md)

## 10. Regression cross-check (R1–R7)
| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression suite | **PASS** | 335 Python + 41 web + 68 UI |
| R2 contract compatibility | **N/A** | No contracts yet (STEP-004) |
| R3 graph diff as expected | **PASS** | One new package; no existing symbol modified |
| R4 untested requirements | **PASS** | Decreased |
| R5 orphan/unowned nodes | **PASS** | Catch-all owner covers `packages/ui/**` |
| R6 closed-bug regression tests | **PASS** | BUG-001…015 |
| R7 tenant isolation | **PASS** | Untouched — tokens carry no data |

**Overall:** PASS / FAIL — a FAIL means this sub-step is not done.

## 11. Rollback
Revert this sub-step's commit; prior sub-steps stay intact and `main` stays deployable. Schema work uses expand/contract, so the expand phase is reversible.

## 12. Acceptance criteria
- [x] Contrast passes for every documented pair — computed, and mutation-tested by lightening a colour below AA
- [x] Both variants exist and are applied by media query **and** an explicit `data-theme` override
- [~] Enforced **within this package** — a test fails on any hex the palettes do not declare. No components exist yet; a lint rule for them is `.02`

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | 2026-08-06 |
| Commit SHA | see git log |
| Pushed | Yes |
| Graph re-indexed at | post-commit |
| `main` green and deployable | Yes — `pnpm verify` and `pnpm ci:local` both green |
| Bugs found | The drift test was **self-repairing** — see below |
| Tests | 68; 5/5 mutants killed |
| Notes / surprises | The prediction was right and drove the design: reduced motion sets every duration to **exactly 0ms** and the test asserts `toBe("0ms")` rather than "shorter than default", because a 60ms animation still moves. **Unpredicted:** the generated-CSS drift test could never have failed — the generator wrote the file at module top level, so importing it rewrote the very file the test was about to compare. Visible only as a stray `wrote src/tokens.css` line in the output. A test that repairs the thing it verifies proves nothing |
| Carried gaps | Lint rule for hard-coded values in components (`.02`); real-browser `forced-colors` verification (`.08`); chart-library token theming, to confirm before STEP-013 |
