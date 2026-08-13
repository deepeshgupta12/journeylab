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

## STEP-001.07 — 2026-08-13 — Database-backed checks run in CI

| Field | Value |
| --- | --- |
| Commit | *(this commit)* |
| Graph indexed commit | `5cd47bb` — matched HEAD at pre-change |

| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression | **PASS** | 665 Python + 63 web + 307 UI + 40 browser |
| R2 contract compatibility | **PASS** | No contract touched |
| R3 graph diff as expected | **PASS** | Configuration, one new helper, one new guard, five test modules simplified |
| R4 untested requirements | **PASS — improved** | REQ-SEC-001/002 go from *asserted locally* to *verified on every push* |
| R5 orphan/unowned nodes | **PASS** | Catch-all owner |
| R6 closed-bug tests | **PASS** | BUG-001…**024**; meta-suite **61/61** (up from 55) |
| **R7 tenant isolation** | **PASS — 18/18, and now inside `pnpm verify`** | Previously reachable only via `pnpm test:security`, which nothing ran automatically |

**Overall:** PASS

### Failures and resolution

| Failure | Cause | Resolution |
| --- | --- | --- |
| The skip-path warning **started the Docker stack** | Backticks inside double quotes are command substitution; `` `pnpm dev` `` in an `echo` executed | Single-quoted, ASCII box, reason recorded at the line. *A guard with a side effect is not a guard* |
| Meta-test failed against correct behaviour | It asserted the wrapper's wording; the suite's ratchet fires first | Assert the outcome; added a case that disables the suite's check to prove the wrapper's alone |
| `NameError: _stack_up` after consolidation | One call site survived the removal of the definition | Replaced with `stack_is_up` |
| 4 × `F811 Redefinition of unused DSN` | The duplicates used `JOURNEYLAB_TEST_DSN`, a **different variable name** my first pass did not match | Removed; `dbcheck` honours both names so no existing override breaks |

### Mutation testing

| Seeded | Result |
| --- | --- |
| No database, flag unset, `verify` gate | **exit 0 with a loud "DID NOT RUN" notice** — the intended behaviour, asserted on the text |
| No database, `JOURNEYLAB_REQUIRE_DB=1`, gate | **killed** — exit 1 |
| Same, with the **suite's** ratchet removed | **killed** by the wrapper — each layer holds alone |
| No database, flag set, pytest | **killed** — refuses at import |
| No database, flag unset, pytest | **skips**, as a laptop should |

### Notes

**The graph's ambiguous answer was the most useful result in the pre-change
check.** `impact(_stack_up)` returned `status: ambiguous` with five candidates —
five copies of the skip decision. That is the mechanism behind BUG-023, and a clean
single-symbol answer would have hidden it.

**The mirror failed on its first run with a database, and that was the point.**
Three tenant-context tests asserted counts against rows the R7 *shell script*
creates as a side effect. They passed on every developer machine — where R7 has
been run at some point — and failed on a clean schema with `assert 0 == 1`.
`BUG-024`, fixed by making them self-seeding, mutation-verified by neutering the
helper and reproducing exactly those three failures.

Six steps of green builds had never executed them anywhere clean, because CI
skipped them. **The sub-step paid for itself before it was pushed.**

**One thing here is unverifiable before pushing.** GitHub Actions service
containers have no local equivalent; `pnpm ci:local` uses a different mechanism, so
it proves the suite runs green on Linux against a real database but says nothing
about whether the workflow YAML is correct. `BR-037` §3 states this, and it is why
that record is MEDIUM confidence.

---

## STEP-002.08 — 2026-08-12 — Server-side session store and revocation

| Field | Value |
| --- | --- |
| Commit | *(this commit)* |
| Graph indexed commit | `5086a8a` — matched HEAD at pre-change |

| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression | **PASS** | **665 Python** (up from 648) + **63 web** (up from 61) + 307 UI + 40 browser |
| R2 contract compatibility | **PASS** | No contract touched; the STEP-004.08 gate reports no diff from the baseline beyond the known additive one |
| R3 graph diff as expected | **PASS** | One migration, one new module, one cascade, one TypeScript interface. `detect_changes()` below |
| R4 untested requirements | **PASS — improved** | REQ-SEC-003 was **claimed** by `.05` and untested; it is now covered |
| R5 orphan/unowned nodes | **PASS** | Catch-all owner |
| R6 closed-bug tests | **PASS** | BUG-001…022; meta-suite 55/55 |
| **R7 tenant isolation** | **PASS — 18/18** locally, up from 12. **Not run in CI — see below** | `sessions` added to the suite: cross-tenant read, **cross-tenant revoke** (denial of service, a different harm), and no DELETE privilege at all |

**Overall:** PASS

### Failures and resolution

| Failure | Cause | Resolution |
| --- | --- | --- |
| `ImportError: cannot import name 'provision_organization'` | I wrote the fixture from my assumption of the API. The function is `create_organization`, with `slug`/`display_name` | Read the module. **Same failure as the STEP-003 e2e probes and the STEP-004.08 consumer expectations** — third occurrence of writing against an imagined API |
| `ForeignKeyViolation: role_key=(traveller)` | Invented a role. The real keys are `trip_owner`/`trip_editor`/`trip_viewer`/… | Queried `roles`; used `trip_viewer` |
| R7 precondition reported `-1 expected table(s) missing` | The gate hardcodes the table count in **four** places and I updated two | All four; a comment now says so |
| 5 TypeScript errors after making `revokedAt` required | Every existing call site lacked the field | **Working as intended** — that is why it is required rather than optional. Fixed all five |
| 2 mypy `call-overload`, 1 ruff `S106` | `int(object)` from a DB row; a token literal read as a password | Narrowed via `str()`; suppression with justification |

### Mutation testing

| Seeded | Result |
| --- | --- |
| `validate_session` ignores `revoked_at` | **killed** by `test_a_revoked_session_fails_before_its_expiry` and 2 more |
| Revocation `DELETE`s instead of stamping | **killed** |
| `revoke_membership` stops cascading | **killed** |
| `revoke_all_for_user` not scoped to the user | **killed** |
| Raw token stored instead of the hash | **killed** by `test_no_raw_token_reaches_the_database` and 5 more |
| TypeScript validator ignores `revokedAt` | **killed** — 2 failed of 63 |
| `FORCE` RLS removed from `sessions` **in the database** | **SURVIVED — see below** |
| `FORCE` RLS removed from the **migration file** | **killed**, naming `sessions` |

### Notes

**One mutant survived, and finding out why was the most useful result here.**
Dropping `FORCE ROW LEVEL SECURITY` on `sessions` in the live database left R7
passing, because the suite **re-applies the migration before asserting** — it
repaired the drift it then checked. The seed had to go into the migration file
instead. Stated plainly: *a suite that heals the condition it tests cannot fail on
it*, and nothing surfaced that until a mutant was tried against it.

**The FORCE-RLS check listed three tables by name**, so a fourth tenant-scoped
table would have been unchecked while the assertion still passed. It is now derived
from the schema — every table with an `organization_id` must force RLS — so the
next such table is covered by whoever creates it. Same pattern as `BUG-021`.

**R7 grew by six assertions and one of them is a new kind.** Revoking across a
tenant boundary is denial of service rather than disclosure. The suite previously
only asserted that a tenant could not *read* another's rows.

### The finding that matters most, and it is not about this sub-step

**None of the database-backed security tests run in CI.** Measured on this
sub-step's `pnpm ci:local`:

| Environment | Python result |
| --- | --- |
| Local, dev stack up | **665 passed, 5 skipped** |
| CI mirror (Linux, cold install) | **624 passed, 46 skipped** |

Forty-one tests are gated on `@requires_db` and skip when Postgres is absent —
including **all 13 database-backed session-revocation tests added here**. Neither
`tests/ci-mirror.sh` nor `.github/workflows/verify.yml` provides a database.

Worse: **`pnpm test:security` is not in `pnpm verify` at all**, so R7 — the check
`CLAUDE.md` §2 calls non-negotiable — has never run in CI. It runs when a human
runs it, on a machine where the stack happens to be up.

This is **pre-existing**, dating from STEP-002.01 rather than introduced here. But
this sub-step just added thirteen more security assertions to the set that CI does
not execute, which makes it worth stating rather than inheriting. The skip is
visible in the output and nothing treats it as a failure, so a green CI run today
is not evidence that tenant isolation holds.

Recorded here rather than fixed: adding a Postgres service to CI is an
infrastructure change with its own blast radius, and doing it inside a security
sub-step is the widening `ENH-001` and `ENH-002` were logged to avoid. **Raised to
the owner as the recommended next piece of work.**

---

## STEP-004.08 — 2026-08-12 — Backward-compatibility and consumer contract tests

| Field | Value |
| --- | --- |
| Commit | *(this commit)* |
| Graph indexed commit | `eb30a26` — matched HEAD at pre-change |

| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression | **PASS** | **648 Python** (up from 592) + 61 web + 307 UI + 40 browser |
| R2 contract compatibility | **PASS — and now enforced rather than asserted** | Two fields became required in response/event shapes (BUG-021). The classifier delivered by this very sub-step rates that additive, and the gate prints it as such. **This is the first sub-step where R2 is a check rather than a judgement** |
| R3 graph diff as expected | **PASS** | Two new tools, one guard, one snapshot directory, three strengthened tests. `detect_changes()` recorded below |
| R4 untested requirements | **PASS — improved** | REQ-PLAT-008 newly covered |
| R5 orphan/unowned nodes | **PASS** | Catch-all owner |
| R6 closed-bug tests | **PASS** | BUG-001…021. Guard meta-suite **55/55** (up from 47: 8 new cases) |
| **R7 tenant isolation** | **PASS — 12/12** | Untouched |

**Overall:** PASS

### Failures and resolution

| Failure | Cause | Resolution |
| --- | --- | --- |
| `test_every_named_schema_on_the_wire_is_reachable` failed on 3 orphans | My test asserted `len(orphans) <= 2` — a threshold, not a property. The three are bare `$ref` aliases, deliberate named exports left by `.06` | Rewritten to assert what actually matters: an unreferenced schema must be a bare alias, never an inline definition. **Raising the threshold would have passed and tested nothing** |
| Consumer expectations named `TripCreate` | The schema is `CreateTripRequest`. Written from assumption rather than from the contract | Read the contract; corrected. Same failure shape as the STEP-003 e2e probes |
| 2 mypy `no-any-return` errors | `yaml.safe_load` and a dict lookup both return `Any` | Narrowed with explicit `isinstance` checks rather than casts |
| The gate reported "no differences" about a contract I had just changed | Safe required-ness changes were classified correctly and then **not reported at all** | Both directions now reported, additive included. Two regression tests added. *A tool silent about safe changes is telling the reader nothing moved* |

### Mutation testing

| Seeded | Result |
| --- | --- |
| Operation removed | **killed** |
| Response property removed | **killed** |
| The same removal behind a major version bump | **correctly PASSES** — the case that proves the gate is not simply alarmed |
| Deprecated operation with no `Sunset` | **killed** |
| Baseline snapshot moved silently | **killed** |
| `BASELINE.md` claiming a version the snapshot does not declare | **killed** |
| `JobEvent.sequence` reverted to optional | **killed** |
| `model_versions` reverted to optional | **killed** |
| An inline unreferenced schema | **killed** |

### Notes

**The audit promised at `.07` paid for itself.** Grepping every
`assert "x" in ...properties` found two real defects in twenty minutes that four
sub-steps of ordinary work had not. Both are BUG-021.

**And it caught me committing the same defect while auditing for it** — see the
orphan-threshold row above. Worth recording plainly: knowing a pattern by name did
not stop me writing it.

**R2 changes character from this sub-step onward.** Every previous entry answered
"no unintended breaking diff" by inspection. From here it is a gate with seeded
proof that it fails, and the honest caveat that it cannot see semantic change
(`ENH-001`, pending).

---

## STEP-004.07 — 2026-08-11 — Client generation and no-hand-edit enforcement

| Field | Value |
| --- | --- |
| Commit | *(this commit)* |
| Graph indexed commit | `73a2780` — matched HEAD at pre-change |

| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression | **PASS** | 592 Python + 61 web + 307 UI + 40 browser. `pnpm verify` green across all 22 steps |
| R2 contract compatibility | **PASS — and this was the last free moment** | `Evidenced.conflicts[]` narrowed: two required members added, object closed (BUG-020). `.06` recorded that such a change becomes breaking once clients exist. The fix and the **first ever generation** are in the same commit, so no client was ever produced from the defective shape. A week later this would have been a migration |
| R3 graph diff as expected | **PASS** | `detect_changes(staged)`: 58 symbols, 23 files, 1 affected process — `main → generate_typescript → run`, the generator's own flow. **No symbol from either generated client appears**, which is the exclusion doing its job |
| R4 untested requirements | **PASS — improved** | REQ-PLAT-007 newly covered by a mutation-tested guard |
| R5 orphan/unowned nodes | **PASS** | Catch-all owner; `guard:codeowners` green on the new `packages/contracts/` tree |
| R6 closed-bug tests | **PASS** | BUG-001…020. Guard meta-suite **47/47** (up from 43: 4 new cases for the drift guard) |
| **R7 tenant isolation** | **PASS — 12/12** | Untouched. No generated model has a tenant field, because no operation declares a tenant parameter |

**Overall:** PASS

### Failures and resolution

| Failure | Cause | Resolution |
| --- | --- | --- |
| `openapi-typescript` v7 crashed in the TypeScript compiler API | ADR-009 — TS 7 is the native compiler and ships no JavaScript API. **Third tool to assume one exists** | Pinned to v6, with the reason recorded at the pin rather than in a changelog |
| Generated Python failed at import: `SyntaxError: invalid character '—'` | `--custom-file-header` is inserted **verbatim**; a prose header is not a comment | Header pre-commented before being passed. The generator does not check that its own output parses |
| `TS2688: Cannot find type definition file for 'node'` | I copied `packages/ui`'s tsconfig into a package with no components, no tooling and no `@types/node` | Config rewritten from what the package actually contains |
| `pnpm lint` — 2 errors, 1 warning | An unnecessary `biome-ignore`, plus formatting and export ordering in the two hand-written files | Suppression removed and replaced with a comment explaining why the aliases are unused **by design**; `biome check --write` for the rest |
| `ruff S105` on generated `token = 'token'` | Ruff was linting generated output | `apps/api/src/generated` added to `extend-exclude`, matching biome's existing `!**/generated`. **A linter that rewrites generated output fights the generator through the drift guard, forever** |
| `ruff S603` on `subprocess.run` | A genuine security lint on a real subprocess call | Suppressed with justification at the call site — fixed argv from module constants, no shell, no caller-reachable parameter |
| One meta-test failed on the first full run | `typecheck.sh` — the new package's broken tsconfig | Fixed above. **The baseline loop caught a defect I had introduced, in a file the meta-suite does not know about** |

### Mutation testing

Every property claimed by this sub-step was seeded with a violation and confirmed to fail.

| Seeded | Result |
| --- | --- |
| Hand edit appended to the generated TypeScript | **killed** — exit 1, `DRIFT` |
| Field added to `openapi.yaml` without regenerating | **killed** — exit 1, `DRIFT` |
| `Money.amount_minor` retyped to `string` | **killed** at compile time |
| `Evidenced.status` widened with a third member | **killed** |
| `Evidenced` losing `validity` | **killed** |
| Conflict entry losing `validity` | **killed** |
| `access_label` losing `internal_only` | **killed** |
| Internal-code check inverted | **killed** |
| `ErrorCode` degraded to `string` | **killed** |
| `conflicts[].source` restored to `{type: object}` | **killed** — the BUG-020 regression test |

### Notes

**The generator found a contract defect that 592 Python tests could not.** BUG-020:
`Evidenced.conflicts[].source` was `{type: object}` and emitted as
`Record<string, never>` — an object permitted to hold nothing. Every YAML assertion
passed because they were all reading the document that was wrong. A second
representation of the same contract is a second reader, and this is the concrete
argument for generating clients rather than hand-writing them.

**A skip is not a pass.** `pnpm e2e` reports 20 passed, 3 skipped — unchanged from
STEP-003 closure, and the skips are the Auth0-dependent checks that need a live
tenant (`DEC-004`, still unverified against a real account).

**The graph exclusion is met; `.gitnexusignore` is not what meets it.** Measured at
`7b1489e` after the re-index: the index is identical with and without the generated
paths listed (353 files, 5,702 nodes, 7,993 edges), because GitNexus skips
`generated/` by default. A control probe ignoring `tools/gen_clients.py` removed 16
nodes, confirming the file works and the null result is real. Corrected in BR-034 §4;
the residual gap — nothing asserts the absence — is carried to `STEP-026`.

---

## STEP-004.06 — 2026-08-11 — Shared JSON Schemas including model-output schemas

| Field | Value |
| --- | --- |
| Commit | *(this commit)* |
| Graph indexed commit | `e1d3194` — matched HEAD at pre-change |

| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression | **PASS** | **592 Python** (up from 552) + 61 web + 307 UI + 40 browser |
| R2 contract compatibility | **PASS — but only because of the timing** | `Evidenced` changed its required set. Nothing consumes it, so nothing breaks; after `.07` generates clients the same change would be **breaking** |
| R3 graph diff as expected | **PASS** | Five JSON documents, one YAML refactor, one test module |
| R4 untested requirements | **PASS — improved** | REQ-AI-002 newly covered; REQ-AI-001 and REQ-AI-004 gain schema-level enforcement |
| R5 orphan/unowned nodes | **PASS** | Catch-all owner |
| R6 closed-bug tests | **PASS** | BUG-001…019; meta-suite 43/43 |
| **R7 tenant isolation** | **PASS — 12/12** | Untouched |

**Overall:** PASS

### Failures and resolution
| Failure | Cause | Resolution |
| --- | --- | --- |
| Two contract tests broke | They read the inline shapes the refactor moved | Both now assert the `$ref` exists and follow it |
| `NameError: json` | I used `json.loads` in a module that only imported `yaml` | Import added |
| mypy: `seeded` needed an annotation | A synthetic document in a meta-test — the same annotation I needed in `.03` | Annotated |

### Notes
**One of the two broken tests would have gone vacuous instead of red**, and that
is the finding worth keeping. It read `schemas["Money"]["properties"]`; after a
bare `$ref` there are no `properties`, so it would have iterated an empty set and
passed. Had I only added the library without refactoring, the duplication gate
would have been the only thing standing between the repository and two silently
diverging `Money` types — and the test that appeared to check `Money` would have
been checking nothing.

**R2 passes on timing, not on design.** `Evidenced` changing its required set is
harmless today because no consumer exists, and would be a breaking change after
`.07`. Doing the library before client generation rather than after was the
difference between a refactor and a migration.

---

## STEP-004.05 — 2026-08-11 — AsyncAPI event contracts

| Field | Value |
| --- | --- |
| Commit | *(this commit)* |
| Graph indexed commit | `d2f950b` — matched HEAD at pre-change |

| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression | **PASS** | **552 Python** (up from 492) + 61 web + 307 UI + 40 browser |
| R2 contract compatibility | **PASS** | A second contract document; `openapi.yaml` untouched |
| R3 graph diff as expected | **PASS** | One YAML document, one test module. **No symbol-level query was applicable and that is recorded rather than substituted for** |
| R4 untested requirements | **PASS — improved** | REQ-PLAT-006, REQ-DATA-008 newly covered; REQ-SEC-001 and REQ-PRIV-006/007 gain stream-level assertions |
| R5 orphan/unowned nodes | **PASS** | Catch-all owner covers `contracts/` |
| R6 closed-bug tests | **PASS** | BUG-001…019; meta-suite 43/43 |
| **R7 tenant isolation** | **PASS — 12/12** | Plus: `tenant_id` required on **every** envelope, and no payload may carry content |

**Overall:** PASS

### Failures and resolution
| Failure | Cause | Resolution |
| --- | --- | --- |
| mypy: two `no-any-return` | Helpers returning `Any` out of an untyped YAML tree | Annotated at the boundary rather than silenced |

Only one failure, and a trivial one — the first sub-step in a while where the
contract did not catch me out. Worth noting *why*: this document had a complete
register to work from (`EVENT_CONTRACTS.md` lists all eight events with payload,
delivery, retention and replay), whereas `.02` and `.03` were reconciling two
documents that had drifted.

### Notes
**The payload rule is the tenancy boundary for the entire stream**, and it is
worth restating as a rule rather than a schema detail: an event is read by
consumers that never authenticated the user who caused it. A payload carrying
content hands them data nobody checked they may see, and the check cannot be
added later because the data is already in the log.

**`exactly-once-effect`, not `exactly-once`.** No transport gives exactly-once
delivery. The contract names the consumer's obligation instead of implying the
transport absorbs it — and a test asserts the description says so, because this
is the guarantee most often written down wrongly.

---

## STEP-004.04 — 2026-08-11 — Privacy, admin, coverage and job operations

| Field | Value |
| --- | --- |
| Commit | *(this commit)* |
| Graph indexed commit | `6ea8436` — matched HEAD at pre-change |

| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression | **PASS** | **492 Python** (up from 469) + 61 web + 307 UI + 40 browser |
| R2 contract compatibility | **PASS** | Purely additive — 6 operations, 8 schemas |
| R3 graph diff as expected | **PASS**, with a caveat | Contract and tests only. **The graph reported `0 impacted` as `epistemic: exact` for a constant with five references** — see BR-031 §3 |
| R4 untested requirements | **PASS — improved** | REQ-PRIV-006/007 and REQ-EVID-006 gain contract assertions |
| R5 orphan/unowned nodes | **PASS** | Catch-all owner |
| R6 closed-bug tests | **PASS** | BUG-001…019; meta-suite 43/43 |
| **R7 tenant isolation** | **PASS — 12/12** | Coverage is public and **tenant-free by construction** — it has no tenant-scoped field to leak |

**Overall:** PASS

### Failures and resolution
| Failure | Cause | Resolution |
| --- | --- | --- |
| YAML would not parse | A description containing `` `kind: correction` `` — an unquoted colon-space reads as a mapping | Block scalar. The document is 1,700 lines and prose is where YAML bites |
| `ruff format` wanted one file | Long assertion lines in the new tests | Reformatted |

### Notes
**R3 carries a caveat that should not be skimmed.** `impact(CLIENT_VISIBLE)`
reported `0 impacted` with `epistemic: exact` for a constant referenced five
times across two files. Unlike the degraded concept search, which warns, this one
issues a guarantee — and a `0 impacted` on a constant is exactly the result that
persuades a reader they need not check further.

Six graph limitations are now recorded across BR-024…BR-031. Functions trace
correctly; nothing else reliably does. The operational rule, now in `CLAUDE.md`,
is that a zero result is trustworthy only for a Python function.

**A correction to a previous hand-off.** I had said `auth/errors.py` migrates to
RFC 9457 at `.04` and that invitation redemption lands here. Neither is true —
STEP-004 declares contracts only, and no route handler exists to verify a
migration against.

---

## STEP-004.03 — 2026-08-11 — Collaboration, booking, live and feedback

| Field | Value |
| --- | --- |
| Commit | *(this commit)* |
| Graph indexed commit | `dd01499` — matched HEAD at pre-change |

| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression | **PASS** | **469 Python** (up from 440) + 61 web + 307 UI + 40 browser |
| R2 contract compatibility | **PASS** | Purely additive — 7 operations, 11 schemas, nothing changed |
| R3 graph diff as expected | **PASS** | Contract and tests only; no Python behaviour changed |
| R4 untested requirements | **PASS — improved** | REQ-BOOK-004, REQ-SEC-008, REQ-CONS-011, REQ-PRIV-003 gain contract assertions |
| R5 orphan/unowned nodes | **PASS** | Catch-all owner |
| R6 closed-bug tests | **PASS** | BUG-001…019; meta-suite 43/43 |
| **R7 tenant isolation** | **PASS — 12/12** | Still no operation accepts a tenant parameter |

**Overall:** PASS

### Failures and resolution
| Failure | Cause | Resolution |
| --- | --- | --- |
| `test_all_nine_operations_are_declared` failed | It asserted **set equality** against exactly the nine operations `.02` added; `.03` correctly added five more | Changed to a subset assertion. An exhaustive check on a growing surface fails on every legitimate addition, which teaches whoever hits it to edit the test without reading it. A uniqueness check was added instead — duplicate `operationId`s generate one client method that silently calls the wrong endpoint |
| mypy: `seeded` needed an annotation | A synthetic document literal in the meta-test | Annotated |

### Notes
**Two stale assertions in two consecutive sub-steps** — `paths == {}` in `.02`,
and the exhaustive operation set in `.03`. Both were correct when written and
became wrong as the surface grew. The pattern is asserting the *current extent*
of something designed to extend; the fix in both cases was to assert the durable
property instead.

The most valuable assertion added here is the payment-field scan, and the second
most valuable is the test that proves the scan works. A test searching for
something absent passes identically when the search is broken — that is how a
"no credentials anywhere" guarantee quietly becomes a "no credentials in the
three schemas I remembered to check".

---

## STEP-004.02 — 2026-08-11 — Trip, brief and scenario operations

| Field | Value |
| --- | --- |
| Commit | *(this commit)* |
| Graph indexed commit | `c524820` — matched HEAD at pre-change |

| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression | **PASS** | **440 Python** (up from 405) + 61 web + 307 UI + 40 browser |
| R2 contract compatibility | **PASS** | Purely additive to `.01`, which declared no paths. Nothing existed to break |
| R3 graph diff as expected | **PASS** | `error_codes.py` regenerated; no Python behaviour changed |
| R4 untested requirements | **PASS — materially improved** | REQ-EVID-001/002/003, REQ-CONS-005/006, REQ-SEC-004 and REQ-PRIV-003 gain contract-level assertions |
| R5 orphan/unowned nodes | **PASS** | Catch-all owner covers `contracts/` |
| R6 closed-bug tests | **PASS** | BUG-001…019; meta-suite 43/43 |
| **R7 tenant isolation** | **PASS — 12/12** | Plus a structural one: **no operation accepts a tenant parameter** |

**Overall:** PASS

### Failures and resolution
| Failure | Cause | Resolution |
| --- | --- | --- |
| Three error codes declared by operations were unregistered | `API_CONTRACTS.md` is prose and nothing read it. Only visible once `.01` made the register generated | Two references corrected, two `validation.*` codes registered, and a **mutation-tested gate** added so the registers cannot drift again |
| `PUT /brief` had no `Idempotency-Key` | I reasoned that a conditional PUT is naturally idempotent | Wrong: a lost response leaves the retry with a stale `If-Match` and a 409, so the client cannot tell whether its change applied |
| Examples failed to validate — `Unresolvable` | The error-code enum is deliberately an **external** `$ref`, and the validator had no retriever | Resolver follows it. Without this the example tests would have passed while validating nothing |
| Examples failed — `additionalProperties` on a required field | `allOf` branches validate independently; a closed branch rejects a property another branch declares | `ConflictSet` is built for composition and is open. Leaves stay closed |
| Examples failed — relaxations were strings | `.01` guessed the remediation payload before an operation needed one | `Problem.remediation` fixes only `kind` |
| A `.01` test failed | It asserted `paths == {}` — true of `.01`, wrong the moment `.02` declared an operation | Replaced with the durable property: the shared components exist and are reusable |

### Notes
**Five of the six failures above are the contract catching itself**, before a
single handler exists. That is what contract-first is for, and it is measurably
cheaper here than at STEP-012 with the solver already written against a wrong
shape.

The one that would have hurt most is the unregistered error codes. It is not a
crash; it is a client branching on a code the server can never send, taking a
branch that is simply never reached, and nobody noticing for a year.

---

## STEP-004.01 — 2026-08-11 — Global API conventions

| Field | Value |
| --- | --- |
| Commit | *(this commit)* |
| Graph indexed commit | `f50d854` — matched HEAD at pre-change |

| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression | **PASS** | **405 Python** (up from 335) + 61 web + 307 UI + 40 browser |
| R2 contract compatibility | **N/A → now baselined** | `contracts/openapi.yaml` is created here and becomes authoritative (`ADR-001`). No operations declared, so nothing can break; from `.02` onward R2 has a real baseline to diff against |
| R3 graph diff as expected | **PASS** | New `conventions/` package and `tools/` generators; one modified test. **`impact(opaque_denial)` traced 2 callers and 1 execution flow — the first useful graph answer here** |
| R4 untested requirements | **PASS** | REQ-PLAT-005 newly covered; REQ-SEC-004 gains a signature-level assertion |
| R5 orphan/unowned nodes | **PASS** | Catch-all owner covers `contracts/` and the new package |
| R6 closed-bug tests | **PASS** | BUG-001…019; meta-suite 43/43 |
| **R7 tenant isolation** | **PASS — 12/12** | Plus a new assertion: a cursor may not carry a tenant, checked on decode |

**Overall:** PASS

### Failures and resolution
| Failure | Cause | Resolution |
| --- | --- | --- |
| Parser refused to run | `tenant.isolation_violation` is written `"500 + **SEV1 alert**"` | **Correct behaviour.** Resolved explicitly with the reasoning, rather than loosening the regex |
| `opaque_denial` returned **403** | The register writes "403/404"; the parser took the first, silently reversing STEP-002.02 | Forced to 404 at the call site. A test now pins the status, the body, the absent `detail` and the function signature |
| Package named `http` | `apps/api/src` is on `pythonpath`, so it **shadowed the standard library** for the whole application — nothing fails at import, things fail later somewhere else | Renamed to `conventions` before anything imported it |
| Cross-tenant ratchet fired on "cache" | The word `redis` appears inside a leak-**prohibition** regex; the detector searched raw source | Detector now strips comments and literals and matches usage. A new test proves the narrowing did not disable it |
| Money test passed for the wrong reason, then failed for the right one | `"float" not in json.dumps(money)` matched the schema's own warning about floats | Asserts on declared types and `additionalProperties: false` |
| `ruff` autofix + my sed removed `.encode()` from the wrong line | `fingerprint` would have hashed a `str` and raised | Caught by the suite immediately |
| mypy: no stubs for `yaml` | The contract tests parse the OpenAPI document | `types-PyYAML` added as a dev dependency |

### Notes
**Two error shapes now exist in the repository.** `auth/errors.py` still returns
its STEP-002.02 body and is *not* RFC 9457. Migrating it means changing a function
with two live callers inside a traced execution flow, with **no HTTP surface to
verify the migration against** — `apps/api` has no routes. Carried to STEP-004.04
and stated in `BR-028` §7 rather than left to be discovered.

**A third graph limitation surfaced.** `gitnexus_query` returned nothing and
warned that its full-text indexes are missing. The concept search `CLAUDE.md`
directs contributors to has been silently degraded for an unknown number of
sub-steps — it did not fail, it returned an empty result, which reads exactly like
"no such concept exists". Not repaired here, because re-indexing mid-change would
invalidate the pre-change state `BR-028` is written against. Carried to STEP-026.

---

## STEP-003.09 — 2026-08-11 — Visual design language

| Field | Value |
| --- | --- |
| Commit | *(this commit)* |
| Graph indexed commit | `3793494` — matched HEAD at pre-change |

| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression | **PASS** | 335 Python + 61 web + **307 UI** + 40 browser |
| R2 contract compatibility | **N/A** | Token keys added, none removed or renamed; no component API touched |
| R3 graph diff as expected | **PASS** | Palette constants, `contrastPairs`, `renderCss`, two stylesheets. **CSS has no representation in the graph at all**, so the component-level reach is established by the browser suite instead — stated in BR-026 §3 rather than left implied |
| R4 untested requirements | **PASS** | 12 new contrast pairs newly proven |
| R5 orphan/unowned nodes | **PASS** | Catch-all owner covers all changed paths |
| R6 closed-bug tests | **PASS** | BUG-001…018; meta-suite 43/43 |
| **R7 tenant isolation** | **PASS — 12/12** | Untouched |

**Overall:** PASS

### Failures and resolution
| Failure | Cause | Resolution |
| --- | --- | --- |
| Touch targets below 24×24, both profiles | I shrank checkbox and radio to 20px because it looks better beside 14px labels | Back to 24. SC 2.5.8 applies to the control, not the row it sits in |
| 2px horizontal overflow at 320px | Gallery grid minimum raised to 22rem; a grid item's default `min-width: auto` refuses to shrink below its widest word | `min-inline-size: 0` and `overflow-wrap: anywhere` on the list cells |
| A further 2px of overflow | `margin: -1px` left on the visually-hidden pattern from the older `clip: rect()` technique | Removed. `clip-path` does not need it |
| Contrast test failed on my own invented threshold | I declared a 1.4:1 floor for the hairline and then chose a colour at 1.26:1 | Hairline darkened to clear it, and the comment now says plainly that the number is this project's choice, not a WCAG requirement |
| Status-coverage test failed on the new tints | The rule could not distinguish a signal colour from a background | Rule sharpened to exclude the `-surface` suffix, **plus a second test proving the exclusion did not disable it** |
| INP reported 422ms once, 7ms when idle | Single-sample lab measurement on a loaded machine | Median of five. BUG-016: a flaky gate is worse than a failing one |
| **`pnpm ci:local` failed twice with 7 of 8 UI suites unable to collect** | Not a code fault. Docker gives the container **4 GB**; vitest spawns one worker per CPU and each builds its own jsdom with axe-core loaded, so eight workers exhaust it. The main thread then cannot answer transform requests and every suite dies with `[vitest-worker]: Timeout calling "fetch"` — a message that names no file of ours and reads like a module-resolution failure | `packages/ui/vitest.config.ts` caps workers at 2 and raises the transform timeout **under CI only**, so the local path stays fast. Verified by running the capped path locally with `CI=true`: 307 passed either way |

### A note on that last one
It is worth being precise about why capping concurrency is a fix and not a
workaround. A suite that only passes with several gigabytes of free memory is
fragile everywhere — a CI runner is always a shared, constrained machine, and
this one would have been one bad scheduling day away from failing in GitHub
Actions too. The cap makes the memory ceiling explicit instead of implicit.

My first two readings of this failure were both wrong, and both were wrong in
the same way: the error text mentions a module path, so I looked for a
dependency problem — first a `vite-node` version mismatch in the lockfile
(there was none), then an incomplete install (there was none). The message named
the wrong cause and I believed it twice before capturing the full log.

### Notes
**The order was the point.** Three of the six failures above are accessibility
defects introduced by a design pass, caught by a gate built one sub-step earlier.
Each looks fine by hand and passes in jsdom. Had `.09` come first, all three
would have shipped and been found — if at all — in an audit months later.

The 20px checkbox is the clearest example: it is a better-looking control, it is
easier to hit than the browser default it replaced, and it is below a standard.
Judgement alone does not catch that; a measurement does.

---

## STEP-003.08 — 2026-08-10 — Automated keyboard and axe checks in CI

| Field | Value |
| --- | --- |
| Commit | *(this commit)* |
| Graph indexed commit | `1d67ffc` — matched HEAD at pre-change |

| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression | **PASS** | 335 Python + 61 web + **267 UI** + **40 browser** |
| R2 contract compatibility | **N/A** | No contracts yet. `packages/ui` gained 7 exports and a `./components.css` entry point; nothing removed |
| R3 graph diff as expected | **PASS** | `detect_changes()` scope as expected — see note below |
| R4 untested requirements | **PASS — materially improved** | Six criteria carried from .01–.07 closed, plus the STEP-002.05 auth-page carry. CWV field measurement recorded unmet, not counted |
| R5 orphan/unowned nodes | **PASS** | Catch-all owner covers `apps/web/src/test/`, `src/app/dev/`, `packages/ui/src/a11y/` |
| R6 closed-bug tests | **PASS** | BUG-001…017 guards pass; meta-suite **43/43** |
| **R7 tenant isolation** | **PASS — 12/12** | Untouched. Nothing here reads tenant data; the counter is per-instance so a server process cannot mix signals |

**Overall:** PASS

### Failures and resolution
| Failure | Cause | Resolution |
| --- | --- | --- |
| **7 browser tests failed on the first run** | Real defects: sub-24px controls, unstyled components, a contrast failure, 32px reflow overflow, forced-colors overridden | All fixed. Enumerated in BR-025 §6 and IMPL-022 |
| 2 of those 7 were **my test's fault, not the product's** | The drawer test did not set a mobile viewport, so it waited for a button correctly hidden above 48rem; the target-size test counted the skip link, which is 1×1 until focused by design | Viewport set; visually-hidden-until-focus detected by the clip technique rather than by exempting anything small |
| A fix introduced a regression one run later | `.jl-gallery a` (specificity 0,1,1) outranked `.jl-nav__link` (0,1,0) and replaced its 44px minimum with 24px | Narrowed to `.jl-gallery__switch`. A gallery must never restyle its specimens |
| `pnpm --filter @journeylab/ui tokens:build` failed | Node's ESM resolver needs explicit extensions; the whole import chain was extensionless | **BUG-018** |
| `pnpm typecheck` then failed in a *different* package | `apps/web` typechecks `packages/ui/src/tokens.ts` through the workspace import and needed the same `allowImportingTsExtensions` | Added there too. Only the full per-package run revealed it |
| A screenshot showed every stylesheet missing | An orphaned `next start` on port 5708 from an earlier run was serving the previous build's HTML, referencing a chunk hash that no longer existed | Not a code defect. The gate guard now refuses to run if the port is occupied rather than measuring the wrong server |
| **`pnpm ci:local` failed three times after the commit, and every failure was worth having** | See below | Fixed; the mirror is green |

### What only the Linux mirror could find
Three failures appeared after the commit and before the push, none of which the
development machine could produce. This is the third sub-step in a row where the
mirror earned its cost.

| # | Failure | Cause |
| --- | --- | --- |
| 1 | `playwright install --with-deps` could not find a single package | The container's apt index is stale and its sources use plain HTTP, which the local egress path blocks — while `apt-get update` **still exits 0**, having quietly kept an empty index. Fixed by switching sources to HTTPS and retrying |
| 2 | The accessibility run died with `127.0.0.1:5708 is already used` | `gallery-gate.sh` cleaned up with `lsof`, **which is not installed in node:24-bookworm**. The cleanup silently did nothing, the guard still reported PASS, and the next step inherited an occupied port. Liveness is now decided by asking the server with curl, and the guard escalates until the port is genuinely free |
| 3 | The seeded-violation meta-test found no violation | The seed is prepended to `<body>`, which React owns. On Linux, hydration finished **after** the injection and discarded it — so the one test that proves the gate can fail had stopped testing anything. Now waits for hydration and asserts the seed is still in the DOM before running axe |

A fourth failure was an assertion of mine that was simply wrong on a narrow
viewport: the RTL check asserted the skip link's `x > width / 2`, which fails at
412px because the link is ~200px wide and its *left* edge sits just left of
centre while its right edge is correctly pinned to the right. Measured from the
trailing edge now, which is the property that was meant.

### Notes
**R3 needs a caveat, and it is a bigger one than last time.** BR-024 recorded that
the graph does not follow `workspace:*` aliases. This sub-step established
something sharper: `impact(SkipLink)` returns **0 impacted** against eight real
references, because `SkipLink` is only ever used as JSX and the graph records
`CALLS` edges from function calls. **Component-level impact analysis in this
repository is unreliable by construction** until STEP-026 addresses it, and a
`0 impacted` result on a component means "not traced".

The value of this sub-step was not the harness. It was discovering that seven
sub-steps of "accessible components" had never been rendered by anything with a
layout engine, and that 28 of 40 component classes had no styling at all. Every
geometric assertion in the jsdom suites was vacuous, and nothing in those suites
could have said so.

---

## STEP-003.07 — 2026-08-10 — Locale, time zone, currency and DST handling

| Field | Value |
| --- | --- |
| Commit | *(this commit)* |
| Graph indexed commit | `bb943f9` — matched HEAD at pre-change |

| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression | **PASS** | 335 Python + **61 web** + **256 UI**; also green under 5 different host time zones |
| R2 contract compatibility | **N/A** | No contracts yet (STEP-004). `packages/ui` gained 25 exports and removed none |
| R3 graph diff as expected | **PASS** | `detect_changes()` reports 3 touched symbols, all in `layout.tsx` (`RootLayout`, `MAIN_ID`, `dir`), 0 affected processes. New files are not yet indexed — they appear after the post-commit re-index |
| R4 untested requirements | **PASS** | `REQ-NFR-007` and `REQ-NFR-008` newly covered. Real-browser RTL rendering recorded unmet, not counted |
| R5 orphan/unowned nodes | **PASS** | Catch-all owner covers `packages/ui/src/i18n/`, `apps/web/src/lib/` and the new guard |
| R6 closed-bug tests | **PASS** | BUG-001…016 guards pass; meta-suite 40/40 |
| **R7 tenant isolation** | **PASS — 12/12** | Untouched. Nothing here reads tenant data or derives a cache key from the locale |

**Overall:** PASS

### Failures and resolution
| Failure | Cause | Resolution |
| --- | --- | --- |
| `pnpm --filter @journeylab/web build` failed | **Pre-existing at `bb943f9`** — Next's type-check step needs a TypeScript compiler API that TypeScript 7 does not ship | Logged `BUG-017`; `pnpm build` added to `verify` so it cannot break silently again |
| `pnpm ci:local` failed **after** the commit | My first BUG-017 fix (`ignoreBuildErrors`) does not gate Next's probe — it works on a developer machine and aborts under `CI=true` | Real fix applied (`@typescript/native-preview` marker), commit amended, mirror re-run green. **The mirror caught this before the push, which is what it is for** |
| 2 UI tests failed on first run | `formatRelative(48, 'de-DE')` is `übermorgen`, not "in 2 Tagen"; and `formatDateTime` did **not** throw on a missing zone | The first was a wrong expectation. The second was a real defect — `Intl` treats `timeZone: undefined` as the system zone, so `assertZone` was added |
| 1 web test failed on first run | The source check for a dynamic import matched the module's own **documentation**, which quotes the forbidden pattern to explain it | Comments are stripped before matching, plus an assertion that stripping left the code intact |
| 3 mutants survived | Three tests passed for the wrong reason — see IMPL-021 | All three tests rebuilt so the mutants die; re-run confirms |
| 2 mutants survive by design | Recorded as **equivalent** with the evidence, not silently dropped | See IMPL-021 |

### Notes
`detect_changes()` reporting only `layout.tsx` is expected and not reassuring on its own: the graph does not follow `workspace:*` package aliases, so the `packages/ui` → `apps/web` edge is invisible to it. That limitation is stated in `BR-024` §3 rather than left as an apparent clean bill of health, and is a candidate finding for STEP-026.

The most valuable output of this sub-step was not the code. It was finding three tests that asserted things they could not have failed on, and one comment of mine that was simply false. Every one of those surfaced through mutation testing, and none would have surfaced from a green run.

---

## STEP-003.06 — 2026-08-10 — Role-aware desktop and mobile navigation

| Field | Value |
| --- | --- |
| Commit | *(this commit)* |
| Graph indexed commit | `94bf916` — matched HEAD at pre-change |

| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression | **PASS** | 335 Python + 41 web + **220 UI** |
| R2 contract compatibility | **N/A** | No contracts yet (STEP-004) |
| R3 graph diff as expected | **PASS** | New `packages/ui/src/nav/`, a second matrix emitter, shell header wired. **The Python emitter is untouched** |
| R4 untested requirements | **PASS** | `REQ-A11Y-001` improved. **`REQ-SEC-004` not fully closed** — the server-denial test needs routes that do not exist |
| R5 orphan/unowned nodes | **PASS** | Catch-all owner covers both packages and `tools/` |
| R6 closed-bug tests | **PASS** | BUG-001…016 guards pass |
| **R7 tenant isolation** | **PASS — 12/12** | Untouched |

**Overall:** PASS

### Failures and resolution
| Failure | Cause | Resolution |
| --- | --- | --- |
| Biome `useValidAriaRole` ×5 | A React prop named `role` is read as the HTML ARIA attribute | Renamed to `actorRole` rather than suppressed — the collision is real for readers too, and I had just added two suppressions that suppressed nothing |
| Two assertions broke after the rename | The blanket regex also renamed a loop variable called `role` | Reverted those two lines. A regex rename is not a refactor; typecheck caught it |

### Notes
`ADR-012`'s review trigger fired and its prediction held: the second emitter reuses the shared parser unchanged, so the TypeScript and Python matrices cannot diverge.

The most important assertions here are not about rendering. They establish that hiding a nav item is **not** an authorization control and cannot quietly become one: `visibleItems` contains no `fetch`, `redirect` or `throw`, the `href` survives filtering, and the module says so in words a future reader will meet before the code.

---

## STEP-003.05 — 2026-08-07 — Application frame, providers and global error boundary

| Field | Value |
| --- | --- |
| Commit | *(this commit)* |
| Graph indexed commit | `b09a0a2` — matched HEAD at pre-change |

| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression | **PASS** | 335 Python + 41 web + **199 UI** |
| R2 contract compatibility | **N/A** | No contracts yet (STEP-004) |
| R3 graph diff as expected | **PASS** | New shell modules; `apps/web` layout replaced; **import specifiers and `'use client'` changed across every `packages/ui` module** — wider than a typical sub-step, and deliberate |
| R4 untested requirements | **PASS** | Decreased for `REQ-NFR-013`. **`REQ-A11Y-001` not fully closed** — CWV unmeasurable here |
| R5 orphan/unowned nodes | **PASS** | Catch-all owner covers both packages |
| R6 closed-bug tests | **PASS** | BUG-001…016 guards pass |
| **R7 tenant isolation** | **PASS — 12/12** | Untouched. The provider order documents the client-side equivalent: nothing that fetches sits above the session |

**Overall:** PASS

### Failures and resolution
| Failure | Cause | Resolution |
| --- | --- | --- |
| `apps/web` typecheck failed | `packages/ui` used `.ts`/`.tsx` import specifiers, which require every consumer to enable `allowImportingTsExtensions` | All relative imports made extensionless. **Invisible until a real app consumed the package** |
| Dev server rendered the pages-router error page | Seven modules use hooks or class lifecycle without `'use client'` | Directive added. Same root cause: only visible once a real app imported it |
| Biome: suppression has no effect | A `biome-ignore` in `providers.tsx` for a rule that never fires | Removed. **Second time in two sub-steps** — a pattern in my own work |
| Parse error after removing a role | JSX comment placed beside the root element of a `return` | Rationale moved to the doc comment. **Also the second time** |

### Notes
CWV budgets (`FRONTEND_ARCHITECTURE` §7) are recorded as **unmet, not assumed**. They need a real browser and Lighthouse, which arrive at STEP-003.08.

---

## STEP-003.04 — 2026-08-07 — Table, list and CSV export

| Field | Value |
| --- | --- |
| Commit | *(this commit)* |
| Graph indexed commit | `c358d4b` — matched HEAD at pre-change |

| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression | **PASS** | 335 Python + 41 web + **179 UI** |
| R2 contract compatibility | **N/A** | No contracts yet (STEP-004) |
| R3 graph diff as expected | **PASS** | New `packages/ui/src/data/`; one dead lint suppression removed |
| R4 untested requirements | **PASS** | Decreased — `REQ-A11Y-002` now has table, list and CSV coverage |
| R5 orphan/unowned nodes | **PASS** | Catch-all owner covers `packages/ui/**` |
| R6 closed-bug tests | **PASS** | BUG-001…016 guards pass |
| **R7 tenant isolation** | **PASS — 12/12** | Untouched |

**Overall:** PASS

### Failures and resolution
| Failure | Cause | Resolution |
| --- | --- | --- |
| Biome: suppression has no effect | A `biome-ignore` added defensively in `dialog.tsx` suppressed a rule that never fired | Removed. A suppression claiming a rule applies where it does not misleads the next reader |
| Biome: `role="region"` should be `<section>` | Correct — a native element carries the role implicitly | Switched to `<section aria-label>` |
| Parse error after that fix | I placed a JSX comment before the root element of a `return` | Rationale moved to the doc comment |

### Notes
CSV export was treated as a security surface. Formula injection is neutralised by prefixing dangerous cells with `'`, and the mutation removing that defence fails two tests — including one asserting the specific `=HYPERLINK(...)` exfiltration payload.

Export uses the full sorted set rather than the rendered window; a mutation to the latter fails, because a silently truncated file is worse than a slow one.

---

## STEP-003.03 — 2026-08-07 — Feedback primitives

| Field | Value |
| --- | --- |
| Commit | *(this commit)* |
| Graph indexed commit | `b28bf15` — matched HEAD at pre-change |

| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression | **PASS** | 335 Python + 41 web + **152 UI** |
| R2 contract compatibility | **N/A** | No contracts yet (STEP-004) |
| R3 graph diff as expected | **PASS** | New `packages/ui/src/feedback/`; no existing symbol modified |
| R4 untested requirements | **PASS** | Decreased — `REQ-A11Y-004` gains state coverage; `REQ-EVID-005`, `REQ-CONS-005` and `REQ-NFR-003` gain UI-level enforcement |
| R5 orphan/unowned nodes | **PASS** | Catch-all owner covers `packages/ui/**` |
| R6 closed-bug tests | **PASS** | BUG-001…016 guards pass |
| **R7 tenant isolation** | **PASS — 12/12** | Untouched |

**Overall:** PASS

### Failures and resolution
| Failure | Cause | Resolution |
| --- | --- | --- |
| Three dialog focus tests failed | The visibility filter used `offsetParent !== null`; jsdom computes no layout so it is always null, and the trap silently did nothing | Replaced with `hidden` / `aria-hidden` / `inert` checks. **This was a real defect, not a jsdom quirk** — `offsetParent` is also null for `position: fixed` elements, which a dialog usually is |

### Notes
Three requirements are enforced by making the wrong thing unconstructible rather than discouraged: `Progress` cannot be built without a label and a cancel path (`REQ-NFR-003`), `InfeasibleState` throws on an empty conflict set (`REQ-CONS-005`), and `StaleDataState` cannot be rendered without naming its subject and observation time (`REQ-EVID-005`).

---

## STEP-003.02 — 2026-08-06 — Form and input primitives with validation states

| Field | Value |
| --- | --- |
| Commit | *(this commit)* |
| Graph indexed commit | `0e3ea40` — matched HEAD at pre-change |

| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression | **PASS** | 335 Python + 41 web + **107 UI** |
| R2 contract compatibility | **N/A** | No contracts yet (STEP-004) |
| R3 graph diff as expected | **PASS** | New `packages/ui/src/form/`; guard + dev-dependency change for BUG-016 |
| R4 untested requirements | **PASS** | Decreased — `REQ-A11Y-001` now has axe coverage on every primitive |
| R5 orphan/unowned nodes | **PASS** | Catch-all owner covers `packages/ui/**` |
| R6 closed-bug tests | **PASS** | BUG-001…015 guards pass |
| **R7 tenant isolation** | **PASS — 12/12** | Untouched — presentation primitives hold no data |

**Overall:** PASS

### Failures and resolution
| Failure | Cause | Resolution |
| --- | --- | --- |
| `verify` failed on "workflow YAML does not parse" | The guard fetched pyyaml at run time via `uv run --with`; a transient network failure was blamed on the workflows | `BUG-016` — pyyaml pinned as a locked dev dependency; the unavailable branch now states it is not a workflow problem |
| Typecheck rejected the prop interfaces | `CommonProps` marks disabled/readOnly/required readonly; the native attribute types do not, so TypeScript refused the merge | Native keys omitted so `CommonProps` owns them — the right complaint, since two sources for one prop is how disabled and readOnly get conflated |
| Biome rejected `aria-required` twice | `input[type=date]` has no ARIA role; a fieldset maps to `role="group"`, which does not support it either | Switched to the **native** `required` attribute, which maps to the same accessibility property |
| A mutant appeared to survive | My harness replaced the first textual occurrence, which was inside a docstring rather than the JSX | Re-run against the attribute — two tests failed as they should |

### Notes
axe passing on the first run was treated as suspicious rather than reassuring. Before trusting it, it was proven to fail on an unlabelled input and an image with no alt; both proofs are now permanent tests, because "zero violations" is otherwise indistinguishable from axe not running.

---

## STEP-003.01 — 2026-08-06 — Design tokens including high-contrast and reduced-motion

| Field | Value |
| --- | --- |
| Commit | *(this commit)* |
| Graph indexed commit | `9f5ff36` — matched HEAD at pre-change |

| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression | **PASS** | 335 Python + 41 web + **68 UI** |
| R2 contract compatibility | **N/A** | No contracts yet (STEP-004) |
| R3 graph diff as expected | **PASS** | One new package. No existing symbol modified |
| R4 untested requirements | **PASS** | Decreased — `REQ-A11Y-004` and `REQ-NFR-013` now have computed coverage |
| R5 orphan/unowned nodes | **PASS** | Catch-all owner covers `packages/ui/**` |
| R6 closed-bug tests | **PASS** | BUG-001…015 guards pass |
| **R7 tenant isolation** | **PASS** | Untouched — tokens carry no data |

**Overall:** PASS

### Failures and resolution
| Failure | Cause | Resolution |
| --- | --- | --- |
| The drift test could never fail | The generator wrote `tokens.css` at module top level, so importing it rewrote the file the test was about to compare | Write guarded behind a direct-invocation check; a hand-edited file now breaks the suite |

### Notes
The sub-step file predicted the graph would be `BLOCKED — no application symbols indexed yet`. That prediction is stale: application code has been indexed since STEP-002.02, so this pre-change check was **RUNNABLE**.

Every accessibility assertion is computed from token values rather than asserted about them, and the contrast function is itself verified against published WCAG reference values first — without that, the other 60-odd assertions would be meaningless.

---

## STEP-002.07 — 2026-08-06 — Audit event emission and runtime flag primitives

| Field | Value |
| --- | --- |
| Commit | *(this commit)* |
| Graph indexed commit | `d7d71cf` — matched HEAD at pre-change |

| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression | **PASS** | 335 Python + 41 TypeScript |
| R2 contract compatibility | **N/A** | No contracts yet (STEP-004). Migration 002 is additive |
| R3 graph diff as expected | **PASS** | Migration 002, three new modules, one test module. No existing symbol modified |
| R4 untested requirements | **PASS** | Decreased — `REQ-SEC-007` and `REQ-PLAT-012` now have executable coverage |
| R5 orphan/unowned nodes | **PASS** | Catch-all owner covers `services/audit/**` |
| R6 closed-bug tests | **PASS** | BUG-001…015 guards pass |
| **R7 tenant isolation** | **PASS** | Shell 12/12; isolation suite 14+5. **Both new tables are RLS `ENABLE` + `FORCE`** |

**Overall:** PASS

### Failures and resolution
| Failure | Cause | Resolution |
| --- | --- | --- |
| Flag inserts rejected with a not-null violation | `PRIMARY KEY (key, organization_id)` makes both columns implicitly `NOT NULL`, so the NULL-means-global row was impossible | Surrogate key + two partial unique indexes — which also prevents duplicate global rows that `(key, NULL)` would have allowed |
| A tuple containing a private key survived redaction | `_redact_value` handles dict/list/str only; the safety sweep did not traverse tuples either, so the fail-closed branch was unreachable | Sweep now checks the string form of unhandled types |
| Test data too short to match the JWT pattern | My sample, not the code | Corrected |
| ruff N802 on an uppercase test name | Style | Renamed |

### Notes
Append-only is enforced by **privilege**, not convention: `journeylab_app` holds INSERT and SELECT only, and `UPDATE`/`DELETE`/`TRUNCATE` were each verified to return `permission denied` against the live database.

---

## STEP-002.06 — 2026-08-06 — Cross-tenant isolation test suite

| Field | Value |
| --- | --- |
| Commit | *(this commit)* |
| Graph indexed commit | `2687bbe` — matched HEAD at pre-change |

| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression | **PASS** | 311 Python + 41 TypeScript |
| R2 contract compatibility | **N/A** | No contracts yet (STEP-004) |
| R3 graph diff as expected | **PASS** | One new test module. **No application symbol modified** |
| R4 untested requirements | **PASS** | Decreased — `REQ-SEC-002` now has executable coverage across five vectors |
| R5 orphan/unowned nodes | **PASS** | Catch-all owner covers `tests/**` |
| R6 closed-bug tests | **PASS** | BUG-001…015 guards pass |
| **R7 tenant isolation** | **PASS** | Shell suite 12/12; **new pytest suite 14 passed, 5 pending**. R7 now runs in the fast tier |

**Overall:** PASS

### Failures and resolution
None. The suite passed on first run; the work was in proving it *could* fail.

### Notes
Five vectors have nothing to test yet (cache, outbox, export, vector store, graph). Rather than omit them or let them pass vacuously, each detects whether its subsystem has landed — skip while absent, **fail** once present. Verified by seeding a fake cache module and an `outbox` table; each converted its placeholder into a failure naming the subsystem.

Mutation testing killed 3/3. The suite's own meta-test disables the RLS policy, asserts the storage vector leaks, and restores it — without which every other assertion could pass with row-level security switched off.

---

## STEP-002.05 — 2026-08-06 — Browser session, token refresh and guest sessions

| Field | Value |
| --- | --- |
| Commit | *(this commit)* |
| Graph indexed commit | `c58be3b` — matched HEAD at pre-change |

| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression | **PASS** | 292 Python + **41 TypeScript**; `pnpm test` now runs both |
| R2 contract compatibility | **N/A** | No contracts yet (STEP-004) |
| R3 graph diff as expected | **PASS** | New `apps/web` package, rewritten typecheck guard, workspace config. No existing symbol modified |
| R4 untested requirements | **PASS** | `REQ-PRIV-001` now tested. **`REQ-SEC-003` counted as still partial** — unverified against a live Auth0 tenant, and the accessibility criterion has no UI to test |
| R5 orphan/unowned nodes | **PASS** | Catch-all owner covers `apps/web/**` |
| R6 closed-bug tests | **PASS** | BUG-001…012 guards pass |
| **R7 tenant isolation** | **PASS — 12/12** | Untouched by this sub-step |

**Overall:** PASS

### Failures and resolution
| Failure | Cause | Resolution |
| --- | --- | --- |
| `typecheck.sh` produced a wall of TS1295/TS2835 | It ran one root config over every package; `apps/web` needs its own module settings | Guard rewritten for per-package configs, and it now fails if a TypeScript package declares no typecheck script |
| Every file treated as CommonJS | `apps/web/package.json` had no `"type": "module"` | Added. **Found by the typecheck guard on its first real run** |
| `vi.fn<[string], Promise<X>>()` rejected | vitest 3 changed the generic to a function type | Updated |
| `pnpm install` refused to build | pnpm 11 blocks install scripts by default | `onlyBuiltDependencies` allowlist with a stated reason per entry, not a blanket approval |

### Notes
Two guards stopped reporting vacuous passes for the first time since STEP-001 — `typecheck.sh` and `module-boundaries.sh`. The latter now checks 7 real files.

R4 does **not** count `REQ-SEC-003` as satisfied. The session mechanics are implemented and mutation-tested, but "sign-in, refresh and sign-out work" has been proven against a conforming OIDC provider, **not** against Auth0, and the accessibility criterion cannot be met until a UI exists.

---

## STEP-002.04 — 2026-08-06 — Identity provisioning

| Field | Value |
| --- | --- |
| Commit | *(this commit)* |
| Graph indexed commit | `19a6037` at pre-change; HEAD advanced to `972b93f` mid-sub-step (BUG-012) |

| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression | **PASS** | `pnpm verify`; 292 tests (was 276) |
| R2 contract compatibility | **N/A** | No contracts yet (STEP-004) |
| R3 graph diff as expected | **PASS** | One new service module, one test module, pyproject paths. No existing symbol modified |
| R4 untested requirements | **PASS** | `REQ-SEC-003` now tested. **`REQ-TRIP-005` remains untested in substance** — no trips exist; counted as still-open, not as satisfied |
| R5 orphan/unowned nodes | **PASS** | Catch-all owner covers `services/**` |
| R6 closed-bug tests | **PASS** | BUG-001…012 guards pass |
| **R7 tenant isolation** | **PASS — 12/12** | Plus a new test asserting provisioning's owner privilege did not leak: `journeylab_app` still `NOBYPASSRLS`, FORCE RLS intact on all 3 tables |

**Overall:** PASS

### Failures and resolution
| Failure | Cause | Resolution |
| --- | --- | --- |
| CI red mid-sub-step | Generated `matrix.py` committed lint-dirty; I verified, then regenerated, then committed | `BUG-012` — generator now self-formats. Fixed and pushed before continuing |
| 8 provisioning tests failed | Fixtures used raw INSERTs that violated `users_identifiable_unless_guest` | Fixtures rebuilt on `provision_user`, so they cannot drift from the schema |
| A claimed schema gap did not exist | I reported `idp_subject` had no unique index; my own `head -14` had truncated the index list | Retracted. The unique index exists and the race test disproved the claim |

### Notes
R4 deliberately does **not** count `REQ-TRIP-005` as satisfied. The migration guarantee is implemented and replay-tested, but it has no trips to apply to until STEP-007. Marking it green here would make the ratchet report progress that does not exist.

---

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
