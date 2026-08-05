# JourneyLab — Assumption Register

| Field | Value |
| --- | --- |
| Owner | TPM (unassigned — `BLK-001`) |
| Status | `DISCOVERY` — 0 of 18 assumptions validated |
| Rule | Nothing in this documentation set may cite an open assumption as a fact |
| Last reviewed | 2026-08-05 |

Navigation: [Charter](../01-product/PRODUCT_CHARTER.md) · [Problem & evidence](../01-product/PROBLEM_AND_EVIDENCE.md) · [Risks](RISK_REGISTER.md) · [Decisions](DECISION_LOG.md) · [Master tracker](MASTER_TRACKER.md) · [00-START-HERE](../00-START-HERE.md)

---

## How this register works

An **assumption** is something we have acted upon but have not verified. It differs from a **decision** (a choice we made and own) and a **risk** (an event that may occur).

- `OPEN` — unvalidated, actively load-bearing.
- `VALIDATED` — evidence obtained; record the evidence and convert to a confirmed fact.
- `INVALIDATED` — disproven; must trigger a scope or design change, recorded in [DECISION_LOG](DECISION_LOG.md).
- **Impact if wrong** is written as the concrete consequence, not "high/medium/low".

---

## 1. Product and market assumptions

| ID | Assumption | Source | Impact if wrong | Validation method | Blocks | Status |
| --- | --- | --- | --- | --- | --- | --- |
| ASM-010 | Travelers will compare scenarios when comparison is faster than manual tabs and spreadsheets | Blueprint §1 | The core product mechanism has no demand; `RISK-002` stop condition triggers and the product is rebuilt or halted | 15+ moderated comparison tasks vs. current workflow (Phase 0 exit) | Phase 1 start | `OPEN` |
| ASM-013 | Users will provide preference feedback if it visibly improves recommendations | Blueprint §1 | Preference learning (`AI-009`) has insufficient signal; ranking stays static and `KPI-009` is unmeasurable | Instrumented feedback prompts in Phase 1 pilot | STEP-020 | `OPEN` |
| ASM-014 | Users will disclose accessibility and mobility constraints to a planning product | Blueprint §5 + privacy analysis | Accessibility-as-first-class-constraint — a core differentiator — has no input data; mixed-mobility value claim fails | Sensitive-topic interview protocol with privacy review | STEP-008 | `OPEN` |
| ASM-015 | A 3–7 day window demonstrates differentiated simulation without unbounded complexity | Blueprint §1 | Either scenarios look trivially similar (too short) or solver latency breaches `REQ-NFR-004` (too long) | Scenario diversity + latency measurement on golden packs | STEP-012 | `OPEN` |
| ASM-017 | Travelers accept a planning tool that cannot book, requiring a handoff to a third party | Derived — not stated in blueprint | Conversion drops at the seam; affiliate model (`KPI-006`) underperforms and business model must change | Phase 1 pilot funnel measurement at handoff | STEP-016 | `OPEN` |
| ASM-018 | A consumer-facing travel product can acquire users economically without paid distribution | Derived — not stated in blueprint | Unit economics (`KPI-007`) never reach contribution margin regardless of product quality | Channel test — **not in current scope**; requires commercial owner | Phase 4 | `OPEN` |

## 2. Data, provider and legal assumptions

| ID | Assumption | Source | Impact if wrong | Validation method | Blocks | Status |
| --- | --- | --- | --- | --- | --- | --- |
| ASM-011 | A destination pack (places, hours, transit, weather, price ranges) can be licensed or lawfully assembled | Blueprint §1 | **Largest single delivery risk.** No evidence pack means no solver input; `RISK-001` stop condition triggers | Provider term review + coverage audit for the candidate region | STEP-005, STEP-010 | `OPEN` |
| ASM-012 | Deep-link affiliate partners preserve enough itinerary context to avoid restarting the purchase journey | Blueprint §1 | Handoff UX breaks; `REQ-BOOK-001` unmeetable; fallback is copyable details only | Technical review of 2–3 candidate partners | STEP-016 | `OPEN` |
| ASM-019 | Provider terms permit caching evidence long enough to make scenario generation reproducible | Derived from `REQ-CONS-006` + `CON-002` | Reproducibility (`REQ-CONS-006`) conflicts with licence terms; evidence packs cannot be immutable | Licence clause review specifically on cache duration | STEP-005 | `OPEN` |
| ASM-020 | Wheelchair/step-free routing data exists at usable quality in the candidate region | Derived from blueprint §9.120 "where data permits" | Accessibility routing degrades to an unverified claim; `REQ-A11Y` scope narrows and must be disclosed to users | Routing provider capability audit (`DEC-008`) | STEP-005 | `OPEN` |
| ASM-021 | Crowd signals are obtainable without tracking individuals | Derived from blueprint §6.4 | "Quieter locations" preference cannot be supported, or supported only via a privacy-invasive source that violates `CON-003` | Source privacy review | STEP-010 | `OPEN` |

## 3. Technical assumptions

| ID | Assumption | Source | Impact if wrong | Validation method | Blocks | Status |
| --- | --- | --- | --- | --- | --- | --- |
| ASM-022 | CP-SAT can solve a 7-day multi-objective itinerary within the p95 ≤ 45 s budget | Blueprint §15 + §9.123 | `REQ-NFR-004` breached; product must reduce scenario count, simplify constraints or change solver strategy | Solver spike on representative instances | STEP-012 | `OPEN` |
| ASM-023 | Three-to-five scenarios can be made *materially* different rather than cosmetically different | Blueprint §13.168 | `RISK-002` — users see no reason to compare; diversity metric fails `REQ-CONS-007` | MMR/diversification measurement on golden packs | STEP-012 | `OPEN` |
| ASM-024 | An LLM can extract a typed TripBrief at acceptable field-level precision across target locales | Blueprint §13.170 | Brief parsing falls back to structured forms only; conversational entry is dropped from MVP | Gold-set extraction evaluation across locales | STEP-009 | `OPEN` |
| ASM-025 | Documentation-only indexing is a valid interim state for the code knowledge graph | Verified observation, 2026-08-05 | None — this is a transitional state; the graph becomes load-bearing only when code exists | Re-index after first code merge; check `REQ-KG-001` coverage | STEP-026 | `OPEN` |

## 4. Programme and environment assumptions

| ID | Assumption | Source | Impact if wrong | Validation method | Blocks | Status |
| --- | --- | --- | --- | --- | --- | --- |
| ASM-001 | A named product owner and per-step owners will be assigned before implementation begins | Derived — no owners exist today | `BLK-001` persists; no step can leave `READY`, and no exit gate can be signed off | Staffing decision | All steps | `OPEN` |
| ASM-002 | Team composition and budget are sufficient for the 18-step manifest at the target release | Not specified anywhere | Roadmap phase durations are unplannable; sequencing must be re-cut | Capacity planning with a named TPM | [ROADMAP](ROADMAP.md) | `OPEN` |
| ASM-003 | No data-residency obligation constrains the initial deployment region | Not specified (`DEC-007`) | Deployment architecture, provider selection and storage design change materially | Legal/privacy review of target user geography | STEP-027 | `OPEN` |
| ASM-004 | The August 2026 technology baseline remains current at implementation time | Blueprint §10, portfolio standard §4.18 | Version choices in [TECHNICAL_ARCHITECTURE](../03-architecture/TECHNICAL_ARCHITECTURE.md) need revalidation before pinning | Dependency review at implementation start | STEP-001 | `OPEN` |

---

## 5. Assumptions that were resolved by direct verification

These were open questions that have been **checked**, not assumed. Recorded here for auditability.

| ID | Question | Verified finding | Date | Method |
| --- | --- | --- | --- | --- |
| ASM-005 | Does an application codebase exist? | **No.** The repository contained only `docs/product/` with three Markdown files and no source, manifests, contracts, migrations, CI or tests | 2026-08-05 | Directory listing + file enumeration |
| ASM-006 | Is a knowledge-graph tool available? | **Yes.** GitNexus is installed and functional; MCP server responds and 5 other repositories are indexed | 2026-08-05 | `list_repos` MCP call |
| ASM-007 | Was `journeylab` already indexed? | **No** — it was absent from the registry, and the directory was not a git repository | 2026-08-05 | `list_repos` + `git status` |
| ASM-008 | Can GitNexus index this repository now? | **Yes.** After `git init` and a baseline commit, `npx gitnexus analyze` succeeded: ~1,860 nodes, ~2,535 edges, index at commit `db32aff` (later amended to `73766ca`) | 2026-08-05 | `npx gitnexus analyze`, `npx gitnexus status` |
| ASM-009 | Is the project-local runner `.gitnexus/run.cjs` available? | **No.** `analyze` did not generate it; `node .gitnexus/run.cjs` fails with `MODULE_NOT_FOUND`. **`npx gitnexus <command>` is the working invocation** and is what the documentation specifies | 2026-08-05 | Direct execution of both forms |
| ASM-016 | What is the realistic cost per saved feasible trip? | **Still open** — no traces exist to measure. Tracked as `EV-GAP-006` | — | — |

---

## 6. Register discipline

1. An assumption may not be closed by opinion. Closing requires recorded evidence and a date.
2. If an assumption is invalidated, the change it forces is logged in [DECISION_LOG](DECISION_LOG.md) — invalidation is a result, not a failure.
3. Any document citing an `OPEN` assumption must label it as an assumption at the point of use.
4. Assumptions carrying a stop condition are cross-referenced in [RISK_REGISTER](RISK_REGISTER.md): `ASM-010`→`RISK-002`, `ASM-011`→`RISK-001`, `ASM-012`→`RISK-005`.
</content>
