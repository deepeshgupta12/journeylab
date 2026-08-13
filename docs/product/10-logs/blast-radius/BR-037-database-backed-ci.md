---
blast_radius_id: BR-037
sub_step_id: STEP-001.07
title: Database-backed checks run in CI
author: Deepesh Kumar Gupta
date: 2026-08-13
score: MEDIUM
confidence: MEDIUM
approval_required: false
---

# BR-037 — Database-backed checks run in CI

## 1. Graph state

| Field | Value |
| --- | --- |
| Indexed commit | `5cd47bb` |
| HEAD at check | `5cd47bb` |
| Freshness | ✅ up to date |
| Result | **NOT BLOCKED** |
| Confidence | **MEDIUM** — see §3. GitHub Actions service containers cannot be exercised locally |

## 2. Queries run, and the one that mattered

| # | Query | Result |
| --- | --- | --- |
| 1 | `impact(_stack_up, upstream, includeTests)` | **`status: ambiguous` — 5 candidates**, max 1 impacted, all LOW |
| 2 | `detect_changes(staged)` | Run pre-commit; recorded in the regression entry |

**The ambiguity was the finding.** Asking for the blast radius of one
`_stack_up()` returned five, one per test module — five independent copies of the
decision "skip these tests", none able to change the others. That is the
mechanism behind `BUG-023`: the decision was taken forty-one times per run and
there was no single place where anyone could see it, let alone change it.

A tool answering "I found five of these" is more useful here than a clean number
would have been.

## 3. Why confidence is MEDIUM rather than HIGH

**GitHub Actions service containers have no local equivalent.** The workflow's
`services:` block is interpreted by the runner; nothing on a developer machine
executes it. `pnpm ci:local` covers Linux, a clean checkout and a cold install,
but it provides its database by a **different mechanism** — a container on a
user-defined network, reached by name.

So the two paths verify different things and **neither proves the other**:

| Path | Proves | Does not prove |
| --- | --- | --- |
| `pnpm ci:local` | The suite runs green on Linux against a real database, cold | That the workflow YAML is correct |
| GitHub Actions | The workflow YAML is correct | Anything before it is pushed |

The workflow change is therefore verified **only by the push that follows this
commit**. That is stated here rather than left implicit, and it is the reason this
record is MEDIUM confidence while the code changes around it are high.

## 4. Change inventory

**Added**

| File | Purpose |
| --- | --- |
| `tests/dbcheck.py` | One skip decision, replacing five. Holds the ratchet |
| `tests/guards/tenant-isolation-gate.sh` | R7 as a `verify` step, with the local/CI difference made explicit |

**Modified**

| File | Change |
| --- | --- |
| `.github/workflows/verify.yml` | `postgres:18-alpine` service, health-checked; migrations; `JOURNEYLAB_REQUIRE_DB=1` |
| `tests/ci-mirror.sh` | Postgres on a user-defined network; `postgresql-client`; migrations; same flag |
| `tests/security/test_tenant_isolation.sh` | Connects by **DSN** rather than `docker exec`; own ratchet |
| 5 test modules | Local `_stack_up`/`DSN`/`requires_db` removed in favour of `dbcheck` |
| `pyproject.toml` | `tests` on `pythonpath` |
| `package.json` | `guard:tenant-isolation`, wired into `verify` |
| `tests/guards/meta/run-all.sh` | 6 new cases |

## 5. Twelve impact categories

| # | Category | Assessment |
| --- | --- | --- |
| 1 | **Callers / call graph** | Five test modules import `dbcheck` instead of defining their own. No production symbol changes |
| 2 | **Public API / contracts** | None |
| 3 | **Database / schema** | None. Migrations are *applied* in new places; none is altered |
| 4 | **Events** | None |
| 5 | **Configuration** | **The bulk of the change.** A CI service, two environment variables, one new `verify` step |
| 6 | **Infrastructure** | A PostgreSQL container in CI and in the mirror. CI time +~30s |
| 7 | **Security** | **This is the point.** R7 moves from "runs when a laptop has the stack up" to "runs on every push, and its absence fails the build" |
| 8 | **Privacy** | None. The CI database is ephemeral and holds only fixtures |
| 9 | **Accessibility** | None |
| 10 | **Performance** | `pnpm verify` +~4s locally for R7; CI +~30s for the service |
| 11 | **Tenancy** | Verified far more often. No isolation logic changed |
| 12 | **Documentation** | This record, `IMPL-034`, `BUG-023`, the regression entry, the sub-step, parent §21, `MASTER_TRACKER`, README |

## 6. Mandatory data-flow inspection

No new runtime flow. What is inspected is **the flow of a verification result** —
how "isolation holds" gets from the database to a green build, and where that
chain could lie.

| Hazard | Control | Evidence |
| --- | --- | --- |
| A missing database read as success | `JOURNEYLAB_REQUIRE_DB` makes absence a failure, in **two** layers | Both seeded and killed independently |
| A renamed or moved service silently restoring the bug | Same ratchet — the flag is set by the environment, not derived from the service | Seeded with an unreachable DSN |
| A probe that disagrees with the connection | The TCP probe derives host and port **from the DSN**, so it cannot report "up" about somewhere the tests will not connect | Structural |
| Two env var names configuring different halves | `dbcheck` honours both, `JOURNEYLAB_DATABASE_URL` winning | Consolidated; documented at the definition |
| `verify` becoming Docker-dependent for everyone | The wrapper tolerates a skip locally and prints a loud notice | Seeded; exit 0 with the notice asserted |
| A developer reading that notice as success | It says "DID NOT RUN" and "This is a SKIP, not a pass" in a box | Asserted on the text, not just the code |
| Credentials in the workflow mistaken for secrets | They match `docker-compose.dev.yml` and are commented as development-only | In-file |

## 7. What went wrong while building it

**My warning box executed a command.** The line
``echo "│ Run `pnpm dev` and re-run …"`` sits inside double quotes, where bash
treats backticks as command substitution — so printing the help text **started the
entire Docker stack**. Caught because the test output showed four containers
becoming healthy during what should have been a message. Now single-quoted, with
the reason recorded at the line.

*A guard with a side effect is not a guard*, and this one's side effect would have
masked the very condition it was reporting: after printing, the database it had
just said was missing would have been running.

**A meta-test asserted one component's wording.** The `REQUIRE_DB` ratchet exists
in both the suite and the wrapper; the suite fires first, so my assertion — which
looked for the wrapper's message — failed against correct behaviour. Fixed to
assert the outcome and the reason, plus a second case that removes the suite's
check to prove the wrapper's holds alone. Belt and braces are worth having only if
each is known to hold on its own.

## 8. Score

| Dimension | Value | Reason |
| --- | --- | --- |
| Reach | Medium | Every future push; every database-backed test |
| Reversibility | High | Revert restores today's behaviour — and re-opens `BUG-023` |
| Detectability | High | 6 meta-tests, both ratchet layers seeded independently |
| Security exposure | **Medium — reducing** | R7 goes from never running in CI to running on every push |
| Performance | Low | CI +~30s |
| **Overall** | **MEDIUM** | **Confidence MEDIUM** — the workflow YAML is unverifiable until pushed (§3). No owner approval required |

## 9. Post-change verification

| Check | Result |
| --- | --- |
| Python suite | 665 passed, 5 skipped locally |
| Guard meta-suite | **61 passed** (up from 55) |
| R7 | 18/18, now inside `pnpm verify` |
| `pnpm verify`, `pnpm ci:local`, R1–R7 | Recorded in the regression entry |
| The workflow itself | **Verified only by the push that follows** — §3 |
