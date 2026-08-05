# JourneyLab — Performance and Resilience Testing

| Field | Value |
| --- | --- |
| Owner | SRE + Backend (unassigned — `BLK-001`) |
| Status | `DISCOVERY` — no tests; **no capacity projections exist** (`ASM-002`) |
| Upstream source | Blueprint §16 (performance, resilience), §15 (SLOs) |
| Last reviewed | 2026-08-05 |

Navigation: [NFRs](../03-architecture/NON_FUNCTIONAL_REQUIREMENTS.md) · [Test strategy](TEST_STRATEGY.md) · [Backup & DR](../07-operations/BACKUP_RESTORE_AND_DR.md) · [Cost & capacity](../07-operations/COST_AND_CAPACITY_MANAGEMENT.md) · [00-START-HERE](../00-START-HERE.md)

---

## 1. Performance test types

| Type | Purpose | Target | Frequency |
| --- | --- | --- | --- |
| **Load** | Sustained expected traffic | `REQ-NFR-002` p95 ≤ 400 ms reads; `REQ-NFR-004` p95 ≤ 45 s generation | Pre-release |
| **Stress** | Find the breaking point | Degrades gracefully; no data corruption | Pre-release |
| **Burst** | Sudden concurrency spike | Job handles still returned within 500 ms | Pre-release |
| **Soak** | 24 h sustained | No memory growth, connection leak or queue drift | Pre-release |
| **Queue saturation** | Generation backlog | Back-pressure applies; users see honest queue status, not a silent hang | Pre-release |
| **Geospatial query** | PostGIS under load | Within read budget | Per schema change |
| **Graph traversal** | Multi-hop impact queries | Within budget at realistic depth | Per graph change |
| **Model concurrency** | Parallel LLM calls | Budget respected; failover works | Per AI change |
| **Provider throttling** | Quota exhaustion | Circuit break; marked-stale degradation | Pre-release |
| **Frontend** | Core Web Vitals on mid-tier mobile/4G | `REQ-NFR-013` | Every release |

---

## 2. Scenario-generation performance — the hard one

`REQ-NFR-004` (p95 ≤ 45 s) is the product's most demanding and most fragile budget, and it composes several unbounded components.

| Component | Contribution | Lever if over budget |
| --- | --- | --- |
| Evidence pack build | Provider-latency-bound | Cache; parallel fetch; pre-warm popular regions |
| Travel matrix | O(places²) | Cache by mode/window; cap candidate count |
| CP-SAT solve | **Unbounded in theory** | Time-boxed solving returning best-known feasible |
| Monte Carlo | Linear in samples | **Reduce sample count first** — widens intervals honestly rather than breaching latency |
| Diverse ranking | Small | — |

**Degradation order, fixed in advance so it is not decided under pressure:**
1. Reduce simulation samples (widen the stated confidence interval).
2. Reduce scenario count (from 5 toward 3 — never below 3, which is `REQ-CONS-007`).
3. Return best-known feasible solutions with the optimality gap disclosed.
4. **Never** relax hard constraints. **Never** return an unvalidated plan.

Test matrix: 3/5/7-day trips × 3/4/5 scenarios × sparse/dense destination packs, with seeds pinned so results are comparable across runs.

---

## 3. Resilience (chaos) tests

| Scenario | Injected | Expected behavior | Requirement |
| --- | --- | --- | --- |
| Provider outage | Places provider returns 5xx | Circuit break; cached data **marked stale**; options needing fresh hours blocked; coverage shows degraded | `TST-DATA-003`, `TST-EVID-006` |
| Stale data | Clock advanced past freshness thresholds | Facts marked stale; confidence lowered; user sees staleness at point of use | `TST-EVID-005` |
| Duplicate events | Same event delivered twice | Idempotent consumers; no duplicate effect or notification | `TST-DATA-009` |
| Model timeout | Gateway hangs | Budget enforced; failover then non-AI fallback | `TST-AI-007`, `TST-AI-008` |
| Queue delay | Outbox publisher paused | Back-pressure; alert; replay from checkpoint on recovery | `RB-QUEUE-001` |
| Corrupted cache | Poisoned entries | Detected; not the sole source of truth; recovered from primary | — |
| Region loss | Availability-zone/region failure | Multi-zone continues; region loss recovers from backup within stated RTO | `BACKUP_RESTORE_AND_DR` |
| Solver pool exhaustion | All workers busy | Honest queue status with cancel; new generations refused rather than silently timing out | `RB-SOLVER-001` |
| Database failover | Primary killed | Managed failover; retries with backoff; no data loss | — |
| Partial provider data | Half the places missing | Coverage report identifies gaps; **no fabricated candidates** | `TST-CONS-003` |
| Offline sync conflict *(P3)* | Divergent offline and server edits | Conflict surfaced visibly; user resolves; nothing silently overwritten | `TST-LIVE-002` |

**Every drill asserts the same invariant: the system degrades honestly.** The failure this product cannot tolerate is quietly producing a plausible plan from bad or missing data.

---

## 4. Drill schedule

| Drill | Frequency | Owner |
| --- | --- | --- |
| Provider outage | Every release | Data |
| Stale data | Every release | Data |
| Model failure/fallback | Every release | AI/ML |
| Solver saturation | Every release | Backend |
| Backup restoration | **Quarterly** | SRE |
| Offline-sync conflict *(P3)* | **Quarterly** | Frontend |
| Deletion propagation | Every release | Privacy |
| Full DR | Before GA, then annually | SRE |

---

## 5. Capacity assumptions

**None exist.** No user or volume projection has been made (`ASM-002`). Load-test parameters must be derived from real projections before Phase 1 exit; inventing them here would produce a test that proves nothing about production.

What can be tested now, once code exists, without projections: relative scaling behavior, degradation ordering, resource limits per worker, and whether back-pressure functions.

---

## 6. Status

| Item | Status |
| --- | --- |
| `tests/resilience/` | Does not exist |
| Load-test harness | Does not exist |
| Performance baselines | Not measured |
| Drill records | None |
| Capacity projections | **Missing — blocks meaningful load testing** |
