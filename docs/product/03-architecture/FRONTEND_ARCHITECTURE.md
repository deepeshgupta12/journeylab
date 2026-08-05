# JourneyLab — Frontend Architecture

| Field | Value |
| --- | --- |
| Owner | Frontend Lead (unassigned — `BLK-001`) |
| Status | `DISCOVERY` — target architecture; **all paths `PROPOSED`, none verified** |
| Upstream source | Blueprint §8 (Frontend requirements), §15 (accessibility, i18n) |
| Last reviewed | 2026-08-05 |

Navigation: [Technical architecture](TECHNICAL_ARCHITECTURE.md) · [Backend](BACKEND_ARCHITECTURE.md) · [API contracts](../04-contracts/API_CONTRACTS.md) · [Personas](../01-product/PERSONAS_AND_JOBS.md) · [00-START-HERE](../00-START-HERE.md)

---

## 1. Goals and technology decisions

The frontend is a **product system**, not a set of screens. Its hardest jobs are making uncertainty legible, keeping a long-running computation comprehensible, and remaining fully usable without a map or a network.

| Decision | Choice | Rationale |
| --- | --- | --- |
| Framework | Next.js 16.2 App Router | Server-render public coverage/SEO pages; stream authenticated planning results |
| Rendering | Server components for read-heavy pages; client islands for interaction | Keeps comparison data server-fetched while map/timeline stay interactive |
| State | TanStack Query (server state) + URL-addressable comparison state + small FSM for multi-step planning | Comparison state must be shareable and restorable via URL |
| Styling | Tailwind 4.3 + accessible headless components | Headless components stay independently testable for WCAG |
| Map | MapLibre GL | Open tiles; **never required for a core action** (`REQ-A11Y-003`) |
| Charts | ECharts or D3 | Uncertainty ranges and budget waterfalls; always with a table equivalent |
| Delivery | Responsive PWA — installable, service worker, background sync | Offline pack (Phase 3) and low-connectivity resilience |

---

## 2. Route inventory and surface matrix

All routes are `PROPOSED`.

| Route/Surface | Persona | Scope Step | Main Components | Server APIs | State | Accessibility | Analytics | Failure States | Tests | Owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `/` , `/coverage` | PER-001 (anon) | STEP-007 | `CoverageMap`, `RegionList`, `PrivacySummary`, `SampleComparison` | API-017 | Server-rendered, cached | Static content, SR landmarks, no map dependency | `coverage_viewed`, `waitlist_joined` | Provider-down, region-unsupported, partial coverage | TST-TRIP-001/002 | FE Lead |
| `/auth/*` | PER-001, PER-002 | STEP-008 | `SignIn`, `PasskeyPrompt`, `GuestStart`, `UpgradeAccount` | API-001 | FSM | Focus management, error announcement | `auth_started/completed` | Provider-down, expired link, interrupted onboarding | TST-SEC-003, TST-TRIP-005 | FE Lead |
| `/settings/privacy`, `/settings/data` | PER-001 | STEP-008, STEP-025 | `ConsentMatrix`, `DataExport`, `DeleteAccount`, `RetentionControls` | API-015 | Server + optimistic | Explicit consent labels, no dark patterns | `consent_changed`, `export_requested` | Deletion pending/failed, export queued | TST-PRIV-002/005/006 | FE Lead |
| `/settings/profile` | PER-001 | STEP-008 | `AccessibilityNeeds`, `SoftPreferences`, `ProfileVersions` | API-003 | Form + autosave | Sensitive fields clearly separated and optional | `profile_updated` | Version conflict, save failure | TST-TRIP-004, TST-PRIV-003 | FE Lead |
| `/trips` | PER-001 | STEP-008 | `TripList`, `TripCard`, `ArchiveControls` | API-002 | TanStack Query | List semantics, keyboard navigation | `trip_list_viewed` | Empty, partial, unauthorized | TST-TRIP-003 | FE Lead |
| `/trips/new` | PER-001 | STEP-007, STEP-008 | `CoverageValidator`, `TripCreateForm` | API-001, API-017 | FSM | Inline validation, clear refusal messaging | `trip_created` | Out-of-coverage refusal (no partial sim) | TST-TRIP-002 | FE Lead |
| `/trips/[id]/brief` | PER-001, PER-002 | STEP-009 | `NaturalLanguageEntry`, `ConstraintEditor`, `ClassificationBadges`, `ClarificationInline` | API-003 | Form + autosave + versions | Hard/soft/inferred/unresolved conveyed by text not colour | `brief_confirmed`, `clarification_answered` | Ambiguity blocking, impossible constraints, autosave conflict | TST-CONS-001/002 | FE Lead |
| `/trips/[id]/generate` | PER-001 | STEP-010, STEP-012 | `GenerationProgress`, `WarningsPanel`, `CancelControl` | API-004, API-005, API-018 (SSE) | SSE stream + FSM | Progress announced; focus restored on completion (`REQ-A11Y-006`) | `generation_started/cancelled/completed` | Solver timeout, infeasible + conflict set, provider-down, partial evidence | TST-CONS-005, TST-A11Y-006 | FE Lead |
| `/trips/[id]/compare` | PER-001, PER-002 | STEP-013 | `ScenarioMap`, `DayTimeline`, `BudgetLedger`, `Scorecard`, `DiffControls`, `EvidenceDrawer`, `ScenarioTable` | API-006, API-007 | URL-addressable selection | **Full parity without map**; table equivalent + CSV (`REQ-A11Y-002`) | `comparison_viewed`, `scenario_selected` | Map failure (list fallback), chart failure, stale evidence, progressive render | TST-CONS-009, TST-A11Y-002/003 | FE Lead |
| `/trips/[id]/whatif` | PER-001 | STEP-014 `DEFERRED` | `WhatIfPanel`, `ImpactPreview`, `UndoRedo`, `DeltaSummary` | API-009 | Optimistic + version history | Non-pointer alternative to drag (`REQ-A11Y-005`) | `whatif_previewed/applied/reverted` | Preview timeout, merge conflict, solver timeout | TST-CONS-010, TST-A11Y-005 | FE Lead |
| `/trips/[id]/collab`, `/share` | PER-001, PER-002 | STEP-015 `DEFERRED` | `InviteManager`, `ProposalList`, `VotePanel`, `ConflictAttribution` | API-010 | Server + realtime | Conflicts explained without exposing sensitive detail | `invite_sent`, `vote_cast` | Expired/revoked link (fail closed), conflicting edits | TST-COLL-001…004 | FE Lead |
| `/trips/[id]/booking` | PER-001 | STEP-016 | `HandoffList`, `EstimateBadge`, `ConfirmedBadge`, `CopyableDetails` | API-011 | Server | Estimated vs confirmed distinct by text + icon, not colour | `handoff_clicked`, `booking_confirmed` | Affiliate down (copyable fallback), availability changed | TST-BOOK-001…004, TST-EVID-003 | FE Lead |
| `/trips/[id]/live` | PER-001 | STEP-017…019 `DEFERRED` | `TodayView`, `NextAction`, `OfflineStatus`, `NotificationCenter`, `RepairOptions` | API-012, API-013 | Service worker + sync queue | One-handed, low-motion, sunlight-readable; no map required | `live_activated`, `repair_accepted` | Offline, sync conflict, no safe repair | TST-LIVE-001…006 | FE Lead |
| `/admin/destinations`, `/admin/providers`, `/admin/support`, `/admin/flags` | PER-004, PER-005 | STEP-021 | `CoverageDashboard`, `OverrideEditor`, `FourEyesApproval`, `ProviderHealth`, `DiagnosticTimeline`, `FlagControls` | API-016, API-017 | Server | Same AA bar as consumer surfaces | `override_proposed/approved` | Approval pending, override conflict, provider disabled | TST-ADMIN-001…005 | FE Lead |
| `/knowledge` | Internal | STEP-026 | `GraphExplorer`, `ImpactView`, `ProvenancePanel` | API-018 | Server | Graph has a list/table equivalent | `graph_query_run` | Graph stale/unavailable, permission-filtered result | TST-KG-005/006 | Platform |
| `/analytics` | PER-005 | STEP-022 `DEFERRED` | `KpiBoard`, `FunnelView`, `ExperimentResults` | — | Server | Charts have table equivalents | — | Insufficient exposure data (blocks result display) | TST-OBS-006 | Data |

---

## 3. State ownership

| State kind | Owner | Example | Rule |
| --- | --- | --- | --- |
| Server state | TanStack Query | Scenarios, evidence, trips | Never duplicated into client stores |
| URL state | Route + search params | Selected scenarios, comparison dimension, day index | Comparison must be shareable and restorable by URL |
| Workflow state | Small finite-state machine | Brief → generate → compare → select | Illegal transitions must be unrepresentable |
| Ephemeral UI state | Component-local | Drawer open, hover | Never persisted |
| Offline state | Service worker + IDB | Offline pack, sync queue | Encrypted; idempotent commands (`REQ-LIVE-002`) |

**Forms:** schema-driven validation shared with the backend via generated types from `contracts/jsonschema/`. Unsaved changes must warn before navigation; autosave shows explicit status and supports version history, undo and conflict resolution.

---

## 4. Quality states — mandatory per major screen

Every major screen must implement **all** of: `skeleton`, `empty`, `partial-data`, `stale-data`, `provider-down`, `infeasible`, `solver-timeout`, `unauthorized`, `offline`.

Rules that follow from the product, not from convention:
- **Never a blank map or a silent spinner** for long work — always progress plus cancel/retry (`REQ-NFR-003`).
- **Feature error boundaries**: a map or chart failure must not remove itinerary text (blueprint §8.114).
- **Stale data is labelled at the point of use**, not only in a global banner (`REQ-EVID-005`).
- **Infeasible is a first-class state** showing the minimal conflict set and suggested relaxations — not an error toast (`REQ-CONS-005`).

---

## 5. Accessibility (WCAG 2.2 AA — release-blocking)

| Requirement | Implementation |
| --- | --- |
| Keyboard-complete + screen-reader complete | Every core task; verified in `TST-A11Y-001` |
| Map-free operation | All MVP tasks complete with map disabled; the list/table view is a first-class surface, not a degraded one |
| Table equivalent + CSV per visualization | Scorecards, budget waterfalls and uncertainty ranges |
| Focus restoration on streamed updates | Focus must not jump when scenarios arrive; changes announced politely |
| Non-colour status | Text or icon accompanies every status colour |
| Reduced motion, high contrast, zoom to 200% | Honored via tokens and media queries |
| Touch targets and drag alternatives | Minimum sizing; keyboard/menu alternative to every drag interaction |

**Localisation:** UTF-8 end to end, ICU messages, locale-aware currency/units/calendar, correct time zones and DST transitions, RTL-ready structure (RTL implementation deferred to Phase 2).

---

## 6. Security in the frontend

| Concern | Control |
| --- | --- |
| XSS | No `dangerouslySetInnerHTML` on provider or model content; sanitise all rendered evidence text |
| CSP | Strict policy; no inline scripts; explicit allowlist for map tiles |
| CSRF | SameSite cookies plus per-request tokens on state-changing calls |
| Secrets | No provider or model keys ever in the client bundle |
| Sensitive data | Accessibility/age/location never in analytics payloads or URL params (`REQ-PRIV-004`) |
| Authorization | Client role checks are presentation only; the server is the control (`REQ-SEC-004`) |
| Offline storage | Encrypted; sensitive documents require explicit opt-in and device protection |

---

## 7. Performance budgets

| Metric | Budget | Note |
| --- | --- | --- |
| LCP (coverage/landing) | ≤ 2.5 s on mid-tier mobile, 4G | Server-rendered |
| INP | ≤ 200 ms | Comparison interactions must stay responsive during streaming |
| CLS | ≤ 0.1 | Reserve space for streamed scenario cards |
| Initial JS (public routes) | Budget set at implementation; map and chart libraries **must be lazy-loaded** | They are the two largest dependencies |
| Comparison route TTI | Measured with 5 scenarios × 7 days | Progressive rendering required |

---

## 8. Testing

| Layer | Coverage |
| --- | --- |
| Component | Design-system primitives, all quality states, form validation |
| Integration | Route + API contract via generated clients and mocked SSE |
| Visual | Comparison, timeline, evidence drawer across breakpoints |
| Accessibility | Automated axe checks in CI + manual screen-reader journeys |
| End-to-end | Golden journeys on desktop, mobile and assistive-technology paths, including refresh, retry, partial failure and interrupted-session recovery |

---

## 9. Proposed file map

**`PROPOSED` — no files exist.**

```text
apps/web/src/
├── app/
│   ├── layout.tsx                     # shell, providers, global error boundary
│   ├── (public)/coverage/page.tsx
│   ├── trips/new/page.tsx
│   ├── trips/[id]/{brief,generate,compare,whatif,collab,booking,live}/page.tsx
│   ├── admin/{destinations,providers,support,flags}/
│   ├── knowledge/                     # graph explorer + impact UI
│   └── analytics/
├── features/
│   ├── brief/ generation/ compare/ whatif/ collaboration/ booking/ evidence/ export/
│   ├── map/ScenarioMap.tsx
│   └── timeline/DayTimeline.tsx
├── components/navigation/
├── lib/{i18n.ts,query.ts,sse.ts,offline.ts}
├── auth/session.ts
└── test/a11y.spec.ts

packages/ui/src/{tokens.css,components/}
packages/analytics/src/events.ts
packages/contracts/src/generated/
```
