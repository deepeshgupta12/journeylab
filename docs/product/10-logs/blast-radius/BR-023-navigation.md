# BR-023 — Role-aware desktop and mobile navigation

| Field | Value |
| --- | --- |
| Sub-step | STEP-003.06 |
| Requirements | REQ-A11Y-001, REQ-SEC-004 |
| Author | Deepesh Kumar Gupta |
| Date | 2026-08-10 |

> **Numbering note:** the sub-step front-matter named `BR-019`. This record is `BR-023`; the front-matter has been corrected.

## 1. Intent (step 1)
Navigation that renders by role on both breakpoints, keyboard-complete — and that is unmistakably presentation, not protection.

## 2. Graph state (step 2 — all six fields)
| Field | Value |
| --- | --- |
| Repository / branch | journeylab / `main` |
| HEAD at analysis | `94bf916` |
| Graph indexed commit | `94bf916` |
| **Match?** | **Yes** |
| Index timestamp | verified at analysis time |
| Extractor / schema version | **Not exposed** — recorded, not invented |
| Coverage and known gaps | Python and TypeScript indexed |
| Status | **RUNNABLE** |

## 3. Target nodes (step 4)
`packages/ui/src/nav/` — `navigation.tsx`, `authz-matrix.ts` (**generated**).
`tools/gen_authz_matrix_ts.py` — second emitter over the existing parser.
`apps/web/src/app/` — `navigation.tsx`, `layout.tsx`, `shell.css`.

## 4. Dependencies (step 5)
**`ADR-012`'s review trigger fired.** That ADR said: *"if the frontend later wants to grey out forbidden actions, it needs the same matrix in TypeScript. That must be generated from the same markdown, never hand-maintained… The generator already isolates parsing in `tools/authz_matrix_source.py` so a second emitter is additive."*

It was additive exactly as predicted: `gen_authz_matrix_ts.py` reuses `parse_matrix()` untouched. The Python emitter is unmodified.

**Inbound:** the app shell header.
**Outbound:** `AUTHORIZATION_MATRIX.md` (via the shared parser), React 19.2, `next/navigation`.

## 5. Impact by category (step 6 — all twelve, enumerated)
| # | Category | Affected | Confidence |
| --- | --- | --- | --- |
| 1 | Requirements / scope steps | `REQ-A11Y-001`, `REQ-SEC-004`. Consumes STEP-002.03's matrix | High |
| 2 | Owners / consumers | Sole owner | High |
| 3 | Frontend routes / components | Fills the `<header>` landmark the frame reserved at `.05` | High |
| 4 | Backend services / workflows / jobs | **None** | High |
| 5 | APIs / schemas / clients / webhooks | **None** | High |
| 6 | Events / producers / consumers | **None** | High |
| 7 | Tables / migrations / caches / indexes | **None** | High |
| 8 | Datasets / models / prompts / retrievers / evals | **None** | High |
| 9 | Tests / fixtures / contract suites | **+21 tests** (220 in `packages/ui`) | High |
| 10 | Services / deployments / infrastructure | **None** — no new dependency | High |
| 11 | Dashboards / alerts / runbooks | **None** | High |
| 12 | Documentation / deprecation commitments | Sub-step record; tracker; `ADR-012` review trigger discharged | High |

## 6. Data-flow inspection (step 7 — REQ-SEC-004)
The security question here is not "does the filter work" but "could anyone mistake it for a control".

| Concern | Evidence |
| --- | --- |
| Does hiding match the server? | Every operation × every role asserted against the generated matrix, which comes from the same markdown as `authz/policy.py` |
| Can the two copies drift? | **No.** One parser, two emitters (`ADR-012`). A drift test re-reads the markdown |
| Is hiding mistaken for protection? | The function is `visibleItems`, not `permittedItems`. A test asserts it contains no `fetch`, `redirect` or `throw`, and that the module says so in plain words |
| Does the href survive? | **Yes, deliberately.** A test asserts the route is still there. Hiding makes the vulnerability harder to notice, not smaller |
| Unknown pairing | Hidden, matching the server's deny-by-default |

## 7. Classification (step 8)
`direct` · `accessibility` · `security/privacy` (presentation of an authorization boundary) · `unknown`: none.

## 8. Risk scoring (step 9)
| Dimension | 1–5 | Rationale |
| --- | --- | --- |
| Likelihood of unintended effect | 2 | Additive; the Python emitter is untouched |
| Severity if it occurs | **4** | Not because hiding fails — because someone could come to rely on it. A hidden item with an open endpoint is a vulnerability, and the hiding is what stops anyone noticing |
| Reach | 4 | Every authenticated page |
| Detectability | 1 | Matrix drift and the presentation-only property are both asserted |
| Reversibility | 1 | Revertible |
| **Confidence** | 4 | Graph runnable; nav verified rendering against the live server |
| Customer criticality | 2 | Accessibility promise |

**Overall: MEDIUM.**

## 9. Unknown or low-confidence areas
| Area | Why uncertain | Residual risk |
| --- | --- | --- |
| **"Directly requesting a hidden route is denied server-side" is UNTESTABLE here** | No routes exist. `/admin/*` and `/trips` are not pages yet, and no HTTP endpoint enforces anything — STEP-004 | **Acceptance criterion UNMET.** The policy itself is proven at STEP-002.03 across 176 cells, but that is a unit test of the decision function, not a request to a route. Recorded unmet rather than counted as covered by the policy tests |
| Touch-target size is declared, not measured | 44×44 is in the CSS; jsdom computes no layout | **Open** — STEP-003.08 |
| Role is hard-coded to `guest` in the shell | No session provider until STEP-004 | **Conservative by construction.** Guest sees the least, so a placeholder cannot reveal an item |
| Responsive breakpoint behaviour | The media query is written; which navigation is visible at a width is a rendering property | **Open** — STEP-003.08 |

## 10. Required actions (step 10)
Second emitter over the existing parser; named landmark with `aria-current`; drawer with trap and restoration; `aria-expanded`/`aria-controls` on the toggle; 44×44 targets; and the presentation-only property asserted rather than asserted-in-a-comment.

## 11. Approval (step 11)
MEDIUM — owner approval; single owner, self-approved (`ADR-010`).

## 12. Post-change verification
| Field | Value |
| --- | --- |
| Re-indexed at commit | post-commit re-index |
| `detect_changes()` | New `packages/ui/src/nav/`, second emitter, shell header wired |
| Regression R1–R7 | **PASS** — 335 Python + 41 web + 220 UI; R7 12/12; meta-suite 36/36 |
| Live render | `<nav aria-label="Main navigation">` with Trips and New trip; **guest sees no `/admin/` links**; zero errors |
| Mutation testing | **5/5 killed** |

## 13. Disposition
**Merged with one acceptance criterion unmet** — the server-denial test needs routes that do not exist yet. Biome's `useValidAriaRole` fired on a React prop named `role`; rather than suppress a false positive, the prop was renamed to `actorRole`, which removes the collision for human readers too. The blanket rename then caught a loop variable of the same name — a reminder that a regex rename is not a refactor.
