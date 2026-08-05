# JourneyLab — Runbook Index

| Field | Value |
| --- | --- |
| Owner | SRE (unassigned — `BLK-001`) |
| Status | `DISCOVERY` — **no runbook exists**; all are `PROPOSED` |
| Rule | Every alert references a runbook; every runbook has an owner and a rehearsal date |
| Last reviewed | 2026-08-05 |

Navigation: [Operations](OPERATIONS_AND_SUPPORT.md) · [Incident response](INCIDENT_RESPONSE.md) · [Runbook template](../09-templates/RUNBOOK_TEMPLATE.md) · [Observability](../03-architecture/OBSERVABILITY_ARCHITECTURE.md) · [00-START-HERE](../00-START-HERE.md)

---

## Index

| ID | Runbook | Trigger / alert | Owner | Rehearsal | Status |
| --- | --- | --- | --- | --- | --- |
| RB-API-001 | API error budget burn / elevated 5xx | `ALRT-API-001` | Backend | Quarterly | `PROPOSED` |
| RB-AUTH-001 | Identity provider outage | Auth failure spike | Security | Quarterly | `PROPOSED` |
| RB-PROV-001 | Provider outage or quota exhaustion | `ALRT-PROV-001`, `EVT-008` | Data | **Every release** | `PROPOSED` |
| RB-PROV-002 | Affiliate partner failure | Handoff error rate | Backend | Quarterly | `PROPOSED` |
| RB-DATA-001 | Evidence freshness breach | `ALRT-DATA-001` | Data | Every release | `PROPOSED` |
| RB-DATA-002 | Stale or incorrect destination coverage | Coverage staleness alert | Data | Quarterly | `PROPOSED` |
| RB-SOLVER-001 | Solver saturation, timeout, or **hard-constraint regression** | `ALRT-SOLVER-001`, `ALRT-SOLVER-002` | Backend | Every release | `PROPOSED` |
| RB-SOLVER-002 | Sparse candidate pool / limited-choice state | Candidate recall alert | Backend | Quarterly | `PROPOSED` |
| RB-AI-001 | Model failure, budget breach, or citation-quality drop | `ALRT-AI-001` | AI/ML | Every release | `PROPOSED` |
| RB-AI-002 | Ranking service unavailable | Ranker health | AI/ML | Quarterly | `PROPOSED` |
| RB-QUEUE-001 | Outbox lag / dead-letter growth | `ALRT-QUEUE-001` | Backend | Quarterly | `PROPOSED` |
| RB-TRIP-001 | Trip state inconsistency | Manual/support escalation | Backend | Quarterly | `PROPOSED` |
| RB-TRIP-002 | Scenario generation stuck workflow | Workflow stuck alert | Backend | Quarterly | `PROPOSED` |
| RB-TRIP-003 | Collaboration conflict or invitation abuse | Abuse report | Backend | Quarterly | `PROPOSED` |
| RB-LIVE-001 | Notification storm or false impact matching *(P3)* | Notification rate alert | Backend | Quarterly | `PROPOSED` |
| RB-PRIV-001 | Deletion failure / DSR breach risk | `ALRT-PRIV-001` | Privacy | **Every release** | `PROPOSED` |
| RB-SEC-001 | Cross-tenant anomaly or suspected breach | `ALRT-SEC-001` (SEV1) | Security | Quarterly | `PROPOSED` |
| RB-KG-001 | Graph refresh lag / index corruption | `ALRT-KG-001` | Platform | Quarterly | `PROPOSED` |
| RB-COST-001 | Cost per trip over budget | `ALRT-COST-001` | Engineering | Quarterly | `PROPOSED` |
| RB-FE-001 | Frontend errors / accessibility regressions | `ALRT-A11Y-001` | Frontend | Quarterly | `PROPOSED` |
| RB-DR-001 | Backup restoration and disaster recovery | DR exercise / region loss | SRE | **Quarterly** | `PROPOSED` |
| RB-REL-001 | Release rollback | Canary abort | SRE | Every release | `PROPOSED` |

---

## Required structure

Every runbook uses [RUNBOOK_TEMPLATE](../09-templates/RUNBOOK_TEMPLATE.md): trigger, scope, customer impact, prerequisites, diagnosis, safe mitigation, rollback, verification, escalation, evidence preservation, retrospective actions.

---

## Runbook quality rules

1. **Written for 3 a.m.** — explicit commands, no assumed context, no "obviously".
2. **Diagnosis precedes mitigation.** A runbook that starts with "restart the service" teaches people to destroy evidence.
3. **Evidence preservation before mitigation** where the two conflict — capture the trace, the queue state, the failing payload.
4. **Every runbook is rehearsed.** An unrehearsed runbook is a document, not a capability.
5. **Rehearsal failures update the runbook**, and the update is the rehearsal's real output.
6. **Escalation is named** — a role and a path, not "escalate if needed".

---

## Product-specific runbook priorities

These matter more here than generic infrastructure runbooks, because they protect the product's core promise rather than its uptime:

| Runbook | Why it is first-tier |
| --- | --- |
| **RB-SOLVER-001** | A hard-constraint regression is S1 — users receive plans that do not work. Every dashboard can be green while this happens |
| **RB-PROV-001** | Provider failure is the most likely real incident, and the wrong response (serving cached data as current) causes user harm |
| **RB-DATA-001** | Freshness breaches are silent by nature |
| **RB-PRIV-001** | Deletion failures create legal exposure and are invisible without the retry queue |
| **RB-SEC-001** | Cross-tenant exposure halts everything |
| **RB-AI-001** | Citation quality is the trust mechanism; degradation is gradual and easy to miss |

---

## Status

No runbook has been written. They are produced in `STEP-024` and must exist, with owners and rehearsal records, before GA.
