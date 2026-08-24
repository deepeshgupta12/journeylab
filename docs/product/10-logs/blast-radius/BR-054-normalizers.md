---
blast_radius_id: BR-054
sub_step_id: STEP-006.05
title: Provider-to-canonical normalizers
author: Deepesh Kumar Gupta
date: 2026-08-24
score: LOW
confidence: MEDIUM
approval_required: false
---

# BR-054 — Normalizers

## 1. Graph state

| Field | Value |
| --- | --- |
| Indexed commit | `e25056c` |
| HEAD at check | `e25056c` |
| Freshness | ✅ up to date |
| Result | **NOT BLOCKED** |
| Confidence | **MEDIUM** — `RISK-016`, ninth reproduction (0/0/0 against 20/5/16) |

## 2. Purity is a reproducibility requirement, not a style preference

A normalizer that reads a clock, a database or an environment variable cannot be
replayed — and replay is the point, because `REQ-CONS-006` makes a scenario
reproducible from its inputs and these records are those inputs.

`observed_at` is a required argument rather than `datetime.now()`. That looks like
ceremony until a backfill replay stamps every historical fact with today's date and
the freshness policy declares the entire corpus current — a defect with no symptom
except that everything looks unusually healthy.

**Tested by walking the AST, not by scanning the text.** The first version of that
test was a substring search and it failed against the module's own docstring, which
explains why `datetime.now()` is forbidden. A text scan cannot tell code from prose
*about* code, so it either misses the real call or trips on the explanation of it.

## 3. Rejection is the feature

`DC-EXT-001`: *"Schema drift ⇒ reject and alert, never coerce."* A normalizer's job
is not to get a row out of every payload. An unmappable field is a provider change
nobody has understood yet, and guessing produces a canonical record wrong in a way
**no downstream check can detect** — provenance says the provider supplied the value,
and it did not.

Rejections are returned as data rather than logged: a rejection nobody counts is
silent data loss, where the batch simply reports a smaller number. One bad payload
does not fail the batch, because a single provider typo blocking an entire ingestion
is its own outage — but the count is visible and `.08` can quarantine on it.

## 4. A guard no test could distinguish

`normalize_place` originally re-checked that `observed_at` was timezone-aware. The
adapter behind it already refuses naive input **and has its own test**, so removing
the duplicate killed no mutant — the two guards are indistinguishable to every
assertion that exists.

It is gone, and the reasoning is recorded at the site: `CanonicalFact` keeps its own
check because nothing sits behind *that* path. The general rule is the inverse of the
one this project usually applies — a control believed to hold and checked by nothing
is the worst state, but a control checked twice by the same assertion is a line
pretending to be a defence.

**Mutation testing: 10 seeded, 10 killed.** Two of the original survivors were
equivalent mutants of my own making, and one exposed a narrow test: a mutant that
re-implemented the field mapping **one function deeper** slipped past a structural
check that inspected only the outer function. The check now covers both hops.

## 5. Assessment

| Category | Assessment |
| --- | --- |
| Code | `services/ingestion/src/normalizers/` — new package |
| Schema / contracts / events | Untouched |
| Security / privacy | None — pure functions over provider payloads |
| Performance | No I/O |

## 6. What this does not close

| Gap | Why |
| --- | --- |
| Only places and generic facts are normalized | Weather, transit and routing payloads have adapters in STEP-005 but no canonical *entity* yet; each needs its own target table beyond `evidence_facts` |
| Nothing writes the normalized output to the database | Repositories exist (`.04`); wiring is `.06` onward |
| `access_label` is hardcoded to `public` | Every current source is open data under `ADR-016`. A licensed source needs the label to come from the licence record, and inventing that mapping before a licensed source exists would be guessing |

## 7. Score

**LOW.** Additive, pure, no I/O, no contract. Confidence MEDIUM under `RISK-016`.
