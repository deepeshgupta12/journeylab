---
blast_radius_id: BR-027
sub_step_id: STEP-003 closure (not a numbered sub-step)
title: End-to-end smoke test and README accuracy
author: Deepesh Kumar Gupta
date: 2026-08-11
score: LOW
confidence: HIGH
approval_required: false
---

# BR-027 — End-to-end smoke test and README accuracy

## 1. What this is, and why it is not a sub-step

Two closure tasks requested at the end of STEP-003:

1. **Test the system end to end** — every layer built so far, in one pass, in the
   order a real request meets them.
2. **Bring the README back to the truth.** It still described a repository with
   no application code.

Neither belongs to a numbered sub-step. Both are repository work, so they get a
record rather than an exemption — `REQ-KG-008` says "code, schema, API, event,
model, prompt, infrastructure **or configuration**", and a test harness plus the
project's front door is configuration in every sense that matters.

## 2. Graph state

| Field | Value |
| --- | --- |
| Indexed commit | `64ce720` (STEP-003.09, pushed) |
| HEAD at check | `64ce720` |
| Freshness | ✅ up to date |
| Result | **NOT BLOCKED** |
| Queries | `detect_changes()`. No symbol-level query: nothing here is a symbol — a shell script and two Markdown files |

## 3. Change inventory

| File | Change |
| --- | --- |
| `tests/e2e/smoke.sh` | **New.** Eight sections, 27 checks — including 5b, the development server (BUG-019) |
| `package.json` | `pnpm e2e` |
| `README.md` | Status, verify description, repository map, what exists, test counts, graph coverage, blockers |
| `apps/web/src/app/dev/gallery/gallery-client.tsx` | **BUG-019** — the error specimen throws from an effect, not during server rendering |
| `tests/guards/readme-accuracy.sh` | Script-name pattern accepts digits (`a11y` was read as `a`) |

## 4. Twelve impact categories

| # | Category | Assessment |
| --- | --- | --- |
| 1 | Callers / call graph | None. No symbol added or changed |
| 2 | Public API / contracts | None |
| 3 | Database / schema | None. The suite **reads** through the existing isolation tests; it creates nothing |
| 4 | Events | None |
| 5 | Configuration | One new script. `pnpm verify` is **unchanged** — see §5 |
| 6 | Infrastructure | None. The suite starts the existing compose stack and stops the server it started |
| 7 | Security | The suite asserts three security properties that nothing else asserted end to end: the session endpoint leaks no token, sign-in carries PKCE S256 and `state`, and the gallery is absent without its flag |
| 8 | Privacy | None. No data created, stored or transmitted |
| 9 | Accessibility | None directly; the suite runs the existing gate. **BUG-019 restored the gallery in dev**, which is where the design system is reviewed |
| 10 | Performance | None in the product. The suite takes ~4 minutes, which is why it is not in `verify` |
| 11 | Tenancy | None. It invokes the R7 suite rather than reimplementing it |
| 12 | Documentation | This record, the README, `IMPL-024` |

## 5. Why `pnpm e2e` is NOT part of `pnpm verify`

`verify` already runs the unit suites, the production build, the gate guard and
the 40 browser tests, and takes about three minutes. The end-to-end suite adds
Docker, a database, a migration and the isolation suite for another four.

A gate that takes seven minutes gets skipped, and a skipped gate is worse than a
slow one. `verify` stays the thing you run constantly; `e2e` is what you run
before closing a step, and the README says so.

The honest cost of that choice: **nothing automatically runs `pnpm e2e`.** It is
a command a person must remember. That is a real gap and it is written here
rather than glossed; it closes when there is a pipeline stage that can afford
Docker (`STEP-027`).

## 5b. The coverage gap BUG-019 exposed

Worth stating separately, because it is larger than the bug.

**Every automated check in this repository builds for production**: the 40 browser
tests, `pnpm verify`, `pnpm ci:local`, and section 5 of this suite. `next dev`
renders on a different path — no minification, different hydration, and a
different tolerance for a throw during server rendering.

That mode had **no coverage at all**. The gallery returned 500 there for a whole
sub-step and was found by the owner opening a URL, not by a test.

Section 5b closes it: start `next dev`, assert three routes return 200, and fail
if the server logged an exception while rendering. It is a smoke check, not a
suite — the question it answers is "does this mode work at all", which had never
been asked.

## 6. Data-flow inspection

The suite reads `.env` to decide whether real Auth0 configuration exists, and
**never prints it**. It greps for the presence of `AUTH0_ISSUER=https://` and
uses only the boolean.

That check exists because the first version got this exactly wrong in the other
direction: it exported placeholder credentials, `process.loadEnvFile` declined to
overwrite them, and the suite then reported "sign-in redirect lacks PKCE S256" —
a defect in the configuration it had itself imposed, reported as a defect in the
product. **A test that supplies broken configuration and then reports the
breakage is worse than no test**, so the placeholders are now applied only when
there is nothing real to use, and the PKCE assertions become a SKIP rather than a
FAIL when they cannot honestly run.

No credential is written to a log. Server output goes to `/tmp/jl-e2e-server.log`,
which contains Next.js startup lines only.

## 7. Score

| Dimension | Value | Reason |
| --- | --- | --- |
| Reach | Low | Nothing in the product changes |
| Reversibility | High | Delete one file and one script entry |
| Detectability | High | The suite reports its own PASS/FAIL/SKIP per check |
| Security exposure | None | Read-only; reveals no secret |
| **Overall** | **LOW** | Confidence HIGH |

## 8. Post-change verification

| Check | Result |
| --- | --- |
| `pnpm e2e` | **25 passed, 0 failed, 2 skipped.** Both skips honest: CSP headers land at STEP-023; the graph is legitimately stale with a dirty tree |
| `pnpm verify` | PASS |
| `readme-accuracy` guard | PASS, after the digit fix |
| First run of the suite | **Found four defects in itself** and one in the tree state; all corrected before commit (`IMPL-024`) |
