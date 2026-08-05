# JourneyLab

**A trip digital twin for comparing feasible futures before and during travel.**

JourneyLab turns a traveler's intent and constraints into several evidence-backed,
*feasible* trip scenarios, makes the trade-offs visible on a synchronized map and
timeline, and maintains the chosen scenario as a live companion.

It is a **simulation and decision system, not a single-answer itinerary chatbot**.
Deterministic solvers own feasibility; the model explains and parses language.

| | |
| --- | --- |
| Status | **Pre-implementation** — foundation in place, no product code yet |
| Target release | Phase 1 MVP — one region, 3–7 day trips, deep-link booking handoff |
| Owner | Deepesh Kumar Gupta (`@deepeshgupta12`) |
| Documentation | **[docs/product/00-START-HERE.md](docs/product/00-START-HERE.md)** ← start here |
| Working agreement | **[CLAUDE.md](CLAUDE.md)** — read before changing anything |

---

## Prerequisites

| Tool | Version | Check |
| --- | --- | --- |
| Node.js | **24 LTS** (not 25+) | `node -v` |
| pnpm | 11+ | `pnpm -v` |
| uv | 0.10+ | `uv --version` |
| Docker | with Compose v2 | `docker compose version` |

> **Node 24 is installed keg-only via Homebrew and is _not_ on your PATH by default.**
> Every session that touches this repo needs:
> ```bash
> export PATH="/opt/homebrew/opt/node@24/bin:$PATH"
> ```
> Verify with `node -v` → `v24.x`. If you see v25+, the export did not apply.

---

## Setup

```bash
export PATH="/opt/homebrew/opt/node@24/bin:$PATH"   # Node 24 LTS
pnpm install                                        # JS workspace
uv sync                                             # Python 3.14 workspace
cp .env.example .env                                # local dev config
pnpm verify                                         # must be green
```

`pnpm verify` runs the full fast tier — 13 checks across guards, linting, formatting
and typechecking, for both JavaScript and Python. **It must pass before you change
anything**, so you know any later failure is yours.

## Local services

```bash
pnpm dev          # start the stack, wait for healthy
pnpm dev:logs     # follow logs
pnpm dev:down     # stop
pnpm dev:reset    # stop, destroy volumes, start fresh
```

JourneyLab reserves the contiguous port block **5700–5709**, all bound to
`127.0.0.1` so nothing is network-reachable. The block is chosen to avoid every
other project on this Docker host and enforced by `tests/guards/port-collisions.sh`.

| Port | Service | Notes |
| --- | --- | --- |
| 5700 | PostgreSQL 18.4 | PostGIS 3.6.4 + pgvector 0.8.6 + pg_trgm |
| 5701 | Redis 8 | cache, job progress, rate limits |
| 5702 | MinIO (S3 API) | object storage |
| 5703 | MinIO console | browser UI |
| 5704 | NATS JetStream | queue — `DEC-009` still open, deliberately substitutable |
| 5705 | OTLP gRPC | traces in |
| 5706 | OTLP HTTP | traces in |
| 5707 | Jaeger UI | trace viewer |

Connection strings are in [`.env.example`](.env.example).

> **PostgreSQL runs under amd64 emulation on Apple Silicon** (~3s to ready). No
> image publishes PG18 with both PostGIS and pgvector, and PostGIS has no arm64
> build for PG18, so `infra/local/postgres/Dockerfile` combines them. This
> preserves the PG18 baseline rather than downgrading.

---

## Repository map

```
apps/              web (Next.js) and api (FastAPI) surfaces          [STEP-002+]
packages/          ui, contracts, authz, analytics, observability    [STEP-003+]
services/          domain, data, retrieval, AI, ML, workflow         [STEP-005+]
contracts/         OpenAPI, AsyncAPI, JSON Schema                    [STEP-004]
db/                migrations, seeds, row-level security             [STEP-006]
infra/local/       local development images
tests/guards/      executable repository guards (run by pnpm verify)
docs/product/      the documentation system — scope, architecture, contracts
docs/adr/          architecture decision records
```

Module import boundaries are **enforced**: a cross-package import that reaches into
another package's `src/` fails the build (`ADR-003`).

## Data classifications

Handle according to [SECURITY_PRIVACY_RESPONSIBLE_AI](docs/product/03-architecture/SECURITY_PRIVACY_RESPONSIBLE_AI.md).

| Class | Examples | Rule |
| --- | --- | --- |
| **Sensitive** | Accessibility needs, age, precise location, travel documents, booking references | Never inferred from behavior; never used for advertising; segregated storage |
| **PII** | Identity, trips, itineraries, feedback | Tenant-scoped, deletable, exportable |
| **Licensed** | Places, hours, transit, weather, crowd signals | Cache duration and attribution governed by provider licence |
| **Derived** | Scenarios, candidates, impact events | Reproducible from inputs; deleted with the trip |
| **Internal** | Provider health, coverage, audit metadata | No customer payloads in telemetry or the code graph |

**No real secrets in the repository.** `.env` is gitignored; `.env.example` holds
development-only placeholder values.

---

## How work happens here

Read [CLAUDE.md](CLAUDE.md) and
[SUB_STEP_PROTOCOL](docs/product/02-delivery/SUB_STEP_PROTOCOL.md) before contributing.
In short:

1. **No change without a pre-change impact record** (`REQ-KG-008`).
2. **One sub-step at a time**, each ending in a regression cross-check, docs, commit, push.
3. **Regression cross-check R1–R7 before every commit** — previous work must not break.
4. **No AI co-authorship attribution** in commits or PRs (`ADR-006`).
5. **Never claim a verification that did not happen.** `BLOCKED` is acceptable; fabrication is not.

Knowledge graph:

```bash
npx gitnexus status     # must be current at HEAD before changing code
npx gitnexus analyze    # refresh after every commit
```

> The graph currently indexes **documentation only** — there is no application
> source yet — so impact analysis on code is `BLOCKED` and the static fallback in
> [CHANGE_IMPACT_PROTOCOL](docs/product/05-knowledge-graph/CHANGE_IMPACT_PROTOCOL.md)
> applies. It does **not** satisfy the release gate.

## Key documents

| I want to… | Go to |
| --- | --- |
| Understand the product | [PRODUCT_CHARTER](docs/product/01-product/PRODUCT_CHARTER.md) |
| See all 28 steps | [PRODUCT_SCOPE](docs/product/01-product/PRODUCT_SCOPE.md) |
| Check delivery status | [MASTER_TRACKER](docs/product/02-delivery/MASTER_TRACKER.md) |
| Make a change safely | [CHANGE_IMPACT_PROTOCOL](docs/product/05-knowledge-graph/CHANGE_IMPACT_PROTOCOL.md) |
| Read decisions | [DECISION_LOG](docs/product/02-delivery/DECISION_LOG.md) · [docs/adr/](docs/adr/) |
| Find a contract | [API](docs/product/04-contracts/API_CONTRACTS.md) · [Event](docs/product/04-contracts/EVENT_CONTRACTS.md) · [Data](docs/product/04-contracts/DATA_CONTRACTS.md) |
| Report a vulnerability | [SECURITY.md](SECURITY.md) |
| Everything else | [00-START-HERE](docs/product/00-START-HERE.md) |

## Current blockers

| ID | Blocker |
| --- | --- |
| `BLK-002` | No application code — contracts are `PROPOSED`, graph coverage gates unevaluable |
| `DEC-002` | Phase 1 destination region undecided — blocks `STEP-005`/`STEP-010` (critical path) |
| `DEC-004` | Identity provider undecided — blocks `STEP-002` |
| `RISK-001` | Provider licence viability unproven (highest exposure) |

Four-eyes approval (`REQ-ADMIN-002`) is **structurally unsatisfiable** with a single
owner — see [ADR-010](docs/adr/ADR-010-repository-ownership.md). Must be resolved
before `STEP-021`.

## Licence

UNLICENSED — private, all rights reserved.
