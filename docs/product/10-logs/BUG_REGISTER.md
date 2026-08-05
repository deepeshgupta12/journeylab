# JourneyLab — Bug Register

| Field | Value |
| --- | --- |
| Owner | Engineering (Deepesh Kumar Gupta) |
| Status | `ACTIVE` — 2 bugs recorded, both closed with regression tests |
| Rule | **Every fixed bug gets a regression test.** Check R6 verifies they all still pass at every sub-step |
| Last reviewed | 2026-08-05 |

Navigation: [Logs index](README.md) · [Implementation log](IMPLEMENTATION_LOG.md) · [Regression log](REGRESSION_LOG.md) · [Incident response](../07-operations/INCIDENT_RESPONSE.md)

---

## Severity

| Level | Definition | Response |
| --- | --- | --- |
| **S1 — Critical** | Wrong plan delivered to a user, cross-tenant exposure, data loss, privacy breach, hard-constraint violation | Stop the line. Incident response. Release halted |
| **S2 — Major** | Core journey broken or materially degraded; citation correctness below gate; provider degradation presented as current data | Fix before the next sub-step proceeds |
| **S3 — Moderate** | Feature defect with a workaround; accessibility defect not blocking task completion | Scheduled within the step |
| **S4 — Minor** | Cosmetic, copy, non-blocking inconsistency | Backlog |

**Any hard-constraint violation is S1 by definition** (`RISK-004`), regardless of how few users saw it. It is the failure mode the product exists to prevent.

---

## Register

| ID | Title | Sev | Found in | Found by | Symptom | Root cause | Fix commit | Regression test | Status | Closed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BUG-006 | CI failed: duplicate pnpm version | **S2** | first real CI run | Repository owner | verify pipeline failed in 7s, ERR_PNPM_BAD_PM_VERSION | `version:` in workflow duplicated `packageManager` in package.json | *(this commit)* | none possible locally — see entry | **CLOSED** | 2026-08-05 |
| BUG-005 | Missing IMPL-003; guard passed on a mention | **S3** | STEP-001 closure audit | Closure audit | 5 IMPL entries for 6 VERIFIED sub-steps, guard reported PASS | Guard grepped for the ID anywhere, not a real heading | *(this commit)* | `tests/guards/meta/run-all.sh` | **CLOSED** | 2026-08-05 |
| BUG-004 | Guards checked only tracked files; new files bypassed them | **S2** | STEP-001.05 post-commit | Post-commit verification | Stray markup shipped in `f80c8b3` despite verify passing | Guards iterated `git ls-files` (tracked only); new files were invisible until after their first commit | *(this commit)* | extended meta-test with an untracked seed | **CLOSED** | 2026-08-05 |
| BUG-003 | Sub-step committed without required documentation | **S3** | STEP-001.04 close-out | Post-commit verification | `8a9af9b` shipped without IMPL-004, regression entry or status update | Log script failed; commit ran in the same shell invocation regardless | *(this commit)* | `tests/guards/substep-docs.sh` | **CLOSED** | 2026-08-05 |
| BUG-002 | `node_modules/` tracked in git | **S3** | STEP-001.02 pre-change analysis | Pre-change inventory | 2 dependency files committed; `.gitignore` contained only `.gitnexus` | `.gitignore` written without dependency/build exclusions in STEP-001.01 | *(this commit)* | `tests/guards/no-tracked-artifacts.sh` | **CLOSED** | 2026-08-05 |
| BUG-001 | Stray authoring markup in 110 committed files | **S2** | STEP-001.01 | `pnpm install` failure | `package.json` invalid JSON at position 1180 | Authoring tool's file-write wrapper leaked a closing-tag line into every file body | *(this commit)* | `tests/guards/no-stray-markup.sh` | **CLOSED** | 2026-08-05 |

---

## BUG-006 — CI workflow failed: duplicate pnpm version

| Field | Value |
| --- | --- |
| Severity | **S2** — the entire verify pipeline failed to start on every push |
| Found during | First real CI run, reported by the repository owner |
| Date found | 2026-08-05 |

### Symptom
`pnpm/action-setup@v4` failed in 7s:
```
Error: Multiple versions of pnpm specified:
  - version 11 in the GitHub Action config with the key "version"
  - version pnpm@11.20.0 in the package.json with the key "packageManager"
Remove one of these versions to avoid version mismatch errors like ERR_PNPM_BAD_PM_VERSION
```

### Root cause
I set `version: 11` in the workflow while `package.json` already declared `packageManager: pnpm@11.20.0`. The action treats two sources as a configuration error, not something to reconcile.

### Why existing tests did not catch it
`workflow-refs.sh` validates that workflows **parse** and that everything they **reference** exists. It cannot validate action *input semantics* — that is knowledge held by the action, not the repository.

**This is the failure `BR-006` explicitly predicted:** *"the workflows have never run on GitHub — the first PR is the real test."* Recording it honestly at the time meant the failure was expected rather than surprising, but it was still a real defect that reached the default branch.

### Fix
Removed `version:` from the workflow. `package.json` `packageManager` is now the single source of truth, matching how `.nvmrc` and `.python-version` are already used.

### Prevention
No local guard can fully substitute for a real CI run. The honest control is the one already applied: **state plainly when something is unverified**, and treat the first run as the test. Local guards now cover parse-and-reference errors; semantic errors in third-party action inputs surface on first execution.

---

## BUG-005 — Missing IMPL-003, and a guard that passed on a mere mention

| Field | Value |
| --- | --- |
| Severity | **S3** — documentation completeness and a weak guard |
| Found during | STEP-001 closure audit |
| Date found | 2026-08-05 |

### Symptom
The closure audit counted **5 implementation-log entries for 6 VERIFIED sub-steps**. `IMPL-003` (STEP-001.03) did not exist — yet `substep-docs.sh` reported PASS.

### Root cause
Two independent defects:
1. `IMPL-003` was never written. STEP-001.03 shipped with `BR-003` and a regression entry, but no implementation entry.
2. `substep-docs.sh` checked `grep -q "$id" "$IMPL"` — **any mention anywhere**. `IMPL-004`'s prose happened to name `STEP-001.03`, so the guard was satisfied by a passing reference to a document that did not exist.

A third, smaller issue surfaced on the fix: the STEP-001.03 regression heading used a non-standard format (`## STEP-001.03 + TS7 — …`), so the strengthened guard rejected it until normalised.

### Why existing tests did not catch it
The guard tested for *presence of a string*, not *presence of an entry*. It was correct about the wrong thing — the fourth instance of that pattern in this repository (`BUG-001` guard, `BUG-004` scope, the exit-127 meta-tests, and now this).

### Fix
Wrote `IMPL-003`; strengthened the guard to require real headings (`^## IMPL-NNN — STEP-X.YY — ` and `^## STEP-X.YY — `); normalised the non-conforming regression heading.

### Regression test
Committed in `tests/guards/meta/run-all.sh`: reformatting an `IMPL` heading makes the guard exit 1. Meta-tested.

### Prevention
**The larger fix is `tests/guards/meta/run-all.sh` itself.** Until the closure audit, every guard's meta-test existed only as ad-hoc commands in an implementation session — the guards were committed, the evidence they worked was not. The suite makes guard validity reproducible by anyone, and it immediately found two defects in its own first run.

---

## BUG-004 — Guards checked only tracked files, so new files bypassed them on first commit

| Field | Value |
| --- | --- |
| Severity | **S2** — a guard that can be bypassed provides false assurance; it let a known-closed bug (BUG-001) recur in a commit |
| Found during | STEP-001.05 post-commit verification |
| Date found | 2026-08-05 |
| Affected requirements | Process integrity; regression check **R6** |

### Symptom
`BR-005-readme-and-adr.md` was committed in `f80c8b3` containing a stray `</content>` line — the exact defect `BUG-001` closed. `pnpm verify` had passed immediately before the commit.

### Root cause
`tests/guards/no-stray-markup.sh` iterated `git ls-files`, which lists **only tracked files**. `BR-005` was still untracked when `verify` ran, so the guard skipped it entirely. `git add -A` then staged and committed it with the defect intact.

**The guard was structurally incapable of catching a defect in any new file on the run before its first commit** — precisely when new files are most likely to carry authoring artifacts.

### Why existing tests did not catch it
The `BUG-001` meta-test seeded its violation into a file it had **already `git add`-ed**, so the seeded file was tracked and the guard saw it. The meta-test validated the detection logic but not the *file selection* logic. A correct-looking meta-test masked an incomplete guard.

### Fix
Both guards now enumerate tracked **and** untracked-but-not-ignored files:
```
{ git ls-files; git ls-files --others --exclude-standard; } | sort -u
```
`--exclude-standard` keeps `.gitignore` honoured, so `node_modules/` is still skipped.

Applied to `no-stray-markup.sh` and `no-tracked-artifacts.sh` — both had the same flaw.

### Regression test
| Field | Value |
| --- | --- |
| Test | `tests/guards/no-stray-markup.sh` meta-test, extended |
| **Proves** | Seeded an **untracked** file containing the tag → guard exits 1. Before the fix the same seed passed |
| Coverage now | 204 tracked + untracked files, up from 190 tracked |

### Prevention
- Both guards fixed; meta-tests now seed **untracked** files specifically.
- **General lesson recorded:** when writing a guard, test its *selection* logic as well as its *detection* logic. Asking "what does this guard not look at?" is as important as "what does it detect?". Three of four bugs in this repository have been guards or checks that were correct about the wrong scope.

---

## BUG-003 — Sub-step committed without its required documentation

| Field | Value |
| --- | --- |
| Severity | **S3** — process integrity; no runtime impact, but it breaks the audit trail the protocol exists to produce |
| Found during | STEP-001.04 close-out |
| Date found | 2026-08-05 |
| Affected requirements | Process — `SUB_STEP_PROTOCOL` §8 |

### Symptom
Commit `8a9af9b` (STEP-001.04) shipped without `IMPL-004`, its regression-log entry, or its sub-step status update. The sub-step file still read `status: NOT_STARTED` after the work was committed and pushed.

### Root cause
The log-writing Python heredoc failed with a `SyntaxError` (an escaped quote inside a single-quoted string). `git commit` ran **in the same shell invocation**, after the failing script, and was not conditional on its success — so the commit proceeded with the documentation unwritten.

### Why existing tests did not catch it
No guard checked the *coupling* between a sub-step's status and its records. Every existing guard verified content (markup, artifacts, ports, ownership, boundaries); none verified that a `VERIFIED` sub-step had actually produced its evidence.

The R1–R7 checks passed legitimately — the implementation was sound. What failed was the requirement that documentation ship *with* it.

### Fix
Wrote the three missing records. Added `tests/guards/substep-docs.sh` to the fast tier: every sub-step marked `VERIFIED` must have a matching implementation-log entry, regression-log entry and blast-radius record.

### Regression test
| Field | Value |
| --- | --- |
| Test | `tests/guards/substep-docs.sh` |
| Wired into | `pnpm verify` (check R6) |
| **Proves** | Meta-tested — removing the `IMPL-004` reference made the guard exit 1; restoring it returned exit 0 across 4 VERIFIED sub-steps |

### Prevention
- Guard makes recurrence a build failure.
- **Sequencing rule:** documentation writes must complete and be verified *before* `git commit` runs, never in the same uninterruptible invocation. A failing script must stop the commit.

---

## BUG-002 — `node_modules/` tracked in git

| Field | Value |
| --- | --- |
| Severity | **S3** — repository hygiene; no runtime or data impact, but pollutes the graph and every clone |
| Found during | **STEP-001.02 pre-change analysis** — not by a test |
| Date found | 2026-08-05 |
| Affected requirements | REQ-PLAT-002 (reproducible, pinned dependency state) |

### Symptom
`git ls-files` showed 2 tracked paths under `node_modules/`:
`.package-map.json` and `.pnpm-workspace-state-v1.json`. `.gitignore` contained a single line: `.gitnexus`.

### Root cause
In STEP-001.01 I created `.gitignore` for the GitNexus index only, then ran `pnpm install` and committed with `git add -A`. pnpm writes workspace-state files at the `node_modules/` root; with no ignore rule they were swept in.

### Why existing tests did not catch it
No guard existed for tracked build artifacts. The STEP-001.01 regression set covered stray markup (`R6`) but nothing about repository hygiene. **The pre-change analysis found it, which is precisely what that step of the protocol is for** — but a protocol step is not a test, and it only runs when a human or agent is paying attention.

### Fix
Full `.gitignore` covering dependencies, build output, test/coverage output, environment files and OS noise; `git rm -r --cached node_modules`.

### Regression test
| Field | Value |
| --- | --- |
| Test | `tests/guards/no-tracked-artifacts.sh` |
| Wired into | `pnpm verify` fast tier — runs at every sub-step (check R6) |
| **Proves** | Meta-tested: seeded `dist/seeded.js`, guard exited 1; removed it, guard exited 0 across 169 tracked files |

### Prevention
The guard makes recurrence a build failure. Broader lesson recorded in the implementation log: `git add -A` is only safe when `.gitignore` is complete, and completeness is worth verifying at the moment the first dependency install happens.

---

## BUG-001 — Stray authoring markup in 110 committed files

| Field | Value |
| --- | --- |
| Severity | **S2** — core tooling broken; blocked all JS/Python dependency resolution |
| Found during | STEP-001.01, first `pnpm install` |
| Date found | 2026-08-05 |
| Affected requirements | REQ-PLAT-001, REQ-PLAT-002 |
| Affected users/tenants | None — pre-release, no users exist |

### Symptom
`pnpm install` failed immediately:
```
[ERROR] Unexpected non-whitespace character after JSON at position 1180 (line 32 column 1)
```
`package.json` had a literal closing-tag line appended after the final `}`.

### Reproduction
Deterministic. `node -e "JSON.parse(...)"` on the committed `package.json` threw at the same offset.

### Diagnosis
| Hypothesis | Tested how | Result |
| --- | --- | --- |
| Hand-editing error in one file | Read `package.json` tail | Confirmed the stray line, but suggested a wider cause |
| Only the three config files affected | `grep -rl` across the repo | **Rejected — 110 files affected**, including every step file, template and log |
| Markdown files harmless because the tag renders invisibly | Considered | Rejected: harmless *rendering* is not harmless *content*; the same defect broke JSON, TOML and YAML |

### Root cause
The file-writing wrapper used throughout this session appended its own closing tag into the written file body. Because Markdown swallows an unknown inline tag without visible effect, the defect stayed invisible for **147 files across ~4 hours** and only surfaced when the first machine-parsed file (`package.json`) was consumed by a real tool.

### Why existing tests did not catch it
**There were no tests.** This was the first executable verification in the repository — the first sub-step of the first step. Every prior artifact was Markdown, which no tool parsed. The defect was undetectable by inspection precisely because the rendered output looked correct.

This is the strongest available argument for the fast-tier discipline in [TEST_STRATEGY](../06-quality/TEST_STRATEGY.md) §6: the first thing a repository should acquire is something that *executes*.

### Fix
| Field | Value |
| --- | --- |
| Approach | Removed the stray line from all 110 files via a scoped `sed` matching only lines consisting solely of the tag |
| Verification | `package.json` re-validated as JSON; `pnpm install` and `uv sync` both succeed |
| Sub-step | STEP-001.01 |
| Blast radius | BR-001 |

### Regression test
| Field | Value |
| --- | --- |
| Test | `tests/guards/no-stray-markup.sh` |
| Wired into | `pnpm verify` (fast tier), so it runs at **every** sub-step as part of check R6 |
| **Proves** | Verified by meta-test: seeded a file containing the tag → guard exited 1 and flagged exactly 1 file; removed it → guard exited 0 across 156 tracked files |

### A second, related defect found while fixing this
The **first version of the guard embedded the literal tag** in its own source. That literal truncated the guard's own file mid-write, producing a script with a bash syntax error. The syntax error exited non-zero, which the meta-test initially misread as "the guard detected the regression".

Two lessons, both recorded in the guard's header comment:
1. The patterns are now **assembled at runtime** from fragments, never written literally.
2. **A non-zero exit is not proof of detection.** The meta-test now asserts the *specific* exit code and the count of flagged files, not merely failure. A test that passes for the wrong reason is worse than one that fails.

### Prevention
- `tests/guards/no-stray-markup.sh` in the fast tier — fails the build on recurrence.
- Meta-testing convention: every guard must be proven to fail against a seeded violation, asserting exit code and output, before it is trusted.

---

## Entry format

```markdown
## BUG-NNN — [Title]

| Field | Value |
| --- | --- |
| Severity | S1–S4 |
| Found during | STEP-NNN.MM / production / review / regression check |
| Found by | |
| Date found | |
| Affected requirements | REQ-… |
| Affected users/tenants | |

### Symptom
What was observed, exactly. Include the correlation ID for production issues.

### Reproduction
Deterministic steps. If non-deterministic, say so and record the frequency.

### Diagnosis
| Hypothesis | Tested how | Result |
| --- | --- | --- |

### Root cause
The actual cause, not the first plausible one. If a wrong hypothesis was
pursued first, record it — the next person will have the same instinct.

### Why existing tests did not catch it
**Required field.** This is the most useful part of the entry.

### Fix
| Field | Value |
| --- | --- |
| Approach | |
| Commit | |
| Blast radius | BR-NNN |
| Sub-step | STEP-NNN.MM |

### Regression test
| Field | Value |
| --- | --- |
| Test ID | TST-… |
| Location | |
| **Proves** | Fails before the fix, passes after |

### Prevention
What changes so this class of bug cannot recur — a lint rule, a contract
constraint, a property-based test, a graph quality check.
```

---

## Rules

1. **A bug is not closed until its regression test exists** and demonstrably fails against the pre-fix code.
2. **Never disable a failing test to go green.** That is itself a bug, logged and escalated.
3. **"Why existing tests did not catch it" is mandatory.** A fix without it repeats.
4. S1 bugs trigger [INCIDENT_RESPONSE](../07-operations/INCIDENT_RESPONSE.md) and a retrospective.
5. Bugs found by the regression cross-check are logged like any other — they are the protocol working, not an embarrassment.
6. A bug caused by a documented assumption being wrong also updates [ASSUMPTION_REGISTER](../02-delivery/ASSUMPTION_REGISTER.md).

---

## Bug classes to watch in this product

Derived from the architecture's known hazards — these are where defects are most likely and most costly:

| Class | Why likely | Guard |
| --- | --- | --- |
| Temporal confusion (observed vs. effective time) | Three time axes; easy to filter on the wrong one | Property-based tests over effective windows |
| Time zone and DST in itinerary arithmetic | Local-time feasibility across boundaries | Golden-set fixtures spanning DST transitions |
| Stale evidence presented as current | Cache and circuit-breaker interaction | `TST-EVID-005`, drills |
| Hard filter bypassed by ranking | Ordering of filter and rank | `TST-CONS-003`, adversarial candidates |
| Protected item mutated by an automated path | Multiple write paths to itinerary items | `TST-CONS-011` |
| Tenant leakage via cache key or job | Tenant context not propagated | `TST-SEC-002` — R7 every sub-step |
| Deletion missing a derived store | Many derived stores | `TST-PRIV-006` traversal proof |
| Model output reaching state without validation | Gateway boundary erosion | `TST-AI-001` |
