---
blast_radius_id: BR-025
sub_step_id: STEP-003.08
title: Automated keyboard and axe checks in CI
author: Deepesh Kumar Gupta
date: 2026-08-10
score: MEDIUM
confidence: HIGH
approval_required: false
---

# BR-025 — Automated keyboard and axe checks in CI

> The sub-step record predicts `BR-021`, which STEP-003.04 already holds. This
> record is `BR-025`, continuing from `BR-024`. Corrected in the sub-step file.

## 1. Graph state at the time of the check

| Field | Value |
| --- | --- |
| Tool | `npx gitnexus status`, `gitnexus_impact` (MCP) |
| Indexed commit | `1d67ffc` |
| HEAD at check | `1d67ffc` |
| Freshness | ✅ up to date |
| Result | **NOT BLOCKED** — queries ran and returned `epistemic: exact` |
| Confidence | **HIGH** for the change itself; the graph's *coverage* of React components is not (see §3) |

## 2. Queries run

| # | Query | Result |
| --- | --- | --- |
| 1 | `impact(RootLayout, upstream, includeTests)` | 0 impacted, `exact`, LOW |
| 2 | `impact(SkipLink, upstream, includeTests)` | 0 impacted, `exact`, LOW |
| 3 | `detect_changes()` | Run pre-commit; recorded in the regression entry |

## 3. A second graph limitation, sharper than BR-024's

`BR-024` recorded that the graph does not follow `workspace:*` package aliases.
This sub-step found a larger one.

`impact(SkipLink)` returns **0 impacted**. `grep` finds eight references across
two files — `layout.tsx` renders it and `shell.test.tsx` renders it four times.
The difference is that `SkipLink` is only ever used as **JSX** (`<SkipLink />`),
never called as `SkipLink(...)`, and the graph records `CALLS` edges from
function calls only.

Contrast with `startOfDayUtc` and `documentLocale` in `BR-024`, which the graph
traced correctly — both are plain functions, invoked with parentheses.

**Therefore: `gitnexus_impact` under-reports for every React component in this
repository, and reports zero for components that are only ever rendered.** A
`0 impacted` result on a component is "not traced", not "not used", and no
pre-change check on a component may be treated as complete on that basis.

This is a material finding for `REQ-KG-008` and is the second entry on the
`STEP-026` list. Until it is fixed, component-level impact analysis is done by
`grep` and the compiler, and recorded as such.

## 4. Change inventory

**Added**

| File | Purpose |
| --- | --- |
| `apps/web/playwright.config.ts` | Two projects (desktop, Pixel 7) against a **production** build on port 5708 |
| `apps/web/src/test/a11y.spec.ts` | 20 tests × 2 projects: axe, keyboard, geometry, forced-colors, RTL, CWV |
| `apps/web/src/app/dev/gallery/*` | Gated component gallery — the surface the browser walks |
| `apps/web/vitest.config.ts` | Excludes `src/test/**` so vitest does not try to run Playwright specs |
| `packages/ui/src/components.css` | Accessibility styling for the 28 component classes that had none |
| `packages/ui/src/a11y/counter.ts` + tests | Runtime accessibility failure counter |
| `tests/guards/gallery-gate.sh` | The gallery must 404 without its flag |
| `docs/product/06-quality/ACCESSIBILITY_AUTOMATION_LIMITS.md` | What automation cannot catch |

**Modified**

| File | Change |
| --- | --- |
| `packages/ui/tools/gen-tokens.ts` | `forced-colors` split from `prefers-contrast` — see §6 |
| `packages/ui/src/tokens.css` | Regenerated |
| `packages/ui/src/tokens.ts`, both `tsconfig.json` | `.ts` specifier + `allowImportingTsExtensions` — **BUG-018** |
| `apps/web/src/app/page.tsx`, `shell.css` | Inline hex colours replaced with tokens — closes the STEP-002.05 carry |
| `packages/ui/src/index.ts` | 7 new exports; none changed or removed |
| `package.json`, `.github/workflows/verify.yml`, `tests/ci-mirror.sh` | Browser install + `pnpm a11y` + `guard:gallery-gate` in `verify` |
| `tests/guards/meta/run-all.sh` | Meta-tests for the new guard |
| `.gitignore` | Playwright report and trace directories |

## 5. Twelve impact categories

| # | Category | Assessment |
| --- | --- | --- |
| 1 | **Callers / call graph** | Additive. The one behavioural change to existing code is `page.tsx`, whose markup was rewritten; its logic (cookie reads) is untouched. `components.css` changes how every component *looks*, not what it does. |
| 2 | **Public API / contracts** | `packages/ui` gains 7 exports and a `./components.css` entry point. Nothing removed. No HTTP contract touched. |
| 3 | **Database / schema** | None. |
| 4 | **Events** | A new **client-side** event name, `journeylab:navigated`, consumed by `observeFocusLoss`. Not a domain event, not on the bus, not in `EVENT_CONTRACTS`. |
| 5 | **Configuration** | `JOURNEYLAB_ENABLE_GALLERY` — new, default off, `=== '1'` only. `verify` gains three steps. CI gains a browser install and a failure-artifact upload. |
| 6 | **Infrastructure** | CI now downloads Chromium (~95 MB) and its system libraries. Adds roughly a minute to a cold run. `pnpm ci:local` does the same, deliberately: a mirror that skips the browser would pass commits CI rejects. |
| 7 | **Security** | **The reason this is MEDIUM.** A new route enumerates every internal component, error string and route shape. Gated, and the gate is guarded. See §7. |
| 8 | **Privacy** | The runtime counter emits `{signal, surface}` and nothing else — no element text, no ids, no URLs, no user identifier. An accessible name can contain a traveller's name or destination, so it is deliberately never reported. A test asserts the event has exactly two keys, so a field cannot be added silently. |
| 9 | **Accessibility** | The point of the sub-step. Seven real defects fixed (§6). Six carried criteria closed. |
| 10 | **Performance** | Measured rather than assumed for the first time: LCP, CLS and interaction latency now gate. `components.css` adds ~4 KB uncompressed and no request (it is bundled). No webfont, so no FOIT and no LCP cost. |
| 11 | **Tenancy** | None. Nothing here reads tenant data. The counter is per-instance precisely so a server process cannot mix tenants' signals. |
| 12 | **Documentation** | This record, `IMPL-022`, `BUG-018`, `ACCESSIBILITY_AUTOMATION_LIMITS`, `REGRESSION_LOG`, the sub-step record, `MASTER_TRACKER`. |

## 6. Seven real defects the browser found that 256 jsdom tests could not

Listed because the list is the argument for the sub-step.

| # | Defect | Why jsdom missed it |
| --- | --- | --- |
| 1 | **Checkboxes and radios 13×13**, text inputs 21px tall, selects 19px, sort buttons 21px — all below SC 2.5.8's 24×24 | jsdom has no layout; every element is 0×0 and every geometric assertion is vacuous |
| 2 | **28 of 40 component classes had no CSS at all.** The design system rendered at browser defaults | Nothing in a semantic test observes appearance |
| 3 | **`color-contrast` failure on the home page** — `#888` inline, 3.5:1 against white | `tokens.test.ts` computes ratios for *declared token pairings*; an inline hex is not one |
| 4 | **32px of horizontal overflow at 320px** (WCAG 1.4.10 Reflow) | No viewport, no scroll width |
| 5 | **`forced-colors` was given our palette instead of the user's** — and axe measured 1.07:1 against a light forced palette | jsdom has no forced-colors mode |
| 6 | **Valid and disabled fields wore the error styling.** `:has(.jl-field__error)` matched every field, because `Field` always renders the error element (deliberately — a live region inserted when it gains content is often not announced) | The rule is correct in the DOM sense; only paint shows the consequence |
| 7 | **The gallery's own link rule outranked `.jl-nav__link`** and cut nav targets from 44px to 24px | Specificity has no effect without layout |

Defect 5 deserves its own note. `tokens.css` had one media query for
`prefers-contrast: more` **and** `forced-colors: active`. Those are different
signals: the first is "I want more contrast", where our palette is the right
answer; the second is "I have chosen my own palette", where it is not ours to
override — and the override does not even work, because the user agent replaces
`background-color` regardless while authored text colour may survive. The
forced-colors branch now maps tokens onto CSS system colours.

## 7. Mandatory data-flow inspection

Two flows are new.

### 7.1 `/dev/gallery` — an information-disclosure surface

**The flow:** request → `galleryEnabled(process.env)` → `notFound()` or render
of every component, every error string and every quality state.

| Hazard | Control | Evidence |
| --- | --- | --- |
| The route reaches production and discloses internal structure | `JOURNEYLAB_ENABLE_GALLERY === '1'`, exact match. `'false'` and `'0'` are truthy strings and both mean off, so "truthy" would be the wrong test | `tests/guards/gallery-gate.sh` boots a production server **without** the flag and asserts 404; meta-tested by forcing the gate open and watching the guard fail |
| A 403 confirms the path exists | `notFound()`, so an enabled and a disabled route are indistinguishable from outside | Guard asserts exactly 404, and asserts `/api/health` is 200 first, so a broken server cannot pass by 404-ing everything |
| Search indexing if it ever does leak | `robots: { index: false, follow: false }` | Belt and braces beside the gate, not instead of it |
| Renders no real data | The gallery's content is hard-coded fixtures — three ferry legs between Greek islands | No fetch, no database, no session read |

The guard is in `pnpm verify`, so the gate cannot regress silently. It is
deliberately **not** a Playwright test: the harness sets the flag in order to
walk the gallery, so it can only ever prove the positive case.

### 7.2 The runtime accessibility counter

**The flow:** DOM observation → `counter.count(signal, surface)` → optional sink
→ telemetry.

| Hazard | Control | Evidence |
| --- | --- | --- |
| Telemetry carrying personal data — an accessible name may contain a traveller's name or destination | The event is `{signal, surface}`. Element text is never read into the payload | Test asserts the event object has exactly the keys `signal` and `surface` |
| High-cardinality identifiers in metrics | `surface` is documented as a route *pattern*, `/trips/[id]`, supplied by the caller | Documented at the type; enforced by review, not by code — stated rather than overclaimed |
| Cross-request mixing on the server | Per-instance state, no module-level singleton | Test asserts two counters do not share |
| Telemetry failure breaking the page | The sink is called inside `try`/`catch` **after** the local total is updated | Test asserts a throwing sink neither throws nor loses the count |

No new personal data enters any store, so `REQ-PRIV-006` gains no traversal
target.

## 8. Score

| Dimension | Value | Reason |
| --- | --- | --- |
| Reach | Medium | `components.css` changes the appearance of every component in the product |
| Reversibility | High | Revert the commit; no schema, no data, no contract |
| Detectability | High | 40 browser tests, 267 UI tests, meta-tested guard, 43/43 guard meta-suite |
| Security exposure | Medium | A new gated route; mitigated and guarded (§7.1) |
| Performance | Low | Measured and within budget; CI is ~1 minute slower |
| **Overall** | **MEDIUM** | **Confidence HIGH.** No owner approval required. |

## 9. Post-change verification

| Check | Result |
| --- | --- |
| `pnpm verify` (guards + lint + typecheck + Python + tests + build + gate + browser) | **PASS** |
| `pnpm ci:local` (Linux, clean checkout, cold install, `CI=true`) | **PASS** |
| Playwright | **40 passed** across desktop and Pixel 7 |
| UI suite | 267 passed |
| Web suite | 61 passed |
| Python suite | 335 passed, 5 skipped |
| Guard meta-suite | **43/43** |
| `pnpm test:security` (R7) | **PASS — 12/12** |
| R1–R7 | PASS |
