---
blast_radius_id: BR-068
sub_step_id: BUG-039
title: The database could be crashed by its own health probe
author: Deepesh Kumar Gupta
date: 2026-10-19
score: LOW
confidence: HIGH
approval_required: false
---

# BR-068 — The database could be crashed by its own health probe

Not a sub-step. Found while verifying `BUG-038`: the browser suite's first run against the
fixed build failed eleven `mobile` tests, every one with the page's own honest message —
*"the coverage service returned 503"*. The API log showed thirteen consecutive 503s; the
Postgres log showed why.

## 1. Graph state

| Field | Value |
| --- | --- |
| Indexed commit | `62b65d0` (forced, see `BR-067` §1) |
| HEAD at check | `62b65d0` |
| Result | **NOT APPLICABLE — no code symbol changes.** Infrastructure configuration only: two container definitions, one CI service, one guard |
| Reference check | grep: every `pg_isready` probe in the repository, enumerated by the guard itself |

## 2. What the logs said, and what the experiments proved

```
10:07:25 [1] LOG:  untracked child process (PID 6244) exited with exit code 2
10:07:25 [1] LOG:  terminating any other active server processes
10:07:28 [1] LOG:  all server processes terminated; reinitializing
   ...   FATAL:  the database system is in recovery mode        (×9)
10:08:32 [1] LOG:  database system is ready to accept connections
10:08:38 [1] LOG:  untracked child process (PID 6283) exited with exit code 2
10:08:38 [1] LOG:  terminating any other active server processes
```

Twice in seventy seconds, inside the browser run. `OOMKilled=false`, 77 MiB in use,
nine of a hundred connections. Not resources.

**What the postmaster does with a child it never forked** — PostgreSQL 17+,
`process_pm_child_exit`: exit status 0 or 1 is logged and ignored; **anything else is
handled as a crash.** The two exit-1 children in the same log were ignored; the two
exit-2 children brought the server down. The log already contained the rule.

| Experiment | Result |
| --- | --- |
| `docker exec … sh -c 'exit 2'` | **No crash, no log line.** An exec'd process is not the postmaster's child |
| `docker exec … sh -c '(sleep 2; exit 2) & exit 0'` — an **orphan** adopted by PID 1, exiting 2 | **Crashed the database in 3 ms**, with the identical log sequence. Recovered in ~1 s |
| control: orphan exiting 1 | Logged, ignored |

**The mechanism.** The health check is `CMD-SHELL "pg_isready -h 127.0.0.1 …"` with
`timeout: 5s`. Under the suite's load — on an amd64 image emulated through Rosetta, where
every fork is slow — a probe runs long. Docker kills the `sh` at five seconds. The
still-running `pg_isready` is reparented to PID 1, which is the postmaster, because the
container has no init process. It then exits **2** ("no response" — the reason it was slow).
The postmaster sees an untracked child exit 2 and terminates every backend. **The harder
the database works, the likelier its own probe is to kill it.** Eight quiet runs today
never triggered it; the first run with real form submissions did, twice.

## 3. What changes

| Category | Change |
| --- | --- |
| **Config — compose** | `docker-compose.dev.yml` `postgres`: `init: true`. Docker's init (`tini`) becomes PID 1; orphans reparent to it and are reaped there. The postmaster never sees them |
| **Config — mirror** | `tests/ci-mirror.sh`: `--init` on the `docker run` that starts the mirror database — same health command, same timeout, same hazard |
| **Config — CI** | `.github/workflows/verify.yml`: `--init` added to the Postgres service's `options`, which GitHub passes to `docker create` |
| **Guard** | `tests/guards/postgres-healthcheck.sh` gains a second rule beside `BUG-009`'s: every file that defines a `pg_isready` health probe must also give the container an init process. Output token `NO INIT`. Two meta-tests seed its removal and prove the guard catches it |
| Code / contract / schema / tenancy | None |

## 4. Why this is not folded into `BR-067`

It was found by `BUG-038`'s verification and it blocks `BUG-038`'s evidence — a browser
suite that can crash its own database proves nothing on a bad day. But it is a different
defect in a different layer with a different regression test, and a reader of `BUG-038`
six months from now should not have to learn about Rosetta and PID 1 to understand a CORS
preflight. Separate record, separate commit, separate bug.

## 5. Scoring

**LOW.** Four one-line configuration changes and a guard. The change cannot alter any
query result or any schema; it changes who reaps an orphan. Risk is in the other
direction: without it, every heavy test run in every environment rolls dice.

## 6. Mutation plan

| # | Seeded defect | Must be killed by |
| --- | --- | --- |
| 1 | `init: true` removed from the compose service | meta-test: guard exits 1 with `NO INIT` |
| 2 | `--init` removed from the mirror's `docker run` | meta-test: guard exits 1 with `NO INIT` |
| 3 | the guard's new rule deleted | meta-test 1 fails to observe `NO INIT` (the meta-suite's vacuous-pass check) |

## 7. Follow-ups

| Item | Type |
| --- | --- |
| `platform: linux/amd64` under Rosetta makes every fork slow; the arm64 PostGIS image question is already in the compose comment | Carried, unchanged |
| GitHub's service-container `--init` is believed to work (`options` are `docker create` flags) and is **unverified until the next CI run** — recorded in `BUG-039` as such | Verify on push |
