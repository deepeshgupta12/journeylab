---
blast_radius_id: BR-067
sub_step_id: BUG-038
title: The browser reaches the API only through the page's own origin
author: Deepesh Kumar Gupta
date: 2026-10-19
score: MEDIUM
confidence: HIGH
approval_required: true
---

# BR-067 — The browser reaches the API only through the page's own origin

Not a sub-step. The fix for `BUG-038`, found by the owner at the first manual review of
`/coverage`: the date check and the waitlist — the only two things a traveller can *do* on
the only product page — fail in every real browser. Design chosen by the owner the same
day: **same-origin proxy** (`ADR-022`), over adding CORS to the API.

## 1. Graph state — and the directory the graph could not see

| Field | Value |
| --- | --- |
| Indexed commit | `62b65d0`, forced re-index after the ignore change below |
| HEAD at check | `62b65d0` |
| Freshness | ✅ up to date before any code edit |
| Result | **NOT BLOCKED — after a repair that is itself part of this record** |
| Confidence | **HIGH**, sourced from grep and `tsc --noEmit`, not from the graph (§2) |

**The first three `impact` queries returned "Target not found."** Not zero dependants —
absent. A Cypher count confirmed it: a fresh index held **zero nodes** under
`apps/web/src/app/coverage/`, while holding `app/api/auth/*`, `app/dev/gallery/*`,
`layout.tsx` and `page.tsx` beside it. The directory containing the product page was
invisible to impact analysis.

**Cause, read from the indexer's source and then tested.** GitNexus 1.6.8 —
`dist/config/ignore-service.js:62` — ships a built-in ignore list containing the bare
name `coverage`, because test tooling writes reports to directories of that name. Ours is
a Next.js route whose name is the public URL `/coverage`. `.gitignore` was *not* the cause
(`git check-ignore` exit 1; `BUG-032` anchored those patterns), and `.gitnexusignore` held
only the two `generated/` entries. Among all tracked directories, `coverage` is the only
name on that default list we did not intend to exclude.

**Repair.** The tool documents its own remedy (ignore-service.js ~L254, upstream #771): a
`!pattern` line in `.gitnexusignore` re-includes what a default excludes. One line added,
`analyze --force` run (plain `analyze` short-circuits on an unchanged HEAD and never reads
the file), and measured: **11,645 → 11,730 nodes, 77 → 79 flows, nine files, 74 nodes**
under the directory. Recorded as **`RISK-018`**. `REQ-KG-001`'s arithmetic: 9 of 578
tracked source files, 1.6% — numerically within the 95% gate, and the nine files were the
product.

## 2. Queries run — the graph was right once and wrong twice, and this time it discriminates

| Symbol | Graph (`upstream`, tests included) | Grep | Agreed? |
| --- | --- | --- | --- |
| `fetchCoverage` | **1** — `CoveragePage` CALLS, confidence 0.9 | `page.tsx:3` import, `:32` call | ✅ |
| `PlanningCheck` | **0, LOW, `"epistemic": "exact"`** | `page.tsx:4` import, `:69` **rendered as JSX**; 10 references in its test | ❌ — **`RISK-016` #20** |
| `Waitlist` | **0, LOW, `"epistemic": "exact"`** | `page.tsx:5` import, `:78` rendered; 15 references in its test | ❌ — **`RISK-016` #21** |

Three symbols, one directory, one index. The plain function call resolved; the two JSX
element usages did not. `BR-062` §2's `DataTable` was also used as a JSX element. **Stated
as an observation about TSX with the test that produced it, not as the mechanism** — it
says nothing about the Python reproductions, and the last mechanism published from a
single run was retracted the next day.

The production dependency set is small and closed: **`page.tsx` is the only non-test
consumer of all three.** `tsc --noEmit` is the complete reference check for the TypeScript
changes, as `RISK-016`'s mitigation names it.

## 3. The decision, and who took it

| Decision | Options | Taken by |
| --- | --- | --- |
| How a client island reaches the API | (a) CORS middleware on the API with a per-environment allowlist · (b) same-origin Next route handlers forwarding server-side | **Owner — (b)**, `ADR-022` |
| Handle the UX finding from the same review | before `STEP-008` · fold into `STEP-008` · log and wait | **Owner — a UX pass on `/coverage` before `STEP-008`** (separate, follows this fix) |

**Why (b).** `/api/auth/*` already proxies the same way, so the pattern exists; the browser
bundle stops carrying the API's address; no origin allowlist has to be kept correct across
environments; and `STEP-008.01`'s guest-session cookie stays first-party, which (a) would
have made cross-origin. `FRONTEND_ARCHITECTURE` said nothing either way — it now will.

## 4. What changes

| Category | Change |
| --- | --- |
| **Code — new** | `apps/web/src/app/api/coverage/_proxy.ts` — one forwarding helper. `check/route.ts`, `waitlist/route.ts`, `waitlist/withdraw/route.ts` — three `POST` handlers mapping to `/coverage:check`, `/waitlist`, `/waitlist:withdraw`. `apps/web/src/app/coverage/api-base.ts` — the server-side base URL, defined once |
| **Code — modified** | `planning-check.tsx`, `waitlist.tsx` — relative paths; `NEXT_PUBLIC_JOURNEYLAB_API_URL` removed; **503 → `unreachable` in all three flows** (today a 503 renders in the withdrawal form as *"That code does not work"*). `fetch-coverage.ts` — imports the shared base instead of declaring its own |
| **Contract** | **None to the platform API.** The three handlers are internal to the web app, like `/api/auth/*`; they appear in no OpenAPI document and are not a public surface |
| **Schema** | None |
| **Config** | `.gitnexusignore` — one negation line (§1). `playwright.config.ts` — `globalSetup`/`globalTeardown`; **and the Core Web Vitals tests move into `vitals-*` projects that `dependencies` run after the functional projects** — the first run against the populated page measured `/coverage` LCP at 2.8 s under eight parallel workers and 2.2–2.4 s alone, against a 2.5 s budget. Same tests, selected by `grep`; CI semantics unchanged (CLS enforced, LCP reported). A gate that passes only on an idle machine is `BUG-016`'s flaky gate |
| **Tests** | `_proxy.test.ts`; `planning-check.test.tsx` and `waitlist.test.tsx` extended; `coverage.spec.ts` — the two empty-state tests replaced by tests that **submit both forms through the real proxy to the real API**; `tools/e2e_region.py` — seeds and removes the suite's reserved region and its waitlist rows |
| **Docs** | `ADR-022`; `FRONTEND_ARCHITECTURE` gains the rule; `BUG-038` → FIXED; `RISK_REGISTER` `RISK-018` new, `RISK-016` #20–21; `CLAUDE.md` §7; `IMPL-069`; `REGRESSION_LOG` |
| **Tenancy** | None — all three operations are public and unauthenticated. **One tenancy-adjacent rule is created:** the proxy forwards an allowlist of headers and **never cookies**, so the session infrastructure cannot leak toward the API by accident |

## 5. The proxy's rules — each one a mutant later

1. Forward **only** `content-type`, `accept`, `Idempotency-Key`, `X-Correlation-Id`. No cookie, no authorization, nothing else.
2. Preserve the upstream **status**, **body** and **content-type** — a problem document arrives as `application/problem+json` and leaves the same way.
3. Return the upstream `X-Correlation-Id` so a traveller's report can be matched to a log line.
4. An unreachable or timed-out upstream is a **503 problem document** of the platform's shape, never an exception, never a 200.
5. ~~A request body over 16 KiB is refused with 413 before anything is forwarded.~~ **Removed before implementation.** The error registry holds four codes and none for an oversize body; a proxy emitting an invented code would be a second place describing the error model, which is the `BUG-029` drift in miniature. Body validation stays where it is — in the API. Recorded rather than deleted so the plan matches what was built.
6. The API base is read from the server's environment, once, in one file. The browser bundle contains no API address.
7. The `Idempotency-Key` stays **client-minted** — it represents one user intent across retries, and a key minted in the proxy would give every browser retry a fresh key, defeating the purpose.

## 6. The end-to-end test owns its data

`coverage.spec` line 89 told its own future: *"When the first region is declared this test
must be replaced by one that exercises the form, not deleted."* It is replaced. The suite
seeds a reserved region (`e2e-bern`) in `globalSetup` and removes it, with any waitlist rows
its run created, in `globalTeardown` — so the result no longer depends on what the
developer's database happens to hold, which is exactly how the owner's review seed would
otherwise have turned the suite red. The empty state stays covered where it already was:
at the component level.

## 7. Scoring

**MEDIUM.** The code reach is small and closed (two components, one page). The weight is
that this **sets the browser→API pattern for every form `STEP-008` builds**, which is why
it is an ADR and why the owner, not the implementer, chose it.

## 8. R2 — stated rather than implied

No platform contract changes, so `check_compatibility.py` has nothing to diff. The three
handlers are not in any contract document; whether internal BFF routes *should* be
described somewhere is a question this record raises and does not answer.

## 9. Mutation plan

| # | Seeded defect | Must be killed by |
| --- | --- | --- |
| 1 | proxy forwards the `cookie` header | `_proxy.test` — cookie never reaches upstream |
| 2 | proxy drops `Idempotency-Key` | `_proxy.test` — key forwarded verbatim |
| 3 | proxy returns 200 on upstream network failure | `_proxy.test` — 503 problem document |
| 4 | proxy rewrites upstream status to 200 | `_proxy.test` — 422 preserved |
| 5 | proxy drops the problem `content-type` | `_proxy.test` — `application/problem+json` preserved |
| — | ~~oversize body forwarded~~ | **No mutant — the cap was removed with rule 5 above** |
| 6 | a component builds an absolute URL again | component tests — URL is relative |
| 7 | `PlanningCheck` treats 503 as a refusal | component test — 503 → "could not check" |
| 8 | `Waitlist` withdrawal treats 503 as "code does not work" | component test — 503 → "could not reach" |
| 9 | the e2e teardown is removed | a second run finds the seed and the waitlist rows (asserted in setup) |
| 10 | `check/route.ts` forwards to the wrong path | `_proxy.test` — path mapping per route |

## 10. Follow-ups created

| Item | Type |
| --- | --- |
| `RISK-018` — the indexer's built-in ignore list hides a route directory; defaults are not ours and can change in a minor version | Risk register |
| `RISK-016` #20, #21 — with the TSX observation in §2 | Risk register |
| Whether internal BFF routes belong in a contract document | Carried to the step that next adds one |
| The UX pass on `/coverage` the owner chose | New sub-step, after this fix |
