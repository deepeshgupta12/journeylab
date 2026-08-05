---
step_id: STEP-026
title: Knowledge graph platform
status: DISCOVERY
release: Phase 1
owners: []
dependencies: [STEP-001]
requirement_ids: [REQ-KG-001, REQ-KG-002, REQ-KG-003, REQ-KG-004, REQ-KG-005, REQ-KG-006, REQ-KG-007, REQ-KG-008]
api_ids: [API-018]
event_ids: []
data_ids: []
ai_ids: []
knowledge_graph_check: REQUIRED
last_updated: 2026-08-05
---

# STEP-026 — Knowledge graph platform

> Status is authoritative in [MASTER_TRACKER](../02-delivery/MASTER_TRACKER.md).
> **Partially started:** GitNexus is installed and indexing (verified 2026-08-05), but covers documentation only.

## 1. Outcome
Two permission-separated graphs — a code graph explaining implementation and impact, and a domain graph explaining product decisions and evidence — refresh continuously, report their gaps, and support tested impact and provenance queries.

## 2. Why this step exists
`REQ-KG-008` blocks any merge without a pre-change impact record. That requirement is unenforceable without a working graph, so this step is on the critical path for **change safety** even though it is not on the critical path for features.

## 3. Scope
Domain and code graph schemas; Tree-sitter and language-server extraction; contract, migration, IaC and model-registry parsing; incremental commit-diff loading with tombstoning; permission-aware query API; graph explorer and impact UI; CI refresh workflow; quality gates.

## 4. Explicit exclusions
Product features consuming domain-graph queries live in their own steps (`KG-Q-001` in [STEP-018](STEP-018-condition-monitoring.md), `KG-Q-005` in [STEP-021](STEP-021-administration-and-curation-console.md)).

## 5. Actors, permissions and data access
| Actor | Permission | Data accessed | Sensitivity |
| --- | --- | --- | --- |
| Engineers | Code graph within repository permissions | Source structure | Internal |
| PER-004 curator | Domain facts subgraph | Destination facts | Licensed |
| Product services | Tenant-scoped domain traversal | Tenant data | PII |

**Code-graph access confers no domain-graph access, and vice versa.**

## 6. Preconditions and dependencies
[STEP-001](STEP-001-foundation-and-repository-governance.md). Code-graph **coverage** additionally requires application source to exist (`BLK-002`); domain graph requires [STEP-006](STEP-006-canonical-data-model-and-event-backbone.md).

## 7. Inputs and source systems
Repository source, contracts, migrations, IaC, CI workflows, model/prompt registries, tests, Git history, OTel runtime data, canonical product data.

## 8. Detailed normal workflow
1. Full index built (`npx gitnexus analyze`).
2. Extractors parse symbols, contracts, data, infrastructure, ML/AI artifacts, tests and requirement IDs.
3. Git provenance and ownership are attached.
4. Runtime OTel evidence joins as `OBSERVED_BY` edges **without customer payloads**.
5. Graph loads with uniqueness constraints, temporal validity and confidence.
6. Quality checks run; gaps are reported.
7. On every merge, the commit diff drives incremental upsert and tombstoning; on release, an immutable graph is tagged.

## 9. Alternate, partial and failure workflows
| Condition | Behavior | User-visible result | Requirement |
| --- | --- | --- | --- |
| Index stale | **Pre-change checks are `BLOCKED`**; static fallback applies | Merges blocked or flagged low-confidence | REQ-KG-008 |
| File fails to parse | Recorded as an **extraction gap**, never silently skipped | Coverage report shows it | REQ-KG-001 |
| Call unresolved | Recorded as a gap with confidence, not dropped | Visible uncertainty | REQ-KG-005 |
| Index corrupt | `clean` then `analyze --force`; checks `BLOCKED` meanwhile | Documented outage | RB-KG-001 |
| Traversal reaches an unauthorized node | Filtered **during** traversal; existence not leaked | No path revealed | REQ-KG-006 |
| Secret detected in content | Excluded from properties and embeddings; alert | Not indexed | REQ-KG-007 |

## 10. State machine and lifecycle transitions
Index: `absent → full → current ↔ stale → corrupt → rebuilt`. Node: `created → updated → tombstoned`. Release graph: `tagged (immutable)`.

## 11. Frontend implementation
`apps/web/src/app/knowledge/` (`PROPOSED`) — graph explorer, impact analysis view, provenance panel. **Inferred edges are visually distinct**; every graph view has a list/table equivalent.

## 12. Backend implementation
`knowledge/schema/{domain,code}.cypher`, `knowledge/extract/{tree_sitter,contracts,infra}.py`, `knowledge/resolve/symbols.py`, `knowledge/load/incremental.py`, `knowledge/api/routes.py`, `services/knowledge/src/{domain_graph,graph_retriever}.py`, `.github/workflows/knowledge-graph.yml` (all `PROPOSED`).

## 13. API, event and integration contracts
`API-018` permission-aware graph search, impact, ownership and evidence queries — **internal only**. Consumes domain events to maintain the domain graph.

## 14. Data model, migration and retention effects
Code graph holds **no customer data by construction**. Domain graph is tenant-scoped and deleted with its subject. Release graphs are immutable — which is precisely why the domain graph is excluded from them.

## 15. AI, LLM, RAG, ML and data-science implementation
Supports GraphRAG retrieval for engineering questions. **Embeddings remain disabled** until a documented scan proves no secret or customer payload can enter them (`REQ-KG-007`). Inferred edges are heuristic, carry confidence, and are human-correctable — corrections become extractor regression tests.

## 16. Security, privacy, accessibility and responsible-AI controls
`REQ-KG-006` permission-aware traversal with no existence leakage via counts, path lengths or timing. `REQ-KG-007` no secrets or payloads. Every graph answer logged with traversed evidence. Explorer meets the accessibility bar.

## 17. Observability, analytics and KPIs
Refresh lag after merge, coverage %, symbols owned %, unresolved calls, extraction failures, index/HEAD divergence, query latency. Alert `ALRT-KG-001`; runbook `RB-KG-001`.

## 18. Files and modules expected to change
All `PROPOSED` except the verified GitNexus artifacts: `.gitnexus/`, `CLAUDE.md`, `AGENTS.md`, `.claude/skills/gitnexus/`.

## 19. Knowledge-graph pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | **AVAILABLE, documentation-only** — ~1,860 nodes, ~2,535 edges (verified 2026-08-05) |
| Queries to run | KG-Q-015 before commits; full gate evaluation after the first code merge |
| Expected impact | **An extractor change alters every downstream answer** — highest-leverage change class in the repository |

## 20. Blast-radius assessment
An extractor defect silently corrupts every impact analysis, which in turn corrupts every other step's safety check. Precision sampling (KG-005) exists specifically to bound this risk before graph results gate releases.

## 21. Implementation task checklist — sub-steps
| Sub-step | Outcome |
| --- | --- |
| STEP-026.01 | GitNexus workflow wiring and freshness checks *(partially done)* |
| STEP-026.02 | Code graph schema and extraction gap reporting |
| STEP-026.03 | Contract, migration, IaC and model-registry extractors |
| STEP-026.04 | Requirement/ScopeStep linkage from `docs/product/` |
| STEP-026.05 | Incremental commit-diff loading with tombstoning |
| STEP-026.06 | CI refresh workflow (≤10 min) and release graph tagging |
| STEP-026.07 | Domain graph schema and construction |
| STEP-026.08 | Permission-aware traversal and query API |
| STEP-026.09 | Graph explorer and impact UI |
| STEP-026.10 | Quality gates, precision sampling, correction-to-test loop |
| STEP-026.11 | Deletion propagation into the domain graph |

## 22. Test and evaluation plan
`TST-KG-001` … `TST-KG-008`. Permission tests must prove no existence leakage. Extractor regression tests are generated from human corrections. **`TST-KG-008` — merge blocked without a pre-change record — is the gate that makes the whole protocol real.**

## 23. Deployment, feature flag and migration plan
Graph refresh runs in CI. The domain-graph store decision (Neo4j vs. PostgreSQL recursive queries) is deliberately made at this step's design review, against measured traversal depth.

## 24. Rollback, compensation and recovery plan
Code graph is **fully reconstructible** — recovery is one index run. Domain graph rebuilds from PostgreSQL and the event log. Release graphs are backed up because they cannot be regenerated identically after refactoring.

## 25. Acceptance criteria
- [ ] ≥95% of first-party source files parsed; exclusions explicit (`REQ-KG-001`)
- [ ] ≥90% of public symbols linked to an owner or parent module (`REQ-KG-002`)
- [ ] Default-branch graph refreshes within 10 minutes of merge (`REQ-KG-003`)
- [ ] Release graphs immutable and tagged (`REQ-KG-004`)
- [ ] Every node and inferred edge carries extractor version, source location, commit, confidence (`REQ-KG-005`)
- [ ] Traversal enforces repository, tenant and source authorization (`REQ-KG-006`)
- [ ] No secrets, payloads or restricted code in properties or embeddings (`REQ-KG-007`)
- [ ] **No change merges without a completed pre-change record** (`REQ-KG-008`)

## 26. Evidence required for completion
Coverage report; ownership report; refresh timing; permission leakage test; precision sampling result; a blocked-merge demonstration proving `TST-KG-008` works.

## 27. Open questions, risks and decisions
`RISK-014` — the graph covers documentation only; every coverage gate is currently **not evaluable**. Domain-graph store undecided. Edge precision threshold unset, so impact results cannot yet gate releases.

## 28. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Sub-steps completed | 0 of 11 (`.01` partially delivered) |
| Regression result | — |
| Verified by | — |
