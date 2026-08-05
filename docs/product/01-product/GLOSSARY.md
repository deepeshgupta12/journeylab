# JourneyLab — Glossary

| Field | Value |
| --- | --- |
| Owner | Product Architect (unassigned — `BLK-001`) |
| Status | `READY` — terminology stable; extend via pull request |
| Upstream source | Blueprint Appendix B, §12 (data model), §20 (knowledge graphs) |
| Last reviewed | 2026-08-05 |

Navigation: [Charter](PRODUCT_CHARTER.md) · [Scope](PRODUCT_SCOPE.md) · [Data contracts](../04-contracts/DATA_CONTRACTS.md) · [KG schema](../05-knowledge-graph/KNOWLEDGE_GRAPH_SCHEMA.md) · [00-START-HERE](../00-START-HERE.md)

---

## 1. Product domain terms

| Term | Definition | Notes |
| --- | --- | --- |
| **TripBrief** | Confirmed, typed, immutable representation of dates, people, budget, commitments, hard constraints and preferences. | Versioned. A new brief creates a new version; it never mutates in place. `DATA-005` |
| **Hard constraint** | A condition that makes a plan invalid if violated (dates, mobility limits, booked commitments, maximum daily spend). | Owned by the deterministic solver. Never traded off. |
| **Soft constraint / preference** | A weighted objective (interests, pace, crowd tolerance, scenic value). | Influences ranking, never feasibility. |
| **Inferred constraint** | A constraint the system derived rather than the user stating it. | Must be visibly labelled and user-editable (`REQ-CONS-001`). |
| **Unresolved constraint** | A stated input the system could not type confidently. | Triggers a blocking clarification only if it affects feasibility. |
| **EvidenceFact** | Atomic, time-aware claim with value, unit, source, observed time, effective time, confidence and access label. | `DATA-007`. The only fact type a solver may consume. |
| **EvidencePack** | Immutable collection of EvidenceFacts plus a coverage report, used by one scenario-generation run. | `DATA-008`. Guarantees reproducibility. |
| **Observed time** | When the fact was retrieved from its source. | Distinct from effective time. |
| **Effective time** | The period during which the fact is true in the world (e.g. summer opening hours). | A fact can be freshly observed yet not effective for the trip dates. |
| **Freshness policy** | Field-specific expiry rule. Hours and disruptions expire faster than descriptions. | `REQ-DATA-005` |
| **Candidate** | An eligible activity, route or lodging anchor with ranking features and exclusion reasons. | `DATA-009`. Produced before optimisation. |
| **Scenario** | A feasible itinerary optimised for a named objective and reproducible from stored inputs, solver config, model versions and seed. | `DATA-010` |
| **ScenarioVersion** | Immutable itinerary DAG with costs, scores, constraints and a change explanation. | `DATA-011`. Edits create versions; they never overwrite. |
| **Objective label** | Deterministic scenario name — `balanced`, `low_cost`, `low_effort`, `weather_resilient`. | Labels are contract values, not model-generated prose. |
| **Fragility** | Sensitivity of a scenario to plausible changes in time, price, weather or provider conditions. | Output of Monte Carlo simulation, shown as a confidence band. |
| **Minimal conflict set** | The smallest set of constraints whose combination makes the problem infeasible. | Returned instead of a plan when no solution exists (`REQ-CONS-005`). |
| **Canonical plan** | The traveler-approved ScenarioVersion used for booking handoff and live monitoring. | Changing it always requires explicit approval. |
| **Protected item** | An itinerary item locked against automated change — booked, confirmed or user-pinned. | Frozen during edits and replans. |
| **Partial replan** | Recomputation limited to affected nodes while protecting completed, booked and explicitly locked items. | Measured by preserved-plan percentage (`KPI-005`). |
| **ImpactEvent** | A deduplicated observed change (closure, delay, weather) with severity, confidence, evidence and affected graph nodes. | `DATA-014` |
| **Offline pack** | Downloaded itinerary, map metadata, ticket references and critical evidence usable without network for ≥72 h. | `REQ-LIVE-001` |
| **Destination pack** | The curated, licensed evidence corpus for one supported region. | Unit of geographic expansion. |
| **Booking handoff** | Deep link to a third-party provider with itinerary context, plus an attribution record. | No payment credentials stored (`REQ-BOOK-002`). |
| **Coverage report** | Machine-readable statement of what the evidence pack could and could not establish. | Drives confidence and blocking. |

---

## 2. Architecture and platform terms

| Term | Definition |
| --- | --- |
| **Modular monolith** | Single deployable application with enforced internal module boundaries, plus isolated compute workers. The documented MVP topology. |
| **Transactional outbox** | Pattern where a domain event is written in the same database transaction as the state change, then published asynchronously. Guarantees no lost or phantom events. |
| **Durable workflow** | A long-running, retryable, resumable business process (Temporal). Distinct from a queued task. |
| **Model gateway** | Provider-neutral boundary applying budgets, structured schemas, timeouts, fallbacks and tracing to every model call. |
| **Deterministic boundary** | The line beyond which model output cannot pass without validation. Money, capacity, eligibility, permissions and workflow state are always on the deterministic side (`CON-004`). |
| **Job handle** | The `{job_id, status, events_url}` triple returned within 500 ms for long-running work, replacing a blocking response. |
| **Expand/migrate/contract** | Three-phase schema migration keeping old and new readers valid throughout the rollout window. |
| **Read model** | A denormalized projection rebuildable from the event log. |
| **Circuit breaker** | Automatic provider isolation after a failure threshold, preventing unmarked stale data from entering plans. |

---

## 3. AI, retrieval and evaluation terms

| Term | Definition |
| --- | --- |
| **Hybrid retrieval** | Combined lexical (names, codes) and dense (intent) retrieval, fused and reranked, with geospatial, temporal and permission filters applied before ranking. |
| **Corrective retrieval** | Detecting low coverage or low source agreement and responding with a second retrieval pass, an uncertainty statement or a blocking question — never model-memory backfill (`REQ-AI-004`). |
| **GraphRAG** | Retrieval that traverses a knowledge graph for multi-hop evidence, subject to the caller's permissions. |
| **Claim-to-source span** | A link from a specific sentence in generated prose to the exact evidence span supporting it. Evaluated independently of prose quality. |
| **Groundedness** | Whether every factual claim in an output is supported by retrieved evidence. |
| **Abstention** | The system declining to answer or blocking an option when evidence is insufficient. A success behavior, not a failure. |
| **Gold set** | Human-verified evaluation dataset defining correct behavior. |
| **Adversarial set** | Evaluation dataset of injection attempts, contradictions, stale facts, ambiguous locales and edge cases. |
| **Champion/challenger** | Promotion gate comparing a candidate model against the incumbent on fixed datasets before rollout. |
| **Calibration** | Whether stated confidence matches observed accuracy. An uncalibrated confidence band is a defect. |
| **Prompt injection** | Untrusted content attempting to issue instructions to the model. Retrieved text, documents and MCP tool descriptions are all untrusted (`REQ-SEC-006`). |
| **CP-SAT** | Constraint-programming satisfiability solver (OR-Tools) used for schedule feasibility and multi-objective optimisation. |
| **Monte Carlo simulation** | Repeated sampling over price, duration, weather and disruption distributions to produce confidence intervals and fragility. |
| **Maximal marginal relevance (MMR)** | Diversification method preventing scenario sets that differ only cosmetically. |

---

## 4. Knowledge-graph terms

| Term | Definition |
| --- | --- |
| **Domain graph** | Product-fact graph explaining decisions, evidence, dependencies and lifecycle effects. Tenant-scoped. |
| **Code graph** | Repository graph explaining implementation, data/model lineage and runtime impact. Repository-permission-scoped. |
| **Blast radius** | The full set of nodes affected by a proposed change, scored by likelihood, severity, reach, detectability, reversibility, confidence and customer criticality. |
| **Pre-change check** | Mandatory graph query performed *before* implementation begins (`REQ-KG-008`). |
| **Post-change verification** | Re-index at the implementation commit and diff the neighborhood against the pre-change snapshot. |
| **Tombstone** | Marking a removed symbol as deleted rather than dropping it, preserving history. |
| **Extraction gap** | A file or symbol the extractor could not parse. Must be visible, never silently skipped. |
| **Inferred edge** | A relationship derived by heuristic rather than exact identifier match. Requires provenance and confidence; correctable by humans. |
| **Release graph** | Immutable, tagged graph snapshot taken at a release commit. |
| **Static fallback** | Repository search, contract, manifest and test inspection used when the graph is unavailable. Does **not** satisfy the release gate. |

---

## 5. Status and governance vocabulary

| Term | Definition |
| --- | --- |
| `NOT_STARTED` / `DISCOVERY` / `READY` / `IN_PROGRESS` / `BLOCKED` / `IN_REVIEW` / `VERIFIED` / `RELEASED` / `DEFERRED` / `NOT_APPLICABLE` | The only permitted delivery statuses. Defined in [MASTER_TRACKER](../02-delivery/MASTER_TRACKER.md). |
| **Confirmed product decision** | Stated in the blueprint or an approved ADR. Binding. |
| **Source-supported fact** | Backed by a cited external source, with publisher and date shown. |
| **Assumption requiring validation** | Plausible but untested. Tracked in [ASSUMPTION_REGISTER](../02-delivery/ASSUMPTION_REGISTER.md). Never cited as fact. |
| **Proposal requiring approval** | Recommended by this documentation set but not yet accepted by an owner. |
| **Stop condition** | A pre-agreed circumstance under which work halts rather than continues. Contractual, not rhetorical. |
| **Four-eyes approval** | Two distinct authorized humans required; the actor cannot be an approver. |
| **Documentation freshness** | Whether a document's `Last reviewed` date is within its review interval and consistent with the release commit. |
</content>
