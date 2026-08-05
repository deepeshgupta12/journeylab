# JourneyLab — Decision Log

| Field | Value |
| --- | --- |
| Owner | Product Architect + Product Lead (unassigned — `BLK-001`) |
| Status | `DISCOVERY` — 6 decisions accepted, 8 open |
| Rule | A decision is not made until it has an owner, a date and recorded consequences |
| Last reviewed | 2026-08-05 |

Navigation: [Charter](../01-product/PRODUCT_CHARTER.md) · [Assumptions](ASSUMPTION_REGISTER.md) · [Risks](RISK_REGISTER.md) · [ADR template](../09-templates/ADR_TEMPLATE.md) · [00-START-HERE](../00-START-HERE.md)

---

## How decisions are recorded

- **Accepted architectural decisions** get a full ADR file (`docs/adr/ADR-NNN-*.md` in the code repository) using [ADR_TEMPLATE](../09-templates/ADR_TEMPLATE.md). This log is the index and the record of decisions not yet promoted to an ADR.
- **Open decisions** block specific work and name what is blocked. An open decision with no blocked work is not a decision — it is a preference.
- A decision that is later reversed is **superseded, not deleted**. History is evidence.

---

## 1. Accepted decisions

### ADR-001 — Documentation is the source of truth before code exists
- **Date:** 2026-08-05 · **Owner:** Documentation lead · **Status:** Accepted
- **Context:** No application code exists. Work must be specifiable and reviewable before implementation.
- **Decision:** `docs/product/` is the operational source of truth for scope, contracts, architecture and delivery status. Markdown explains contracts; when machine-readable contracts exist (`contracts/openapi.yaml`), those become authoritative for schemas and Markdown must link rather than duplicate.
- **Consequences:** Documentation drift becomes a release blocker (`REQ-PLAT-009`). Every contract in [API_CONTRACTS](../04-contracts/API_CONTRACTS.md) is marked `PROPOSED` until a schema file exists.
- **Alternatives rejected:** Code-first with documentation after (loses the pre-change impact discipline required by `REQ-KG-008`).

### ADR-002 — Deterministic engines own feasibility; the LLM owns language
- **Date:** 2026-08-05 · **Owner:** AI/ML Architect · **Status:** Accepted (inherited from blueprint §1.3, portfolio standard §4.20)
- **Context:** Travel planning is a constrained decision problem. Model fluency is not feasibility.
- **Decision:** CP-SAT and deterministic validators own time, route, budget, eligibility, permissions and workflow state. The LLM parses intent, asks clarifications and explains trade-offs. Model output can never mutate trip state without command validation and user authorization (`REQ-AI-001`).
- **Consequences:** Every AI capability needs a non-AI fallback (`REQ-AI-007`). Scenario scores are never model-generated.
- **Alternatives rejected:** LLM-orchestrated planning with tool calls deciding feasibility — unreproducible and unverifiable against `REQ-CONS-004`.

### ADR-003 — Modular monolith plus isolated compute workers for the MVP
- **Date:** 2026-08-05 · **Owner:** Product Architect · **Status:** Accepted (blueprint §9.117)
- **Context:** Blueprint names 14 service boundaries. Deploying 14 services at MVP adds operational cost without scaling need.
- **Decision:** Start as one deployable API application with enforced internal module boundaries, plus separately scaled solver, simulation and ingestion workers. Split only when scaling, ownership or failure isolation justifies it.
- **Consequences:** Module boundaries must be enforced in CI (import rules), otherwise the split becomes impossible later. Solver workers get explicit CPU/memory budgets.
- **Alternatives rejected:** Microservices from day one (premature); single process including solvers (a solver timeout would degrade API availability).

### ADR-004 — Immutable evidence packs as solver input
- **Date:** 2026-08-05 · **Owner:** Data Architect · **Status:** Accepted (blueprint §10.140)
- **Context:** `REQ-CONS-006` requires reproducible scenario runs. Live provider data is not reproducible.
- **Decision:** An `EvidencePack` is assembled, versioned and frozen before solving. Solvers read only from the pack, never from arbitrary web content or live provider calls.
- **Consequences:** Requires cache rights from providers (`ASM-019`). Stale packs must be detected and rebuilt. Storage grows per generation run and needs a retention policy.
- **Alternatives rejected:** Live provider calls during solve (unreproducible, latency-unbounded, quota-fragile).

### ADR-005 — GitNexus is the knowledge-graph toolchain
- **Date:** 2026-08-05 · **Owner:** Platform · **Status:** Accepted
- **Context:** `KNOWLEDGE_GRAPH_TOOL` was `AUTO_DISCOVER`. GitNexus was verified present and functional, with an MCP server and CLI.
- **Decision:** GitNexus provides the codebase knowledge graph, pre-change impact analysis and change detection. The **product domain graph is a separate concern** and is not served by GitNexus; it is specified in [DOMAIN_KNOWLEDGE_GRAPH](../05-knowledge-graph/DOMAIN_KNOWLEDGE_GRAPH.md) as a Neo4j/PostgreSQL design to be built in `STEP-026`.
- **Verified evidence:** `npx gitnexus analyze` succeeded on 2026-08-05 — 119 nodes, 143 edges; `npx gitnexus status` reports the index up to date. **The index currently covers Markdown documentation only, because no source code exists.**
- **Consequences:** `npx gitnexus <command>` is the documented invocation (the project-local `run.cjs` runner was not generated — see `ASM-009`). Graph coverage gates in `REQ-KG-001` cannot be meaningfully evaluated until code lands.
- **Alternatives rejected:** Hand-maintained dependency documentation (drifts immediately); deferring graph tooling until code exists (would let the first commits merge without impact analysis).

### ADR-006 — Commit messages carry no AI co-authorship attribution
- **Date:** 2026-08-05 · **Owner:** Repository owner (user directive) · **Status:** Accepted
- **Context:** Default tooling appends a `Co-Authored-By: Claude` trailer to commits.
- **Decision:** Commit messages and pull-request descriptions in this repository must **not** contain AI co-authorship trailers or attribution.
- **Consequences:** Contributors and agents must strip the trailer. The baseline commit was amended to comply (`73766ca`). This rule is restated in `CLAUDE.md`, [CONTRACT_CHANGE_POLICY](../04-contracts/CONTRACT_CHANGE_POLICY.md) and [CHANGE_IMPACT_PROTOCOL](../05-knowledge-graph/CHANGE_IMPACT_PROTOCOL.md).
- **Alternatives rejected:** Leaving the default trailer (contradicts an explicit repository-owner directive).

---

## 2. Open decisions

| ID | Decision needed | Options under consideration | Blocks | Owner | Needed by |
| --- | --- | --- | --- | --- | --- |
| DEC-002 | Which destination region is the Phase 1 pack | Not yet enumerated; selection criteria must include data licensability (`ASM-011`), transit data quality, accessibility data (`ASM-020`) and crowd-signal privacy (`ASM-021`) | STEP-005, STEP-010, all evaluation corpora, Phase 0 exit | Product Lead | Before Phase 1 start |
| DEC-003 | Business model: affiliate-only, subscription, or hybrid | (a) affiliate-only; (b) freemium with paid comparison depth; (c) advisor-licensing-first | Whether a billing step `STEP-029` exists; [SUCCESS_METRICS](../01-product/SUCCESS_METRICS.md) `KPI-007` targets | Product Lead + Commercial | Before Phase 1 exit |
| DEC-004 | Identity provider | Managed OIDC vendor vs. self-hosted | STEP-002 | Security Architect | Before STEP-002 |
| DEC-005 | Numeric KPI thresholds | Requires Phase 0/1 baselines; must not be asserted in advance | Release gates, [RELEASE_READINESS_CHECKLIST](../06-quality/RELEASE_READINESS_CHECKLIST.md) | Product Lead | Before Phase 1 exit |
| DEC-006 | KPI review cadence and decision forum | Weekly delivery review vs. monthly product review | Governance | TPM | Before Phase 1 |
| DEC-007 | Cloud provider, region, residency posture | Undetermined; `ASM-003` assumes no residency constraint | [DEPLOYMENT_ARCHITECTURE](../03-architecture/DEPLOYMENT_ARCHITECTURE.md), STEP-027 | Product Architect | Before STEP-027 |
| DEC-008 | Routing provider and wheelchair profile support | Determines whether accessible routing is a product claim or a disclosed limitation | STEP-005, `REQ-A11Y` routing scope | Product Architect + Data | Before STEP-005 |
| DEC-009 | Event backbone for MVP: managed queue vs. Kafka 4.3 | Blueprint permits a managed queue at MVP scale while preserving AsyncAPI contracts | STEP-006 | Product Architect | Before STEP-006 |

---

## 3. Decisions deliberately deferred

| Topic | Why deferred | Revisit at |
| --- | --- | --- |
| Splitting the monolith into independent services | No scaling or ownership pressure exists yet (`ADR-003`) | When a module's scaling or failure profile diverges |
| Neo4j adoption for the domain graph | PostgreSQL may suffice for MVP traversal depth; polyglot persistence is a cost | STEP-026 design review |
| Tenant-managed encryption keys | No enterprise tier exists | Phase 4 |
| Native mobile applications | PWA is the documented vehicle (`EXC-009`) | If offline/notification limits prove blocking |
| Model fine-tuning | No training-data consent basis (`EXC-011`) | Requires a consent design decision first |

---

## 4. Superseded decisions

None. This log begins at 2026-08-05.
</content>
