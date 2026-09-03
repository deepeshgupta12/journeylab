---
blast_radius_id: BR-057
sub_step_id: STEP-006.08
title: Data-quality expectations, drift and quarantine
author: Deepesh Kumar Gupta
date: 2026-09-03
score: MEDIUM
confidence: MEDIUM
approval_required: false
---

# BR-057 — Data quality

## 1. Graph state

| Field | Value |
| --- | --- |
| Indexed commit | `7299ef1` |
| HEAD at check | `7299ef1` |
| Freshness | ✅ up to date |
| Result | **NOT BLOCKED** for Python; **`RISK-017`** for the migration |
| Confidence | **MEDIUM** |

## 2. A suite that ran nothing must not report a pass

The failure this module is shaped around. An expectation runner naturally reports
"0 failures" for a batch it never examined — a mistyped id, a filter that matched
nothing, a batch of a kind nobody wrote expectations for — and **zero failures and
zero checks are the same number describing very different situations**.

So `run_suite` counts what it ran, requires every class declared in
`domain_expectations.yml` to have an implementation, and refuses rather than skipping.
The YAML is the specification a curator reads; a class declared there and missing in
code means the specification and the runner disagree while the report says green.

## 3. Two defects external review found that this suite did not

Recorded in full because the interesting part is *why the tests missed them*.

### Drift reported a pass without measuring drift

`_distribution_drift` returned `PASSED` whenever a `baseline_mean` field was merely
present. It compared nothing. **The one check whose entire job is noticing a
distribution move could not notice a distribution moving** — the exact vacuous pass
§2 is about, written into this module by the person writing §2.

Every test asserted the verdict for one input, and none asserted that a *drifted*
batch produced a different one. Fourteen mutants passed over it because no mutant
targeted a function that already did nothing.

Now: the batch mean is compared against the baseline in **standard deviations** rather
than percent, because a 10% move in price and a 10% move in duration are not
comparably surprising and a percentage threshold has to be retuned per field. A
baseline with zero spread reports `UNAVAILABLE` — any non-zero move is infinitely many
sigma, which would quarantine every batch.

Fixing it also broke a test: the "clean batch" fixture had a baseline and no
observation, and had been passing on exactly the vacuousness that hid the defect.

### The quarantine reached nobody

§5 requires quarantine "visible to curators, not just logged". `Quarantine` held
entries in a list that lived for the duration of one batch run, and the
`quarantined_batches` table it was written against was never touched by it. Every test
passed, because every test exercised the class.

Now behind a `QuarantineStore` port with `PostgresQuarantineStore` as the real
implementation, and `Quarantine.persisted` reports `False` when a batch was held with
no store — not an exception, because a runner without a store is a legitimate test
configuration, but the caller has to know that nothing reached anybody.

## 4. Block and quarantine are different affordances, not different severities

`REQ-NFR-012` makes an unresolved location a hard block. A quarantined batch is
inspectable and releasable once the cause is understood; a blocked one is not, because
releasing it puts an itinerary item pointing at nothing into planning.

Modelling both as severities loses that: the UI grows one release button, somebody
uses it, and the hard block becomes a strongly-worded warning. Refused in the Python
**and** by a database check constraint — deliberate duplication, because the database
is the layer a second writer bypasses.

## 5. Mutation testing — 14 seeded, 14 killed

Two survived the first run, and both were **database constraints with no test behind
them**: releasing a blocking row, and a quarantine row with no failure detail. The
suite exercised the class and nothing wrote to the table, so the migration's
guarantees were unverified.

**The restore then failed the same way it did in `.01`** — a mutant that permits a
write leaves rows that trip the constraint's own re-creation. I recorded that lesson
in `BR-050` §7 and did not carry it into this harness. The verification line caught it
again.

## 6. Assessment

| Category | Assessment |
| --- | --- |
| Code | `services/ingestion/src/quality.py`, `data/quality/domain_expectations.yml` — new |
| Schema | `014_data_quality.sql`: one table, RLS, three check constraints |
| Contracts / events | Untouched |
| Security | RLS on `quarantined_batches` |
| Privacy | Failure details describe records, not their contents |

## 7. What this does not close

| Gap | Why |
| --- | --- |
| No baseline exists to drift from | No provider corpus has been fetched — the disclosure carried since `.02`. Drift now *measures*, and reports `UNAVAILABLE` until there is something to measure against |
| The six checks read flat dicts | The canonical entities exist (`.03`) and nothing assembles a batch of them yet; `.09` is the first real producer |
| `DRIFT_SIGMA` is provisional | `DEC-005`. Expressed in sigma so it does not need per-field retuning |
| Quarantine has no UI | `STEP-021`. The table and the release path are what it will read |

## 8. Score

**MEDIUM.** Additive schema and an unwired runner, but it is the gate that decides
whether data enters planning, and `REQ-NFR-012`'s hard block lives here.
