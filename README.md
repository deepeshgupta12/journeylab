# JourneyLab

**A trip digital twin for comparing feasible futures before and during travel.**

JourneyLab turns a traveler's intent and constraints into several evidence-backed,
*feasible* trip scenarios, makes the trade-offs visible on a synchronized map and
timeline, and maintains the chosen scenario as a live companion.

It is a **simulation and decision system, not a single-answer itinerary chatbot**.
Deterministic solvers own feasibility; the model explains and parses language.

| | |
| --- | --- |
| Status | **In implementation** — STEP-001 and STEP-003 `VERIFIED`, STEP-002 in progress |
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

`pnpm verify` is the whole gate: 23 steps across 17 repository guards, linting,
formatting, typechecking, the JavaScript and Python suites, a production build, and
a **real-browser accessibility run**. **It must pass before you change anything**, so
you know any later failure is yours.

The last step launches Chromium, so the first run needs the browser once:

```bash
pnpm --filter @journeylab/web exec playwright install --with-deps chromium
```

| Command | What it does |
| --- | --- |
| `pnpm verify` | The full gate. Nothing merges without it |
| `pnpm test` | Python + JavaScript suites only |
| `pnpm a11y` | The 40 browser accessibility tests |
| `pnpm ci:local` | **Runs CI's job on Linux, in a clean checkout, with a cold install.** Run it before pushing anything touching dependencies, generated files, or CI itself — it has caught seven failures that a macOS run could not |
| `pnpm build` | Production build of every package |
| `pnpm contracts:generate` | Rebuilds the API clients from `contracts/` — run it after **any** contract change |
| `pnpm contracts:baseline` | Promotes the current contracts to the compatibility baseline. **This declares a release** — see `contracts/baseline/BASELINE.md` |

### Changing the API contract

`contracts/openapi.yaml` is the source. The TypeScript and Python clients are
built from it and **must never be edited by hand** (`REQ-PLAT-007`):

```bash
# 1. edit contracts/openapi.yaml (or contracts/jsonschema/*.json)
pnpm contracts:generate     # 2. rebuild both clients
pnpm verify                 # 3. drift guard + compatibility gate
```

Two gates run, and they answer different questions:

| Gate | Question |
| --- | --- |
| `guard:generated-clients` | Do the committed clients match the contract? |
| `guard:contract-compatibility` | Did this change break an existing consumer? |

The compatibility gate diffs against `contracts/baseline/` and **fails on a
breaking change that is not carried by a major version bump**. It is
direction-aware: adding a required property breaks a *request* and is harmless in a
*response*, and relaxing required-ness is the reverse. It also fails a deprecated
operation that declares no `Sunset` date.

Two things it cannot do, both deliberate. It does not detect **semantic change** —
a field that keeps its name and type while changing meaning (`ENH-001`, pending) —
and it does not diff **AsyncAPI**, because event compatibility depends on delivery
semantics and `DEC-009` is open. A green run means "not breaking in a way a machine
can recognise", not "safe".

`pnpm verify` regenerates and diffs. If the committed client differs from what
the contract produces, the build fails — whether that is because someone edited
a generated file or because someone changed the contract and did not regenerate.
The guard deliberately cannot tell those apart, since the remedy is the same.

| Generated, do not edit | Built from |
| --- | --- |
| `packages/contracts/src/generated/openapi.ts` | `contracts/openapi.yaml` |
| `apps/api/src/generated/models.py` | `contracts/openapi.yaml` |
| `contracts/schemas/error-codes.json` | `docs/product/04-contracts/ERROR_MODEL.md` §3 |
| `apps/api/src/conventions/error_codes.py` | `docs/product/04-contracts/ERROR_MODEL.md` §3 |

`packages/contracts/src/index.ts` and `contract.assert.ts` are **hand-written** and
outside the guard: the first is the package's public surface, the second holds
compile-time assertions that the generated types did not silently degrade.

### Seeing the UI

```bash
JOURNEYLAB_ENABLE_GALLERY=1 pnpm dev:web
```

Then <https://localhost:5709/dev/gallery> — every design-system component in every
quality state, on one page. Append `?dir=rtl` to check the right-to-left layout.

The route is **off unless that flag is set**, and `tests/guards/gallery-gate.sh`
proves it 404s without it: a page enumerating every internal component and error
string does not belong in a deployment.

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
apps/web/          Next.js 16 — app shell, Auth0 sign-in, gallery     built
apps/api/          FastAPI — auth, tenancy, authorization             built
packages/ui/       design system: tokens, primitives, a11y            built
services/audit/    append-only audit with redaction                   built
db/migrations/     schema + row-level security                        built
contracts/         OpenAPI, AsyncAPI, JSON Schema — the source of truth  built
contracts/baseline/ what compatibility is measured against          built
packages/contracts/ generated TypeScript client (never hand-edited)   built
services/          domain, data, retrieval, AI, ML, workflow          [STEP-005+]
infra/local/       local development images
tests/guards/      17 executable repository guards (run by pnpm verify)
tests/security/    cross-tenant isolation suite (R7)
docs/product/      the documentation system — scope, architecture, contracts
docs/adr/          architecture decision records
```

### What actually exists today

| Area | State |
| --- | --- |
| **Identity** | Auth0 OIDC with PKCE, refresh-token rotation, `__Host-` cookies, 7-day guest sessions. Proven against a live tenant |
| **Tenancy** | PostgreSQL row-level security with `FORCE`, a `NOBYPASSRLS` application role, and a 12-assertion isolation suite including a meta-test that a weakened policy exposes both tenants |
| **Authorization** | Deny-by-default matrix generated from markdown into both Python and TypeScript, so the server and the menu cannot disagree (`ADR-012`) |
| **Audit** | Append-only **by privilege**, not by convention — `GRANT SELECT, INSERT` with `UPDATE` and `DELETE` revoked |
| **Design system** | 40 components across 9 sub-steps: forms, table/list with CSV export, dialog, notifications, ten quality states, role-aware navigation, i18n with DST-correct durations, and money as integer minor units |
| **Accessibility** | Gated, not aspirational — see below |

### Tests

| Suite | Count | Runs in |
| --- | --- | --- |
| Python | 648 | `pnpm verify` |
| Design system (jsdom) | 307 | `pnpm verify` |
| Web (unit) | 61 | `pnpm verify` |
| **Real browser (Playwright + axe)** | **40** | `pnpm verify` |
| Cross-tenant isolation (R7) | 12 | `pnpm test:security` |
| Guard meta-tests | 55 | `pnpm guard:meta` |

The browser suite is the one to know about. It runs axe over five surfaces in two
device profiles and asserts keyboard traversal, focus visibility, 24×24 touch
targets, no reflow at 320px, forced-colors rendering, right-to-left layout, and
Core Web Vitals — with `retries: 0`, because a retry policy on an accessibility
gate is a way of not fixing accessibility.

**A green run is not accessibility.** Automation finds a third to a half of real
defects; [ACCESSIBILITY_AUTOMATION_LIMITS](docs/product/06-quality/ACCESSIBILITY_AUTOMATION_LIMITS.md)
lists what stays manual and why the screen-reader journeys are scheduled every
release.

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

The graph indexes application code as well as documentation, so pre-change impact
analysis is **runnable** — a `BLOCKED` result is now a real finding, not the
expected default.

> **Two coverage gaps are known and must not be papered over.** The graph records
> `CALLS` edges from function calls, so a React component used only as JSX has
> **zero** traced dependents (`impact(SkipLink)` returns 0 against 8 real
> references), and CSS is not represented at all. Component-level impact analysis
> is therefore established by the compiler and the browser suite, and said to be
> so. See `BR-025` §3 and `BR-026` §3; owned by `STEP-026`.

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
| `DEC-002` | **Phase 1 destination region undecided** — blocks `STEP-005`/`STEP-010`. The critical path |
| `DEC-007` | Cloud provider, region and data residency — blocks `STEP-027` |
| `RISK-001` | Provider licence viability unproven (highest exposure) |
| — | Contracts remain `PROPOSED` until `STEP-004` |

Closed since the last revision: `BLK-002` (application code exists),
`DEC-004` (**Auth0**, `ADR-013`, proven against a live tenant), `RISK-014` (the
graph indexes code).

Carried and deliberately unmet, each with an owner: real-user Core Web Vitals
(`STEP-024`), server-side denial tests against real routes (`STEP-004`), manual
screen-reader journeys (every release), and a design review by someone who is
not the implementer (before GA).

Four-eyes approval (`REQ-ADMIN-002`) is **structurally unsatisfiable** with a single
owner — see [ADR-010](docs/adr/ADR-010-repository-ownership.md). Must be resolved
before `STEP-021`.

## Licence

UNLICENSED — private, all rights reserved.
