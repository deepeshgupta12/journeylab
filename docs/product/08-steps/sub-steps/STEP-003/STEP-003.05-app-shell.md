---
sub_step_id: STEP-003.05
parent_step: STEP-003
title: Application frame, providers and global error boundary
status: IN_PROGRESS
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-A11Y-001, REQ-NFR-013]
blast_radius_id: BR-022
depends_on: [STEP-003.04]
last_updated: 2026-08-07
---

# STEP-003.05 — Application frame, providers and global error boundary

## 1. Outcome
The app frame renders with providers, metadata, skip links and a global error boundary, so a feature failure degrades one region instead of blanking the page.

## 2. Scope and boundary
**In scope:** `apps/web/src/app/layout.tsx`; query/session/i18n providers; skip-to-content; global and feature error boundaries; metadata.

**Not in this sub-step:** Navigation (`.06`); route-level pages.

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-A11Y-001, REQ-NFR-013 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | *(record at execution)* — run `npx gitnexus status` and confirm it matches HEAD. **Application code has been indexed since STEP-002.02**, so a `BLOCKED` result here is a real finding to investigate, not the expected default. |
| HEAD / indexed commit | `b09a0a2` / `b09a0a2` — matched |
| Queries run | KG-Q-015 `detect_changes()`; KG-Q-006 once symbols exist |
| Unknown / low-confidence areas | **Acted on:** order documented outermost-in in `providers.tsx`, with the rule it produces — *nothing that fetches sits above the session* |
| Blast radius | [BR-022](../../../10-logs/blast-radius/BR-022-app-shell.md) — **MEDIUM**; confidence 4/5, graph runnable |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [x] Order documented outermost-in: global boundary → locale → session → query/data. The rule: **nothing that fetches sits above the session**, because a client cache keyed without one can serve one tenant's data to another
- [x] First in the document, verified against the **live dev server** as well as in tests. Its target carries `tabIndex={-1}` — without that, browsers scroll without moving focus and the link looks like it worked
- [x] `role="alert"` here, because there is nothing left to interrupt; offers reload and states that trips are saved
- [x] `FeatureErrorBoundary` contains the failure between siblings. **The error message is never rendered** — it can carry a URL, stack frame or provider response; it goes to `onError` instead
- [x] `lang` and `dir` **derived together** — a mismatched pair is worse than either alone, and that is what a hand-maintained setting drifts into

## 6. Contracts and schema changes
Contracts are declared in [STEP-004](../../STEP-004-contract-first-platform-apis.md); this sub-step consumes them. Any change here follows [CONTRACT_CHANGE_POLICY](../../../04-contracts/CONTRACT_CHANGE_POLICY.md).

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-A11Y-001 | e2e | Skip link works; landmarks present |
| — | component | A throwing child is contained by its feature boundary |

## 8. Telemetry, security and accessibility
Traces carry tenant-safe correlation IDs; no PII in telemetry. Any user-facing surface is keyboard and screen-reader complete (`REQ-A11Y-001`) and completable without the map (`REQ-A11Y-003`).

## 9. Documentation to update
- [x] Sub-step completion record
- [x] `IMPL-019` · regression entry · no new BUG
- [x] `BR-022` post-change section
- [x] Parent step §21 · [MASTER_TRACKER](../../../02-delivery/MASTER_TRACKER.md)

## 10. Regression cross-check (R1–R7)
| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression suite | **PASS** | 335 Python + 41 web + 199 UI |
| R2 contract compatibility | **N/A** | No contracts yet (STEP-004) |
| R3 graph diff as expected | **PASS** | Wider than usual — every `packages/ui` module changed import specifiers and gained `'use client'` |
| R4 untested requirements | **PASS** | `REQ-A11Y-001` not fully closed — CWV unmeasurable here |
| R5 orphan/unowned nodes | **PASS** | Catch-all owner covers both packages |
| R6 closed-bug regression tests | **PASS** | BUG-001…016 |
| R7 tenant isolation | **PASS — 12/12** | Untouched |

**Overall:** PASS / FAIL — a FAIL means this sub-step is not done.

## 11. Rollback
Revert this sub-step's commit; prior sub-steps stay intact and `main` stays deployable. Schema work uses expand/contract, so the expand phase is reversible.

## 12. Acceptance criteria
- [x] Present, first, and functional — verified against the live server
- [x] `header`, `main`, `footer` present in the rendered document
- [x] Asserted directly, and mutation-tested by making the boundary re-throw
- [~] **NOT MET — unmeasurable here.** LCP, INP and CLS need a real browser and Lighthouse (STEP-003.08). The shell is small and static and likely passes; likely is not measured

## 13. Completion record
| Field | Value |
| --- | --- |
| Status | **`IN_PROGRESS`, not `VERIFIED`** — "CWV budgets met on the empty shell" cannot be measured without a browser, and marking it done would put a false green in the tracker |
| Delivered 2026-08-07 | Landmarks, skip link, provider order, feature and global error boundaries, derived `lang`/`dir` |
| Remaining, and its dependency | CWV measurement — **blocked on STEP-003.08**, which brings a real browser and Lighthouse. Nothing else outstanding |
| Implementation | [IMPL-019](../../../10-logs/IMPLEMENTATION_LOG.md) |
| Tests | 20 added (199 in `packages/ui`); 5/5 mutants killed; shell verified against the live dev server |
| Notes / surprises | The prediction was right and drove the design — containment is per-feature, and a test asserts the itinerary survives when the map throws. **Unpredicted:** two architectural problems appeared the moment a real app imported `packages/ui` — `.tsx` import specifiers require every consumer to enable `allowImportingTsExtensions`, and seven modules needed `'use client'`. Neither was visible while the package was consumed only by its own tests. Also: Biome flagged a **dead suppression comment for the second sub-step running**, which is a habit of mine rather than bad luck |
| Carried gaps | CWV measurement (`.08`); locale/session/query providers (`.07`, STEP-004); error reporting sink (STEP-024) |
