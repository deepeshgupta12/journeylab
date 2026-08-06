# JourneyLab — Regression Cross-Check Log

| Field | Value |
| --- | --- |
| Owner | Implementing engineer per entry |
| Status | `READY` — no entries; no implementation has occurred |
| Rule | **One entry per sub-step.** A sub-step without a passing entry may not be committed |
| Origin | Repository-owner directive: previous implementations and fixes must not break |
| Last reviewed | 2026-08-05 |

Navigation: [Logs index](README.md) · [Sub-step protocol](../02-delivery/SUB_STEP_PROTOCOL.md) · [Change impact protocol](../05-knowledge-graph/CHANGE_IMPACT_PROTOCOL.md) · [Bug register](BUG_REGISTER.md)

---

## The seven checks

Run **after** the sub-step's own tests pass and **before** committing.

| # | Check | What it protects | Pass condition |
| --- | --- | --- | --- |
| **R1** | Full regression suite — this step's completed sub-steps **and** every `VERIFIED` step | Accumulated work | All green; no unexplained skips |
| **R2** | Contract compatibility vs. last release | Consumers | No unintended breaking diff |
| **R3** | `detect_changes()` graph diff | Unintended blast radius | Only expected symbols and flows changed |
| **R4** | Untested-requirement count (`KG-Q-008`) | Coverage erosion | Not increased |
| **R5** | Orphan / unowned node count (`KG-Q-008`) | Governance erosion | Not increased |
| **R6** | Every closed bug's regression test | Fixed bugs staying fixed | All passing |
| **R7** | Cross-tenant isolation (`TST-SEC-002`) | The one thing that must never break | Pass — **non-negotiable** |

**R4 and R5 are ratchets.** They may improve or stay flat; they may never worsen. This is what stops quality debt accumulating one "just this once" at a time.

---

## Entry format

```markdown
## STEP-NNN.MM — YYYY-MM-DD — <sub-step title>

| Field | Value |
| --- | --- |
| Commit | `<sha>` |
| Author | |
| Graph indexed commit | `<sha>` — matched HEAD? |
| Duration | |

| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression | PASS / FAIL | N tests, M skipped (reasons) |
| R2 contract compatibility | PASS / FAIL | diff summary |
| R3 graph diff expected | PASS / FAIL | new/removed nodes and edges |
| R4 untested requirements | PASS / FAIL | before → after |
| R5 orphan/unowned nodes | PASS / FAIL | before → after |
| R6 closed-bug tests | PASS / FAIL | N tests |
| R7 tenant isolation | PASS / FAIL | |

**Overall:** PASS / FAIL

### Failures and resolution
| Check | Failure | Cause | Resolution | Bug ID |
| --- | --- | --- | --- | --- |

### Notes
Anything a future reader should know — flaky tests identified, durations
trending up, coverage gaps accepted with a reason.
```

---

## Entries

## STEP-002.03 — 2026-08-06 — Role and attribute policy definitions

| Field | Value |
| --- | --- |
| Commit | *(this commit)* |
| Graph indexed commit | `d9be78b` — matched HEAD at pre-change |

| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression | **PASS** | `pnpm verify`; 276 tests (was 29) |
| R2 contract compatibility | **N/A** | No contracts yet (STEP-004) |
| R3 graph diff as expected | **PASS** | Three new authz modules, one shared parser, two test modules, docs. **No existing `auth/` symbol modified** — confirmed by `impact(RequestContext)` returning `epistemic: exact` |
| R4 untested requirements | **PASS** | Decreased — `REQ-SEC-004` now has 176-cell coverage; `REQ-ADMIN-002` four-eyes now tested |
| R5 orphan/unowned nodes | **PASS** | Catch-all owner covers `apps/api/**`, `tools/**` |
| R6 closed-bug tests | **PASS** | BUG-001…011 guards all pass |
| **R7 tenant isolation** | **PASS — 12/12** | Unchanged; policy adds a second, independent tenant check above the database |

**Overall:** PASS

### Failures and resolution
| Failure | Cause | Resolution |
| --- | --- | --- |
| Generator refused to run | 11 conditional matrix cells named no condition | 10 resolved from §4's own rules; the 11th raised `DEC-010` and is encoded to fail closed |
| mypy could not import the shared parser | `tools/` not on `mypy_path`/`pythonpath` | Added both |
| A mutant appeared to survive | `ruff format` reflowed the generated file; my `str.replace` pattern silently matched nothing | Re-run with a pattern spanning the reflowed entry — 3 tests failed as expected. **The harness was broken, not the guard** |

### Notes
This is the first sub-step whose pre-change check was **RUNNABLE rather than `BLOCKED`**. `impact(RequestContext, upstream, depth 3)` returned `epistemic: exact`, risk LOW, 4 direct dependents — all inside `auth/`, none modified. Confidence in BR-012 is scored 4/5, against 2/5 for every prior record.

---

## STEP-002.02 — 2026-08-06 — Tenant and actor context resolution at the API boundary

| Field | Value |
| --- | --- |
| Commit | *(this commit)* |
| Graph indexed commit | `f544d38` — matched HEAD at pre-change |

| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression | **PASS** | `pnpm verify` — and for the first time it actually executes tests (`BUG-011`) |
| R2 contract compatibility | **N/A** | No contracts yet (STEP-004) |
| R3 graph diff as expected | **PASS** | Six new auth modules, one test module, three guard fixes, compose healthcheck, docs. No unexpected scope |
| R4 untested requirements | **PASS** | Decreased — `REQ-SEC-004` now has executable tests for the first time |
| R5 orphan/unowned nodes | **PASS** | Catch-all owner covers `apps/api/**` and `tests/api/**` |
| R6 closed-bug tests | **PASS** | BUG-001…008 guards pass. **BUG-004 found to have recurred** in three guards (`BUG-010`) — fixed, and this check is why it surfaced |
| **R7 tenant isolation** | **PASS — 12/12** | Plus a new application-layer pooled-leak test that R7 did not cover |

**Overall:** PASS

### Failures and resolution
| Failure | Cause | Resolution |
| --- | --- | --- |
| R7 failed from a cold database | Postgres healthcheck went green against the first-boot temporary server | `BUG-009` — TCP healthcheck; verified over three cold boots |
| `py-typecheck` reported "0 Python files" with 7 present | `git ls-files` is tracked-only — BUG-004 recurrence | `BUG-010` — three guards fixed to union tracked + untracked |
| `pnpm test` executed nothing | Placeholder script from STEP-001.02 | `BUG-011` — now `uv run pytest` |
| Every API test returned `422` | PEP 563 + `Annotated[..., Depends(local)]` — FastAPI resolves the annotation in module globals | Removed `from __future__ import annotations` from the test module; hazard recorded for STEP-004 |
| One mutant survived the suite | `set_config(…, false)` made binding session-wide; no test covered `bind_tenant`'s transaction scope | Pooled-leak test added; mutant now killed |

### Notes
Mutation testing was run as part of this cross-check rather than trusting a green suite: five security properties were each broken deliberately, and the one that survived exposed a genuine gap. A suite that has never been shown to fail is a claim, not evidence.

---

## STEP-002.01 — 2026-08-05 — Identity schema and row-level security

| Field | Value |
| --- | --- |
| Commit | *(this commit)* |
| Graph indexed commit | `0cac408` — matched HEAD at pre-change |

| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression | **PASS** | `pnpm verify` — 15 checks |
| R2 contract compatibility | **N/A** | No contracts yet (STEP-004) |
| R3 graph diff as expected | **PASS** | Migration, security suite, docs |
| R4 untested requirements | **PASS** | Decreased — `REQ-SEC-001`/`002` now have executable tests |
| R5 orphan/unowned nodes | **PASS** | All paths owned |
| R6 closed-bug tests | **PASS** | BUG-001…007 guards all pass |
| **R7 tenant isolation** | **PASS — 12/12** | **Established by this sub-step.** Non-negotiable from here on |

**Overall:** PASS

### Failures and resolution
| Failure | Cause | Resolution |
| --- | --- | --- |
| Migration failed | `citext` not created by local init SQL | Migration now declares its own extensions — self-contained for any target database |
| **3 write assertions falsely passed** | Tables absent; a failed query is indistinguishable from a policy denial | `BUG-007` — precondition gate + assert on error text |
| 8 assertions failed on parsing | `psql -c` echoes a `SET` line per statement | Capture the final line only |
| Migration not idempotent | Bare `CREATE TABLE` / `CREATE POLICY` | `IF NOT EXISTS`, `ON CONFLICT DO NOTHING`, `DROP POLICY IF EXISTS` — proven by applying twice |

### Notes
**R7 now exists and has real detection power** — proven by its own meta-test rather than
asserted. The security controls were correct throughout; the failures were in how the
test measured them, which is exactly the distinction `BUG-007` records.

Alerting is a known gap: `ALRT-SEC-001` is specified but not implemented until
`STEP-024`, so a cross-tenant denial is logged and tested but does not page anyone.
Recorded in `BR-008` §5 category 11, not glossed.

## STEP-001.06 — 2026-08-05 — CI workflows and the change-impact merge gate

| Field | Value |
| --- | --- |
| Commit | *(this commit)* |
| Graph indexed commit | `e0062c2` — matched HEAD at pre-change |

| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression | **PASS** | `pnpm verify` — 15 checks (new: `guard:workflows`) |
| R2 contract compatibility | **N/A** | No contracts yet |
| R3 graph diff as expected | **PASS** | Workflows, two guards, docs; no application symbols |
| R4 untested requirements | **PASS** | Not increased |
| R5 orphan/unowned nodes | **PASS** | All tracked paths owned |
| R6 closed-bug tests | **PASS** | BUG-001/002/003/004 guards all pass |
| R7 tenant isolation | **N/A** | No tenancy until STEP-002.01 |

**Overall:** PASS

### Failures and resolution
| Failure | Cause | Resolution |
| --- | --- | --- |
| Meta-test B exit 127 | `git stash -u` stashed the untracked guard script; bash could not find it | Committed the guard first, then tested on a scratch branch |
| Meta-test B2 exit 127 | `git checkout` likewise removed the untracked script | Same |
| `guard:markup` failed pre-commit | Stray tag in untracked `BR-006` | **BUG-004's fix caught it before commit** — the same defect that shipped in `f80c8b3` |

### Notes
Two meta-tests reported failures that had nothing to do with the gate — the harness
could not find the script it was testing. Read naively, exit 127 looks like "the gate
blocked it". This is the third instance of the repository's recurring lesson: **verify
that a check failed for the reason you think it did.**

`BUG-004`'s fix proved itself one sub-step after being written, catching a stray tag in
an untracked file before it could be committed.

Two claims are deliberately **not** made: the workflows have never run on GitHub, and
the 10-minute refresh target is unmeasured. Both are recorded as outstanding.

## STEP-001.05 — 2026-08-05 — README, architecture map and ADR files

| Field | Value |
| --- | --- |
| Commit | *(this commit)* |
| Graph indexed commit | `23ec095` — matched HEAD at pre-change |

| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression | **PASS** | `pnpm verify` — 14 checks (new: `guard:readme`) |
| R2 contract compatibility | **N/A** | No contracts yet |
| R3 graph diff as expected | **PASS** | Documentation and one guard; no symbols |
| R4 untested requirements | **PASS** | Not increased |
| R5 orphan/unowned nodes | **PASS** | 190 tracked paths owned |
| R6 closed-bug tests | **PASS** | BUG-001/002/003 guards all pass |
| R7 tenant isolation | **N/A** | No tenancy until STEP-002.01 |

**Overall:** PASS

### Failures and resolution
| Failure | Cause | Resolution |
| --- | --- | --- |
| `guard:substep-docs` failed mid-run | `STEP-001.05` marked `VERIFIED` before its records were written | Wrote `IMPL-005` and this entry, then re-ran. **The BUG-003 guard worked exactly as designed** |

### Notes
This is the first sub-step where a guard from a *previous* sub-step caught a live
mistake rather than a seeded one. The failure mode it prevented — a sub-step declared
complete without evidence — is precisely `BUG-003`, one sub-step earlier.

One acceptance criterion is deliberately recorded as **partial**: the README's
commands are proven correct by execution, but its comprehensibility to a newcomer
cannot be self-certified by its author.

## STEP-001.04 — 2026-08-05 — Local dependency stack

| Field | Value |
| --- | --- |
| Commit | `8a9af9b` |
| Graph indexed commit | `28923aa` — matched HEAD at pre-change |

| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression | **PASS** | `pnpm verify` — 12 checks (new: `guard:ports`) |
| R2 contract compatibility | **N/A** | No contracts yet |
| R3 graph diff as expected | **PASS** | Compose, Dockerfile, guards, env template; no symbols |
| R4 untested requirements | **PASS** | Not increased |
| R5 orphan/unowned nodes | **PASS** | 183 tracked paths owned |
| R6 closed-bug tests | **PASS** | BUG-001 and BUG-002 guards pass |
| R7 tenant isolation | **N/A** | No tenancy until STEP-002.01 |

**Overall:** PASS (implementation) — **but see the process failure below**

### Failures and resolution
| Failure | Cause | Resolution |
| --- | --- | --- |
| PostGIS PG18 build failed | Image is amd64-only on an arm64 host | Platform pin + emulation (~3s to ready) |
| pgvector install failed | No PGDG package; no compiler in base image | Multi-stage copy from the pgvector image |
| Postgres container exited (1) | **PG18 changed the volume mount point** | Mount `/var/lib/postgresql`, not `.../data` |
| Jaeger image pull failed | Tag `all-in-one:1.62` invented; does not exist | `jaegertracing/jaeger:2.0.0` |
| Jaeger reported unhealthy | Healthcheck used bash `/dev/tcp`; image has no bash | wget-based healthcheck (wget is present) |
| **Documentation not written before commit** | Log-writing script failed; commit ran in the same shell invocation and proceeded regardless | `BUG-003` — see below |

### Process failure — BUG-003
`8a9af9b` was committed **without** `IMPL-004`, this regression entry, or the sub-step
status update. The R1–R7 checks above genuinely passed, but
[SUB_STEP_PROTOCOL](../02-delivery/SUB_STEP_PROTOCOL.md) §8 requires documentation in
the *same commit* — so the sub-step was not actually complete when it was committed.

Corrected in the follow-up commit. Guard added: `tests/guards/substep-docs.sh`.

### Notes
Five technical assumptions failed here, every one caught by execution rather than
review. The port work is the part most likely to have caused real harm: checking only
live sockets would have allocated 5544, colliding with Saakshya on its next start.

New guard `port-collisions.sh` reads other projects' compose files precisely because
`lsof` cannot see a stopped project's claim.

## STEP-001.03 — 2026-08-05 — Ownership assignment and TypeScript 7 upgrade

| Field | Value |
| --- | --- |
| Commit | *(this commit)* |
| Graph indexed commit | `ef7af7a` — matched HEAD at pre-change |
| Decisions applied | `ADR-009`, `ADR-010` |

| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression | **PASS** | `pnpm verify` — 11 checks incl. new CODEOWNERS guard |
| R2 contract compatibility | **N/A** | No contracts yet |
| R3 graph diff as expected | **PASS** | Config, governance and docs; no symbols |
| R4 untested requirements | **PASS** | Not increased |
| R5 orphan/unowned nodes | **PASS — GAP NOW CLOSED** | `CODEOWNERS` created; all 178 tracked paths resolve to an owner. This was the known gap carried since STEP-001.01 |
| R6 closed-bug tests | **PASS** | BUG-001 and BUG-002 guards both pass |
| R7 tenant isolation | **N/A** | No tenancy until STEP-002.01 |

**Overall:** PASS

### Failures and resolution
| Check | Failure | Cause | Resolution | Bug ID |
| --- | --- | --- | --- | --- |
| R1 (`guard:boundaries`) | **Boundary enforcement silently became a no-op** under TS 7 | dependency-cruiser 18.1.1 supports `typescript <7`; cruised 0 modules and reported "no violations" | Rewrote the guard TypeScript-independently; removed dependency-cruiser | — (tooling defect, not a product bug) |
| Validation probe | Probe reported success while `tsc` errored | `head` masked the real exit code | Re-probed asserting exit codes explicitly | — |

### Notes
**R5's long-standing gap is now closed** — this was the check that had been passing
only because "not increased" is satisfied by "already zero-owned". With `CODEOWNERS`
in place it becomes a real ratchet.

The boundary-tool failure is the most instructive event so far: a green check that
verified nothing. It was caught because the meta-test asserts a **specific rule name**,
not merely a non-zero exit. Both prior false passes in this repository (BUG-001's guard,
this probe) had the same shape.

## STEP-001.02 — 2026-08-05 — Formatting, linting, strict TypeScript and module boundaries

| Field | Value |
| --- | --- |
| Commit | *(this commit)* |
| Graph indexed commit | `11e47a6` — **stale on entry (`2fe8318`), refreshed per protocol step 3** |
| Author | Implementation session |

| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression | **PASS** | `pnpm verify` — 10-command chain incl. all STEP-001.01 guards |
| R2 contract compatibility | **N/A** | No contracts exist yet (STEP-004) |
| R3 graph diff as expected | **PASS** | `detect_changes()`: 0 changed symbols, 4 changed files, risk low — config-only, as expected |
| R4 untested requirements | **PASS** | Not increased |
| R5 orphan/unowned nodes | **PASS (known gap)** | Not increased. All paths remain unowned — `CODEOWNERS` awaits `STEP-001.03`, blocked by `BLK-001` |
| R6 closed-bug tests | **PASS** | BUG-001 guard PASS (169 files); **BUG-002 guard added** and meta-tested |
| R7 tenant isolation | **N/A** | No application or tenancy until STEP-002.01 |

**Overall:** PASS

### Failures and resolution
| Check | Failure | Cause | Resolution | Bug ID |
| --- | --- | --- | --- | --- |
| Pre-change inventory | `node_modules/` tracked in git | `.gitignore` incomplete from STEP-001.01 | Full `.gitignore` + `git rm --cached` + permanent guard | **BUG-002** |
| `pnpm lint` | Biome rejected its own config — deprecated `recommended` field | Config written against an older schema | `biome migrate --write` | — |
| `pnpm lint` | Biome config failed its own formatter | Written by `json.dump`, not Biome | `biome check --write` self-format | — |
| `pnpm typecheck` | `tsc` errors on empty tree | No TS files exist | Explicit vacuous-pass guard rather than a silent skip | — |
| `pnpm py:typecheck` | `mypy` errors on empty tree | No Python files exist | Same pattern | — |

### Notes
Three checks remain `N/A` and one is a **known gap** (R5, unowned paths). The gap is
acceptable only because `STEP-001.03` — which creates `CODEOWNERS` — is itself hard-blocked
by `BLK-001`. It is tracked, not silently accepted.

Boundary enforcement is now live **before any source exists**, which is the point: the rule
has never had to be retrofitted against existing violations. Both new guards were meta-tested
against seeded violations, asserting rule name and exit code rather than mere failure.

## STEP-001.01 — 2026-08-05 — Workspace skeleton and pinned toolchain

| Field | Value |
| --- | --- |
| Commit | *(this commit)* |
| Graph indexed commit | `c37d106` at pre-change; re-indexed post-commit |
| Duration | — |

| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression | **PASS** | `pnpm verify` green. Suite is minimal by construction — this is the first sub-step; lint/type/test are placeholders until STEP-001.02 |
| R2 contract compatibility | **N/A** | No contracts exist yet (STEP-004) |
| R3 graph diff as expected | **PASS** | New root config files and workspace dirs only; no unexpected scope |
| R4 untested requirements | **BASELINE** | First measurement — establishes the ratchet floor |
| R5 orphan/unowned nodes | **BASELINE (known gap)** | `CODEOWNERS` does not exist until STEP-001.03, so all paths are unowned. Expected and tracked, not silently accepted |
| R6 closed-bug tests | **PASS** | `BUG-001` guard passes; meta-tested to fail on a seeded violation |
| R7 tenant isolation | **N/A** | No application, no tenancy until STEP-002.01 |

**Overall:** PASS

### Failures and resolution
| Check | Failure | Cause | Resolution | Bug ID |
| --- | --- | --- | --- | --- |
| Acceptance (`pnpm install`) | Invalid JSON in `package.json` | Stray authoring markup in 110 files | Scoped removal + permanent guard | **BUG-001** |
| Guard meta-test | Guard reported failure for the wrong reason (bash syntax error, not detection) | Guard embedded the literal pattern and truncated itself | Runtime pattern assembly; meta-test now asserts exit code **and** flagged-file count | Folded into BUG-001 |

### Notes
Several checks are `N/A` or `BASELINE` here — legitimately, since this is the first
executable commit. That will not hold from STEP-001.02 onward: R1 and R3 must produce
real results, and R4/R5 become ratchets that may not worsen.

The R5 gap is the honest one to watch: **every path is currently unowned**, and that
is only acceptable because `STEP-001.03` (which is itself `BLOCKED` by `BLK-001`,
no named owners) has not run yet.

---

## Handling failures

| Situation | Action |
| --- | --- |
| A check fails | **Sub-step is not done.** Fix forward or revert |
| Failure reveals a defect | Log `BUG-NNN`, add a regression test, then re-run |
| Same sub-step fails twice | Stop; re-plan with the step owner ([WAYS_OF_WORKING](../02-delivery/WAYS_OF_WORKING.md) §6) |
| A test is flaky | Log as a bug; **quarantining requires an owner and a deadline**, never silent deletion |
| R7 fails | **Immediate SEV1.** Halt all work; incident response |
| R4/R5 would worsen | Either add the missing test/owner now, or record an explicit, approved exception with an expiry date |

**Never disable a failing test to make a check pass.** That converts a visible problem into an invisible one and is itself logged as a bug.

---

## Suite growth expectations

The R1 suite grows with every sub-step, which is the point — and also a cost. Manage it deliberately:

| Concern | Approach |
| --- | --- |
| Runtime growth | Parallelise; tier into fast (every sub-step) and full (pre-push, pre-release) as defined in `STEP-027` |
| Slow suite tempting shortcuts | Track suite duration in this log; a trend upward is a scheduled task, not a reason to skip |
| Redundant tests | Prune only with owner approval and a recorded rationale |
| Fast tier must always include | R7 tenant isolation, R6 closed-bug tests, contract compatibility |
