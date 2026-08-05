# JourneyLab — Test Strategy

| Field | Value |
| --- | --- |
| Owner | Engineering + QA (unassigned — `BLK-001`) |
| Status | `DISCOVERY` — strategy defined; **no tests exist** |
| Upstream source | Blueprint §16 (testing and evaluation strategy) |
| Last reviewed | 2026-08-05 |

Navigation: [Acceptance tests](ACCEPTANCE_TEST_CATALOG.md) · [AI evaluation](AI_ML_EVALUATION.md) · [Security testing](SECURITY_TESTING.md) · [Performance & resilience](PERFORMANCE_AND_RESILIENCE_TESTING.md) · [Release readiness](RELEASE_READINESS_CHECKLIST.md) · [00-START-HERE](../00-START-HERE.md)

---

## 1. Principles

1. **A requirement without a test is not a requirement** — it is an intention. All 130 requirements map to a test ID.
2. **Test the prohibitions.** Requirements phrased "must not" need adversarial tests; absence of a positive case proves nothing.
3. **The regression suite is a ratchet.** Coverage may improve or hold; it may never worsen (checks R4/R5).
4. **Every fixed bug adds a permanent regression test** (R6).
5. **Determinism where it matters.** Solver and simulation tests pin seeds; a flaky feasibility test is a defect, not noise.
6. **Never disable a failing test to go green.**

---

## 2. Test layers

| Layer | Scope | Runs | Owner |
| --- | --- | --- | --- |
| **Unit** | Business rules, calculations, parsers, mappers, scoring, UI state, accessibility utilities | Every commit | Author |
| **Component** | Design-system primitives with all quality states | Every commit | Frontend |
| **Contract** | OpenAPI/AsyncAPI compatibility, generated clients, schema evolution, provider adapters, webhook signatures | Every commit + pre-release | Architect |
| **Integration** | Database, cache, graph, object store, queue, identity provider, model gateway, third-party sandbox | Every sub-step | Backend |
| **End-to-end** | Golden journeys across desktop, mobile and assistive technology, including refresh, retry, partial failure, interrupted session | Pre-push + pre-release | QA |
| **Data quality** | Schema, freshness, completeness, uniqueness, referential integrity, drift, reconciliation | Per ingestion run | Data |
| **ML** | Leakage, backtests, calibration, subgroup performance, uncertainty, drift, reproducibility, champion/challenger | Per model change | AI/ML |
| **LLM/RAG** | Retrieval recall, citation correctness, groundedness, tool selection, adversarial injection, refusal, latency, cost | Per prompt/model/retrieval change | AI/ML |
| **Security** | SAST, DAST, dependency/container/IaC scanning, authorization fuzzing, tenant isolation, secret detection | Every commit + annual pen test | Security |
| **Performance** | Load, soak, burst, queue saturation, geospatial query, graph traversal, model concurrency, provider throttling | Pre-release | SRE |
| **Resilience** | Provider failure, stale data, duplicate events, model timeout, queue delay, region loss, corrupted cache | Pre-release + quarterly drill | SRE |
| **Migration** | Expand/migrate/contract forward and backward, with data | Per migration | Data |
| **Backup/restore** | Restoration to a working system | Quarterly | SRE |
| **Deletion** | Traversal proof across every store | Every release | Privacy |

---

## 3. Product-specific test priorities

These are where this product's real defects will live — generic coverage will not find them.

| Priority | Area | Why | Method |
| --- | --- | --- | --- |
| 1 | **Hard-constraint enforcement** | A violation is S1 and is the product's core promise | Property-based tests generating adversarial constraint combinations; zero violations across the full corpus |
| 2 | **Infeasibility handling** | Must return a minimal conflict set, never a plausible-looking invalid plan | Deliberately unsatisfiable briefs; assert conflict-set minimality |
| 3 | **Temporal correctness** | Three time axes plus DST and time zones | Golden fixtures spanning DST transitions, seasonal hours, cross-zone travel |
| 4 | **Evidence freshness and staleness display** | Stale data presented as current destroys trust | Clock-controlled tests; provider outage drills |
| 5 | **Citation correctness** | ≥95% release gate, evaluated independently of prose quality | Claim-to-span dataset |
| 6 | **Tenant isolation** | R7, non-negotiable | Fuzzing across API, cache, jobs, exports, graph |
| 7 | **Map-free accessibility** | All MVP tasks with map disabled | Automated axe + manual screen-reader journeys |
| 8 | **Deletion completeness** | Must traverse vector, graph and cache stores | Seed data in every store, delete, assert absence |
| 9 | **Reproducibility** | Same inputs + seed ⇒ same scenarios | Repeat-run equality assertions |
| 10 | **Prompt injection** | Retrieved content is untrusted | Adversarial corpus with embedded instructions |

---

## 4. Test data

| Kind | Source | Rule |
| --- | --- | --- |
| Synthetic fixtures | Generated | Default for all local and CI testing |
| Sanitized provider payloads | Recorded, scrubbed | Success, empty, error, quota and schema-change cases |
| Golden destination packs | Curated per region | The corpus release gates are measured against |
| Adversarial sets | Curated | Injection, contradiction, staleness, locale ambiguity, impossible constraints |
| **Production personal data** | — | **Never used in any test environment** |

---

## 5. Mapping to requirements

Every requirement in [FUNCTIONAL_REQUIREMENTS](../01-product/FUNCTIONAL_REQUIREMENTS.md) has a `TST-*` ID in [ACCEPTANCE_TEST_CATALOG](ACCEPTANCE_TEST_CATALOG.md). The graph query `KG-Q-008` reports requirements with no test edge; that count is regression check **R4** and may never increase.

---

## 6. Execution tiers

| Tier | Contents | When |
| --- | --- | --- |
| **Fast** (target ≤ 10 min) | Unit, component, contract, R6 closed-bug tests, **R7 tenant isolation** | Every sub-step |
| **Full** | Fast + integration, e2e, data quality, ML/LLM evals | Pre-push, nightly |
| **Release** | Full + performance, resilience, security scans, deletion proof, DR check | Pre-release |

R7 and R6 are in the fast tier deliberately: isolation and previously-fixed bugs are the two things that must never regress silently even for ten minutes.

---

## 7. Current state

| Artifact | Status |
| --- | --- |
| `tests/unit/`, `tests/integration/`, `tests/e2e/`, `tests/contracts/`, `tests/security/`, `tests/resilience/`, `tests/evals/` | **None exist** |
| CI pipeline | Does not exist |
| Golden destination packs | Cannot be built — region undecided (`DEC-002`) |
| Test owners | Unassigned (`BLK-001`) |

Created in `STEP-027`; individual suites are built within the sub-steps that produce the code they cover.
</content>
