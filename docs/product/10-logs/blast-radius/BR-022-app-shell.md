# BR-022 — Application frame, providers and global error boundary

| Field | Value |
| --- | --- |
| Sub-step | STEP-003.05 |
| Requirements | REQ-A11Y-001, REQ-NFR-013 |
| Author | Deepesh Kumar Gupta |
| Date | 2026-08-07 |

> **Numbering note:** the sub-step front-matter named `BR-018`. This record is `BR-022`; the front-matter has been corrected.

## 1. Intent (step 1)
An application frame with landmarks, a working skip link, documented provider order, and error boundaries scoped so a feature failure degrades one region instead of blanking the page.

## 2. Graph state (step 2 — all six fields)
| Field | Value |
| --- | --- |
| Repository / branch | journeylab / `main` |
| HEAD at analysis | `b09a0a2` |
| Graph indexed commit | `b09a0a2` |
| **Match?** | **Yes** |
| Index timestamp | verified at analysis time |
| Extractor / schema version | **Not exposed** — recorded, not invented |
| Coverage and known gaps | Python and TypeScript indexed |
| Status | **RUNNABLE** — `impact(layout.tsx, upstream, 3)` returned `epistemic: exact`, **0 upstream** (a framework entry point; nothing imports it) |

## 3. Target nodes (step 4)
`packages/ui/src/shell/` — `error-boundary.tsx`, `skip-link.tsx`, `locale.ts`.
`apps/web/src/app/` — `layout.tsx` (**replaced**, the STEP-002.05 scaffold), `providers.tsx`, `shell.css`.
Plus every `packages/ui` module: import specifiers changed and `'use client'` added — see §9.

## 4. Dependencies (step 5 — graph-derived)
`epistemic: exact`, 0 upstream on `layout.tsx`. Nothing depends on the frame; the frame depends on everything.

**Inbound:** the whole application, from STEP-003.06 onward.
**Outbound:** `@journeylab/ui` (new workspace dependency of `apps/web`), React 19.2.

## 5. Impact by category (step 6 — all twelve, enumerated)
| # | Category | Affected | Confidence |
| --- | --- | --- | --- |
| 1 | Requirements / scope steps | `REQ-A11Y-001`, `REQ-NFR-013`. **Precondition** for STEP-002.05's unmet accessibility criterion — necessary, not sufficient: that needs a sign-in *page* | High |
| 2 | Owners / consumers | Sole owner | High |
| 3 | Frontend routes / components | **Every route from here on.** The STEP-002.05 scaffold layout is replaced | High |
| 4 | Backend services / workflows / jobs | **None** | High |
| 5 | APIs / schemas / clients / webhooks | **None** | High |
| 6 | Events / producers / consumers | **None** | High |
| 7 | Tables / migrations / caches / indexes | **None**. But the provider order below encodes a caching rule: nothing that fetches may sit above the session | High |
| 8 | Datasets / models / prompts / retrievers / evals | **None** | High |
| 9 | Tests / fixtures / contract suites | **+20 tests** (199 in `packages/ui`) | High |
| 10 | Services / deployments / infrastructure | `apps/web` now depends on `@journeylab/ui`. **Every UI module changed** — see §9 | **Medium** |
| 11 | Dashboards / alerts / runbooks | `onError` hooks exist and log to console. Real reporting is STEP-024 | **Medium — carried gap** |
| 12 | Documentation / deprecation commitments | Sub-step record; tracker; provider order documented in `providers.tsx` | High |

## 6. Data-flow inspection (step 7)
Two paths matter here.

**Error text must not reach the user.** `FeatureErrorBoundary` renders the feature name and nothing else. An `Error.message` can carry a URL, a stack frame or a provider response — a test asserts a thrown `ECONNREFUSED https://provider.internal/key=abc123` leaves neither the host nor the key in the DOM. The detail goes to `onError` for reporting.

**Provider order encodes a tenancy rule.** Documented outermost-in: global boundary → locale → session → query/data. The rule it produces: **nothing that fetches sits above the session.** A client cache keyed without a session is a cache that can serve one tenant's data to another — the client-side form of the hazard `REQ-SEC-002` names for server caches.

## 7. Classification (step 8)
`direct` · `accessibility` · `architecture` (provider order, package boundary) · `unknown`: CWV, see §9.

## 8. Risk scoring (step 9)
| Dimension | 1–5 | Rationale |
| --- | --- | --- |
| Likelihood of unintended effect | **3** | Raised: every `packages/ui` module was touched to change import specifiers and add `'use client'` |
| Severity if it occurs | 4 | The frame failing takes the whole application with it |
| Reach | **5** | Every route |
| Detectability | 2 | 199 UI tests, plus the shell verified rendering in a real Next server |
| Reversibility | 2 | Revertible, but `apps/web` now depends on `@journeylab/ui` |
| **Confidence** | 4 | Graph runnable; render verified against the live dev server, not only jsdom |
| Customer criticality | 2 | Accessibility is a product promise |

**Overall: MEDIUM.**

## 9. Unknown or low-confidence areas
| Area | Why uncertain | Residual risk |
| --- | --- | --- |
| **CWV budgets are NOT measured** | `FRONTEND_ARCHITECTURE` §7 sets LCP ≤ 2.5 s, INP ≤ 200 ms, CLS ≤ 0.1. None can be measured in jsdom; they need a real browser and Lighthouse | **Acceptance criterion UNMET.** Recorded as unmet rather than assumed — the shell is small and static, which makes it *likely* to pass, and likely is not measured |
| Every UI module changed at once | `.ts`/`.tsx` import specifiers removed; `'use client'` added to seven modules | **Mitigated but real.** All 199 tests pass and typecheck is clean, but this was a wide mechanical edit. It was necessary: `.tsx` specifiers require every consumer to enable `allowImportingTsExtensions`, which made the package unusable from `apps/web` and from Next's bundler |
| Providers are placeholders | Locale, session and query providers do not exist yet | **Open.** The ORDER is documented and the contract stated; the providers arrive at STEP-003.07 and STEP-004 |
| Skip link visibility on focus | The CSS is written; that it is *visible* on focus is a rendering property | **Open** — STEP-003.08. The tests prove it is focusable and first, which is the part that fails silently |

## 10. Required actions (step 10)
Landmarks; skip link first in the document with a focusable target; documented provider order; feature boundaries that contain rather than blank; a global boundary as last resort; `lang` and `dir` derived together.

## 11. Approval (step 11)
MEDIUM — owner approval; single owner, self-approved (`ADR-010`).

## 12. Post-change verification
| Field | Value |
| --- | --- |
| Re-indexed at commit | post-commit re-index |
| `detect_changes()` | New shell modules; `apps/web` layout replaced; import specifiers and `'use client'` across `packages/ui` |
| Regression R1–R7 | **PASS** — 335 Python + 41 web + 199 UI; R7 12/12; meta-suite 36/36 |
| Live render | Verified against the running dev server: three landmarks, skip link **first focusable in body**, `lang="en" dir="ltr"`, zero errors |
| Mutation testing | **5/5 killed** |

## 13. Disposition
**Merged with one acceptance criterion unmet** — CWV budgets are unmeasurable without a browser and are recorded as unmet, not assumed. Biome again flagged a suppression comment of mine that suppressed nothing; that is twice in two sub-steps, which suggests I add them reflexively rather than in response to a rule that fires.
