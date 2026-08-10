---
sub_step_id: STEP-003.06
parent_step: STEP-003
title: Role-aware desktop and mobile navigation
status: IN_PROGRESS
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-A11Y-001, REQ-SEC-004]
blast_radius_id: BR-023
depends_on: [STEP-003.05]
last_updated: 2026-08-10
---

# STEP-003.06 — Role-aware desktop and mobile navigation

## 1. Outcome
Navigation renders by role on desktop and mobile, keyboard-complete, with the clear caveat that **rendering is presentation only and the server is the control**.

## 2. Scope and boundary
**In scope:** `apps/web/src/components/navigation/`; role-aware menu construction; mobile drawer; current-page indication.

**Not in this sub-step:** Server-side authorization ([STEP-002](../../STEP-002-identity-tenancy-and-authorization.md)); admin console navigation ([STEP-021](../../STEP-021-administration-and-curation-console.md)).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-A11Y-001, REQ-SEC-004 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | *(record at execution)* — run `npx gitnexus status` and confirm it matches HEAD. **Application code has been indexed since STEP-002.02**, so a `BLOCKED` result here is a real finding to investigate, not the expected default. |
| HEAD / indexed commit | `94bf916` / `94bf916` — matched |
| Queries run | KG-Q-015 `detect_changes()`; KG-Q-006 once symbols exist |
| Unknown / low-confidence areas | None material |
| Blast radius | [BR-023](../../../10-logs/blast-radius/BR-023-navigation.md) — **MEDIUM**; confidence 4/5, graph runnable |
| Approval required? | Per blast-radius score (HIGH/CRITICAL/low-confidence ⇒ owner approval) |

## 5. Implementation plan
- [x] Named `<nav>` landmark; `aria-current="page"`, and the CSS styles **from that attribute** rather than a separate class, so the visual state cannot say something different from what a screen reader announces
- [x] Trap, restoration and Escape; toggle carries `aria-expanded` and `aria-controls`. All mutation-tested
- [x] Driven by a matrix **generated from the same markdown as the server policy** (`ADR-012`'s review trigger fired; the second emitter reuses the shared parser unchanged). Role is hard-coded to `guest` until the session provider lands — the conservative placeholder
- [x] Stated at the top of the module — **and asserted by tests**: `visibleItems` contains no `fetch`/`redirect`/`throw`, the `href` survives filtering, and the function is named for what it does. A comment alone would be the thing a future reader overrides
- [~] 44×44 declared (AAA 2.5.5, not the 24×24 of AA 2.5.8 — the difference between compliant and usable with a thumb on a moving train). **Declared, not measured**: jsdom computes no layout

## 6. Contracts and schema changes
Contracts are declared in [STEP-004](../../STEP-004-contract-first-platform-apis.md); this sub-step consumes them. Any change here follows [CONTRACT_CHANGE_POLICY](../../../04-contracts/CONTRACT_CHANGE_POLICY.md).

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-A11Y-001 | e2e | Navigation fully keyboard-operable; current page announced |
| TST-SEC-004 | security | Hidden routes remain **server-denied** when requested directly |

## 8. Telemetry, security and accessibility
Traces carry tenant-safe correlation IDs; no PII in telemetry. Any user-facing surface is keyboard and screen-reader complete (`REQ-A11Y-001`) and completable without the map (`REQ-A11Y-003`).

## 9. Documentation to update
- [x] Sub-step completion record
- [x] `IMPL-020` · regression entry · no new BUG
- [x] `BR-023` post-change section
- [x] Parent step §21 · [MASTER_TRACKER](../../../02-delivery/MASTER_TRACKER.md)

## 10. Regression cross-check (R1–R7)
| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression suite | **PASS** | 335 Python + 41 web + 220 UI |
| R2 contract compatibility | **N/A** | No contracts yet (STEP-004) |
| R3 graph diff as expected | **PASS** | New nav package, second emitter; Python emitter untouched |
| R4 untested requirements | **PASS** | `REQ-SEC-004` not fully closed — see acceptance criteria |
| R5 orphan/unowned nodes | **PASS** | Catch-all owner covers both packages and `tools/` |
| R6 closed-bug regression tests | **PASS** | BUG-001…016 |
| R7 tenant isolation | **PASS — 12/12** | Untouched |

**Overall:** PASS / FAIL — a FAIL means this sub-step is not done.

## 11. Rollback
Revert this sub-step's commit; prior sub-steps stay intact and `main` stays deployable. Schema work uses expand/contract, so the expand phase is reversible.

## 12. Acceptance criteria
- [~] Keyboard-complete and axe-clean on both, in jsdom. **Which navigation is visible at a given width** is a rendering property needing a browser (`.08`)
- [x] Every operation × every role, not sampled — and the matrix is generated from the same source as the server's
- [~] **NOT MET — no routes exist to request.** `/admin/*` and `/trips` are not pages and no endpoint enforces anything until STEP-004. The policy is proven at STEP-002.03 across 176 cells, but that is a unit test of the decision function, not a request to a route

## 13. Completion record
| Field | Value |
| --- | --- |
| Status | **`IN_PROGRESS`, not `VERIFIED`** — "directly requesting a hidden route is denied server-side" cannot be tested against routes that do not exist |
| Delivered 2026-08-10 | Desktop nav, mobile drawer, generated matrix, presentation-only property asserted |
| Remaining, and its dependency | Server-denial test — **blocked on STEP-004** creating routes and endpoints. Touch-target and breakpoint measurement — **blocked on `.08`** |
| Implementation | [IMPL-020](../../../10-logs/IMPLEMENTATION_LOG.md) |
| Tests | 21 added (220 in `packages/ui`); 5/5 mutants killed |
| Notes / surprises | The prediction drove the whole design — the security assertions outnumber the rendering ones, and the most valuable of them proves hiding is **not** a control: `visibleItems` contains no `fetch`/`redirect`/`throw` and the `href` survives filtering. **Unpredicted:** `ADR-012`'s review trigger fired here and its prediction held exactly — the second emitter reused the shared parser without touching the Python one. Also: Biome's `useValidAriaRole` fired on a React prop named `role`; renaming to `actorRole` beat suppressing a false positive, and the blanket rename then caught a loop variable of the same name |
| Carried gaps | Server-denial e2e (STEP-004); touch targets and breakpoints in a browser (`.08`); session provider replacing the hard-coded `guest` (STEP-004) |
