# BR-004 — Local development dependency stack

| Field | Value |
| --- | --- |
| Sub-step | STEP-001.04 |
| Requirements | REQ-PLAT-001, REQ-PLAT-002 |
| Author | Deepesh Kumar Gupta |
| Date | 2026-08-05 |

## 1. Intent
One documented command brings up PostgreSQL 18 + PostGIS + pgvector, cache, object store, queue and tracing locally — on a **port block that cannot collide with the other projects on this Docker host**.

## 2. Graph state
| Field | Value |
| --- | --- |
| HEAD / indexed commit | `28923aa` / `28923aa` — **matched, verified before starting** |
| Status | `BLOCKED` for application code — static fallback |

## 3. Impact
Local development environment only. No production surface, no application code, no contracts.

## 4. Environmental constraints DISCOVERED (not assumed)
Each was verified by execution, and several contradicted the plan:

| Finding | Evidence | Consequence |
| --- | --- | --- |
| Ports 3307/5433/6380/8080 live; 3000/3001/5460/5544/6379/8000/9090/27017 claimed by stopped projects | `docker ps`, `docker compose ls`, other projects' compose files | Reserved block **5700-5709** |
| **A stopped project still owns its ports** | 5544 read as free to `lsof` because Saakshya was stopped | Guard reads compose *files*, not just live sockets |
| Host is **arm64** | `uname -m` | Platform constraints below |
| `postgis/postgis:18-3.6` is **amd64-only** | `docker manifest inspect` | Emulated; ~3s to ready — acceptable |
| `postgis/postgis:17-*`, `16-*` have no arm64 either | manifest inspect | Downgrading PostgreSQL would not have helped |
| PGDG has **no** `postgresql-18-postgis` or `-pgvector` | apt search in both images | Package install impossible |
| postgis image repo carries only 4 packages, **no compiler** | `apt-cache pkgnames` | Source build impossible |
| **PG18 changed the volume mount point** | container refused to start | Mount `/var/lib/postgresql`, not `.../data` |
| `jaegertracing/all-in-one:1.62` does not exist | manifest inspect | Used `jaegertracing/jaeger:2.0.0` |

## 5. Resolution
Multi-stage build: PostGIS base + prebuilt pgvector copied from the pgvector image (both PostgreSQL 18.4). This preserves the **full blueprint baseline** — PG18 with both extensions — rather than downgrading PostgreSQL or dropping a required extension. Validated functionally, not just by presence.

## 6. Risk
| Dimension | 1–5 | Rationale |
| --- | --- | --- |
| Likelihood | 2 | Several assumptions already proved wrong; all found and fixed |
| Severity | 2 | Local environment only; no production or data impact |
| Reach | 2 | **Shared Docker host** — a port collision would break the user's other projects |
| Detectability | 1 | Services fail loudly; guard catches port drift |
| Reversibility | 1 | `pnpm dev:down`; compose is additive |
| **Confidence** | 2 | Every claim verified by execution |
| Customer criticality | 1 | None |

**Overall: LOW**

## 7. Post-change verification
| Check | Result |
| --- | --- |
| All 5 services healthy | **PASS** |
| PostgreSQL 18.4 + postgis 3.6.4 + vector 0.8.6 + pg_trgm 1.6 | **PASS** |
| Functional spatial + vector ops | **PASS** — 157 km geodesic; L2 5.196 (=√27) |
| Init SQL on fresh volume | **PASS** — 3 of 3 extensions |
| Host connectivity on documented ports | **PASS** — 5700-5707 |
| No collision with other projects | **PASS** — trekyatra retains 3307/5433/6380/8080 |
| Port guard meta-test | **PASS** — exit 1 on out-of-block port |
| `pnpm verify` | **PASS** — 12 checks |

## 8. Disposition
**Merged.** Follow-up: `.env.example` values are development-only; real secrets never enter the repository.
