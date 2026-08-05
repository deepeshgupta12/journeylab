# JourneyLab — Implementation Log

| Field | Value |
| --- | --- |
| Owner | Implementing engineer per entry |
| Status | `READY` — **no entries yet; no implementation has occurred** |
| Cadence | One entry per sub-step, written in the same commit as the work |
| Last reviewed | 2026-08-05 |

Navigation: [Logs index](README.md) · [Bug register](BUG_REGISTER.md) · [Regression log](REGRESSION_LOG.md) · [Sub-step protocol](../02-delivery/SUB_STEP_PROTOCOL.md)

---

## Entry format

```markdown
## IMPL-NNN — STEP-NNN.MM — [Sub-step title]

| Field | Value |
| --- | --- |
| Date | YYYY-MM-DD |
| Author | |
| Requirements | REQ-… |
| Blast radius | BR-NNN (LOW/MEDIUM/HIGH/CRITICAL) |
| Commit | `<sha>` |
| Graph indexed commit | `<sha>` — matched HEAD? yes/no |

### What was built
Concrete description of the delivered behavior.

### Why this approach
The options considered and why this one. **If an obvious simpler approach was
rejected, say why** — this is the field future readers actually need.

### Decisions taken during implementation
| Decision | Alternatives | Rationale | Promoted to ADR? |
| --- | --- | --- | --- |

### Deviations from the step file
What differed from the plan, and why. If none, say "none".

### What surprised us
Anything that behaved differently from expectation. This is where the
expensive knowledge lives.

### Follow-up created
| Item | Type | ID |
| --- | --- | --- |

### Verification
| Check | Result |
| --- | --- |
| Sub-step tests | |
| Regression R1–R7 | see REGRESSION_LOG |
| detect_changes() scope | |
| Documentation updated | |
```

---

## Entries

## IMPL-005 — STEP-001.05 — README, architecture map and ADR files

| Field | Value |
| --- | --- |
| Date | 2026-08-05 |
| Requirements | REQ-PLAT-001, REQ-PLAT-004 |
| Blast radius | BR-005 (LOW) |
| Graph indexed commit | `23ec095` — matched HEAD at pre-change |

### What was built
`README.md` (orientation, prerequisites, setup, port table, repository map, data
classifications, working agreement, blockers); `docs/adr/` with **10 ADR files** plus
an index; ADR cross-links added to `DECISION_LOG`; and
`tests/guards/readme-accuracy.sh`.

### Why this approach
A README is the first thing a newcomer runs, so its failure mode is silent: it drifts,
and the reader concludes the documentation cannot be trusted. Rather than asserting it
is accurate, the guard **executes the claim** — every `pnpm` script it mentions must
exist, every link must resolve, every documented port must match
`docker-compose.dev.yml` in both directions, and the documented Node path must yield
v24.

ADRs were promoted from decision-log entries into files because a decision that lives
only inside a larger document cannot be reviewed, superseded or linked from a commit
message independently.

### Decisions taken during implementation
| Decision | Alternatives | Rationale |
| --- | --- | --- |
| Keep `ADR-NNN-<slug>.md` numbering | Rename to `0001-architecture.md` as `STEP-001` §18 listed | The step file's name predates ADR numbering. `ADR-001` is "documentation is the source of truth"; the architecture decision is `ADR-003`. Renumbering would break cross-references across ~100 documents and invalidate commit messages citing ADRs. **Step file corrected instead** |
| Guard checks ports **bidirectionally** | Only check README→compose | A port published but undocumented is as bad as one documented but unpublished |
| Guard does not run `pnpm verify` | Run full setup end to end | It is itself part of `pnpm verify` — that would recurse |

### The acceptance criterion I did not claim
The sub-step required *"an engineer who did not write the README completes setup using
it alone."* **I wrote it, so I cannot certify that.** The guard proves the commands are
correct and current; it cannot prove they are comprehensible to a newcomer.

Recorded as **partially satisfied**, with the human half outstanding. Marking it done
would have been the fourth false pass in this repository — the pattern each time is a
check that verifies something adjacent to, but not the same as, the actual claim.

### What surprised us
The `substep-docs` guard added in the previous sub-step **immediately blocked this
one**: I set `STEP-001.05` to `VERIFIED` before writing this entry, and `pnpm verify`
failed with *"1 missing record across 5 VERIFIED sub-steps"*. The guard written to
prevent `BUG-003` caught the same mistake one sub-step later. That is the clearest
evidence so far that these guards earn their cost.

### Follow-up created
| Item | Type |
| --- | --- |
| Newcomer walkthrough of the README | **Open** — needs a second person |
| ADR files for future decisions | Use `ADR_TEMPLATE`, index in `DECISION_LOG` |

### Verification
| Check | Result |
| --- | --- |
| README guard — scripts, links, ports, Node path | PASS |
| Guard meta-tests (bogus script, broken link, port mismatch) | PASS — all three caught, exit 1 each |
| 10 ADR files created and indexed | PASS |
| `pnpm verify` (14 checks) | PASS |

---

## IMPL-004 — STEP-001.04 — Local dependency stack

| Field | Value |
| --- | --- |
| Date | 2026-08-05 |
| Requirements | REQ-PLAT-001, REQ-PLAT-002 |
| Blast radius | BR-004 (LOW) |
| Graph indexed commit | `28923aa` — matched HEAD at pre-change |
| Commit | `8a9af9b` |

### What was built
`docker-compose.dev.yml` bringing up PostgreSQL 18.4 (PostGIS 3.6.4 + pgvector 0.8.6 + pg_trgm 1.6), Redis 8, MinIO, NATS JetStream and Jaeger v2 — all on the reserved port block **5700-5709**, bound to `127.0.0.1` only. Plus `infra/local/postgres/Dockerfile`, init SQL, `.env.example`, a port-collision guard, and `pnpm dev` / `dev:down` / `dev:reset` / `dev:logs`.

### Why this approach
**Port isolation was an explicit repository-owner constraint** — multiple projects share this Docker host. Rather than picking ports ad hoc, JourneyLab reserves a contiguous documented block and a guard enforces it.

The important subtlety: **a stopped project still owns its ports.** Port 5544 read as free to `lsof` purely because Saakshya was stopped. The guard therefore parses other projects' compose *files*, not just live sockets. Checking only what is running would have produced a collision the first time that project restarted.

### Decisions taken during implementation
| Decision | Alternatives | Rationale |
| --- | --- | --- |
| Multi-stage PostGIS + copied pgvector | Downgrade to PG17; drop pgvector locally; build from source | **Preserves the full baseline.** PG17 has no arm64 PostGIS either; dropping an extension would make local diverge from production; no compiler exists in the base image |
| amd64 emulation for PostgreSQL | Native PG17 | Measured ~3s to ready — cheaper than breaching the PG18 baseline |
| NATS as local queue | Kafka, Redpanda | `DEC-009` is open; the AsyncAPI contract is transport-independent, so this is deliberately substitutable |
| Bind all ports to `127.0.0.1` | Default `0.0.0.0` | Nothing on a dev machine should be network-reachable by default |
| Pinned MinIO `RELEASE.*` tag | `latest` | `REQ-PLAT-002` forbids floating tags |

### What surprised us — five wrong assumptions, all caught by execution
1. **`postgis/postgis:18-3.6` is amd64-only.** `docker manifest inspect` said EXISTS, so it looked fine until the build failed with "no match for platform". Existence and runnability are different questions on Apple Silicon.
2. **PGDG has no PostGIS or pgvector package for PG18** on either image's repo — the postgis image carries only 4 packages and no compiler, ruling out both apt and source builds.
3. **PostgreSQL 18 changed its volume mount point.** Mounting `/var/lib/postgresql/data` makes the container refuse to start; PG18 wants `/var/lib/postgresql` so `pg_upgrade --link` does not cross a mount boundary.
4. **`jaegertracing/all-in-one:1.62` does not exist.** I invented a plausible tag; the correct image is `jaegertracing/jaeger:2.0.0`.
5. **I twice wrote a wrong comment about the Jaeger image** — first "distroless, no shell" (it has a shell), then "no wget or nc" (it has both). Corrected to a working healthcheck rather than documenting a limitation that was not real. Writing a confident explanation for a failure is easy; verifying it is the work.

### Process slip — recorded rather than hidden
The heredoc that should have written this entry, the regression entry and the sub-step status **failed with a Python syntax error, and the commit proceeded anyway**. `8a9af9b` therefore shipped without its required documentation, violating [SUB_STEP_PROTOCOL](../02-delivery/SUB_STEP_PROTOCOL.md) §8.

Cause: the commit ran in the same shell invocation as the log-writing script, so a failure in the first half did not stop the second. **Correction:** documentation writes must succeed before `git commit` runs, not alongside it. Logged as `BUG-003`.

### Verification
| Check | Result |
| --- | --- |
| 5/5 services healthy | PASS |
| Extensions functional (157 km geodesic; L2 √27) | PASS |
| Host connectivity on 5700-5707 | PASS |
| No collision with trekyatra / saakshya / real-estate | PASS |
| Port guard meta-test | PASS |
| `pnpm verify` (12 checks) | PASS |

---

## IMPL-002 — STEP-001.02 — Formatting, linting, strict TypeScript and module boundaries

| Field | Value |
| --- | --- |
| Date | 2026-08-05 |
| Requirements | REQ-PLAT-001 (and enables ADR-003 enforcement) |
| Blast radius | BR-002 (LOW) |
| Graph indexed commit | `11e47a6` — **found stale at `2fe8318`, refreshed per protocol step 3 before proceeding** |
| Commit | *(this commit)* |

### What was built
`.editorconfig`, `biome.json` (Biome 2.5.7), `tsconfig.base.json` (TypeScript 7.0.3, strict + `noUncheckedIndexedAccess` + `exactOptionalPropertyTypes`), `.dependency-cruiser.cjs` module boundary rules, four guards in `tests/guards/`, and a full `pnpm verify` chain covering both JS and Python.

### Why this approach
**Module boundaries are enforced from before the first source file exists.** `ADR-003` chose a modular monolith on the promise it can be split later; that promise is only real if cross-module reach-ins fail the build. Adding the rule after packages exist means retrofitting against violations already written.

The five boundary rules encode architecture decisions directly:
- `no-cross-module-internals` — packages expose entry points, not internals
- `services-not-imported-by-web` — the web app talks to services over generated clients only
- `no-generated-edits` — protects `REQ-PLAT-007`
- `no-circular` — circular imports are the leading indicator of boundary erosion
- `no-orphans` (warn) — surfaces dead modules

### Decisions taken during implementation
| Decision | Alternatives | Rationale | Promoted to ADR? |
| --- | --- | --- | --- |
| **TypeScript 7.0.3, not 7.0.2** | Adopt latest | Blueprint baseline is TS 6.0. Honoring a documented decision is not a new decision; deviating would be. **TS 7 surfaced to the owner for explicit `ASM-004` revalidation rather than silently adopted** | Not yet — pending owner |
| Biome over ESLint+Prettier | ESLint ecosystem | Baseline is silent on linter; Biome is one tool for lint+format, and nothing depends on it yet so it is cheaply replaceable | No |
| dependency-cruiser for boundaries | Biome/ESLint import rules | Only tool that expresses cross-package path rules with the needed precision | No |
| Vacuous-pass guards for empty tree | Omit the scripts until code exists | `tsc` and `mypy` error on an empty tree — a false failure. Guards make the empty case **explicit and self-documenting** rather than silently skipped, and convert to real checks the moment source lands | No |

### Deviations from the step file
Sub-step listed "per-package `tsconfig.json` extending the base" — **deferred**, because zero packages exist. It moves to STEP-002 where the first package is created. Recorded rather than silently dropped.

### What surprised us
1. **The pre-change analysis earned its keep.** It found `BUG-002` (`node_modules` tracked) before any code was written — a defect no existing test covered.
2. **The graph was stale on entry** (`2fe8318` vs `11e47a6`). Protocol step 3 says refresh before continuing; had I skipped it, the analysis would have been against the wrong tree.
3. **Biome rejected its own config twice** — a deprecated `recommended` field and formatting that did not match its own formatter. Fixed via `biome migrate --write` and self-format. A linter that lints its own configuration is a genuinely good property.

### Follow-up created
| Item | Type | ID |
| --- | --- | --- |
| TypeScript 7 vs 7 baseline decision | **Open — owner** | `ASM-004` revalidation |
| Per-package `tsconfig.json` | Deferred | STEP-002 |
| Real lint/typecheck targets | Deferred | STEP-002 |
| `node_modules` artifact guard | Regression test | BUG-002 |

### Verification
| Check | Result |
| --- | --- |
| `pnpm verify` (10-command chain) | **PASS** |
| Boundary rule meta-test | **PASS** — rule `no-cross-module-internals` fired on seeded violation |
| Artifact guard meta-test | **PASS** — exit 1 on seeded `dist/seeded.js` |
| `ruff check` / `ruff format --check` | PASS — 12 files formatted |
| `detect_changes()` | 0 changed symbols, 4 changed files, risk low |

---

## IMPL-001 — STEP-001.01 — Workspace skeleton and pinned toolchain

| Field | Value |
| --- | --- |
| Date | 2026-08-05 |
| Requirements | REQ-PLAT-001, REQ-PLAT-002 |
| Blast radius | BR-001 (LOW) |
| Graph indexed commit | `c37d106` — matched HEAD at pre-change |

### What was built
pnpm workspace (`package.json`, `pnpm-workspace.yaml`) and uv Python workspace
(`pyproject.toml`), version pins (`.nvmrc` 24, `.python-version` 3.14), workspace
directories (`apps/`, `packages/`, `services/`, `tests/`) with boundary READMEs,
and both lock files generated.

### Why this approach
Two toolchain decisions were escalated to the repository owner under `ADR-007`
(propose, then confirm), because the environment did not match the documented plan:

| Decision | Environment finding | Owner choice |
| --- | --- | --- |
| Package manager | pnpm absent, corepack unavailable | **Install pnpm globally** (over npm workspaces) |
| Node runtime | local v25.9.0 vs. Node 24 LTS baseline | **Install Node 24 locally** (over adopting 25) |

Both preserve the blueprint baseline rather than bending it to the machine, which
keeps `ASM-004` honest.

### Decisions taken during implementation
| Decision | Alternatives | Rationale | Promoted to ADR? |
| --- | --- | --- | --- |
| Ruff `DTZ` rule enabled | Default rule set | Flags naive datetimes. This product has three time axes; a naive datetime becomes an infeasible itinerary in STEP-012 | No — captured in `pyproject.toml` comment |
| Placeholder scripts exit 0 with a `[STEP-001.02]` marker | Omit scripts entirely | `pnpm verify` is runnable from day one; markers make the gap visible rather than silent | No |
| pytest markers for `security`/`contract`/`property` | Add later | R7 and R2 need selectable suites from the first test | No |

### Deviations from the step file
None in scope. The step file assumed pnpm and Node 24 were present; both had to be
installed first. Recorded as environment facts, not scope change.

### What surprised us
Two things, both instructive:

1. **`pnpm install` was the first thing in this repository that actually executed
   anything** — and it immediately found `BUG-001`, a defect present in 110 files
   for hours. Markdown had silently absorbed it.
2. **The regression guard reproduced the bug inside itself.** Embedding the literal
   offending pattern truncated the guard's own source file. Fixed by assembling the
   pattern at runtime; the failure mode is now documented in the guard's header so
   nobody "simplifies" it back.

### Follow-up created
| Item | Type | ID |
| --- | --- | --- |
| Stray-markup guard | Regression test | `tests/guards/no-stray-markup.sh` |
| Lock-file drift CI enforcement | Deferred | STEP-001.03 |
| Node 24 PATH is not persistent (keg-only brew install) | Documentation | STEP-001.05 README |

### Verification
| Check | Result |
| --- | --- |
| `pnpm install` under Node 24.19.0 | PASS — `pnpm-lock.yaml` created |
| `uv sync` | PASS — Python 3.14.2 resolved, `uv.lock` created |
| `pnpm verify` | PASS |
| Regression R1–R7 | See REGRESSION_LOG |

---

## What must be logged

| Event | Log here | Also log |
| --- | --- | --- |
| Sub-step implemented | ✅ | Regression log, tracker |
| Bug found during implementation | Reference it | [BUG_REGISTER](BUG_REGISTER.md) |
| Bug fixed | Reference it | [BUG_REGISTER](BUG_REGISTER.md) + regression test |
| Enhancement beyond requirement | Reference it | [ENHANCEMENT_LOG](ENHANCEMENT_LOG.md) |
| Architectural decision taken mid-work | ✅ + promote | [DECISION_LOG](../02-delivery/DECISION_LOG.md) as an ADR |
| Assumption invalidated | ✅ | [ASSUMPTION_REGISTER](../02-delivery/ASSUMPTION_REGISTER.md) |
| Approach abandoned | ✅ **with the reason** | Sub-step marked `DROPPED` |
| Dependency or version change | ✅ | Blast-radius record |

**Negative results are recorded, not discarded** (portfolio standard §7.38). An approach that failed and why is more valuable to the next engineer than a clean history that hides it.
