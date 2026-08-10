---
step_id: STEP-003
title: Design system and application shell
status: DISCOVERY
release: Phase 1
owners: ["Deepesh Kumar Gupta"]
dependencies: [STEP-002]
requirement_ids: [REQ-A11Y-001, REQ-A11Y-004, REQ-NFR-007, REQ-NFR-013]
api_ids: []
event_ids: []
data_ids: []
ai_ids: []
knowledge_graph_check: REQUIRED
last_updated: 2026-08-05
---

# STEP-003 — Design system and application shell

> Status is authoritative in [MASTER_TRACKER](../02-delivery/MASTER_TRACKER.md).

## 1. Outcome
An accessible, responsive application shell and reusable primitives exist, meeting WCAG 2.2 AA, with loading, empty, partial, error and retry behavior defined for every state — before workflow pages diverge.

## 2. Why this step exists
Accessibility and quality states retrofitted across a dozen feature screens is a rewrite. Building them once in the design system makes `REQ-A11Y-001` achievable; building them per-feature guarantees inconsistency and gaps.

## 3. Scope
Design tokens (colour, typography, spacing, elevation, motion, high contrast); accessible headless components (buttons, forms, dialogs, tables, cards, notifications, empty/error states); application frame with providers, metadata and global error boundaries; role-aware navigation; i18n/locale/time-zone/currency loading; automated keyboard and axe checks.

## 4. Explicit exclusions
Map and chart components belong to [STEP-013](STEP-013-visual-comparison.md) — they carry domain semantics. Route-specific pages belong to their own steps. RTL *implementation* is Phase 2; only RTL-ready structure is here.

## 5. Actors, permissions and data access
| Actor | Permission | Data accessed | Sensitivity |
| --- | --- | --- | --- |
| All personas | Role-aware navigation rendering | None directly | — |

The shell renders navigation by role but enforces nothing — the server is the control (`REQ-SEC-004`).

## 6. Preconditions and dependencies
[STEP-002](STEP-002-identity-tenancy-and-authorization.md) exit — navigation needs session and policy.

## 7. Inputs and source systems
WCAG 2.2 AA; Tailwind 4.3 baseline; accessible headless component library; locale data (ICU).

## 8. Detailed normal workflow
1. Designer and engineer define tokens including high-contrast and reduced-motion variants.
2. Engineer builds primitives, each with all quality states as first-class variants.
3. Engineer builds the app frame with providers, metadata and a global error boundary.
4. Engineer builds role-aware desktop and mobile navigation.
5. Engineer wires locale, time zone, currency and message loading.
6. Engineer adds automated keyboard and axe checks over the shell and component stories.

## 9. Alternate, partial and failure workflows
| Condition | Behavior | User-visible result | Requirement |
| --- | --- | --- | --- |
| A feature component throws | Feature error boundary contains it | Rest of the page still usable | blueprint §8.114 |
| Locale data missing | Fall back to a documented default; never crash | Content in fallback locale | REQ-NFR-007 |
| Reduced motion requested | Animations suppressed | Static transitions | REQ-A11Y |
| Slow network | Skeletons with progress, never a silent spinner | Honest progress | REQ-NFR-003 |

## 10. State machine and lifecycle transitions
Each component: `idle → loading → (empty | partial | success | stale | error | unauthorized | offline)`. **Every state is reachable in the component stories**, which is what makes them testable.

## 11. Frontend implementation
`packages/ui/src/tokens.css`, `packages/ui/src/components/`, `apps/web/src/app/layout.tsx`, `apps/web/src/components/navigation/`, `apps/web/src/lib/i18n.ts`, `apps/web/src/test/a11y.spec.ts` (all `PROPOSED`).

## 12. Backend implementation
`NOT_APPLICABLE`. Reason: this step delivers no server behavior. Navigation role data comes from the existing session helpers built in `STEP-002`.

## 13. API, event and integration contracts
None. Map tile integration (`INT-008`) is referenced by CSP configuration only, not consumed here.

## 14. Data model, migration and retention effects
None.

## 15. AI, LLM, RAG, ML and data-science implementation
`NOT_APPLICABLE`. Reason: design-system construction is deterministic. No AI capability would improve correctness here, and introducing one would violate `CON-004`'s spirit by making presentation non-reproducible.

## 16. Security, privacy, accessibility and responsible-AI controls
Strict CSP with an explicit tile-origin allowlist; no `dangerouslySetInnerHTML` on provider or model content; no secrets in the client bundle; **WCAG 2.2 AA is the acceptance bar, not an aspiration**; non-colour status indicators; focus management primitives; minimum target sizes.

## 17. Observability, analytics and KPIs
Core Web Vitals instrumentation; accessibility failure counter (`ALRT-A11Y-001`); component error-boundary trigger rate. Typed analytics events carry a privacy tier from the outset.

## 18. Files and modules expected to change
All `PROPOSED` — see §11.

## 19. Knowledge-graph pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | `BLOCKED` for application code — static fallback |
| Queries to run | KG-Q-006 on shared components once they exist |
| Expected impact | Every UI step depends on these primitives — high fan-out |

## 20. Blast-radius assessment
High fan-out (all UI steps), high detectability (visual and automated a11y tests), high reversibility. Component API changes after adoption are the real risk — hence primitives are versioned within the package.

## 21. Implementation task checklist — sub-steps
| Sub-step | Outcome |
| --- | --- |
| STEP-003.01 | Tokens incl. high-contrast and reduced-motion |
| STEP-003.02 | Form and input primitives with validation states |
| STEP-003.03 | Feedback primitives (dialog, notification, empty, error, skeleton) |
| STEP-003.04 | Table and list primitives (the accessible alternative to every visualization) |
| STEP-003.05 | Application frame, providers, global error boundary |
| STEP-003.06 | Role-aware navigation (desktop + mobile) |
| STEP-003.07 | i18n, time zone, currency, DST handling — ✅ **VERIFIED** 2026-08-10 (BR-024, IMPL-021) |
| STEP-003.08 | Automated keyboard + axe checks in CI |

## 22. Test and evaluation plan
`TST-A11Y-001`, `TST-A11Y-004`, `TST-NFR-007`, `TST-NFR-013`. Component tests must assert **every** quality state, not only success. Manual screen-reader journeys supplement automation, which cannot detect misleading-but-valid semantics.

## 23. Deployment, feature flag and migration plan
No user-facing deployment. Components ship as an internal package consumed by later steps.

## 24. Rollback, compensation and recovery plan
Package version pinning; a regressed component reverts by version. No data impact.

## 25. Acceptance criteria
- [ ] Core components pass automated WCAG 2.2 AA checks (`REQ-A11Y-001`)
- [ ] Every component exposes loading, empty, partial, error and retry states
- [ ] No status is conveyed by colour alone (`REQ-A11Y-004`)
- [ ] Keyboard navigation and focus management work throughout the shell
- [ ] Locale, currency, time zone and DST render correctly for the test matrix (`REQ-NFR-007`)
- [ ] Reduced motion, high contrast and 200% zoom verified
- [ ] Core Web Vitals budgets met on the shell (`REQ-NFR-013`)

## 26. Evidence required for completion
Axe report; manual screen-reader journey recording; component story coverage of all states; Lighthouse/CWV measurement.

## 27. Open questions, risks and decisions
Headless component library not selected. RTL implementation deferred to Phase 2 — **structure must not preclude it**, which is cheaper to guarantee now than to retrofit.

## 28. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Sub-steps completed | 0 of 8 |
| Regression result | — |
| Verified by | — |
