---
blast_radius_id: BR-024
sub_step_id: STEP-003.07
title: Locale, time zone, currency and DST handling
author: Deepesh Kumar Gupta
date: 2026-08-10
score: MEDIUM
confidence: HIGH
approval_required: false
---

# BR-024 — Locale, time zone, currency and DST handling

> The sub-step record predicts `BR-020`. That number was taken by
> STEP-003.03 (feedback primitives) when the numbering ran ahead of the
> plan; this record is `BR-024`, continuing from `BR-023`. The stale
> prediction is corrected in the sub-step file.

## 1. Graph state at the time of the check

| Field | Value |
| --- | --- |
| Tool | `npx gitnexus status`, `gitnexus_impact` (MCP) |
| Indexed commit | `bb943f9` |
| HEAD at check | `bb943f9` |
| Freshness | ✅ up to date |
| Result | **NOT BLOCKED** — TypeScript symbols resolve; three real impact queries returned `epistemic: exact` |
| Confidence | **HIGH** for symbol-level reach inside a package; **MEDIUM** at the package boundary (see §3) |

## 2. Queries run

| # | Query | Result |
| --- | --- | --- |
| 1 | `impact(startOfDayUtc, upstream, includeTests)` | 1 direct — `form/form.test.tsx`. LOW, `exact` |
| 2 | `impact(documentLocale, upstream, includeTests)` | 1 direct — `shell/shell.test.tsx`. LOW, `exact` |
| 3 | `impact(packages/ui/src/index.ts, upstream)` | **0 impacted** — see §3, this is a graph limitation, not a fact |
| 4 | `detect_changes()` | Run pre-commit; recorded in the regression entry |

## 3. A graph limitation worth stating, not glossing

Query 3 reports that **nothing** depends on the design-system barrel. That is
false in the source: `apps/web/src/app/layout.tsx`, `navigation.tsx` and
`providers.tsx` all import from `@journeylab/ui`, which resolves through the
pnpm workspace link to that file.

The graph resolves relative imports and does not follow the `workspace:*`
package alias. So **cross-package impact is invisible to `gitnexus_impact` in
this repository**, and a `0 impacted` result on a package entry point means
"not traced", not "not used".

Consequence for this record: the within-package reach below is graph-verified;
the `packages/ui` → `apps/web` edge is verified by `grep` and by the compiler,
and its confidence is stated as MEDIUM rather than borrowed from the graph.
This is the honest position under `REQ-KG-008`, and it is a candidate finding
for `STEP-026`.

## 4. Change inventory

**Added**

| File | Purpose |
| --- | --- |
| `packages/ui/src/i18n/money.ts` | Money as integer minor units |
| `packages/ui/src/i18n/datetime.ts` | Locale/zone-explicit formatting; DST-correct durations |
| `packages/ui/src/i18n/messages.ts` | ICU-shaped catalogue loading with a documented fallback |
| `packages/ui/src/i18n/i18n.test.tsx` | TST-NFR-007, TST-NFR-008 |
| `apps/web/src/lib/i18n.ts` | Request-scoped negotiation (the path the sub-step names) |
| `apps/web/src/lib/messages/en.ts` | Source-language catalogue |
| `apps/web/src/lib/i18n.test.ts` | TST-NFR-007, TST-SEC-006 |
| `tests/guards/logical-css.sh` | Physical CSS properties fail the build |

**Modified**

| File | Change |
| --- | --- |
| `packages/ui/src/index.ts` | 25 new exports; **no existing export changed or removed** |
| `apps/web/src/app/layout.tsx` | Locale negotiated per request; `lang`/`dir` derived together |
| `apps/web/src/app/shell.css` | `top`/`left` → `inset-block-start`/`inset-inline-start` |
| `apps/web/next.config.ts` | `typescript.ignoreBuildErrors` — **BUG-017**, see §6 |
| `apps/web/package.json` | `@typescript/native-preview` marker devDependency — **BUG-017** |
| `package.json` | `guard:logical-css` and `build` added to `verify` |
| `tests/guards/meta/run-all.sh` | Meta-tests for the new guard |

## 5. Twelve impact categories

| # | Category | Assessment |
| --- | --- | --- |
| 1 | **Callers / call graph** | Additive. `startOfDayUtc` and `documentLocale` are *read* by the new code, not modified; their only callers are their own tests. `datetime.ts` imports `isValidTimeZone` from `form/zoned-date.ts` — a new intra-package edge, no cycle (`guard:boundaries` PASS). |
| 2 | **Public API / contracts** | `packages/ui` gains 25 exports and loses none. No HTTP contract touched — STEP-004 owns those. |
| 3 | **Database / schema** | None. No migration, no query. |
| 4 | **Events** | None. |
| 5 | **Configuration** | `verify` gains two steps (`guard:logical-css`, `build`). `next.config.ts` gains one flag. No environment variable added, so no deployment change. |
| 6 | **Infrastructure** | None. |
| 7 | **Security** | **Material, and the reason this is MEDIUM not LOW.** `Accept-Language` becomes a request input the server reads. It is untrusted (`REQ-SEC-006`). See §7. |
| 8 | **Privacy** | `Accept-Language` is weakly identifying and contributes to a browser fingerprint. It is read, used to select a catalogue, and **not stored, logged or emitted in telemetry** — no cookie, no database column, no event field. `REQ-PRIV-003` (no sensitive attribute inferred from behaviour) holds: a language preference is not treated as a proxy for nationality, ethnicity or residence anywhere. |
| 9 | **Accessibility** | Positive. `lang` and `dir` are now derived together and cannot drift into the `lang="ar" dir="ltr"` pair. Logical CSS is a precondition for RTL. `REQ-A11Y-001` unaffected otherwise; axe passes under an RTL locale. |
| 10 | **Performance** | **A real cost, accepted and documented.** `headers()` in the root layout opts every route out of static rendering — the build output now marks all 7 routes `ƒ (Dynamic)`. Free today (the only page is already `force-dynamic` for session cookies); not free once STEP-007 adds cacheable pages. Migration path — a `/[locale]/` segment — is written into `layout.tsx`. |
| 11 | **Tenancy** | None. Nothing here reads or writes tenant-scoped data; no cache key is derived from the locale. `R7` unaffected by construction. |
| 12 | **Documentation** | This record, `IMPL-021`, `REGRESSION_LOG`, `BUG-017`, the sub-step record, `MASTER_TRACKER`. |

## 6. Pre-existing defect found while doing the work — BUG-017

`pnpm --filter @journeylab/web build` **failed at `bb943f9`, before any change
in this sub-step**. Verified by stashing the working tree and building at HEAD:
identical failure. It is logged as `BUG-017` and fixed here rather than left,
because the completion record asks whether `main` is deployable and it was not.

Root cause and fix are in the bug register. Two points belong here:

**The first fix was incomplete and `pnpm ci:local` caught it after the commit
and before the push.** `ignoreBuildErrors` made the build pass locally; under
`CI=true` the same probe aborts on a different branch. Fixed properly with
Next's own `@typescript/native-preview` signal, then re-verified in the mirror.

**The structural fix is that `pnpm build` is now part of `pnpm verify`**, so the
production build cannot break silently again. It also protects its own fix:
removing the marker dependency fails `verify`, with no extra guard needed.

## 7. Mandatory data-flow inspection

**The flow:** `Accept-Language` header → `parseAcceptLanguage` →
`negotiateLocale` → key lookup in a statically-imported `CATALOGUES` object →
`createTranslator` → rendered text.

**What could go wrong, and what stops it:**

| Hazard | Control | Evidence |
| --- | --- | --- |
| **Path traversal** — the naive loader is `import('./messages/' + locale)`, and `Accept-Language: ../../../../etc/passwd` then reads an arbitrary module | The header is never concatenated into anything. Catalogues are statically imported into a fixed object; a miss is `undefined` | 9 hostile headers asserted to yield a shipped locale; a source check (comments stripped) asserts no dynamic specifier is constructed |
| **CPU exhaustion** — a 2 MB header with 50,000 q-weighted tags, on every request | 512-byte cap, checked **before** any splitting | Mutation: removing the cap fails the suite |
| **Injection into rendered output** | The header never reaches the DOM. Only catalogue *values* are rendered, and React escapes them | The negotiated value is always a key of `CATALOGUES`, asserted for every hostile input |
| **Cross-request leakage** — a cached "current locale" shared between concurrent requests, so one user sees another's language | No module-level mutable state; the translator is a value built per request | Test asserts two translators coexist without interference |
| **Silent wrong language** — a dropped catalogue rendering raw message keys to users | Load-time invariant throws if the fallback locale has no catalogue | Proven by renaming the catalogue key and observing the error |

**Personal data:** none stored. The header is read and discarded within the
request. No new field enters logs, telemetry, the database or a cache key, so
`REQ-PRIV-006` (deletion traversal) acquires no new store.

## 8. Score

| Dimension | Value | Reason |
| --- | --- | --- |
| Reach | Low–Medium | Additive within `packages/ui`; one modified rendering path in `apps/web` |
| Reversibility | High | Revert the commit; no schema, no data, no contract |
| Detectability | High | 26 mutants killed; both suites pass under 5 host time zones |
| Security exposure | Medium | A new untrusted request input, fully mitigated (§7) |
| Performance | Medium | Every route becomes dynamic — accepted, documented, with a named migration |
| **Overall** | **MEDIUM** | **Confidence HIGH.** No owner approval required. |

## 9. Post-change verification

| Check | Result |
| --- | --- |
| `pnpm verify` (guards + lint + typecheck + Python + tests + **production build**) | PASS |
| Guard meta-suite | 40/40 |
| `pnpm test:security` (R7) | **PASS — 12/12**, including the meta-test that a weakened policy exposes both tenants |
| `pnpm ci:local` (Linux, clean checkout, cold install) | PASS |
| UI suite | 256 passed |
| Web suite | 61 passed |
| Python suite | 335 passed, 5 skipped |
| Host-zone independence | PASS under UTC, Pacific/Auckland, America/Los_Angeles, Asia/Kolkata, Europe/London |
| `detect_changes()` scope | As expected — recorded in `REGRESSION_LOG` |
| R1–R7 | PASS |
