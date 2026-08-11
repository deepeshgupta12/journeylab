---
blast_radius_id: BR-026
sub_step_id: STEP-003.09
title: Visual design language
author: Deepesh Kumar Gupta
date: 2026-08-11
score: MEDIUM
confidence: HIGH
approval_required: false
---

# BR-026 — Visual design language

## 1. Graph state at the time of the check

| Field | Value |
| --- | --- |
| Tool | `npx gitnexus status`, `gitnexus_impact` (MCP) |
| Indexed commit | `3793494` |
| HEAD at check | `3793494` |
| Freshness | ✅ up to date |
| Result | **NOT BLOCKED** — both queries returned `epistemic: exact` |
| Confidence | **HIGH** for the token layer; the component layer is established by the compiler and the browser suite, not the graph (§3) |

## 2. Queries run

| # | Query | Result |
| --- | --- | --- |
| 1 | `impact(contrastPairs, upstream, includeTests)` | 1 direct — `tokens.test.ts`. LOW, `exact` |
| 2 | `impact(renderCss, upstream, includeTests)` | 2 direct — `gen-tokens.ts`, `tokens.test.ts`. LOW, `exact` |
| 3 | `detect_changes()` | Run pre-commit; recorded in the regression entry |

## 3. Graph coverage, restated

`BR-025` §3 established that the graph records `CALLS` edges from function calls
only, so a React component used as JSX is invisible to it. That applies here in
full: **CSS has no representation in the graph at all**, and the largest change
in this sub-step is a stylesheet.

So the reach below is established three other ways, and the record says which:

- **Tokens** — by the graph (queries 1 and 2), and by `tokens.test.ts`, which
  recomputes every contrast ratio from the data.
- **Components** — by the 40-test real-browser suite from `.08`, which measures
  the rendered result rather than the source.
- **Nothing else** — no API, event, schema or data surface is touched, so there
  is nothing for the graph to have missed.

A CSS change is the case where "the graph says LOW risk" carries the least
information, and saying so is more useful than quoting the LOW.

## 4. Change inventory

| File | Change |
| --- | --- |
| `packages/ui/src/tokens.ts` | Warm neutral ramp; `border-subtle` added; 4 status surface tints per theme; `RADIUS` scale; font-family, tracking and measure tokens; two-layer elevation; **12 new contrast pairs** |
| `packages/ui/src/tokens.css` | Regenerated |
| `packages/ui/tools/gen-tokens.ts` | Emits the radius scale |
| `packages/ui/src/tokens.test.ts` | Status-coverage rule sharpened to exclude `-surface`, plus a test proving the exclusion did not disable it |
| `packages/ui/src/components.css` | Rewritten as a design language rather than a set of minimums |
| `apps/web/src/app/shell.css` | Header, footer, measure, skip link, nav, error panels |
| `apps/web/src/app/dev/gallery/gallery.css` | Specimen cards, section rhythm |
| `apps/web/src/test/a11y.spec.ts` | INP check takes the median of five samples |

**Nothing was removed.** No token key deleted, no class name changed, no
component API touched — so no consumer can break.

## 5. Twelve impact categories

| # | Category | Assessment |
| --- | --- | --- |
| 1 | **Callers / call graph** | Additive. `contrastPairs` gains 12 entries; its only caller is its test. `renderCss` gains one block |
| 2 | **Public API / contracts** | `packages/ui` token keys added, none removed or renamed. No HTTP contract exists yet |
| 3 | **Database / schema** | None |
| 4 | **Events** | None |
| 5 | **Configuration** | None. No new environment variable, no build flag |
| 6 | **Infrastructure** | None. No new dependency — deliberately: a webfont was rejected on LCP grounds, and that decision also means no CDN, no font licence and no third-party request |
| 7 | **Security** | None. No new input, no new sink, no new network call. **No webfont is a security fact as well as a performance one**: it is one fewer third-party origin in the CSP |
| 8 | **Privacy** | None. Nothing stored, logged or transmitted |
| 9 | **Accessibility** | **Unchanged by contract, improved in practice.** The same 40 browser assertions pass. 12 new contrast pairs are now proven. The three regressions the gate caught (§6) would each have been an accessibility defect |
| 10 | **Performance** | Neutral-to-positive. No font request. `components.css` grows ~3 KB uncompressed and is bundled, so no extra request. LCP, CLS and interaction latency all still measured and within budget |
| 11 | **Tenancy** | None |
| 12 | **Documentation** | This record, `IMPL-023`, the sub-step record, `REGRESSION_LOG`, `MASTER_TRACKER`, parent §21 |

## 6. What the accessibility gate rejected

The reason this is MEDIUM rather than HIGH is that `.08` exists. Three of the
changes attempted here were accessibility defects, and all three were caught
before commit:

| Attempt | Why it was wrong | Caught by |
| --- | --- | --- |
| Checkbox and radio at 20px | Looks better beside 14px labels; SC 2.5.8 requires 24×24, and a checkbox is its own target regardless of its 44px row | Touch-target test, both device profiles |
| Gallery grid minimum raised to 22rem | A grid item's default `min-width: auto` refuses to shrink below its widest word; one long place name pushed the document 2px wide at 320px | Reflow test |
| `margin: -1px` left on the visually-hidden pattern | A leftover from the older `clip: rect()` technique; put the skip link at `x = -1` | Reflow test |

A fourth was a flaw in the gate rather than the design: the INP check measured a
single interaction and reported 422 ms once on a loaded machine against 7 ms
idle. `BUG-016` already established that a flaky gate is worse than a failing
one, so it now takes the median of five.

## 7. Data-flow inspection

**Not applicable, and that is a finding rather than an omission.** This sub-step
introduces no input, no output, no storage and no network call. The only data
that moves is CSS custom property values, from `tokens.ts` through the generator
into a stylesheet, and that path is covered by the drift test.

The one place a design decision could have created a data flow is a webfont —
a request to a third-party origin on every first load, carrying the referring
page and the visitor's IP. It was rejected for performance reasons, and the
privacy and CSP consequences are a second reason not to revisit it lightly.

## 8. Score

| Dimension | Value | Reason |
| --- | --- | --- |
| Reach | Medium | Every rendered surface changes appearance |
| Reversibility | High | Two stylesheets and a token file; revert the commit |
| Detectability | High | 307 unit + 40 browser assertions, which rejected three attempts |
| Security exposure | None | No new input, sink, dependency or origin |
| Performance | Neutral | No new request; budgets still measured and met |
| **Overall** | **MEDIUM** | **Confidence HIGH.** No owner approval required |

## 9. Post-change verification

| Check | Result |
| --- | --- |
| `pnpm verify` (guards + lint + typecheck + Python + tests + build + gate + browser) | **PASS** |
| `pnpm ci:local` (Linux, clean checkout, cold install, `CI=true`) | **PASS** |
| Playwright | **40 passed** |
| UI suite | **307 passed** (up from 267: 12 new contrast pairs × themes, plus the sharpened status rule) |
| Web suite | 61 passed |
| Python suite | 335 passed, 5 skipped |
| Guard meta-suite | 43/43 |
| R1–R7 | PASS |
