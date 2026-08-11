---
blast_radius_id: BR-033
sub_step_id: STEP-004.06
title: Shared JSON Schemas including model-output schemas
author: Deepesh Kumar Gupta
date: 2026-08-11
score: MEDIUM
confidence: HIGH
approval_required: false
---

# BR-033 — Shared JSON Schema library

> The sub-step record predicts `BR-027`, held by the STEP-003 closure. This is
> `BR-033`.

## 1. Graph state

| Field | Value |
| --- | --- |
| Indexed commit | `e1d3194` |
| HEAD at check | `e1d3194` |
| Freshness | ✅ up to date |
| Result | **NOT BLOCKED** |
| Confidence | HIGH. Tooling caveats from `BR-031` §3 stand |

## 2. Queries run

| # | Query | Result |
| --- | --- | --- |
| 1 | `detect_changes()` | Run pre-commit |
| 2 | — | **No symbol-level query applicable.** Five JSON documents, one YAML refactor, one test module; no Python symbol changed |

## 3. This sub-step is a refactor, not only an addition — and that was the finding

§5 asks for "reuse enforced — no duplicate inline definitions". Creating the
library alone would have **produced** the duplication it forbids: `Money` and the
provenance/time fields were already defined inline in `openapi.yaml` by `.01` and
`.02`.

So `.06` had to change contracts that were already `VERIFIED`:

| Was | Now |
| --- | --- |
| `Money` inline in `openapi.yaml` | `$ref: './jsonschema/money.json'` |
| `Evidenced` restating `source`, `confidence`, `observed_at`, `effective_from`, `effective_to` | Composed from `Provenance` + `TemporalValidity` |

**The shapes are equivalent, but `Evidenced` is a structural change**: its required
set moves from `{value, status, source, observed_at, confidence}` to
`{value, status, provenance, validity}`. Nothing consumes it — no handler, no
generated client — so nothing breaks. Under `CONTRACT_CHANGE_POLICY` it would be
**breaking** the moment a consumer exists, which is precisely why doing it now
rather than at `.07` matters: client generation is the next sub-step.

Two tests broke and were correct to break. Both read the inline shapes that moved.
One of them would have kept passing had I only added the library — it read
`schemas["Money"]["properties"]`, which after a bare `$ref` is absent, so the
assertion would have gone **vacuous** rather than failing. It now follows the
reference and asserts the `$ref` exists first.

## 4. Change inventory

| File | Change |
| --- | --- |
| `contracts/jsonschema/money.json` | **New.** Moved from `openapi.yaml` |
| `contracts/jsonschema/temporal-validity.json` | **New.** The three time axes |
| `contracts/jsonschema/provenance.json` | **New.** Source, confidence, access label |
| `contracts/jsonschema/constraint-class.json` | **New.** The four classes |
| `contracts/jsonschema/trip-brief-extraction.json` | **New.** AI-001 model output |
| `contracts/openapi.yaml` | Four types now referenced; `Evidenced` recomposed |
| `tests/api/test_json_schemas.py` | **New.** 40 assertions |
| `tests/api/test_api_conventions.py`, `test_api_operations.py` | Two assertions follow the refs |

## 5. Twelve impact categories

| # | Category | Assessment |
| --- | --- | --- |
| 1 | Callers / call graph | None. No Python symbol changed |
| 2 | **Public API / contracts** | `Evidenced` changes shape (§3). No consumer exists, so no break — and `.07` generates clients next, which is why the timing matters |
| 3 | Database / schema | None |
| 4 | Events | None. The AsyncAPI document is untouched; unifying its envelope with this library is a candidate for later and is **not** claimed here |
| 5 | Configuration | None |
| 6 | Infrastructure | None |
| 7 | **Security** | **The model-output schema is the deterministic boundary.** See §6 |
| 8 | **Privacy** | `Provenance.access_label` makes "may plan with, may not display" expressible. Without it every renderer guesses, and renderers guess permissively |
| 9 | Accessibility | None |
| 10 | Performance | None |
| 11 | Tenancy | None |
| 12 | Documentation | This record, `IMPL-030`, the sub-step record, `REGRESSION_LOG`, `MASTER_TRACKER` |

## 6. Data-flow inspection — the AI boundary

**The flow:** free text + locale → model → JSON → **this schema** → deterministic
validators → human confirmation → trip state.

`ADR-002` gives feasibility to deterministic engines and language to the model.
`REQ-AI-001` says model output can never mutate trip state without validation and
user authorization. `trip-brief-extraction.json` is where "never" stops being a
sentence in a document.

| Hazard | Control | Evidence |
| --- | --- | --- |
| A hallucinated constraint | **`source_span` is required.** A model claiming "travelling with a dog" must point at the characters that say so, and a span not containing the claim is caught deterministically rather than by the reader's memory of what they typed | Rejection tested |
| An unknown constraint class | The four values are the contract; `maybe_hard` has no solver rule | Rejection tested |
| The model doing something we did not design | `additionalProperties: false` **everywhere** — an unexpected `tool_call` is rejected, not ignored | Rejection tested |
| A shape we never wrote a validator for | `schema_version` is `const: 1` | Rejection tested |
| Silent backfill instead of abstention | `abstained` required with **no default** — a model omitting it is not permitted to have the safer value chosen for it (`REQ-AI-004`) | Rejection tested |
| One confidence hiding a guess | Confidence is **per field**. A model can be certain about dates and guessing about accessibility; one number averages those into something true of neither | Structural |
| Trusting the model's own parsing | `value` is deliberately untyped. The deterministic validators own date, currency and unit parsing — a schema that accepted the model's idea of a date would be trusting the thing it exists to check | Structural |

**What the schema explicitly does not do**, stated in the schema itself: it checks
shape, not truth. It cannot tell whether "2 hours" was really said or whether
"step-free" meant the hotel or the ferry. It is the **first gate of three** —
schema, then deterministic validators, then the human confirmation `AI-001`
requires. A test asserts that sentence is present, because a reader who believes
otherwise will skip the two gates that follow.

## 7. Score

| Dimension | Value | Reason |
| --- | --- | --- |
| Reach | Medium | Every contract type and every AI extraction |
| Reversibility | High | Files plus four `$ref`s; nothing consumes them |
| Detectability | High | 40 assertions, two of them meta-tested |
| Security exposure | Medium | The AI boundary is defined here |
| **Overall** | **MEDIUM** | Confidence HIGH |

## 8. Post-change verification

| Check | Result |
| --- | --- |
| Python suite | **592 passed, 5 skipped** (up from 552) |
| `ruff` / mypy | Clean, 35 source files |
| Every schema is valid Draft 2020-12; `$id`s unique and matching filenames | Asserted |
| No inline type duplicates a shared one — **searched by shape, not by name** | Asserted, with the scan meta-tested |
| `pnpm verify`, `pnpm ci:local`, R1–R7 | Recorded in the regression entry |
