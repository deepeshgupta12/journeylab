---
blast_radius_id: BR-062
sub_step_id: BUG-033
title: A focusable scroll region for the design system's table
author: Deepesh Kumar Gupta
date: 2026-09-09
score: MEDIUM
confidence: HIGH
approval_required: false
---

# BR-062 — The table's scroll region

Not a sub-step. This is the fix for `BUG-033`, deferred at STEP-007.02 because the
component belongs to `STEP-003.04` and a design-system change earns its own record
rather than riding along inside a product sub-step.

## 1. Graph state

| Field | Value |
| --- | --- |
| Indexed commit | `7f17bb6`, re-indexed to `93f93de` scope |
| HEAD at check | `93f93de` |
| Freshness | ✅ `status` reports up to date |
| Result | **NOT BLOCKED** |
| Confidence | **HIGH — by grep and the type-checker, not by the graph** |

The re-index reported **11,054 nodes, 16,850 edges, 224 clusters, 77 flows**, and
three files whose scopes it could not extract:

```
apps/api/src/conventions/__init__.py
services/ingestion/src/entity_resolution.py
tests/api/test_api_operations.py
```

None is touched here, but a file the analyser cannot scope is a file impact analysis
under-reports, which is the `RISK-016` mechanism. Carried as a follow-up rather than
fixed in a UI change.

## 2. Queries run — and RISK-016's fourteenth reproduction, first in TypeScript

| Symbol | Graph (`upstream`) | Grep | Agreed? |
| --- | --- | --- | --- |
| `DataTable` | **0, LOW, `"epistemic": "exact"`** | **4 dependants** | ❌ |

```
impact({target: "DataTable", direction: "upstream", repo: "journeylab",
        file_path: "packages/ui/src/data/table.tsx", maxDepth: 3, includeTests: true})
-> impactedCount 0 · risk LOW · epistemic "exact" · byDepth {}
```

What grep found in the same second:

| Dependant | Why it matters |
| --- | --- |
| `packages/ui/src/index.ts:32` | the barrel every consumer imports through |
| `packages/ui/src/data/data.test.tsx:43` | the design-system suite |
| `apps/web/src/app/dev/gallery/gallery-client.tsx:255,264` | two specimens |
| `apps/web/src/app/coverage/coverage-table.tsx:76` | **the shipped coverage page** |

**This is the first reproduction of `RISK-016` outside Python.** Every previous one
(thirteen, worst measured at STEP-007.03) was the API application's route handlers
being island nodes. The risk register describes the failure as specific to
`apps/api/src/app.py`; it is not. A design-system component exported through a barrel
and imported by four modules also reports zero dependants at `"epistemic": "exact"` —
the word the tool uses to mean "this count is not an estimate".

`RISK-016` should be widened accordingly. Its current wording would let a reader
conclude a TypeScript `LOW` is trustworthy. It is not.

**Confidence is HIGH regardless, and not from the graph.** `DataTable` is exported
from one barrel in a pnpm workspace under `tsc --noEmit`; a missed consumer is a
compile error, not a silent break. The type-checker is the complete reference check
the graph failed to be. Recorded this way so the confidence is attributed to the
thing that actually earned it.

## 3. Scoring

| Category | Assessment |
| --- | --- |
| Code | `packages/ui/src/data/table.tsx`, `packages/ui/src/components.css` |
| Contract / schema / event | **None** |
| Data / migration | **None** |
| Security / tenancy | **None** — a public, unauthenticated surface; no data path changes |
| Surfaces | `/coverage` (product), `/dev/gallery` (flag-gated), every future table |
| Tests | 4 added (design system), 4 added (browser), 2 rewritten |
| **Score** | **MEDIUM** |
| Approval | **Not required** — MEDIUM with HIGH confidence |

MEDIUM rather than LOW because the DOM structure of every table in the product
changes, and because it adds a tab stop to a keyboard order other tests assert
against — which it did: one existing test failed and was updated, deliberately.

## 4. What changed, and the part that is not tidying

The wrapper became two elements: a focusable `<section class="jl-table__scroll">`
holding the table, and the CSV button **outside** it.

Moving the button is the substance of the fix, not housekeeping. `BUG-033`'s root
cause was that axe's `scrollable-region-focusable` was satisfied by a focusable
descendant that sat outside the overflowing content. Adding `tabindex` alone would
have fixed the product and left the detector still passing for the wrong reason.

Proven, not asserted — with the button moved back inside and `tabindex` retained,
**all three axe tests still report zero AA violations** and only the explicit
boundary assertion fails. See §6.

## 5. The trade taken: an unconditional tab stop

Whether a table overflows is a fact about layout. It does not exist at render time
and differs between the server and client passes, so a `tabindex` conditioned on it
is a hydration mismatch dressed as an accessibility feature.

The tab stop is therefore unconditional: a table that fits gets one extra stop. That
is a smaller defect than content no key can reach, and it is visible in the tab-order
test rather than hidden.

**The bare-table form was measured, not assumed.** `apps/web/src/app/page.tsx` applies
`.jl-table` directly to a `<table>`. At 412px it measures **380 scrollWidth of 380
clientWidth — it does not overflow**, so it has no defect today and was given no tab
stop. Because "does not overflow today" is a fact about content, the invariant is
asserted instead of the measurement: every horizontally-scrolling element on `/`,
`/coverage` and `/dev/gallery` must be able to take focus.

## 6. Mutation testing

| # | Seeded defect | Killed by | Result |
| --- | --- | --- | --- |
| 1 | `tabIndex` removed | `exposes the table in a focusable region`; tab-order test | ✅ 2 failed |
| 2 | `aria-labelledby` removed | all four scroll-region tests + tab order | ✅ 5 failed |
| 3 | **CSV button moved back inside the region** | `KEEPS THE CSV BUTTON OUT` **only** | ✅ 1 failed |
| 4 | `tabIndex` removed, in a real browser | 10 browser tests, both projects | ✅ 10 failed |

Mutant 3 is the one worth reading twice. It restores the exact condition of
`BUG-033`, and **axe passes it** — `table has zero AA violations`, `list has zero AA
violations`, `empty table has zero AA violations`, all green. The only thing that
catches it is an assertion written because a human read the rule's purpose rather
than its result.

Mutant 4 also showed where the new invariant does **not** yet bite: `every
horizontally-scrolling element on /coverage can take focus` passed under the mutant,
because the coverage page currently renders an empty region list that does not
overflow. The invariant is real but presently vacuous on that surface; the gallery,
where the fixture is ours to control, is what makes it a gate.

## 7. Follow-up created

| Item | Type |
| --- | --- |
| Widen `RISK-016` beyond `apps/api/src/app.py` — it reproduces in TypeScript | Risk register |
| Three files the analyser cannot scope | Investigate before the next impact query touching them |
