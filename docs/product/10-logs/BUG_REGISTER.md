# JourneyLab — Bug Register

| Field | Value |
| --- | --- |
| Owner | Engineering (Deepesh Kumar Gupta) |
| Status | `ACTIVE` — 20 bugs recorded, all closed with regression tests |
| Rule | **Every fixed bug gets a regression test.** Check R6 verifies they all still pass at every sub-step |
| Last reviewed | 2026-08-11 |

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
| BUG-020 | A retained evidence conflict could not name its own source | **S3** | STEP-004.07 | **The client generator** — `Record<string, never>` in the emitted TypeScript | `Evidenced.conflicts[].source` was `{type: object}`, so a conflicting claim carried no id, confidence, access label or observation time | The test asserted only that the `conflicts` KEY existed, which is true of an object that can hold nothing | *(this commit)* | `test_conflicting_sources_are_retained_not_averaged`, rewritten to assert substance; mutation-verified against the old shape | **CLOSED** | 2026-08-11 |
| BUG-008 | Guards assumed macOS paths; failed in CI | **S2** | second CI run | Repository owner | verify failed: documented Node path not executable on ubuntu-latest | Guards encoded Homebrew paths and BSD sed; meta-tested on macOS only | *(this commit)* | all 11 guards verified in a Linux container | **CLOSED** | 2026-08-05 |
| BUG-007 | Security suite passed while schema was absent | **S2** | STEP-002.01 | First R7 run | 3 write-denial assertions passed with no tables; migration had failed on missing citext | Migration not self-contained; assertions could not distinguish policy denial from query error | *(this commit)* | suite meta-test: weakened policy must expose both tenants | **CLOSED** | 2026-08-05 |
| BUG-006 | CI failed: duplicate pnpm version | **S2** | first real CI run | Repository owner | verify pipeline failed in 7s, ERR_PNPM_BAD_PM_VERSION | `version:` in workflow duplicated `packageManager` in package.json | *(this commit)* | none possible locally — see entry | **CLOSED** | 2026-08-05 |
| BUG-005 | Missing IMPL-003; guard passed on a mention | **S3** | STEP-001 closure audit | Closure audit | 5 IMPL entries for 6 VERIFIED sub-steps, guard reported PASS | Guard grepped for the ID anywhere, not a real heading | *(this commit)* | `tests/guards/meta/run-all.sh` | **CLOSED** | 2026-08-05 |
| BUG-004 | Guards checked only tracked files; new files bypassed them | **S2** | STEP-001.05 post-commit | Post-commit verification | Stray markup shipped in `f80c8b3` despite verify passing | Guards iterated `git ls-files` (tracked only); new files were invisible until after their first commit | *(this commit)* | extended meta-test with an untracked seed | **CLOSED** | 2026-08-05 |
| BUG-003 | Sub-step committed without required documentation | **S3** | STEP-001.04 close-out | Post-commit verification | `8a9af9b` shipped without IMPL-004, regression entry or status update | Log script failed; commit ran in the same shell invocation regardless | *(this commit)* | `tests/guards/substep-docs.sh` | **CLOSED** | 2026-08-05 |
| BUG-002 | `node_modules/` tracked in git | **S3** | STEP-001.02 pre-change analysis | Pre-change inventory | 2 dependency files committed; `.gitignore` contained only `.gitnexus` | `.gitignore` written without dependency/build exclusions in STEP-001.01 | *(this commit)* | `tests/guards/no-tracked-artifacts.sh` | **CLOSED** | 2026-08-05 |
| BUG-001 | Stray authoring markup in 110 committed files | **S2** | STEP-001.01 | `pnpm install` failure | `package.json` invalid JSON at position 1180 | Authoring tool's file-write wrapper leaked a closing-tag line into every file body | *(this commit)* | `tests/guards/no-stray-markup.sh` | **CLOSED** | 2026-08-05 |

---

## BUG-020 — A retained evidence conflict could not name its own source

| Field | Value |
| --- | --- |
| Severity | **S3** — no runtime path exists yet; the contract would have propagated the defect into every consumer of `Evidenced` |
| Found during | STEP-004.07 — **by generating the client**, which is the sub-step's entire argument |
| Date found | 2026-08-11 |
| Affected requirements | REQ-EVID-002 (conflicting evidence stays visible, never averaged) |

### Symptom

The generated TypeScript client rendered a conflicting source as an object that
can hold nothing at all:

```ts
conflicts?: {
    source: Record<string, never>;   // <- no property is permitted
    value: unknown;
  }[];
```

### Root cause

`contracts/openapi.yaml` declared the entry as:

```yaml
required: [source, value]
properties:
  source: { type: object }
  value: {}
```

`type: object` with no `properties` is an object with nothing in it. Every
required-ness check passed — `source` **is** required — while the thing being
required was empty.

### Why it matters more than it looks

`REQ-EVID-002` exists because averaging two disagreeing ferry departure times
produces a time no ferry leaves. Retaining the disagreement is only half of that:
a conflict a user cannot attribute is a number with no argument attached to it,
and the interface has no basis on which to show one source over another.

Two members were missing and each has a distinct consequence:

| Missing | Consequence |
| --- | --- |
| `provenance.access_label` | A licensed source may be `internal_only` — usable for planning, **not displayable**. Without the label the interface cannot know that, and the safe default (hide everything) discards evidence the product paid for |
| `validity` | Two observations hours apart look like a **disagreement** when they are one value that **changed**. Conflict and staleness have different remedies, and only the time axes separate them |

### Fix

The entry is now composed from the same shared schemas as the primary claim —
`provenance.json` and `temporal-validity.json` — and closed with
`additionalProperties: false`. A conflicting claim now carries exactly what the
claim it disputes carries, which is the only defensible answer to "how much
evidence does a disagreement need".

### Why the tests missed it — the finding worth keeping

```python
assert "conflicts" in SPEC["components"]["schemas"]["Evidenced"]["properties"]
```

**The assertion tested for a key, not for a capability.** It would have passed if
`conflicts` had been `{}`.

This is the same shape as the stale assertions in `.02` and `.03` and the
would-have-gone-vacuous test in `.06`: an assertion written against the existence
of a thing rather than against the property the requirement actually names. A
requirement that says conflicting evidence "stays visible" is not satisfied by a
field being present — it is satisfied by the field carrying enough to act on.

**It also took a second tool to find it.** 470 Python assertions read the YAML and
all agreed it was fine, because they were reading the same document that was
wrong. The generator produced a *different representation* of the same contract,
and `Record<string, never>` is a shape a human notices immediately. Generating a
client is not only a delivery mechanism; it is a second reader.

### Regression test

`test_conflicting_sources_are_retained_not_averaged` now asserts the exact
required set, that the entry is closed, that both members are `$ref`s to the
shared schemas rather than restatements, and that `access_label` survives into
the resolved provenance. **Mutation-verified:** restoring `source: {type: object}`
fails the test.

The compile-time side is covered too —
`packages/contracts/src/contract.assert.ts` asserts the emitted conflict shape,
and that assertion was itself mutation-tested by removing `validity` from the
expected key union.

---

## BUG-019 — The component gallery returned 500 in development, and nothing looked

| Field | Value |
| --- | --- |
| Severity | **S2** — the design-system review surface was unusable in the only mode a developer opens it in |
| Found during | STEP-003.09 review — **by the owner asking to see the UI**, not by any test |
| Date found | 2026-08-11 |
| Affected requirements | REQ-A11Y-001 (the review surface), REQ-PLAT-001 |

### Symptom
```
$ JOURNEYLAB_ENABLE_GALLERY=1 pnpm dev:web
$ curl -k -o /dev/null -w '%{http_code}' https://localhost:5709/dev/gallery
500

⨯ Error: gallery: deliberate failure to render the contained-error state
```

The same route returns 200 from a production build, renders correctly, and passes
all 40 accessibility assertions.

### Root cause
The error-containment specimen renders a component that throws on purpose, so that
`FeatureErrorBoundary` can be seen containing it. It threw unconditionally —
including during **server** rendering.

React error boundaries are a client concept. A production build tolerates the
server-side throw and recovers on the client; `next dev` treats a throw during
server rendering as a route-level failure and returns 500.

### Why nothing caught it — and this is the real finding
**Every automated check in this repository runs against a production build.**

| Check | Build |
| --- | --- |
| 40 browser accessibility tests | `next build && next start` |
| `pnpm verify` | production |
| `pnpm e2e` §5 | production |
| `pnpm ci:local` | production |

`next dev` renders on a different path — no minification, different hydration,
and a different tolerance for server-side errors. **It had no coverage at all.**
That is not a gap in one test; it is a whole rendering mode nobody was looking at.

The bug survived an entire sub-step and was found by a human opening a URL.

### Fix
Two parts, and the second matters more.

**1.** The specimen throws from an effect rather than during render, so the server
render is clean and the boundary still catches a genuine error on the client. No
hydration mismatch: the first client render matches the server's.

**2.** `pnpm e2e` gained section 5b — it starts `next dev`, asserts `/`,
`/dev/gallery` and the RTL variant each return 200, **and fails if the dev server
logged a server-side exception while rendering**. A route that renders while
logging an exception is half-broken, which is what this looked like in production.

### Verification
Gallery returns 200 in dev. The production path is unchanged: 40/40 still pass.

### Prevention
- **Test the mode people use, not only the mode you ship.** Both are real; only
  one had coverage.
- A defect that a production build tolerates and a development build rejects is
  invisible to any pipeline that only builds for production — which is most
  pipelines, including this one until now.

---

## BUG-018 — The documented token-rebuild command had never worked

| Field | Value |
| --- | --- |
| Severity | **S3** — a generated file could not be regenerated by its own documented command; no wrong output shipped |
| Found during | STEP-003.08, regenerating `tokens.css` for the forced-colors fix |
| Date found | 2026-08-10 |
| Affected requirements | REQ-A11Y-004, REQ-NFR-013 |

### Symptom
`tokens.css` says, in its first two lines:

```
/* GENERATED from src/tokens.ts — do not edit by hand.
 * Rebuild: pnpm --filter @journeylab/ui tokens:build
```

Running that command:

```
Error [ERR_MODULE_NOT_FOUND]: Cannot find module '.../packages/ui/src/tokens'
  imported from .../packages/ui/tools/gen-tokens.ts
```

### Root cause
`gen-tokens.ts` imports `'../src/tokens'` and `tokens.ts` imports `'./contrast'`,
both extensionless. That is what `moduleResolution: bundler` expects and what
every other file in the repository does — but the generator is the only thing
executed by **Node**, and Node's ESM resolver requires an explicit extension.

The whole chain therefore fails on the first import, before any code runs.

### Why nothing caught it
The drift test in `tokens.test.ts` imports `renderCss()` and compares its output
to the committed file, so token drift *is* caught. But vitest resolves
extensionless specifiers, so the test exercises the generator **function** while
never exercising the generator **script**. The command in the header comment was
documentation, and nothing tests documentation.

The same shape as `BUG-011` and `BUG-017`: a path everyone assumes runs, that
nothing runs.

### Fix
Explicit `.ts` specifiers in `gen-tokens.ts` and `tokens.ts`, plus
`allowImportingTsExtensions: true` in `packages/ui/tsconfig.json` — legal
because that project is `noEmit`.

**A second package needed the same setting, and only the full typecheck said so.**
`apps/web` typechecks `packages/ui/src/tokens.ts` through the workspace import,
so it failed with `TS5097` after the change. The per-package typecheck in
`pnpm verify` caught it; running only the UI package's would not have.

### Verification
`pnpm --filter @journeylab/ui tokens:build` writes `src/tokens.css`. The drift
test then passes against the regenerated file, so the script and the function now
demonstrably produce the same output — which is what the header claimed all
along.

### Prevention
- **A command in a comment is a claim.** If a file says "rebuild with X", X belongs
  in CI or in a test, or the claim decays unnoticed.
- Adopting a toolchain ahead of its ecosystem (`ADR-009`) surfaces in resolution
  differences between the type checker and the runtime. They are separate
  resolvers and they disagree.

---

## BUG-017 — The production build of the web app was broken, and nothing ran it

| Field | Value |
| --- | --- |
| Severity | **S2** — `main` was not deployable; no incorrect behaviour shipped to a user because nothing was deployed |
| Found during | STEP-003.07 regression run |
| Date found | 2026-08-10 |
| Affected requirements | REQ-PLAT-001, REQ-NFR-013 |

### Symptom
```
✓ Compiled successfully in 1474ms
  Running TypeScript ...
It looks like you're trying to use TypeScript but do not have the required package(s) installed.
Installing devDependencies (pnpm): - typescript
Done in 1.5s using pnpm v11.20.0

The "id" argument must be of type string. Received undefined
Next.js build worker exited with code: 1
```

The application compiled. TypeScript **was** installed — `require.resolve('typescript')` succeeded from `apps/web`. The error names nothing that is actually wrong.

### Confirmed pre-existing, not caused by this sub-step
`git stash push -u`, rebuild at `bb943f9`, identical failure, `git stash pop`. This is stated because "the build broke during my change" and "the build was already broken" call for different responses, and guessing between them is how a real regression gets attributed to history.

### Root cause
Two layers.

**1. Next's type-check step needs the TypeScript compiler API; TypeScript 7 does not ship one.** `ADR-009` adopted TypeScript 7.0.2, the native compiler. Its package contains `bin/tsc`, `lib/tsc.js`, `lib/getExePath.js` and `lib/version.cjs` — and no `lib/typescript.js`, which is the exact path `next/dist/lib/verify-typescript-setup.js` probes for. Next concludes TypeScript is absent and takes one of two bad branches:

| Environment | Branch | Outcome |
| --- | --- | --- |
| `CI` unset (a developer machine) | auto-install | Installs a package that is already there, mutates `node_modules` mid-build, then dereferences an undefined value: `The "id" argument must be of type string. Received undefined` |
| `CI=true` (GitHub Actions, `pnpm ci:local`) | `missingDepsError` | Aborts, printing the single word **`Failed`** and nothing else |

**2. Nothing ever ran `next build`.** `pnpm verify` did not include it and neither did the workflow. The gap is the same shape as `BUG-011`, where `pnpm test` was a placeholder that echoed and exited 0: a check that everyone assumes is running because a script exists with the right name.

### Why existing tests did not catch it
They could not. `pnpm typecheck` runs `tsc --noEmit` per package and passes — it uses the TypeScript 7 **binary**, which works fine. The vitest suites do not build. The `workflow-refs` guard verifies that every script a workflow names exists, not that the set of scripts is sufficient. No guard has ever asserted "the thing we would deploy can be produced".

### The first fix was incomplete, and `pnpm ci:local` is why that is known
`typescript.ignoreBuildErrors: true` made the build pass **on my machine** and I committed it. `pnpm ci:local` — Linux, clean checkout, cold install, `CI=true` — then failed on the very next run.

That flag does not gate the probe. Reading `next/dist/build/type-check.js` confirms it: `verifyAndRunTypeScript` is called unconditionally, and `ignoreBuildErrors` only decides whether its *result* is enforced. Locally the auto-install branch happened to stumble through; under `CI=true` the same probe aborts. Same defect, two symptoms, and only one of them was visible where I was looking.

This is the fifth time an environment difference has produced a green local run and a red CI one, and the first time the mirror caught it **before** the push.

### Fix
Three parts.

**1. `@typescript/native-preview` as a devDependency of `apps/web`.** Next 16 has an explicit branch for it: if that package resolves and `typescript` is the only thing "missing", Next logs a notice, skips its check and returns — no install, no abort. It is Microsoft's package for the same native compiler `typescript@7` now ships as. Here it functions as a **marker**: nothing imports it, and `tsc` still resolves to 7.0.2 (native-preview installs its binary as `tsgo`, so the two do not collide). Pinned to an exact version because a dev-channel package with a range is a rebuild that changes under you.

**2. `typescript.ignoreBuildErrors: true`.** With the marker present the build succeeds either way — but at `false` it prints *"Running TypeScript … Finished TypeScript in 75ms"* while checking nothing, because the native-preview branch returned before any checking happened. A green message for work that did not occur is the most expensive kind of wrong. At `true` it prints *"Skipping validation of types"*, which is what is actually happening. Types are checked by `pnpm typecheck`, proven non-vacuous by injecting `const _typeProbe: number = "not a number"` and observing `error TS2322`.

**3. `pnpm build` is now a step in `pnpm verify`.** Local and CI run the same thing, per the workflow's own rule that CI must never be the only place a check exists.

Remove parts 1 and 2 when Next recognises `typescript@7` directly; `pnpm build` will say so by failing.

### Verification
`pnpm verify` and `pnpm ci:local` both pass; all 7 routes emit. Regression proof: removing the marker dependency makes `pnpm build` fail under `CI=true`, and `pnpm build` is inside `pnpm verify`, so no separate guard is needed to protect the fix.

### Prevention
- **A build is a check.** "It typechecks and the tests pass" is not "it can be deployed", and the difference is invisible until someone tries to deploy.
- When adopting a toolchain ahead of its ecosystem (`ADR-009`), the failure will surface somewhere that names something else entirely. The error here blamed a missing package that was present.
- **Run `pnpm ci:local` before pushing anything that touches the toolchain, and believe it over the local run.** It is the only place `CI=true` and a cold install exist together, and both mattered here.

---

## BUG-016 — Flaky workflow guard blamed the workflows for a failed download

| Field | Value |
| --- | --- |
| Severity | **S3** — intermittent false failure of `pnpm verify`; no incorrect code shipped |
| Found during | STEP-003.02 regression run |
| Date found | 2026-08-06 |
| Affected requirements | REQ-PLAT-001 |

### Symptom
`pnpm verify` failed with:
```
  FAIL: workflow YAML does not parse
FAIL: 1 broken workflow reference(s).
```
The workflows were valid. Running the same guard again immediately afterwards passed, three times in a row, as did invoking it through `pnpm guard:workflows`.

### Root cause
The guard validated YAML with `uv run --quiet --with pyyaml python -c ...`. `--with` **fetches the package at guard time**, so a transient network failure made the command exit non-zero — and the guard attributed that to the workflows.

This is `BUG-008` one level deeper. That fix taught the guard to distinguish "uv is missing" from "YAML is invalid"; it did not anticipate a third state, "uv is present but its dependency could not be downloaded".

### Why existing tests did not catch it
The meta-suite seeds a *broken workflow* and asserts the guard fails — which it does, for the right reason, in a healthy environment. Nothing simulated a dependency fetch failing, and nothing could: the fetch only happens when the package is absent from the cache.

### The worse problem: it was flaky, not merely wrong
**A flaky gate is worse than a failing one.** A failure that disappears on re-run teaches people that re-running is the fix, and the next real failure gets the same treatment. That is how a gate stops being a gate.

### Fix
`pyyaml` is now a **locked dev dependency** (`uv add --dev pyyaml`), so the guard imports it from the synced environment with no network access at all. The unavailable branch now says so explicitly and states it is **not** a workflow problem.

### Verification
Guard passes; seeding malformed YAML still produces `INVALID YAML … while parsing a flow sequence` and exit 1; restoring the file returns exit 0.

### Prevention
- **A guard must not perform a network fetch.** Anything it needs belongs in the locked environment, or the guard reports the network's health rather than the code's.
- When distinguishing failure modes, enumerate the states rather than the two you have seen. `BUG-008` split one state into two and stopped there; the third was already reachable.

---

## BUG-015 — `useNodeVersion` looked applied and was not; my verification was contaminated

| Field | Value |
| --- | --- |
| Severity | **S3** — no CI failure, but a false claim was committed as "VERIFIED" |
| Found during | Owner ran `pnpm verify` and the engine warning still reported v25.9.0 |
| Date found | 2026-08-06 |
| Affected requirements | REQ-PLAT-001 |

### Symptom
`pnpm-workspace.yaml` set `useNodeVersion: 24.19.0` to stop local and CI running different Node majors. Every `pnpm` invocation still printed:

```
[WARN] Unsupported engine: wanted: {"node":">=24 <25"} (current: {"node":"v25.9.0"})
```

### Root cause — two independent failures
**1. The setting does nothing here.** pnpm 11 *recognises* the key — `pnpm config get useNodeVersion` returns `24.19.0` and it appears in the resolved config — but does not switch the runtime. In a shell with Node 25 on PATH, `pnpm exec node --version` still reported `v25.9.0`.

**2. My verification could not have detected that.** I tested with `export PATH="/opt/homebrew/opt/node@24/bin:$PATH"` already in the shell, so `pnpm exec node --version` reported 24 **because of the PATH, not because of the setting**. I then wrote "VERIFIED honoured" into a commit message.

The controlled test is to run with the machine's default PATH. Doing that showed 25 immediately.

### Why existing tests did not catch it
Nothing asserted the running Node matched `.nvmrc`. The engine warning was visible in every command's output and read as cosmetic noise.

### Fix
The setting is **removed** — a recognised-but-ineffective key is exactly the "looks configured, isn't" trap of `BUG-013`, and leaving it in place would mislead the next reader.

Replaced with enforcement: `tests/guards/node-version.sh` compares the running Node major against `.nvmrc` and fails with the exact command to fix it. Wired into `verify` as the **first** check, and meta-tested by setting `.nvmrc` to 22 and asserting failure. Meta-suite 33 → 36.

### Prevention
- **Never verify a setting from a shell you have already tuned.** Reproduce the default environment; contaminated verification is worse than none, because it produces a confident false claim.
- A configuration key being *recognised* says nothing about it being *effective* — same lesson as `BUG-013`, arrived at from the opposite direction.
- Prefer a guard that fails loudly over a setting that silently might work.

---

## BUG-014 — 9.2 MB tool database committed; artifact guard was a denylist

| Field | Value |
| --- | --- |
| Severity | **S2** — CI red on `main`; 9.2 MB of binary added to repository history |
| Found during | Fifth real CI run, reported by the repository owner |
| Date found | 2026-08-06 |
| Affected requirements | REQ-PLAT-001 |

### Symptom
`biome check .` failed on a file nobody wrote:
```
× Formatter would have printed the following content:
  .vexp/manifest.json
```
Biome was the messenger. The real problem was that `.vexp/` was tracked at all: `index.db` (**9.2 MB**), `index.db-shm`, `index.db-wal`, `index.lock` and `manifest.json` — a tool's private SQLite index, its write-ahead sidecars, and a lock file that changes on every read.

### Root cause
Introduced by commit `7f9c310` — **the BUG-013 fix itself** — via `git add -A`. I staged everything in the working tree without looking at what was in it, and a tool had written its index there during the session.

`no-tracked-artifacts.sh` passed throughout. Its `FORBIDDEN` pattern is a **denylist of directory names**: `node_modules`, `dist`, `build`, `.next`, `.venv`, `coverage`, `htmlcov`, `__pycache__`. `.vexp/` was not on it, because in STEP-001.02 nobody had heard of it.

**That is the actual defect.** A denylist only ever catches artifacts someone thought of in advance, so it is guaranteed to miss the next new tool. BUG-002 was fixed as an instance; the guard never generalised.

### Why existing tests did not catch it
The guard's meta-test seeded a `dist/` directory — an artifact already on the denylist. It proved the mechanism worked on a known name and said nothing about unknown ones. Passing that meta-test was compatible with the guard being useless against anything new.

### Fix
Three layers, so the class is caught and not just this instance:
1. `.gitignore` gains `.vexp/`; `git rm -r --cached .vexp` untracks it.
2. **Shape rule** — any tracked `*.db`, `*.sqlite`, `*.sqlite3`, their `-wal`/`-shm`/`-journal` sidecars, or an `index.lock`, fails.
3. **Size rule** — any tracked file over **512 KB** fails. The largest legitimate file in this repository is ~31 KB of Markdown; the accidental commit was 9.2 MB. Raising the limit requires a deliberate edit and a stated reason.

Both new rules are meta-tested against seeded violations, asserting the exit code **and** the specific message. Meta-suite is now 31/31.

### Not fixed: the history
The 9.2 MB blob remains in `7f9c310`. Removing it requires rewriting pushed history on `main`, which is destructive and is the repository owner's call — **not something to do unilaterally**. Untracking stops further growth; the one-off cost stays until someone decides otherwise.

### Prevention
- **`git add -A` stages what a tool wrote while you were not looking.** Review `git status` before staging, especially after a session where background tooling ran.
- **A denylist guard needs a shape or size rule beside it**, or it silently expires the moment the toolchain changes.
- A meta-test that seeds a violation *already on the list* proves the mechanism, not the coverage. Seed something the list has never heard of.

---

## BUG-013 — pnpm build allowlist used a pnpm 10 key that pnpm 11 silently ignores

| Field | Value |
| --- | --- |
| Severity | **S2** — CI red on `main`; `pnpm install --frozen-lockfile` failed before any check could run |
| Found during | Fourth real CI run, reported by the repository owner |
| Date found | 2026-08-06 |
| Affected requirements | REQ-PLAT-001 |

### Symptom
```
[ERR_PNPM_IGNORED_BUILDS] Ignored build scripts: esbuild@0.28.1, sharp@0.34.5
Error: Process completed with exit code 1.
```
STEP-002.05 had added an allowlist for exactly these two packages, and locally every command passed.

### Root cause — three layers, each of which hid the next
**1. Wrong key.** pnpm 11 renamed the install-script allowlist from `onlyBuiltDependencies` (a **list**, pnpm 10) to `allowBuilds` (a **map** of package → boolean). I wrote the pnpm 10 spelling.

**2. `pnpm config get` confirmed the wrong thing.** Running `pnpm config get onlyBuiltDependencies` returned `["esbuild","sharp"]`, so the setting appeared to be read. It is parsed as configuration and ignored by the installer. The check I used to confirm the fix could not distinguish "applied" from "parsed and discarded".

**3. Local `node_modules` masked it entirely.** After the first failure I ran `pnpm rebuild esbuild sharp`, which built them and recorded that in `node_modules/.modules.yaml`. Every later `pnpm install` reported "Already up to date" and exited 0. **The only environment that could observe the bug was one without `node_modules` — which is CI.**

A fourth wrinkle: when pnpm blocks a build it **auto-writes a stub** into `pnpm-workspace.yaml` containing the literal placeholder `set this to true or false`. That stub was present alongside my hand-written block, producing a duplicate-key YAML error once I added the correct one.

### Why existing tests did not catch it
No check installed from scratch. `pnpm verify` runs against whatever `node_modules` already exists, so it cannot see an install-time failure. This is the same shape as `BUG-009` (a race only visible from a cold start) and `BUG-008` (a macOS assumption only visible on Linux): **the failing condition was structurally unreachable in the environment where I was verifying.**

### Fix
`pnpm-workspace.yaml` now uses `allowBuilds: {esbuild: true, sharp: true}`; the auto-written stub is removed; the dead `pnpm` field is removed from `package.json` (pnpm 11 ignores it and warns).

New guard `tests/guards/pnpm-config.sh`, wired into `verify` and meta-tested, fails on:
- pnpm's auto-written `set this to true or false` placeholder
- the dead `onlyBuiltDependencies` / `neverBuiltDependencies` keys
- a `pnpm` field in `package.json`

### Verification
`rm -rf node_modules apps/web/node_modules && pnpm install --frozen-lockfile` → exit 0, esbuild binary linked, `apps/web/node_modules/.bin/vitest` present, then full `pnpm verify` green with 292 Python + 41 TypeScript tests. Meta-suite 28/28.

### Prevention
- **After changing any dependency or workspace configuration, verify from a wiped `node_modules`.** A warm install proves nothing about a cold one.
- **`pnpm config get <key>` is not proof a setting is honoured** — it echoes back keys the installer ignores. Confirm behaviour, not configuration.
- When a tool auto-writes configuration into a tracked file, treat that write as untrusted input: it may be a placeholder.

---

## BUG-012 — Generated matrix committed in a lint-failing state; CI red

| Field | Value |
| --- | --- |
| Severity | **S2** — CI red on `main`; the merge gate could not run |
| Found during | Third real CI run, reported by the repository owner |
| Date found | 2026-08-06 |
| Affected requirements | REQ-PLAT-001, REQ-SEC-004 |

### Symptom
`pnpm verify` failed on `ubuntu-latest` at `uv run ruff check .`:
```
I001 [*] Import block is un-sorted or un-formatted
  --> apps/api/src/authz/matrix.py:9:1
```
Every other check passed. The file is generated, so nobody had hand-edited it.

### Root cause — two layers
**1. The generator's output was not lint-clean.** `tools/gen_authz_matrix.py` emitted a docstring followed by imports in a layout `ruff check` rejects under I001. Nothing normalised it.

**2. I verified, then modified, then committed.** `pnpm verify` passed while `matrix.py` was in a lint-clean state (I had run `ruff check --fix` on it earlier by hand). *After* that, I regenerated the file as part of a determinism check and ran only `ruff format` — not `ruff check`. **Format and lint are different tools**: `ruff format` does not sort imports, because import order is a lint rule, not a formatting one. The regenerated, lint-dirty file was then committed.

The verification was real. It just no longer described the tree I committed.

### Why existing tests did not catch it
`pnpm verify` would have caught it — it is exactly what CI ran. It was not re-run after the last file modification. No guard enforces "verify must be the final action before commit", and the sub-step protocol states it as sequence rather than as something checked.

This is BUG-003's shape again: there, a log script failed and `git commit` ran anyway in the same shell invocation. Here, a file changed after its verification. **Both are ordering failures in the commit sequence, not defects in any individual check.**

### Fix
`tools/gen_authz_matrix.py` now runs `uv run ruff check --fix` and `uv run ruff format` on its own output before finishing, so generated code is canonical and CI-clean by construction. A comment records that format alone is insufficient and why.

### Verification
Two consecutive regenerations produce a byte-identical, lint-clean, format-clean file. `pnpm verify` green with nothing touched afterwards.

### Prevention
- **A generator must emit code that passes the same checks as hand-written code.** Otherwise every regeneration is a coin flip against CI.
- `ruff format` is not `ruff check`. Passing one says nothing about the other.
- Re-run `pnpm verify` as the **last** action before `git commit`, after any regeneration, hash check or cleanup. A verification describes a tree, not a moment.

---

## BUG-011 — `pnpm test` was a stub, so no Python test ever ran in CI

| Field | Value |
| --- | --- |
| Severity | **S2** — the verify gate reported success without executing any test |
| Found during | STEP-002.02, running `pnpm verify` after adding the first Python code |
| Date found | 2026-08-06 |
| Affected requirements | REQ-PLAT-001, REQ-SEC-001, REQ-SEC-004 |

### Symptom
The last line of `pnpm verify` was:
```
$ echo "[STEP-001.02] tests not yet configured" && exit 0
[STEP-001.02] tests not yet configured
```
`verify` exited 0. The 29 security tests written in this sub-step would not have run in CI.

### Root cause
`package.json` carried a placeholder `"test"` script from STEP-001.02, when no test framework existed. Nothing forced it to be revisited once tests appeared — the placeholder exits 0, so it never complained.

### Why existing tests did not catch it
No guard asserted that `pnpm test` actually executes anything. Every guard checked the *content* of the repository; none checked that the verify chain does real work. A stub that exits 0 is indistinguishable from a passing suite unless something looks.

### Fix
`"test": "uv run pytest"`. CI already runs `uv sync --frozen` before `pnpm verify`, so no workflow change was needed.

### Prevention
This is the third member of a family now: BUG-001's self-truncating guard, the dependency-cruiser cruising 0 modules, and this. **A check that reports success without doing work.** The standing rule from STEP-001 — assert the check can fail — applies to the *verify chain itself*, not only to individual guards.

---

## BUG-010 — BUG-004 recurred: three guards still checked only tracked files

| Field | Value |
| --- | --- |
| Severity | **S2** — `py-typecheck` reported a vacuous pass on the repository's first Python code |
| Found during | STEP-002.02, running `pnpm verify` before commit |
| Date found | 2026-08-06 |
| Affected requirements | REQ-PLAT-001 |

### Symptom
With seven new Python files in the working tree:
```
$ bash tests/guards/py-typecheck.sh
PASS (vacuous): 0 Python files. Real typecheck begins with STEP-002.
```
The guard announced that Python typechecking begins at STEP-002 while standing inside STEP-002 with the files in front of it.

### Root cause
`git ls-files` lists **tracked** files only. New files are untracked until first commit, so the guard counted zero and took its vacuous-pass branch.

This is exactly BUG-004. That fix was applied to `no-stray-markup.sh` and `no-tracked-artifacts.sh` but **not** to every guard. An audit of all guards found the same defect in three:

| Guard | Consequence |
| --- | --- |
| `py-typecheck.sh` | Vacuous pass; mypy never ran on new code |
| `typecheck.sh` | Same shape, would trigger when TypeScript arrives |
| `substep-docs.sh` | A newly added sub-step file would not be validated on the commit that adds it |

`codeowners-coverage.sh` also uses `git ls-files`, but only to print a count described as "tracked paths", and its catch-all rule covers untracked paths. Left as-is deliberately.

### Why existing tests did not catch it
The meta-suite seeds violations as **untracked** files, which is why it caught BUG-004 for the markup guard. But `py-typecheck` and `typecheck` had **no meta-test at all** — they were treated as trivial wrappers. A guard whose entire behaviour is a conditional is not trivial: the condition is the guard.

### Fix
All three now union tracked and untracked-not-ignored paths, with a comment naming BUG-004 so the next person does not re-simplify it.

### Prevention
When a bug is fixed in one instance of a repeated pattern, **grep for the pattern across the repository** and fix or explicitly exempt every instance. Recording BUG-004 as fixed while three copies survived is what made this recurrence possible.

---

## BUG-009 — Postgres reported healthy during first-boot init, and R7 misdiagnosed the result

| Field | Value |
| --- | --- |
| Severity | **S2** — intermittent false failure of the R7 security gate; a real one would be indistinguishable |
| Found during | STEP-002.02 pre-work: verifying STEP-002.01 against a **clean** database |
| Date found | 2026-08-06 |
| Affected requirements | REQ-SEC-001, REQ-PLAT-001 |

### Symptom
Running the isolation suite immediately after `docker compose up -d --wait` on fresh volumes:
```
=== applying migration 001 ===
  migration applied

ERROR:  expected table(s) missing — the schema is not in place.
```
All five tables existed. Re-running the identical command passed 12/12.

### Root cause — two distinct defects
**1. The healthcheck could pass against a server that was about to be destroyed.**
The official Postgres entrypoint starts a *temporary* server during first-boot initialisation with `listen_addresses=''` — Unix socket only. `pg_isready -U journeylab` uses that socket, so it reported ready against the throwaway server. Compose marked the service healthy and `--wait` returned; ~3s later the server shut down and restarted for real.

Measured directly by polling both transports during boot:

| t | socket | tcp |
| --- | --- | --- |
| 1250ms | **UP** | down |
| 1750ms | **UP** | down |
| 2000ms | down | **UP** |

The container log confirms the sequence: `ready to accept connections` → `shutting down` → `PostgreSQL init process complete` → `ready to accept connections`.

**2. The R7 precondition gate blamed the wrong cause.**
The gate ran a table-count query with `2>/dev/null` and defaulted to "5 missing" whenever the result was empty. A connection failure and an absent schema produced the same message. It failed closed — correct — but sent the reader hunting a migration bug that did not exist.

### Why existing tests did not catch it
STEP-002.01 was verified against a database that was **already running and already seeded**. The suite was never once executed against a cold stack, so the only window in which the bug exists was never entered. The 12/12 result was true and not evidence of what it appeared to prove.

### Fix
1. `docker-compose.dev.yml`: healthcheck is now `pg_isready -h 127.0.0.1 …`. TCP is unavailable during init, so the check cannot pass early.
2. `tests/security/test_tenant_isolation.sh`: an explicit connectivity probe runs first and reports "cannot reach the database — this is NOT a schema problem", keeping the schema check for genuinely missing tables.

### Verification
Three consecutive `down -v` → `up --wait` → R7 cycles: 12/12 each, `--wait` now taking 6s instead of returning early.

### Prevention
- A service is not ready because a healthcheck says so; it is ready when the check exercises **the transport clients actually use**.
- Verify a gate from the cold state at least once. Steady-state verification cannot observe startup races.

---

## BUG-008 — Guards encoded macOS-specific assumptions and failed in CI

| Field | Value |
| --- | --- |
| Severity | **S2** — CI red on `main`; the merge gate could not run |
| Found during | Second real CI run, reported by the repository owner |
| Date found | 2026-08-05 |
| Affected requirements | REQ-PLAT-001 |

### Symptom
`pnpm verify` failed on `ubuntu-latest`:
```
4. documented Node PATH yields Node 24
   FAIL documented Node path not executable: /opt/homebrew/opt/node@24/bin
FAIL: 1 README inaccuracy/ies. The README must match reality.
```
The README was **not** inaccurate. The guard asserted a macOS Homebrew path exists — impossible on a Linux runner.

### Root cause
Three host-specific assumptions, only the first of which CI had reached:
1. `readme-accuracy.sh` check 4 asserted `/opt/homebrew/opt/node@24/bin/node` is executable.
2. `meta/run-all.sh` used `sed -i ''` — BSD/macOS syntax that fails on GNU sed.
3. `workflow-refs.sh` reported *"YAML does not parse"* whenever `uv` was missing — blaming the workflows for a toolchain gap.

Only #1 was reported. **#2 and #3 were found by probing every guard under Linux** rather than fixing the one failure and pushing.

### Why existing tests did not catch it
Every guard had been meta-tested — **on macOS only**. The meta-suite proved detection logic, never portability. Same shape as `BUG-004` (scope untested) and `BUG-007` (a check correct about the wrong thing): **the tests were right about what they measured and silent about where they ran.**

This is the second CI failure from a local assumption (`BUG-006` was the duplicate pnpm version). Both were invisible locally by construction.

### Fix
1. **Check 4 split into a portable invariant and a host-conditional check.** Always: the Node major version in the README must match `.nvmrc` — the single source of truth CI's `setup-node` reads, and the check that actually catches drift. Conditionally: where the Homebrew path exists, confirm it yields that version; otherwise `skip` with a reason.
2. `sedi()` helper detecting GNU vs BSD sed.
3. `workflow-refs.sh` distinguishes "uv unavailable" from "YAML invalid".

### Regression test
Proven in a real Linux container (`node:24-bookworm`, no Homebrew, no uv):
- `readme-accuracy.sh` → exit 0, check 4 reports `skip`
- **All 11 guards → exit 0**
- Drift still caught: setting `.nvmrc` to 22 while the README says 24 → exit 1

The last point matters most — the portable check is **weaker in reach but not in power**. It still fails on real README drift.


### A self-inflicted defect while fixing this
The `sedi` helper was introduced by a blind string replace of `sed -i ''` → `sedi`,
which also rewrote the literal **inside the helper's own definition**. The BSD branch
then called `sedi` recursively until the stack overflowed — the meta-suite died with
SIGSEGV (exit 139) rather than reporting a test failure.

Same family as `BUG-001`'s first guard, which embedded the very pattern it searched
for and truncated its own source. **A fix expressed as a global substitution can hit
the fix itself.** The definition now carries a comment warning against re-normalising it.

### Prevention
- **Run guards under Linux before pushing**, not only on the developer machine. A guard is a cross-platform contract.
- Prefer asserting **consistency between two repository files** over the existence of a host path. `.nvmrc` vs README is portable; a Homebrew prefix is not.
- When a check cannot apply, print `skip` **with a reason** — never `FAIL`. A false failure trains people to ignore the gate.

---

## BUG-007 — Security suite reported passes while the schema was absent

| Field | Value |
| --- | --- |
| Severity | **S2** — a tenant-isolation suite that passes without a schema is the most dangerous kind of false assurance |
| Found during | STEP-002.01, first run of `tests/security/test_tenant_isolation.sh` |
| Date found | 2026-08-05 |
| Affected requirements | REQ-SEC-001, REQ-SEC-002; regression check **R7** |

### Symptom
The first run reported **3 passes** for cross-tenant INSERT, UPDATE and DELETE denial — while the tables did not exist. Migration 001 had failed (`type "citext" does not exist`), so every write query errored. The assertions tested only "did the command fail?", and a missing table fails exactly like a policy denial.

### Root cause
Two independent defects:
1. **Migration not self-contained.** It used `citext` but relied on `infra/local/postgres/init/01-extensions.sql`, which creates only postgis, vector and pg_trgm. A managed production database never runs that init script, so the migration would have failed there too.
2. **Assertions could not distinguish denial from error.** `if <query>; then bad else ok` treats *any* non-zero exit as a successful denial.

A third, cosmetic issue surfaced next: `psql -c` echoes a `SET` status line per statement, so captured values were `"SET\nSET\n1"` and comparisons failed even when the security behaviour was correct.

### Why existing tests did not catch it
This *is* the test. Nothing sat above it. The suite was written and immediately trusted — the same pattern as `BUG-004` (guard trusted before its scope was tested) and `BUG-001`'s first guard (passed for the wrong reason).

**Sixth occurrence of the same class in this repository: a check that was correct about the wrong thing.**

### Fix
1. Migration declares its own extensions (`citext`, `pgcrypto`) — self-contained for any target database.
2. **Precondition gate:** the suite counts the 5 expected tables and **exits 1 with `ERROR` if any is missing**, refusing to run assertions that would report false passes.
3. Write denial asserts on **error text** (`row-level security`), distinguishing a policy denial from a schema error, and reporting which occurred.
4. UPDATE/DELETE assert on **affected row count** via a CTE rather than empty output.
5. Output parsing takes the final line only.

### Regression test
The suite's own **meta-test**: a deliberately weakened policy (`USING (true)`) must expose both tenants. It reports 2 rows, then the strict policy is restored and it reports 1. Without that, a suite passing against disabled RLS would look identical to one passing against working RLS.

### Prevention
- **Precondition gates on security tests.** A security test whose subject is absent must ERROR, never pass.
- **Assert on the reason, not the exit code.** "It failed" is not "it was denied."
- Migrations declare their own extension dependencies rather than inheriting from local bootstrap.

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
