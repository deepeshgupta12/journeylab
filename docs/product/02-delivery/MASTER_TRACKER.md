# JourneyLab — Master Delivery Tracker

> **This is the single canonical source of delivery status.** Other documents explain work; none of them may maintain a competing status. If a step file's front-matter `status` disagrees with this table, this table is authoritative and the step file is a defect.

| Field | Value |
| --- | --- |
| Owner | TPM (Deepesh Kumar Gupta) |
| Target release | Phase 1 MVP — one region, 3–7 day trips, deep-link handoff |
| Overall status | `DISCOVERY` |
| Last reviewed | 2026-08-05 |

Navigation: [Scope](../01-product/PRODUCT_SCOPE.md) · [Roadmap](ROADMAP.md) · [Dependencies](DEPENDENCY_REGISTER.md) · [Risks](RISK_REGISTER.md) · [Step files](../08-steps/) · [00-START-HERE](../00-START-HERE.md)

---

## 1. Release summary

| Metric | Value |
| --- | --- |
| Scope steps defined | **28** |
| Step files created | **28** |
| Steps in Phase 1 (target release) | **19** |
| Steps deferred to Phase 2/3/4 | **9** |
| Steps `VERIFIED` | **1** (STEP-001) |
| Requirements defined | **130** |
| Requirements verified against implementation | **0** |
| Application code files | **0** product code; foundation + 11 guards + 3 CI workflows |
| Open blockers | **1** (`BLK-002`) — `BLK-001` closed via `ADR-010` |
| Open decisions | **7** — `ASM-004` TS revalidation closed via `ADR-009` |
| Open assumptions | **18** |

**Status legend (the only permitted values):**

`NOT_STARTED` · `DISCOVERY` · `READY` · `IN_PROGRESS` · `BLOCKED` · `IN_REVIEW` · `VERIFIED` · `RELEASED` · `DEFERRED` · `NOT_APPLICABLE`

| Status | Meaning |
| --- | --- |
| `NOT_STARTED` | Defined but not yet analysed |
| `DISCOVERY` | Being specified; assumptions still open |
| `READY` | Specified, owned, dependencies clear, safe to implement |
| `IN_PROGRESS` | Implementation underway |
| `BLOCKED` | Cannot proceed; blocker recorded |
| `IN_REVIEW` | Implementation complete, awaiting verification |
| `VERIFIED` | Exit criteria met with recorded evidence |
| `RELEASED` | Shipped to production |
| `DEFERRED` | Deliberately gated to a later phase |
| `NOT_APPLICABLE` | Does not apply; reason and reactivation condition recorded |

---

## 2. Critical blockers and decisions

| ID | Blocker | Impact | Owner | Needed by |
| --- | --- | --- | --- | --- |
| ~~BLK-001~~ | ~~No named owners~~ — **CLOSED 2026-08-05** (`ADR-010`): Deepesh Kumar Gupta owns all roles | Steps may now leave `READY`. **New gap:** four-eyes approval structurally unsatisfiable with one owner | Deepesh Kumar Gupta | Resolved |
| **BLK-002** | No application code exists. Repository contains documentation only | All contracts are `PROPOSED`; graph coverage gates unevaluable; traceability unverified | Engineering | Before `STEP-001` exit |
| `DEC-002` | Phase 1 destination region undecided | Blocks `STEP-005`, `STEP-010`, all evaluation corpora — **critical path** | Product Lead | Before Phase 1 |
| `DEC-004` | Identity provider undecided | Blocks `STEP-002` → 12-step fan-in | Security Architect | Before `STEP-002` |
| `DEC-005` | KPI thresholds undefined | Phase 1 exit gates not objectively evaluable | Product Lead | Before Phase 1 exit |
| `DEC-007` | Cloud provider/region/residency undecided | Blocks `STEP-027` | Product Architect | Before `STEP-027` |
| `DEC-008` | Routing provider undecided | Accessibility routing claim unvalidated | Product Architect | Before `STEP-005` |
| `DEC-009` | Event backbone undecided | Blocks `STEP-006` shape | Product Architect | Before `STEP-006` |
| `EV-GAP-002` | Provider licence viability unproven | `RISK-001` — highest exposure (20) | Data Architect + Legal | Before Phase 1 |

---

## 3. Scope completion dashboard

| Phase | Steps | `DISCOVERY` | `DEFERRED` | `VERIFIED` | % complete |
| --- | --- | --- | --- | --- | --- |
| Phase 1 (MVP) | 19 | 19 | 0 | 0 | 0% |
| Phase 2 | 3 | 0 | 3 | 0 | 0% |
| Phase 3 | 4 | 0 | 4 | 0 | 0% |
| Phase 4 | 1 | 0 | 1 | 0 | 0% |
| **Total** | **28** | **19** | **9** | **0** | **0%** |

Documentation completeness is **100%** (28/28 step files exist with all 28 sections). Implementation completeness is **0%**. These are deliberately reported separately so documentation progress is never mistaken for delivery progress.

---

## 4. Dependency and critical-path summary

**Critical path to Phase 1:**
`STEP-001` → `STEP-002` → `STEP-004` → `STEP-005` → `STEP-006` → `STEP-010` → `STEP-011` → `STEP-012` → `STEP-013`

| Concern | Detail |
| --- | --- |
| Highest fan-in | `STEP-002` blocks 12 steps; `STEP-004` blocks 9; `STEP-005` and `STEP-006` block 8 each |
| Critical-path risk concentration | `STEP-005` — cannot start until `DEC-002` and `EV-GAP-002` close |
| External dependencies unidentified | `EXT-001` … `EXT-010` (10 of 11); only `EXT-011` GitNexus is verified available |

---

## 5. Risk and quality-gate summary

| Exposure | Risks | Gate impact |
| --- | --- | --- |
| 20 | `RISK-001` data availability, `RISK-011` no owners | Phase-gate review required before proceeding |
| 15 | `RISK-002` scenario sameness, `RISK-006` location privacy | Active mitigation owner required |
| 12 | `RISK-003`, `RISK-005`, `RISK-008`, `RISK-009`, `RISK-013`, `RISK-014` | Reviewed each phase |

| Quality gate | Status | Note |
| --- | --- | --- |
| Hard-constraint violations = 0 | `NOT_STARTED` | No solver exists |
| Citation correctness ≥ 95% | `NOT_STARTED` | No retrieval exists |
| WCAG 2.2 AA + map-free journey | `NOT_STARTED` | No UI exists |
| Offline/sync/deletion tests | `NOT_STARTED` | Phase 3 for offline; deletion is Phase 1 |
| Provider outage / stale-data drills | `NOT_STARTED` | No connectors exist |
| Knowledge-graph freshness | **`VERIFIED` (partial)** | Index current at `HEAD`; **covers documentation only** |
| Blast-radius closure | `NOT_APPLICABLE` | No code changes have occurred |

---

## 6. Knowledge-graph freshness status

**Verified by direct execution on 2026-08-05 — not asserted.**

| Field | Value |
| --- | --- |
| Tool | GitNexus (`ADR-005`) |
| Invocation | `npx gitnexus <command>` — the project-local `.gitnexus/run.cjs` runner was **not** generated (`ASM-009`) |
| Repository | `/Users/deepeshgupta/Projects/journeylab`, registered as `journeylab` |
| Remote | `https://github.com/deepeshgupta12/journeylab.git` |
| Index state | ✅ up to date with `HEAD` at index time |
| Graph size | **~1,860 nodes, ~2,535 edges**, 0 clusters, 0 execution flows |
| **Coverage caveat** | The graph indexes **Markdown documentation only**. There is no application source code, so no symbols, APIs, tables, models or tests are represented (`RISK-014`, `ASM-025`) |
| Pre-change check capability | **`BLOCKED` for application code** — static fallback applies and does not satisfy the release gate |
| Required next action | Re-run `npx gitnexus analyze` immediately after the first source-code merge, then evaluate `REQ-KG-001` (≥95% files parsed) and `REQ-KG-002` (≥90% symbols owned) |

---

## 7. Step tracker

Legend for sub-columns: `—` not applicable to this step · `NS` not started · `DEF` deferred · `BLK` blocked · `N/A` not applicable.
**KG pre-check** = knowledge-graph pre-change analysis; **BR** = blast-radius review.

| Step | Name | Phase | Outcome | Deps | Status | Owner | FE | BE | API/Evt | Data | AI/ML | Sec/Priv | KG pre-check | BR | Impl | Test | Docs | PR/Release | Exit criteria | Blockers | Updated |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [STEP-001](../08-steps/STEP-001-foundation-and-repository-governance.md) | Foundation & repo governance | 1 | Reproducible monorepo with ownership and contract boundaries | — | **`VERIFIED`** | Deepesh Kumar Gupta | ✅ | ✅ | — | — | — | ✅ | partial | ✅ BR-001…007 | ✅ 6/6 | ✅ 15 checks + 25 meta | ✅ | `8dd20f4` | New engineer runs lint/tests/app from docs; CI rejects unowned changes | BLK-001, BLK-002 | 2026-08-05 |
| [STEP-002](../08-steps/STEP-002-identity-tenancy-and-authorization.md) | Identity, tenancy & authorization | 1 | Isolation and permission primitives | 001 | **`IN_PROGRESS`** 5/7 + .04/.05 partial | Deepesh Kumar Gupta | NS | ✅ .01–.07 | **✅ .05 (auth only)** | ✅ .01, .04 | — | ✅ R7 12/12 | ✅ **RUNNABLE** (BR-012, BR-013) | ✅ BR-008, BR-010…017 | ✅ 5/7 + .04/.05 partial | ✅ 335 py + 41 ts + 12 R7 | ✅ | — | Cross-tenant ops fail deterministically and are audited | ~~`DEC-004`~~ **CLOSED — Auth0**; `DEC-010` (fails closed); **REQ-TRIP-005 open** (STEP-007); **REQ-SEC-003 partial** (no live Auth0 tenant; a11y needs STEP-003) | 2026-08-06 |
| [STEP-003](../08-steps/STEP-003-design-system-and-application-shell.md) | Design system & app shell | 1 | Accessible responsive shell and primitives | 002 | **`VERIFIED`** 9/9 | Deepesh Kumar Gupta | ✅ .01–.09 | — | — | — | — | ✅ | ✅ **RUNNABLE** (BR-018…026) — but component impact is **unreliable**: JSX usage is not traced, and CSS is not in the graph at all (BR-025 §3, BR-026 §3) | ✅ BR-018…026 | ✅ 9/9 | ✅ 307 UI + 61 web + **40 browser** | ✅ | — | WCAG 2.2 AA on core components; all states implemented; **axe, keyboard, touch targets, forced-colors, RTL and CWV gate the build** | **BUG-018 closed.** CWV are lab numbers — field measurement is STEP-024. Manual screen-reader journeys **required every release**: see [ACCESSIBILITY_AUTOMATION_LIMITS](../06-quality/ACCESSIBILITY_AUTOMATION_LIMITS.md). **.09 added post-review** — the plan had no design sub-step; icons, a logo and a non-implementer design review remain open | 2026-08-11 |
| [STEP-004](../08-steps/STEP-004-contract-first-platform-apis.md) | Contract-first platform APIs | 1 | Stable resource/command/event contracts | 002 | **`IN_PROGRESS`** 2/8 | Deepesh Kumar Gupta | ✅ .01–.02 | — | ✅ **`contracts/openapi.yaml` exists and is authoritative** (ADR-001) | — | — | ✅ .01 | ✅ **RUNNABLE** — `impact(opaque_denial)` traced 2 callers and 1 flow, the first useful graph answer here | ✅ BR-028…029 | ✅ 2/8 | ✅ 440 py + 61 web + 307 UI + 40 browser | ✅ | — | CI generates clients, validates examples, blocks breaking change | **Two error shapes coexist** — `auth/errors.py` is not yet RFC 9457, migrates at .04. Rate-limit values deferred (`ASM-002`). **`gitnexus_query` is unusable — `--repair-fts` is not a valid flag** (BR-029 §3). `DATA-010/011` referenced but undefined (STEP-006) | 2026-08-11 |
| [STEP-005](../08-steps/STEP-005-source-integrations-and-ingestion.md) | Source integrations & ingestion | 1 | Inputs with consent, provenance, replay | 004 | `BLOCKED` | — | — | NS | NS | NS | — | NS | `BLOCKED` | N/A | NS | NS | ✅ | — | Every source has credentials, limits, checkpoints, reconciliation, deletion | DEC-002, DEC-008, EV-GAP-002, RISK-001 | 2026-08-05 |
| [STEP-006](../08-steps/STEP-006-canonical-data-model-and-event-backbone.md) | Canonical model & event backbone | 1 | Versioned entities and replayable events | 005 | `DISCOVERY` | — | — | NS | NS | NS | — | NS | `BLOCKED` | N/A | NS | NS | ✅ | — | Records retain provenance; events rebuild read models | BLK-001, DEC-009 | 2026-08-05 |
| [STEP-007](../08-steps/STEP-007-discovery-landing-and-destination-coverage.md) | Discovery landing & coverage | 1 | Expectations set before signup | 003, 006 | `DISCOVERY` | — | NS | NS | NS | NS | — | NS | `BLOCKED` | N/A | NS | NS | ✅ | — | User knows what is supported and what JourneyLab will not do pre-signin | BLK-001 | 2026-08-05 |
| [STEP-008](../08-steps/STEP-008-account-consent-and-traveler-profile.md) | Account, consent & profile | 1 | Portable profile with minimal data | 002, 007 | `DISCOVERY` | — | NS | NS | NS | NS | — | NS | `BLOCKED` | N/A | NS | NS | ✅ | — | Planning completes with minimal data; every attribute inspectable/removable | BLK-001, ASM-014 | 2026-08-05 |
| [STEP-009](../08-steps/STEP-009-trip-brief-and-structured-constraints.md) | Trip brief & constraints | 1 | Auditable planning specification | 008, 004 | `DISCOVERY` | — | NS | NS | NS | NS | NS | NS | `BLOCKED` | N/A | NS | NS | ✅ | — | User edits structured brief and understands every inferred field | BLK-001, ASM-024 | 2026-08-05 |
| [STEP-010](../08-steps/STEP-010-destination-evidence-assembly.md) | Destination evidence assembly | 1 | Time-aware evidence pack | 006, 009 | `DISCOVERY` | — | NS | NS | NS | NS | NS | NS | `BLOCKED` | N/A | NS | NS | ✅ | — | Every solver fact is source-addressable and freshness-governed | BLK-001, RISK-001 | 2026-08-05 |
| [STEP-011](../08-steps/STEP-011-candidate-generation.md) | Candidate generation | 1 | Diverse eligible candidate pool | 010 | `DISCOVERY` | — | — | NS | — | NS | NS | NS | `BLOCKED` | N/A | NS | NS | ✅ | — | Recall meets evaluation set; prohibited options never reach solver | BLK-001 | 2026-08-05 |
| [STEP-012](../08-steps/STEP-012-scenario-optimisation-and-simulation.md) | Scenario optimisation & simulation | 1 | Multiple feasible itineraries | 011 | `DISCOVERY` | — | NS | NS | NS | NS | NS | NS | `BLOCKED` | N/A | NS | NS | ✅ | — | Zero hard-constraint violations; runs reproducible from seed | BLK-001, ASM-022, ASM-023 | 2026-08-05 |
| [STEP-013](../08-steps/STEP-013-visual-comparison.md) | Visual comparison | 1 | Traveler understands differences | 012, 003 | `DISCOVERY` | — | NS | NS | NS | NS | NS | NS | `BLOCKED` | N/A | NS | NS | ✅ | — | Keyboard/SR users complete the same comparison without a map | BLK-001 | 2026-08-05 |
| [STEP-014](../08-steps/STEP-014-interactive-what-if-editing.md) | Interactive what-if editing | 2 | Smallest affected recompute | 013 | `DEFERRED` | — | DEF | DEF | DEF | DEF | DEF | DEF | `BLOCKED` | N/A | DEF | DEF | ✅ | — | No unaffected day changes without explanation; every edit reversible | Phase 1 exit | 2026-08-05 |
| [STEP-015](../08-steps/STEP-015-collaboration-and-decision.md) | Collaboration & decision | 2 | Group constraints, explicit decision | 013, 002 | `DEFERRED` | — | DEF | DEF | DEF | DEF | — | DEF | `BLOCKED` | N/A | DEF | DEF | ✅ | — | Owner reconstructs who proposed/approved/changed every choice | Phase 1 exit | 2026-08-05 |
| [STEP-016](../08-steps/STEP-016-booking-handoff.md) | Booking handoff | 1 | External purchase without false confirmation | 013, 005 | `DISCOVERY` | — | NS | NS | NS | NS | — | NS | `BLOCKED` | N/A | NS | NS | ✅ | — | Estimated vs confirmed distinct; no final price without provider confirmation | BLK-001, ASM-012 | 2026-08-05 |
| [STEP-017](../08-steps/STEP-017-live-trip-activation-and-offline-pack.md) | Live activation & offline pack | 3 | Reliable mobile companion | 016 | `DEFERRED` | — | DEF | DEF | DEF | DEF | — | DEF | `BLOCKED` | N/A | DEF | DEF | ✅ | — | Critical info readable ≥72 h offline; conflicts resolved visibly | Phase 2 exit, RISK-006 | 2026-08-05 |
| [STEP-018](../08-steps/STEP-018-condition-monitoring.md) | Condition monitoring | 3 | Material changes detected, not noise | 017, 006 | `DEFERRED` | — | DEF | DEF | DEF | DEF | — | DEF | `BLOCKED` | N/A | DEF | DEF | ✅ | — | Notifications timely, deduplicated, traceable to evidence | Phase 2 exit | 2026-08-05 |
| [STEP-019](../08-steps/STEP-019-controlled-replanning.md) | Controlled replanning | 3 | Repair without rebuilding | 018, 012 | `DEFERRED` | — | DEF | DEF | DEF | DEF | DEF | DEF | `BLOCKED` | N/A | DEF | DEF | ✅ | — | Replan time, preserved-plan %, accepted delta meet targets | Phase 2 exit | 2026-08-05 |
| [STEP-020](../08-steps/STEP-020-post-trip-learning.md) | Post-trip learning | 3 | Inspectable preference improvement | 019 | `DEFERRED` | — | DEF | DEF | DEF | DEF | DEF | DEF | `BLOCKED` | N/A | DEF | DEF | ✅ | — | Preference changes explainable and measurable | Phase 2 exit, ASM-013 | 2026-08-05 |
| [STEP-021](../08-steps/STEP-021-administration-and-curation-console.md) | Administration & curation | 1 | Correct facts and control rollout safely | 006, 010 | `DISCOVERY` | — | NS | NS | NS | NS | — | NS | `BLOCKED` | N/A | NS | NS | ✅ | — | Every override has reason, period, evidence, audit; four-eyes on high impact | BLK-001 | 2026-08-05 |
| [STEP-022](../08-steps/STEP-022-analytics-feedback-and-experimentation.md) | Analytics & experimentation | 2 | Usage and outcomes drive priorities | 006, 013 | `DEFERRED` | — | DEF | DEF | — | DEF | DEF | DEF | `BLOCKED` | N/A | DEF | DEF | ✅ | — | Every KPI has owner, formula, lineage, guardrail | Phase 1 exit | 2026-08-05 |
| [STEP-023](../08-steps/STEP-023-security-privacy-and-compliance-controls.md) | Security & privacy controls | 1 | Controls as testable behavior | 002 | `DISCOVERY` | — | NS | NS | — | NS | — | NS | `BLOCKED` | N/A | NS | NS | ✅ | — | Threat-model actions closed; DSR and tenant deletion rehearsed | BLK-001 | 2026-08-05 |
| [STEP-024](../08-steps/STEP-024-observability-sre-and-support-readiness.md) | Observability & SRE readiness | 1 | Failures detectable and recoverable | 006, 027 | `DISCOVERY` | — | NS | NS | — | — | NS | NS | `BLOCKED` | N/A | NS | NS | ✅ | — | On-call identifies tenant impact and degrades safely via rehearsed runbooks | BLK-001 | 2026-08-05 |
| [STEP-025](../08-steps/STEP-025-support-deletion-and-data-lifecycle.md) | Support, deletion & lifecycle | 1 | Closed data lifecycle incl. retirement | 023, 026 | `DISCOVERY` | — | NS | NS | NS | NS | — | NS | `BLOCKED` | N/A | NS | NS | ✅ | — | Automated tests prove removal across all stores | BLK-001 | 2026-08-05 |
| [STEP-026](../08-steps/STEP-026-knowledge-graph-platform.md) | Knowledge graph platform | 1 | Domain + code graphs continuously updated | 001 | `DISCOVERY` | — | NS | NS | NS | NS | NS | NS | **partial ✅** | N/A | NS | NS | ✅ | — | Graph covers main branch, reports gaps, supports tested impact queries | BLK-002, RISK-014 | 2026-08-05 |
| [STEP-027](../08-steps/STEP-027-release-automation-and-controlled-rollout.md) | Release automation & rollout | 1 | Single release gate, reversible increments | 004, 023 | `DISCOVERY` | — | — | NS | — | NS | NS | NS | `BLOCKED` | N/A | NS | NS | ✅ | — | Release blocked by any gate regression; canary and rollback automated | BLK-001, DEC-007 | 2026-08-05 |
| [STEP-028](../08-steps/STEP-028-advisor-workspace-and-commercial-scale.md) | Advisor workspace & scale | 4 | White-label and partner economics | Phase 3 exit | `DEFERRED` | — | DEF | DEF | DEF | DEF | DEF | DEF | `BLOCKED` | N/A | DEF | DEF | ✅ | — | Repeatable onboarding, positive margin, partner conversion | Phase 3 exit | 2026-08-05 |

---

## 8. Documentation freshness

**Freshness definition:** a document is fresh when its `Last reviewed` date is within its review interval **and** it is consistent with the current release commit. A stale document blocks its step's transition to `VERIFIED`.

| Group | Files | Status | Review interval | Last reviewed |
| --- | --- | --- | --- | --- |
| `00-START-HERE.md` | 1 | `READY` | Every release | 2026-08-05 |
| `01-product/` | 9 | `DISCOVERY` | Each phase gate | 2026-08-05 |
| `02-delivery/` | 8 | `DISCOVERY` | Weekly during delivery | 2026-08-05 |
| `03-architecture/` | 11 | `DISCOVERY` | Each phase gate + on ADR change | 2026-08-05 |
| `04-contracts/` | 7 | `DISCOVERY` (all `PROPOSED`) | On every contract change | 2026-08-05 |
| `05-knowledge-graph/` | 8 | `READY` | On extractor/schema change | 2026-08-05 |
| `06-quality/` | 6 | `DISCOVERY` | Each release | 2026-08-05 |
| `07-operations/` | 6 | `DISCOVERY` | Quarterly + post-incident | 2026-08-05 |
| `08-steps/` | 28 | `DISCOVERY` / `DEFERRED` | On step status change | 2026-08-05 |
| `09-templates/` | 6 | `READY` | On governance change | 2026-08-05 |
| Root `CLAUDE.md` | 1 | `READY` | On rule or graph change | 2026-08-05 |
| `08-steps/sub-steps/` | 48 | `NOT_STARTED` | At step start (`ADR-008`) | 2026-08-05 |

---

## 9. Change history

| Date | Change | By |
| --- | --- | --- |
| 2026-08-05 | Tracker created; 28 steps registered; blockers `BLK-001`/`BLK-002` raised; GitNexus freshness recorded from verified execution | Documentation lead |

---

## 10. Tracker discipline

1. Only the statuses in §1 may be used.
2. A step moves to `VERIFIED` only when its exit criteria **and** evidence requirements (step file §26) are complete.
3. A step may not be `READY` while it has an unresolved blocking dependency or no owner.
4. `KG pre-check` and `BR` columns must be non-empty before `IMPL` may start (`REQ-KG-008`).
5. Status changes require the `Updated` date to change in the same edit.
6. Documentation-only progress is never reported as delivery progress (see §3).
