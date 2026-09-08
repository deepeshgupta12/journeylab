---
blast_radius_id: BR-061
sub_step_id: STEP-007.03
title: Date and geography validation, and the contradiction it had to resolve
author: Deepesh Kumar Gupta
date: 2026-09-04
score: MEDIUM
confidence: MEDIUM
approval_required: true
---

# BR-061 — Date and geography validation

## 1. Graph state

| Field | Value |
| --- | --- |
| Indexed commit | `7adead2` |
| HEAD at check | `7adead2` |
| Freshness | ✅ up to date |
| Result | **NOT BLOCKED** |
| Confidence | **MEDIUM** — `RISK-016`, and see §2 |

## 2. Queries run, and the one that was wrong

| Symbol | Graph (upstream) | Grep (non-test) | Agree? |
| --- | --- | --- | --- |
| `read_coverage` | 1 — `get_coverage`, LOW | 1 | ✅ |
| `CoverageModel.assess` | 1 — `public_view`, LOW | 1 | ✅ |
| `get_coverage` | **0, LOW** | **1 — `app.py:126`** | ❌ |

The third row is `RISK-016` reproduction **#13**, and it is the sharpest one so far.
The previous twelve were cross-language, dynamic dispatch, or a symbol the parser
never saw. This one is a direct, static, same-language call between two nodes the
graph already holds, and the graph says the blast radius is empty.

I checked why rather than recording the symptom, because the answer changes what
else I cannot trust:

```
MATCH (a)-[r:CodeRelation]->(b)
WHERE a.filePath='apps/api/src/app.py' OR b.filePath='apps/api/src/app.py'
```

`apps/api/src/app.py` has **no outgoing `IMPORTS` edge and no outgoing `CALLS` edge
that leaves the file.** Its only `CALLS` edge is `lifespan → database_url`, which is
module-local. `Function:apps/api/src/app.py:coverage` — the only route handler in the
application — has **zero edges in either direction**. It is an island with a name.

This is not a general Python limitation, which is what makes it dangerous. Measured
across the repository:

| Edge class | Count |
| --- | --- |
| Python `CALLS`, same file | 750 |
| Python `CALLS`, cross file | **450** |
| Python file→file `IMPORTS` | 75 |

Cross-file resolution works 450 times and fails for this file. So the failure is not
announced anywhere: `impact` returns `"risk": "LOW", "epistemic": "exact"` — a
confident, well-formed, wrong answer, which is the same failure mode as
`gitnexus_query` returning empty (`BR-029` §3) and worse, because that one at least
prints a warning.

**The practical consequence, and it is not confined to this sub-step:** every impact
query on any symbol the API application consumes under-reports by exactly the API
application. `apps/api/src/app.py` is the only deployable HTTP surface in the
repository (`ADR-003`). A query that misses it misses the product.

Recorded against `RISK-016`. The mitigation is unchanged and now has a number
attached: grep is the authority, the graph is the hint.

### Queries that ran and returned nothing useful

`api_impact({file: "apps/api/src/app.py"})` resolves `/coverage` and reports
`directConsumers: 0, riskLevel: LOW`. It is reading the same missing edges.
`check({cycles: true})` is clean. Both are recorded so that "ran and was empty" is
distinguishable from "was not run".

## 3. One word, two meanings, and one of them is an enum value

Four documents say a degraded region refuses new trips. One of them is a contract:

| Where | Words |
| --- | --- |
| `STEP-007` §9 | "Provider degraded → **Refuse rather than partially simulate**" |
| `STEP-005.10` §1 | "causes new trips in affected regions to be **refused rather than partially simulated**" |
| `STEP-005.10` §12 | "Region degradation refuses new trips" — **ticked** |
| `ERROR_MODEL.md` §3 | `coverage.provider_degraded` · 503 · "Refuse rather than produce a partial simulation" |

The shipped code, `VERIFIED`, appears to do the opposite:

```python
if state is PublishedState.DEGRADED:
    return TripAccepted(region_id=region_id, disclosures=(...))
```

**My first reading was that the prose was wrong and the code was right. That reading
was itself wrong**, and reading the error register is what corrected it. The conflict
is terminological, and the register settles it in the `meaning` column rather than in
the code's name:

> `coverage.provider_degraded` — *"Provider health **insufficient for reliable
> planning**"*

"Insufficient for reliable planning" is `PublishedState.UNAVAILABLE`. It is not the
enum member spelled `DEGRADED`, which `STEP-005.10` defines as *less certain, and
disclosed*. The prose uses "degraded" in the ordinary sense — a provider has gone
bad — and the enum uses it as one of three specific published states. The two senses
overlap on the word and not on the meaning.

The structural check that this is the right reading, rather than a convenient one:
**there is no `coverage.provider_unavailable` in the register.** If
`coverage.provider_degraded` meant only the enum member, then `assess`'s actual
refusal — the one `REQ-TRIP-002` requires — would have no error code at all and could
not be served as a problem document. A requirement whose own refusal path is
uncodeable is not the intended reading of the register.

So both are right, and they were never in conflict:

| Published state | Decision | Surface |
| --- | --- | --- |
| `UNAVAILABLE` — insufficient for reliable planning | **Refuse** | 503 `coverage.provider_degraded` |
| `DEGRADED` — less certain | **Accept, disclose** | 200 with disclosures (`REQ-EVID-006`) |
| `HEALTHY` | Accept | 200 |

**It is still a defect, and it is logged as `BUG-034`.** A word that means two things
inside one requirement chain is how the wrong thing gets built, and the wrong thing
here is specific and severe:
`PUBLICATION[HealthState.RECOVERING] is PublishedState.DEGRADED`. `STEP-005.10` made
recovery publish as degraded deliberately, so a half-recovered provider does not get
full traffic. An implementer who reads §9 literally and refuses on the enum member
turns **every recovery window into a total outage for the traveller** — the
hysteresis added to protect the provider would start refusing users. Two correct
local decisions composing into a wrong one, visible only where they meet, which is
here.

Fixed by disambiguating the prose in all four documents, not by changing behaviour.

**Renaming the code to `coverage.provider_unavailable` was considered and
declined.** It would be clearer, and `BASELINE.md` §2 is right that a breaking change
is cheap before release. But the register is generated from `ERROR_MODEL.md` and
consumed by `problem()`, the client generator and the baseline digest; the rename
buys precision in one identifier and spends a contract change to get it, when the
`meaning` column already carries the precision and only needed to be believed.

## 4. What is being added

| Change | Kind | Why it is here and not elsewhere |
| --- | --- | --- |
| `018_coverage_time_zone.sql` | Migration | A date bound cannot be evaluated without the destination's zone. §5 |
| `platform_api/trip_request.py` | New module | The rule. §6 |
| `POST /v1/coverage:check` | Contract addition | The rule must have exactly one implementation. §6 |
| `app.py` route | Route | Three lines; the handler delegates |
| `apps/web` planning form | Page | Where a traveller meets the refusal |

`RISK-017` applies to the migration: the graph holds one node per `.sql` file, so it
gets no pre-change check at all and its blast radius comes from reading it and from
mutating the **deployed** schema.

## 5. The zone is a column because guessing it is the bug

`coverage_read_model` has `date_bounds_start` and `date_bounds_end` and no zone.
Comparing a requested date against those bounds needs an answer to "what is today",
and **"today" is not a property of the server or of the browser.**

At 23:30 UTC on 4 September it is already 5 September in Zurich and still
13:30 on the 4th in Honolulu. A traveller in Honolulu asking for 5 September in Bern
is asking about tomorrow-there, which is today-here. Whichever clock is chosen by
default, one of those two users is told their date is in the past when it is not.

There is no `regions` table — `coverage_read_model` *is* the region registry — so the
zone goes there: `time_zone text NOT NULL`, no default. `001_identity_tenancy.sql`
defaults `time_zone` to `'UTC'` for a user, which is defensible for a display
preference and would be a silent wrong answer for a feasibility bound.

## 6. One rule, one implementation, and therefore a server endpoint

The alternative was validating in the browser against the coverage document, which is
already fetched. It was rejected for a reason this repository has already paid for
once: `POST /trips` (`STEP-008.06`) must enforce the same rule, so a TypeScript copy
would be the second place the rule lives, in a second language, where the two drift.
`BUG-029` is exactly that failure between a projection and a contract, and
`fetch-coverage.ts` already carries the note.

`POST /v1/coverage:check` — public and unauthenticated like `/coverage`, for the same
reason: asking somebody to register in order to be told no.

**A refusal is a problem document, not a 200 with a `refused` field.** I designed it
the other way first — "can I plan this?" answered "no, because…" reads like a
successful answer to a well-formed question — and the register had already decided,
with statuses attached (422, 422, 503). Following it is not deference: a 200 carrying
`{"decision": "refused"}` is a body a careless client renders as success, and this
repository has already paid for that exact shape once. `BUG-032` was three tests
passing against a 404 because they asserted absence and absence is what a 404 gives
you. A 422 cannot be read as an acceptance by any client, however badly written.

The distinction `fetch-coverage.ts` draws — *the answer is no* versus *we could not
ask* — survives intact, because it was never carried by the status. It is carried by
the code: `coverage.unsupported_region` is a refusal, `platform.dependency_unavailable`
is an inability to answer, and `retryable` already separates them mechanically.

| Outcome | Status | Code |
| --- | --- | --- |
| Plannable | 200 | — (disclosures when the region is `degraded`) |
| Region not declared | 422 | `coverage.unsupported_region` |
| Dates outside bounds, in the past, or wrong length | 422 | `coverage.unsupported_dates` |
| Health insufficient for reliable planning | 503 | `coverage.provider_degraded` |
| Malformed request | 400 | `validation.invalid_request` |
| Database unreachable | 503 | `platform.dependency_unavailable` |

### A second refusal type, deliberately

`TripRefused` stays in `services/ingestion` and keeps answering one question: is this
region plannable right now, given its suppliers. The new `PlanningRefused` answers a
different one: is this *request* plannable — which is about the request, and reaches
the supply answer by reading the projection. Pushing date bounds into `CoverageModel`
would make the ingestion service know what a trip request is.

The new type carries a machine-readable `code` as well as prose, because `STEP-007`
§17 asks for "refusal rate **by reason**" and a bare sentence cannot be counted.
`TripRefused` was not given one: extending a `VERIFIED` frozen dataclass with a
required field to serve a consumer it does not have is the wrong direction of fit.

## 7. Trip length: enforcing the declared bound, and flagging that I doubt half of it

`PRODUCT_SCOPE` §81 says "one region, **3–7 days**". `ASM-015` says a 3–7 day window
"is large enough to demonstrate differentiated simulation without unbounded
complexity". The sub-step record flagged this as a product decision rather than an
implementation one, and it is.

**Implemented: refuse outside 3–7, naming the supported range.** Above 7, the
argument is `REQ-TRIP-002` itself — the solver is exercised at 3–7 days, so a 9-day
plan would be of unvalidated quality, and a plan of unvalidated quality presented as
a plan is the partial simulation the requirement names.

**Below 3, I think the bound is probably wrong, and I implemented it anyway.** A
2-day trip is *less* complex than a 3-day one; nothing in `ASM-015`'s reasoning
applies downward. But `PRODUCT_SCOPE` says 3, and quietly shipping 1–7 because I find
it more sensible would be me editing declared scope through code. Raised as
**`DEC-011`** with that recommendation. One constant, one place, one line to change
when it is answered.

## 8. What this does not close

- **No trip is created.** `POST /trips` is `STEP-008.06`. This answers whether one
  *could* be, which is what `STEP-007` is for.
- **The read model is still empty.** Every path here is exercised against rows the
  tests insert. `ENH-007` is the standing record that nothing real has passed through
  the pipeline; this sub-step does not change that and does not pretend to.
- **"No partial simulation" is asserted structurally, not behaviourally.** There is no
  scenario engine yet, so no test can observe a scenario failing to be produced. The
  assertions are on the type having nowhere to put one and the module importing
  nothing that could make one — the practice established at `STEP-005.03`. When
  `STEP-011` exists, this becomes observable and the test should be upgraded.
- **`DEC-011` is open.** The lower bound ships as declared, not as recommended.

## 9. Score

| Dimension | Rating | Reasoning |
| --- | --- | --- |
| Reach | **MEDIUM** | One new module, one route, one migration, one page. Nothing existing changes behaviour except the corrected prose |
| Criticality | **HIGH** | First refusal a traveller meets. `REQ-TRIP-002` is the honesty gate for the product |
| Reversibility | **HIGH** | Revert the commit; `018` is additive and a dropped column loses a declaration, not data |
| Detectability | **MEDIUM** | A wrong zone shows as a one-day error that looks like a rendering bug — the failure this record was written to anticipate |
| Confidence | **MEDIUM** | `RISK-016` #13 found the API application invisible to the graph; the dependant set here is grep's, not the graph's |

**Overall: MEDIUM.** Approval required on two counts — a contract addition, and
`DEC-011` shipping a bound I have recommended against.

---

## 10. Post-change — what the change actually did

| Field | Value |
| --- | --- |
| Date completed | 2026-09-05 |
| Regression | R1–R7 **PASS**. 1373 Python, 71 web, 307 UI, 58 browser, 18 R7, meta 76/76 |
| Mutation testing | **20 seeded, 20 killed, 0 survivors** |
| Contract gate | `[ADDITIVE] POST /coverage:check — new operation` |
| Predicted score | MEDIUM / MEDIUM |
| Actual | **MEDIUM, and the confidence rating earned itself** |

### The prediction that was right for the wrong reason

§9 rated detectability MEDIUM because "a wrong zone shows as a one-day error that
looks like a rendering bug". True — but the harder part turned out to be that there
are **three** candidate clocks, not two. The record framed the hazard as *browser
versus destination*, and a server-side implementation quietly satisfies that framing
while still being wrong for every caller whose calendar day differs from the
server's. Every zone test is therefore written across the date line, with a negative
control that declares the same region in UTC and accepts.

### What the gates caught that review did not

Three of my own defects, none found by reading the code back:

| Defect | Caught by |
| --- | --- |
| Refusals missing the contract's required `remediation.kind` | The Problem schema test |
| A package-wide `jsdom` default disabling a **security** test in `i18n.test.ts` | That test failing |
| `[aria-live="polite"]` matching a `Field`'s empty error slot, not the notification region | The acceptance announcement test |

The second is the one worth carrying forward. `i18n.test.ts` reads its own source to
prove the locale never reaches a module specifier. A configuration default switched
it off, and the failure surfaced as `TypeError: The URL must be of scheme file` — a
message that names no security property at all. **A test that is not running is
indistinguishable from a test that passes**, which is the same shape as the
`guard:meta` finding at STEP-007.01 and `gitnexus_query` at STEP-004.01.

### The two guards that fired

Both were tripwires doing their job, and neither was loosened to fit.

`test_exactly_one_operation_is_public` now names two operations and says why a third
would need an argument. `test_every_mutating_operation_requires_an_idempotency_key`
now reads `x-journeylab-safe` **from the contract** rather than an allowlist of ids in
the test, and two new tests check the claim is true: a safe operation may not return
201, 202, a `Location`, or accept `If-Match`. The rule itself moved into one function,
because it was asserted in two places and an exemption added to one and not the other
is a hole that reads as coverage.

### Still open after this change

- **`DEC-011`** — the 3-day lower bound ships as `PRODUCT_SCOPE` declares it, and
  I have recorded that I think it is wrong. One constant.
- **Owner approval** — a contract addition and `DEC-011`, per §9.
- **`ENH-007`** — every path here runs against rows the tests insert. Nothing real
  has passed through the pipeline, and this sub-step does not change that.
- **`RISK-016` #13** — the API application is invisible to the code graph. Not fixed
  here; recorded with a measurement so the next pre-change check starts from it.
