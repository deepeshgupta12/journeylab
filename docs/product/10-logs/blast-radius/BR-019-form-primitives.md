# BR-019 — Form and input primitives with validation states

| Field | Value |
| --- | --- |
| Sub-step | STEP-003.02 |
| Requirements | REQ-A11Y-001 |
| Bug found | `BUG-016` |
| Author | Deepesh Kumar Gupta |
| Date | 2026-08-06 |

> **Numbering note:** the sub-step front-matter named `BR-015`, which belongs to STEP-002.05's neighbourhood. This record is `BR-019`; the front-matter has been corrected.

## 1. Intent (step 1)
Accessible inputs, selects, checkboxes, radio groups and fieldsets with error, disabled, read-only and required states — each announced correctly, none relying on a convention a component author must remember.

## 2. Graph state (step 2 — all six fields)
| Field | Value |
| --- | --- |
| Repository / branch | journeylab / `main` |
| HEAD at analysis | `0e3ea40` |
| Graph indexed commit | `0e3ea40` |
| **Match?** | **Yes** |
| Index timestamp | verified at analysis time |
| Extractor / schema version | **Not exposed** — recorded, not invented |
| Coverage and known gaps | Python and TypeScript indexed |
| Status | **RUNNABLE** |

> The sub-step predicted `BLOCKED — no application symbols indexed yet`. Stale, as at `.01`: the graph has indexed application code since STEP-002.02.

## 3. Target nodes (step 4)
`packages/ui/src/form/` — `field.tsx`, `inputs.tsx`, `locale-number.ts`, `zoned-date.ts`. Plus `tests/guards/workflow-refs.sh` (BUG-016) and `pyproject.toml` (pyyaml pinned).

## 4. Dependencies (step 5 — graph-derived)
`impact({target: "tokens.ts", direction: "upstream", maxDepth: 3})` → `epistemic: exact`, risk LOW, 3 direct — generator, token test, package index. This sub-step **consumes** tokens without modifying them.

**Inbound:** none — no product form uses these yet; the trip brief editor is STEP-009.
**Outbound:** React 19.2, and `Intl` for locale and time-zone behaviour. Test-only: jsdom, Testing Library, axe-core.

## 5. Impact by category (step 6 — all twelve, enumerated)
| # | Category | Affected | Confidence |
| --- | --- | --- | --- |
| 1 | Requirements / scope steps | `REQ-A11Y-001`; prerequisite for STEP-003.03–.08, STEP-008, STEP-009 | High |
| 2 | Owners / consumers | Sole owner | High |
| 3 | Frontend routes / components | **First components in the repository.** Every later form inherits their association and announcement behaviour | High |
| 4 | Backend services / workflows / jobs | **None** | High |
| 5 | APIs / schemas / clients / webhooks | **None** | High |
| 6 | Events / producers / consumers | **None** | High |
| 7 | Tables / migrations / caches / indexes | **None** | High |
| 8 | Datasets / models / prompts / retrievers / evals | **None** | High |
| 9 | Tests / fixtures / contract suites | **+39 tests** (107 in `packages/ui`). jsdom, Testing Library and axe-core added — the first browser-like test environment | High |
| 10 | Services / deployments / infrastructure | React added to `@journeylab/ui`. `pyyaml` pinned as a dev dependency (BUG-016) | High |
| 11 | Dashboards / alerts / runbooks | **None** | High |
| 12 | Documentation / deprecation commitments | Sub-step record; tracker; `BUG-016` | High |

## 6. Data-flow inspection (step 7)
`NOT_APPLICABLE` to tenancy and redaction — these are presentation primitives holding no persisted data.

**One data-correctness path does matter.** `DateInput` returns a `CalendarDate`, never a `Date`. A `Date` is an instant; the value of a date input is not one. Attaching the browser's zone silently is the bug the sub-step warns "becomes an infeasible itinerary in STEP-012", so `startOfDayUtc` requires an explicit IANA zone with no default.

## 7. Classification (step 8)
`direct` (first components) · `accessibility` · `data-correctness` (locale and time zone) · `unknown`: ICU message loading, carried below.

## 8. Risk scoring (step 9)
| Dimension | 1–5 | Rationale |
| --- | --- | --- |
| Likelihood of unintended effect | 2 | No product form consumes them yet |
| Severity if it occurs | **4** | WCAG 2.2 AA is release-blocking; a mis-associated error is invisible to the users who most need it. A locale or time-zone bug is silent and corrupts trip data |
| Reach | **5** | Every form in the product |
| Detectability | 1 | axe on every primitive, and axe itself proven able to fail |
| Reversibility | 1 | Nothing depends on them yet |
| **Confidence** | 4 | Graph runnable; every claim executed |
| Customer criticality | 2 | Accessibility is a product promise |

**Overall: MEDIUM.**

## 9. Unknown or low-confidence areas
| Area | Why uncertain | Residual risk |
| --- | --- | --- |
| **ICU message loading vs server components** | Named by the sub-step | **Open** — must resolve before STEP-003.07. No message catalogue exists yet, so nothing is committed |
| axe is a floor, not a ceiling | Automated checks catch roughly a third of real WCAG issues | **Inherent.** Focus theft, live-region politeness and time-zone correctness are asserted directly because axe cannot see them. Real assistive-technology testing is STEP-003.08 |
| jsdom is not a browser | Focus, live regions and `type="date"` behave differently in real engines | **Open** — STEP-003.08 adds browser-based verification |
| No lint rule stops a component hard-coding a token value | Carried from `.01` | **Open** — these primitives set no colours themselves, so nothing is violated yet |

## 10. Required actions (step 10)
Centralised association so it cannot be forgotten; polite live regions that never steal focus; locale-derived numeric parsing that refuses ambiguity; dates that carry no implicit zone; disabled and read-only kept distinct; axe on every primitive, with axe itself proven able to fail.

## 11. Approval (step 11)
MEDIUM — owner approval; single owner, self-approved (`ADR-010`).

## 12. Post-change verification
| Field | Value |
| --- | --- |
| Re-indexed at commit | post-commit re-index |
| `detect_changes()` | New `packages/ui/src/form/`; guard and dev-dependency changes for BUG-016 |
| Regression R1–R7 | **PASS** — 335 Python + 41 web + 107 UI; R7 12/12; meta-suite 36/36 |
| Mutation testing | **5/5 killed**, after one false survival |

## 13. Disposition
**Merged.** Biome's accessibility rules caught two genuine standards errors I had written — `aria-required` on `input[type=date]`, which has no ARIA role to support it, and then on a `fieldset`, whose `group` role does not support it either. The fix in both cases was to stop reaching for ARIA and use the native attribute, which already maps to the same accessibility property.
