# JourneyLab — Cost and Capacity Management

| Field | Value |
| --- | --- |
| Owner | Engineering + Finance (unassigned — `BLK-001`) |
| Status | `DISCOVERY` — **no cost model, no capacity projection, no target margin** |
| Blocking | `RISK-003` stop condition is **currently unmeasurable** because the target contribution margin is undefined (`DEC-003`) |
| Last reviewed | 2026-08-05 |

Navigation: [NFRs](../03-architecture/NON_FUNCTIONAL_REQUIREMENTS.md) · [Success metrics](../01-product/SUCCESS_METRICS.md) · [Deployment](../03-architecture/DEPLOYMENT_ARCHITECTURE.md) · [Performance testing](../06-quality/PERFORMANCE_AND_RESILIENCE_TESTING.md) · [00-START-HERE](../00-START-HERE.md)

---

## 1. The unit that matters

**`KPI-007` — cost per saved feasible trip.** Not cost per user, per request or per month. A trip that never produced a feasible scenario consumed cost and delivered nothing, and the metric must reflect that.

```
cost_per_saved_trip = (llm_cost + provider_cost + compute_cost + storage_cost)
                      / trips_with_a_saved_feasible_scenario
```

**Guardrail (non-negotiable):** quality, latency and diversity thresholds stay **fixed** during cost optimisation. Cost may not be reduced by weakening citations, cutting scenario diversity below three, or relaxing hard constraints.

---

## 2. Cost drivers

| Driver | Behavior | Lever | Risk of the lever |
| --- | --- | --- | --- |
| **Provider API calls** | Per place/route/forecast lookup | Cache evidence and travel matrices | Cache duration is licence-limited (`ASM-019`); over-caching breaches terms |
| **Solver compute** | CPU-bound, superlinear with candidates | Cap candidate count; time-box solving | Fewer candidates can reduce scenario diversity (`RISK-002`) |
| **Simulation compute** | Linear in samples | Reduce samples | Widens confidence intervals — acceptable **if disclosed** |
| **LLM tokens** | Per brief parse and explanation | Route by task; smaller models for extraction; cache explanations | Quality gates must hold (`AI-001` accuracy, `AI-003` groundedness) |
| **Embeddings** | Per evidence chunk | Embed only what retrieval needs | Recall loss |
| **Storage** | Immutable evidence packs accumulate | Retention policy on superseded packs | Reproducibility window shortens (`ADR-004`) |
| **Graph refresh** | Per merge | Incremental indexing | None — already incremental |
| **Egress and tiles** | Per map session | Lazy-load; list-first | None — list view is already required |

**The structural insight:** the deterministic architecture is the cost strategy. CP-SAT solving and cached matrices are far cheaper per decision than an LLM-orchestrated planning loop would be, which is why `ADR-002` is a cost decision as much as a correctness one.

---

## 3. Budgets

| Budget | Target | Enforcement | Status |
| --- | --- | --- | --- |
| Per-request AI cost | Per capability | Model gateway; degrade rather than exceed | **Unset** |
| Per-trip AI cost | Aggregate | Trace aggregation | **Unset** |
| Provider quota | Per provider, per environment | Quota budget in the connector | **No provider selected** |
| Solver CPU/memory per job | Explicit limits | Worker resource limits | **Unset** |
| Storage growth | Per month | Lifecycle policies | **Unset** |
| Total infrastructure | Per month | Cloud budget alerts | **No cloud provider** (`DEC-007`) |

Every budget is unset because there is no baseline. Inventing them would produce numbers people plan against; the gap is recorded instead (`EV-GAP-006`).

---

## 4. Capacity planning

**No projection exists** (`ASM-002` — team size, budget, launch scale all unspecified).

| Input needed | Drives |
| --- | --- |
| Expected trips per day | Solver pool size, provider quota |
| Peak concurrency | Burst capacity, queue depth |
| Trips per active user | Storage growth, retention cost |
| Destination pack size | Evidence storage, embedding cost, pack-build latency |
| Scenario regeneration rate | Compute multiplier — often underestimated, since edits and stale packs trigger re-solves |
| Geographic distribution | Region strategy, residency |

---

## 5. Monitoring

| Metric | Alert | Owner |
| --- | --- | --- |
| Cost per saved feasible trip | `ALRT-COST-001` over budget | Engineering |
| AI cost per trip | Budget breach | AI/ML |
| Provider quota consumption | Approaching limit | Data |
| Solver pool utilisation | Sustained saturation | Backend |
| Storage growth rate | Trend deviation | SRE |
| Cost per region | Anomaly | Finance |

**Cost is reviewed weekly against quality.** A cost improvement that coincides with a quality decline is a regression, not a saving — which is why the dashboards place the guardrail next to the metric.

---

## 6. Optimisation sequence

Cheapest and safest first; each step is measured before the next:

1. **Cache aggressively within licence limits** — travel matrices, evidence lookups, coverage.
2. **Right-size workers** — solver and simulation resource limits from measured usage.
3. **Route models by task** — a small model for extraction, a larger one only where quality demands it.
4. **Reduce simulation samples** before touching scenario count.
5. **Prune storage** — retire superseded evidence packs past the reproducibility window.
6. **Only then** revisit scenario count, and never below three.

**Never on the list:** reducing citations, hiding uncertainty, weakening hard constraints, or removing the accessible fallback paths.

---

## 7. Status

| Item | Status |
| --- | --- |
| Cost model | Does not exist |
| Baseline measurement | Impossible — no traces (`EV-GAP-006`) |
| Target contribution margin | **Undefined** (`DEC-003`) |
| Capacity projections | None (`ASM-002`) |
| Budget alerts | Not configured |
| `RISK-003` stop condition | **Currently unmeasurable** — a gap that must close before Phase 1 exit |
