# BR-018 — Design tokens including high-contrast and reduced-motion

| Field | Value |
| --- | --- |
| Sub-step | STEP-003.01 |
| Requirements | REQ-A11Y-004, REQ-NFR-013 |
| Author | Deepesh Kumar Gupta |
| Date | 2026-08-06 |

> **Numbering note:** the sub-step front-matter named `BR-014`, which belongs to STEP-002.05. This record is `BR-018`; the front-matter has been corrected.

## 1. Intent (step 1)
Colour, typography, spacing, elevation and motion tokens with high-contrast and reduced-motion variants, so no component invents its own values — and so the accessibility claims are **computed rather than asserted**.

## 2. Graph state (step 2 — all six fields)
| Field | Value |
| --- | --- |
| Repository / branch | journeylab / `main` |
| HEAD at analysis | `9f5ff36` |
| Graph indexed commit | `9f5ff36` |
| **Match?** | **Yes** |
| Index timestamp | verified at analysis time |
| Extractor / schema version | **Not exposed** — recorded, not invented |
| Coverage and known gaps | Python and TypeScript indexed |
| Status | **RUNNABLE** |

> The sub-step file predicted `BLOCKED — no application symbols indexed yet`. That prediction is now stale: the graph has indexed application code since `STEP-002.02`.

## 3. Target nodes (step 4)
`packages/ui/` — new package. `src/tokens.ts` (source of truth), `src/tokens.css` (**generated**), `src/contrast.ts`, `tools/gen-tokens.ts`.

## 4. Dependencies (step 5)
**Inbound:** none. Greenfield package; nothing imports it yet. `apps/web` will consume `tokens.css` when the shell arrives at `.05`.
**Outbound:** none at runtime — no dependency beyond TypeScript and vitest. The tokens are plain CSS custom properties, deliberately not tied to Tailwind's config, so a component library swap does not invalidate them.

## 5. Impact by category (step 6 — all twelve, enumerated)
| # | Category | Affected | Confidence |
| --- | --- | --- | --- |
| 1 | Requirements / scope steps | `REQ-A11Y-004`, `REQ-NFR-013`; prerequisite for STEP-003.02–.08 and every later UI step | High |
| 2 | Owners / consumers | Sole owner | High |
| 3 | Frontend routes / components | **None yet.** Constrains every future component: `.02`–`.04` may not hard-code a value a token owns | High |
| 4 | Backend services / workflows / jobs | **None** | High |
| 5 | APIs / schemas / clients / webhooks | **None** | High |
| 6 | Events / producers / consumers | **None** | High |
| 7 | Tables / migrations / caches / indexes | **None** | High |
| 8 | Datasets / models / prompts / retrievers / evals | **None.** Chart palettes are `STEP-013`, and the open question about token-driven chart theming is carried below | High |
| 9 | Tests / fixtures / contract suites | **+68 tests.** Contrast ratios are computed from token values, so a failing colour breaks the build | High |
| 10 | Services / deployments / infrastructure | New workspace package `@journeylab/ui`. No new runtime dependency | High |
| 11 | Dashboards / alerts / runbooks | **None** | High |
| 12 | Documentation / deprecation commitments | Sub-step record; tracker; `FRONTEND_ARCHITECTURE` §5 satisfied for tokens | High |

## 6. Data-flow inspection (step 7)
`NOT_APPLICABLE` — no authentication, tenancy, redaction, retrieval, prompt, export or deletion path is touched. Tokens are static presentation values containing no data.

## 7. Classification (step 8)
`direct` (new package) · `accessibility` · `documentation-coupled` (the token data generates the CSS) · `unknown`: whether the eventual chart library honours token-driven theming.

## 8. Risk scoring (step 9)
| Dimension | 1–5 | Rationale |
| --- | --- | --- |
| Likelihood of unintended effect | 1 | Greenfield; nothing consumes it yet |
| Severity if it occurs | **4** | WCAG 2.2 AA is **release-blocking** (`FRONTEND_ARCHITECTURE` §5). A token that fails contrast propagates into every component built on it |
| Reach | **5** | Every UI surface in the product, permanently |
| Detectability | 1 | Ratios are computed on every test run, not reviewed by eye |
| Reversibility | 1 | Revert; nothing depends on it yet |
| **Confidence** | 4 | Graph runnable; every claim executed rather than asserted |
| Customer criticality | 2 | Accessibility is a product promise, not a preference |

**Overall: MEDIUM** — high reach, but detectability is as good as it gets and nothing consumes it yet.

## 9. Unknown or low-confidence areas
| Area | Why uncertain | Residual risk |
| --- | --- | --- |
| **Chart library token theming** | Named by the sub-step; no chart library chosen | **Open** — must be verified before committing to one in `STEP-013`. A library that cannot read CSS custom properties would force a second, divergent palette |
| Contrast is computed, appearance is not | A pair can pass 4.5:1 and still be unpleasant or ambiguous to some users | **Inherent.** The maths is a floor, not a design review. Real user testing is `STEP-003.08` / release readiness |
| No component consumes the tokens yet | `.02`–`.04` | **Open.** "No component hard-codes a value a token should own" is enforced only within this package today; it needs a lint rule once components exist |
| `forced-colors` behaviour untested in a real browser | No browser test infrastructure until `STEP-003.08` | **Open.** The media query is emitted and asserted in the CSS; that it *renders* correctly in Windows High Contrast Mode is unverified |

## 10. Required actions (step 10)
Tokens as data with generated CSS; computed contrast for every declared pairing; a distinct AAA high-contrast palette; reduced motion that suppresses rather than shortens; status tokens with both icon and label; a drift gate between data and CSS.

## 11. Approval (step 11)
MEDIUM risk — owner approval; single owner, self-approved (`ADR-010`).

## 12. Post-change verification
| Field | Value |
| --- | --- |
| Re-indexed at commit | post-commit re-index |
| `detect_changes()` | One new package. No existing symbol modified |
| Regression R1–R7 | **PASS** — 335 Python + 41 web + 68 UI; shell R7 12/12; meta-suite 36/36 |
| Mutation testing | **5/5 killed** |

## 13. Disposition
**Merged.** The drift test was initially **self-repairing**: importing the generator ran its top-level write, so the test regenerated the file it was about to compare. It could never have failed. The write is now guarded behind a direct-invocation check, and a hand-edited `tokens.css` was confirmed to break the suite.
