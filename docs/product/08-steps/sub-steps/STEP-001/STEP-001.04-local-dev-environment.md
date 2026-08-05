---
sub_step_id: STEP-001.04
parent_step: STEP-001
title: Local dependency stack
status: NOT_STARTED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-PLAT-001]
blast_radius_id: BR-004
depends_on: [STEP-001.02]
last_updated: 2026-08-05
---

# STEP-001.04 — Local dependency stack

## 1. Outcome
An engineer starts PostgreSQL/PostGIS, cache, object store, queue and observability locally with one documented command, and the application connects to all of them.

## 2. Scope and boundary
**In scope:** `docker-compose.dev.yml`, local environment template, health checks, seed-free bootstrap.
**Not in this sub-step:** schema migrations (`STEP-006`), production infrastructure (`STEP-027`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test ID |
| --- | --- | --- |
| REQ-PLAT-001 | The documented command brings up all dependencies and the app connects | TST-PLAT-001 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | **BLOCKED — static fallback** |
| Queries run | KG-Q-015 |
| Direct dependents | Every future integration test |
| Unknown / low-confidence areas | Extension availability (PostGIS + pgvector) in the chosen image — verify, do not assume |
| Blast radius | BR-004 — LOW production reach, HIGH developer-experience reach |
| Approval required? | No |

## 5. Implementation plan
- [ ] `docker-compose.dev.yml` with PostgreSQL 18 + **PostGIS and pgvector extensions**
- [ ] Redis-compatible cache service
- [ ] S3-compatible object store
- [ ] Queue service (shape per `DEC-009`, substitutable)
- [ ] Local observability (OTel collector + viewer)
- [ ] Health checks on every service so startup failures are visible, not silent
- [ ] `.env.example` with **no real secrets**
- [ ] Document the single bring-up command in `README.md`

## 6. Contracts and schema changes
None. No migrations run at this sub-step.

## 7. Tests to add
| Test ID | Type | Asserts |
| --- | --- | --- |
| TST-PLAT-001 (partial) | CI/local | All services reach healthy state; extensions load |

## 8. Telemetry, security and accessibility
Local observability makes tracing available from day one. `.env.example` contains placeholders only; secret scanning covers it.

## 9. Documentation to update
- [ ] Sub-step completion record · `IMPLEMENTATION_LOG` · `REGRESSION_LOG` · `BR-004` · parent §21 · tracker
- [ ] `README.md` local setup section with troubleshooting

## 10. Regression cross-check (R1–R7)
| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression suite | | Includes `.01`, `.02` |
| R2–R7 | | As applicable |

## 11. Rollback
Remove the compose file; earlier sub-steps remain functional (they need no services).

## 12. Acceptance criteria
- [ ] One documented command starts every dependency
- [ ] PostGIS and pgvector extensions verified present
- [ ] All services report healthy
- [ ] No real secrets committed
- [ ] Troubleshooting documented for the common failures

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Commit SHA | — |
| Notes / surprises | — |
