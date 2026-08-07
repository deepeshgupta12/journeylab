# BR-020 — Feedback primitives: dialog, notification, empty, error, skeleton

| Field | Value |
| --- | --- |
| Sub-step | STEP-003.03 |
| Requirements | REQ-A11Y-001, REQ-A11Y-004 |
| Author | Deepesh Kumar Gupta |
| Date | 2026-08-07 |

> **Numbering note:** the sub-step front-matter named `BR-016`. This record is `BR-020`; the front-matter has been corrected.

## 1. Intent (step 1)
A reusable, accessible primitive for every quality state FRONTEND_ARCHITECTURE §4 mandates, so features cannot invent inconsistent ones — plus a dialog that traps and restores focus, and a notification with honest live-region semantics.

## 2. Graph state (step 2 — all six fields)
| Field | Value |
| --- | --- |
| Repository / branch | journeylab / `main` |
| HEAD at analysis | `b28bf15` |
| Graph indexed commit | `b28bf15` |
| **Match?** | **Yes** |
| Index timestamp | verified at analysis time |
| Extractor / schema version | **Not exposed** — recorded, not invented |
| Coverage and known gaps | Python and TypeScript indexed |
| Status | **RUNNABLE** |

> The sub-step predicted `BLOCKED — no application symbols indexed yet`. Stale for the third consecutive sub-step; the graph has indexed application code since STEP-002.02.

## 3. Target nodes (step 4)
`packages/ui/src/feedback/` — `states.ts`, `dialog.tsx`, `panels.tsx`, `notification.tsx`.

## 4. Dependencies (step 5 — graph-derived)
`impact({target: "field.tsx", direction: "upstream", maxDepth: 3})` → `epistemic: exact`, risk LOW, 2 direct (`index.ts`, `inputs.tsx`), 1 at depth 2 (the form test). This sub-step adds siblings and modifies none of them.

**Inbound:** none — no screen consumes these yet.
**Outbound:** React 19.2 only.

## 5. Impact by category (step 6 — all twelve, enumerated)
| # | Category | Affected | Confidence |
| --- | --- | --- | --- |
| 1 | Requirements / scope steps | `REQ-A11Y-001`, `REQ-A11Y-004`; also `REQ-EVID-005`, `REQ-CONS-005`, `REQ-NFR-003`. Prerequisite for every screen from STEP-007 | High |
| 2 | Owners / consumers | Sole owner | High |
| 3 | Frontend routes / components | **The vocabulary every later screen must use.** A feature inventing its own empty state is now a review failure, not a matter of taste | High |
| 4 | Backend services / workflows / jobs | **None** | High |
| 5 | APIs / schemas / clients / webhooks | **None** | High |
| 6 | Events / producers / consumers | **None** | High |
| 7 | Tables / migrations / caches / indexes | **None** | High |
| 8 | Datasets / models / prompts / retrievers / evals | **None** | High |
| 9 | Tests / fixtures / contract suites | **+45 tests** (152 in `packages/ui`) | High |
| 10 | Services / deployments / infrastructure | **None** — no new dependency | High |
| 11 | Dashboards / alerts / runbooks | **None** | High |
| 12 | Documentation / deprecation commitments | Sub-step record; tracker | High |

## 6. Data-flow inspection (step 7)
`NOT_APPLICABLE` to tenancy and redaction — presentation only.

**One security-adjacent path.** `UnauthorizedState` renders no retry affordance and no detail about what exists. STEP-002.02 made denial and absence indistinguishable at the API; a UI panel saying "you do not have permission to view trip 4821" would undo that at the last hop. A test asserts the rendered text contains none of *forbidden*, *permission*, *not found*, *exists* or *tenant*.

## 7. Classification (step 8)
`direct` · `accessibility` · `product-correctness` (stale-data and infeasible carry requirement semantics, not just styling) · `unknown`: live-region politeness for streamed updates, carried below.

## 8. Risk scoring (step 9)
| Dimension | 1–5 | Rationale |
| --- | --- | --- |
| Likelihood of unintended effect | 1 | Nothing consumes them yet |
| Severity if it occurs | **4** | A dialog that does not restore focus strands keyboard users; a stale-data panel that hides its subject makes every price untrustworthy |
| Reach | **5** | Every screen in the product |
| Detectability | 1 | axe on all ten primitives, plus direct assertions for what axe cannot see |
| Reversibility | 1 | Nothing depends on them |
| **Confidence** | 4 | Graph runnable; every claim executed |
| Customer criticality | 2 | Accessibility is a product promise |

**Overall: MEDIUM.**

## 9. Unknown or low-confidence areas
| Area | Why uncertain | Residual risk |
| --- | --- | --- |
| **Live-region politeness for streamed scenario updates** | Named by the sub-step: "validate with a real screen reader, not only axe" | **Open.** The politeness map is asserted in code, but whether a stream of arriving scenarios is announced usefully or becomes noise cannot be judged from jsdom. Binds at STEP-011/STEP-003.08 |
| jsdom is not a browser | Focus behaviour especially | **Open** — STEP-003.08. Already bit once here: `offsetParent` is null in jsdom, which silently disabled the focus trap |
| Icons are names, not artwork | `data-icon` strings with no sprite yet | **Open** — an icon set arrives with `.04`/`.05`. The non-colour affordance is currently the visible LABEL, which is the part REQ-A11Y-004 actually requires |
| Feature error boundaries | FRONTEND_ARCHITECTURE §4 requires a map or chart failure not to remove itinerary text | **Not in this sub-step.** No map or chart exists; binds at STEP-013 |

## 10. Required actions (step 10)
All nine states as data so completeness is testable; dialog with trap, restoration and escape; notification with required politeness; stale-data that names its subject; infeasible that refuses an empty conflict set; progress that cannot be built without a label and a cancel path.

## 11. Approval (step 11)
MEDIUM — owner approval; single owner, self-approved (`ADR-010`).

## 12. Post-change verification
| Field | Value |
| --- | --- |
| Re-indexed at commit | post-commit re-index |
| `detect_changes()` | New `packages/ui/src/feedback/`; no existing symbol modified |
| Regression R1–R7 | **PASS** — 335 Python + 41 web + 152 UI; R7 12/12; meta-suite 36/36 |
| Mutation testing | **6/6 killed** |

## 13. Disposition
**Merged.** The focus trap was silently inert on first write: the visibility filter used `element.offsetParent !== null`, which jsdom always reports as null because it computes no layout — and which is also wrong in real browsers for `position: fixed` elements, exactly what a dialog is. Three tests caught it immediately.
