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

## STEP-001.03 + TS7 — 2026-08-05 — Ownership assignment and TypeScript 7 upgrade

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
