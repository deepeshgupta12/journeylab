---
sub_step_id: STEP-001.07
parent_step: STEP-001
title: Database-backed checks run in CI
status: VERIFIED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-PLAT-002, REQ-SEC-001, REQ-SEC-002]
blast_radius_id: BR-037
depends_on: [STEP-001.06, STEP-002.08]
last_updated: 2026-08-13
---

# STEP-001.07 — Database-backed checks run in CI

> **Why this sub-step exists.** It was not in the original plan, and it moves
> STEP-001 from `VERIFIED` 6/6 to 7/7. Measured at `f2f21a9`: **665 passed / 5
> skipped locally, 624 passed / 46 skipped in CI.** Forty-one tests are gated on a
> database that CI does not provide, and `pnpm test:security` — R7, which
> `CLAUDE.md` §2 calls non-negotiable — is not in `pnpm verify` at all, so it has
> **never run in CI**. Logged as `BUG-023`. Authorised by the repository owner on
> 2026-08-13.

## 1. Outcome
Every check this repository claims runs in CI actually runs in CI, and a missing
database fails the build instead of quietly skipping forty-one tests.

## 2. Scope and boundary
**In scope:** a PostgreSQL service in `.github/workflows/verify.yml` and in
`tests/ci-mirror.sh`; migrations applied in both; `pnpm test:security` wired into
`pnpm verify`; R7 made transport-portable; **one shared skip decision** that can be
turned into a hard failure.

**Not in this sub-step:** Redis, MinIO, NATS or Jaeger in CI — no test depends on
them yet, and adding services nothing uses is cost without coverage. Deployment
pipelines and release gates remain `STEP-027`.

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-PLAT-002 | The gate a developer runs locally is the gate CI runs | §7 |
| REQ-SEC-001/002 | Cross-tenant isolation is verified on every push, not when a laptop happens to have the stack up | R7 in CI |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | ✅ up to date. **NOT BLOCKED** |
| HEAD / indexed commit | `5cd47bb` — matched HEAD at pre-change |
| Queries run | `impact(_stack_up, upstream, includeTests)` — **ambiguous, 5 candidates**, max 1 impacted, all LOW |
| What the ambiguity told me | The graph found **five separate definitions of `_stack_up`**, one per test module. Five independent copies of "is the database up?", each deciding on its own to skip. That duplication is not incidental to this bug — it is why the decision could never be changed in one place, and why nobody noticed it was being made forty-one times |
| Unknown / low-confidence areas | GitHub Actions service containers cannot be exercised locally. `pnpm ci:local` is the closest proxy and uses a different mechanism (a container on a user-defined network), so **the two paths are verified separately and neither proves the other** |
| Blast radius | **[BR-037](../../../10-logs/blast-radius/BR-037-database-backed-ci.md)** |
| Approval required? | Per blast-radius score |

## 5. Implementation plan
- [x] One shared `requires_db` in `tests/dbcheck.py`, replacing five copies — **and two different env var names**
- [x] **`JOURNEYLAB_REQUIRE_DB=1` turns a skip into a hard failure**, in two independent layers
- [x] PostgreSQL service in `.github/workflows/verify.yml`, health-checked, migrations applied
- [x] PostgreSQL in `tests/ci-mirror.sh` on a user-defined network, plus `postgresql-client`
- [x] R7 connects by DSN rather than `docker exec`, so it runs anywhere
- [x] R7 in `pnpm verify` via `guard:tenant-isolation`, which keeps `verify` usable without Docker
- [x] Meta-test: with the flag set and no database, **both layers fail** — proven separately

## 6. The part that matters more than adding the service

Adding PostgreSQL to CI is the easy half and, on its own, it is a fix that can
regress silently. If the service is ever renamed, its health check changes, or a
port moves, `_stack_up()` returns `False` and **forty-one tests go back to
skipping** — with a green build, exactly as today.

So the sub-step's real deliverable is the **ratchet**: in any environment that
declares a database is expected, its absence is a failure rather than a skip.

```
JOURNEYLAB_REQUIRE_DB=1   # set in CI and in the mirror
```

With it set, `requires_db` raises instead of skipping. A broken service container
then produces a red build naming the missing database, rather than a green one
missing half its security coverage.

This follows the repository's existing rule, already written in `tests/e2e/smoke.sh`
and quoted at every close-out: **a skip is not a pass.** Until now that rule was
enforced by a human reading the output.

## 7. Tests to add
| Test | Type | Asserts |
| --- | --- | --- |
| TST-PLAT-002c | Guard meta | With `JOURNEYLAB_REQUIRE_DB=1` and no database, the suite **fails** |
| TST-PLAT-002d | Guard | `pnpm verify` includes `test:security` |
| — | Python | The shared `requires_db` skips when the flag is unset and raises when it is set |
| — | CI | R7 runs and passes on the runner |

## 8. Telemetry, security and accessibility
No runtime surface. The CI database is ephemeral, seeded only by migrations and
test fixtures, and holds no real data. Its credentials are the same
development-only values already in `docker-compose.dev.yml` and are not secrets —
they are published in the repository deliberately, because a credential that looks
secret but is not is worse than one that is obviously local.

## 9. Documentation to update
- [x] Sub-step completion record
- [x] IMPLEMENTATION_LOG `IMPL-034` · REGRESSION_LOG · BUG_REGISTER `BUG-023`
- [x] `BR-037`
- [x] Parent step §21 · MASTER_TRACKER · README

## 10. Regression cross-check (R1–R7)
| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression suite | **PASS** | 665 Python + 63 web + 307 UI + 40 browser |
| R2 contract compatibility | **PASS** | No contract touched |
| R3 graph diff as expected | **PASS** | Configuration, one helper, one guard, five modules simplified |
| R4 untested requirements | **PASS — improved** | REQ-SEC-001/002 move from *asserted locally* to *verified every push* |
| R5 orphan/unowned nodes | **PASS** | Catch-all owner |
| R6 closed-bug regression tests | **PASS** | BUG-001…023; meta-suite **61/61** |
| R7 tenant isolation | **PASS — 18/18, and now inside `pnpm verify`** | Previously only reachable by a command nothing ran automatically |

**Overall:** **PASS**.

## 11. Rollback
Revert the commit. CI returns to skipping the database tests, which is the current
state — so rollback is safe and also re-opens `BUG-023`.

## 12. Acceptance criteria
- [x] R7 runs in `pnpm verify`, therefore in CI and in `pnpm ci:local`
- [x] The Python skip count in CI matches the local count — verified by the mirror
- [x] A missing database **fails** the build where one is expected — both layers seeded
- [x] `pnpm verify` and CI run the same set of checks

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | 2026-08-13 |
| Commit SHA | *(this commit)* |
| Pushed | ✅ |
| Graph re-indexed at | post-commit |
| `main` green and deployable | ✅ |
| Bugs found | **BUG-023** — the defect this sub-step exists to close |
| Notes / surprises | **The graph's *ambiguous* answer was the most useful thing in the pre-change check.** `impact(_stack_up)` returned five candidates rather than one — five copies of the skip decision, taken forty-one times a run, none able to change the others. A clean single-symbol answer would have hidden the mechanism behind the bug.<br><br>**Adding the service is the easy half and regresses silently on its own.** Rename it, move its port, break its health check, and forty-one tests return to skipping under a green build. The ratchet is the real deliverable: `JOURNEYLAB_REQUIRE_DB=1` makes absence a failure, in two independent layers, each seeded separately to prove it holds alone.<br><br>**Keeping `pnpm verify` usable without Docker needed an explicit decision.** R7 exits 2 for "no database" and `&&` treats 2 like 1, so wiring it in directly would fail the headline command on any machine without the stack — for a CSS change. Swallowing the 2 is worse, because a green `verify` would then mean "isolation holds **or** was never checked", which is how BUG-023 survived. The wrapper puts that difference in one readable place instead of leaving it emergent.<br><br>**My warning box executed a command.** Backticks inside double quotes are command substitution, so printing "Run `pnpm dev`" **started the whole Docker stack**. I caught it only because four containers reported healthy during what should have been a message. A guard with a side effect is not a guard, and this one's would have masked the condition it was reporting.<br><br>**A meta-test asserted a component's wording rather than the outcome**, and failed against entirely correct behaviour because the suite's ratchet fires before the wrapper's. Fixed, and a second case now disables the suite's check to prove the wrapper's holds alone.<br><br>**One thing here cannot be verified before pushing.** GitHub Actions service containers have no local equivalent; the mirror uses a different mechanism, so it proves the suite runs green on Linux against a real database and says nothing about whether the workflow YAML is right. `BR-037` §3 records that, and it is why the record is MEDIUM confidence while the code is high. |
