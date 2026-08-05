# JourneyLab — Operations and Support

| Field | Value |
| --- | --- |
| Owner | SRE + Support Lead (unassigned — `BLK-001`) |
| Status | `DISCOVERY` — no service is running |
| Upstream source | Blueprint §18 (deployment, operations, support) |
| Last reviewed | 2026-08-05 |

Navigation: [Observability](../03-architecture/OBSERVABILITY_ARCHITECTURE.md) · [Runbooks](RUNBOOK_INDEX.md) · [Incident response](INCIDENT_RESPONSE.md) · [Backup & DR](BACKUP_RESTORE_AND_DR.md) · [00-START-HERE](../00-START-HERE.md)

---

## 1. Service ownership

**Every deployable unit needs an owner, SLOs, dashboards, alerts, a runbook, a rollback path and documented deletion behavior before GA** (portfolio standard §4.23).

| Service | Owner role | SLO | Runbook |
| --- | --- | --- | --- |
| Web / PWA | Frontend Lead | Core Web Vitals budgets | RB-FE-001 |
| API application | Backend | p95 ≤ 400 ms; 99.9% availability | RB-API-001 |
| Identity | Security | p95 ≤ 200 ms; fail closed | RB-AUTH-001 |
| Evidence builder | Data | Pack build p95 ≤ 20 s | RB-DATA-001 |
| Integrations/ingestion | Data | Per-provider freshness SLO | RB-PROV-001 |
| Solver / simulation | Backend | Generation p95 ≤ 45 s | RB-SOLVER-001 |
| Retrieval / AI | AI/ML | Per-capability budget | RB-AI-001 |
| Events / outbox | Backend | Publish lag p95 ≤ 5 s | RB-QUEUE-001 |
| Privacy | Privacy Owner | Deletion within policy window | RB-PRIV-001 |
| Knowledge graph | Platform | Refresh ≤ 10 min post-merge | RB-KG-001 |
| Affiliate | Backend | p95 ≤ 500 ms | RB-PROV-002 |
| Live *(P3)* | Backend | Impact match p95 ≤ 60 s | RB-LIVE-001 |

**All owners unassigned (`BLK-001`).** A service with no owner cannot go to production.

---

## 2. Support hours and escalation

**Undecided** — support model, hours and on-call rotation are open (`DEC-006` adjacent). Required before GA:

| Question | Status |
| --- | --- |
| Support hours (business vs. 24/7) | Open |
| On-call rotation and compensation | Open |
| First-response and resolution targets by severity | Open |
| Escalation path to engineering | Open |
| User-facing support channel | Open |

**Consumer travel product note:** users need help *while travelling* — in another time zone, possibly offline, possibly mid-disruption. A business-hours-only model is likely incompatible with the Phase 3 live companion, and that tension should be resolved before Phase 3 rather than during it.

---

## 3. Support diagnostics

| Principle | Implementation |
| --- | --- |
| **Tenant-safe by default** | Diagnostic bundles contain source and version IDs, correlation IDs and state transitions — **not raw sensitive payloads** |
| Single-trip scope | Reconstructing one trip must never require unrestricted tenant access (`REQ-ADMIN-005`) |
| Audited | Every support access is logged with actor, scope and reason |
| Escalation for raw data | Viewing raw trip content requires explicit, time-boxed, audited elevation with a recorded justification |

**Diagnostic bundle contents:** correlation ID, trip state timeline, brief version, evidence pack ID + coverage report, solver config + seed + optimality gap, model/prompt versions, provider health at the time, error codes, feature-flag state.

**What it deliberately excludes:** constraint values, evidence prose, place names as free text, location, booking references, personal identifiers.

That exclusion list is what makes it possible to debug a user's trip without reading their private plans.

---

## 4. Degraded operation modes

| Mode | Trigger | Behavior | User-visible |
| --- | --- | --- | --- |
| **Provider degraded** | Circuit breaker open | Cached data marked stale; options needing fresh facts blocked | Region shows degraded; staleness at point of use |
| **Coverage suspended** | Critical provider unavailable | New trips refused for that region | Honest refusal, no partial simulation |
| **AI disabled** | Budget breach or provider outage | Structured forms; templated explanations | Reduced assistance; core tasks unaffected |
| **Solver saturated** | Pool exhausted | Queue with honest status and cancel | "Queued, N ahead" — never a silent spinner |
| **Read-only** | Database degradation | Existing plans readable; no new generation | Explicit banner |
| **Map unavailable** | Tile provider down | List/table comparison | Fully functional (`REQ-A11Y-003`) |

**Every degraded mode discloses itself.** The prohibited failure is looking healthy while producing unreliable plans.

---

## 5. Routine operations

| Task | Frequency | Owner |
| --- | --- | --- |
| Provider health and quota review | Daily | Data |
| Evidence freshness review | Daily | Data |
| Error budget review | Weekly | SRE |
| Cost per saved trip review | Weekly | Engineering + Finance |
| AI quality review (citations, abstention) | Weekly | AI/ML |
| Deletion queue review | Daily | Privacy |
| Graph coverage review | Per release | Platform |
| Backup restoration drill | Quarterly | SRE |
| Offline-sync conflict drill *(P3)* | Quarterly | Frontend |
| Runbook rehearsal | Quarterly | Owning team |
| Access review | Quarterly | Security |

---

## 6. Operational controls

| Control | Purpose | Authorization |
| --- | --- | --- |
| Provider disable | Stop ingesting from a failing/wrong source | Ops admin, audited |
| Model rollback | Revert a regressed model/prompt | AI/ML, audited |
| Feature flag | Disable a feature without deploy | Ops admin, audited |
| Notification suppression | Stop a notification storm | Ops admin, audited |
| Scenario regeneration | Rebuild after a fact correction | Curator/Ops, audited |
| Destination override | Correct a fact with an effective period | Curator; **four-eyes for high impact** |
| Region suspension | Stop new trips for a region | Ops admin, audited |

---

## 7. Status

Nothing is operational. Every runbook, dashboard, alert and rotation is `PROPOSED`, created in `STEP-024`. The support model itself is an open decision that must close before GA.
</content>
