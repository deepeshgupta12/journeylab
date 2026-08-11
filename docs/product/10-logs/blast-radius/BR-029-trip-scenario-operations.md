---
blast_radius_id: BR-029
sub_step_id: STEP-004.02
title: Trip, brief and scenario operations (API-001…009)
author: Deepesh Kumar Gupta
date: 2026-08-11
score: MEDIUM
confidence: HIGH
approval_required: false
---

# BR-029 — Trip, brief and scenario operations

> The sub-step record predicts `BR-023`, held by STEP-003.06. This is `BR-029`,
> continuing from `BR-028`. Corrected in the sub-step file.

## 1. Graph state

| Field | Value |
| --- | --- |
| Indexed commit | `c524820` |
| HEAD at check | `c524820` |
| Freshness | ✅ up to date (full `--force` re-index) |
| Result | **NOT BLOCKED** |
| Confidence | **HIGH** for the Python surface; the contract itself has no graph representation (§3) |

## 2. Queries run

| # | Query | Result |
| --- | --- | --- |
| 1 | `impact(problem, upstream, includeTests)` | 1 direct (`opaque_denial`), **2 affected processes**, LOW, `epistemic: exact` |
| 2 | `query("problem details error response correlation id")` | **Empty, with "FTS indexes missing"** — still degraded after `--force`; see §3 |
| 3 | `detect_changes()` | Run pre-commit; recorded in the regression entry |

## 3. The FTS repair does not exist

`BR-028` §3 recorded that `gitnexus_query` returns nothing and advises
`gitnexus analyze --repair-fts`. Acting on that advice:

```
$ npx gitnexus analyze --repair-fts
error: unknown option '--repair-fts'
$ npx gitnexus analyze --force        # the documented alternative
  5,219 nodes | 7,260 edges | 90 clusters | 53 flows
$ gitnexus_query(...)
  warning: FTS indexes missing — keyword search degraded.
```

**The tool's own remediation is wrong for the installed version, and the
documented alternative does not repair it either.** The concept search is
therefore unavailable, not merely stale.

`CLAUDE.md` instructs contributors to use it *instead of grepping*. Following
that instruction now produces an empty result that reads as "no such concept
exists" — a confident wrong answer. A warning has been added to the
hand-maintained section of `CLAUDE.md` so nobody trusts it in the meantime.
Carried to `STEP-026`.

## 4. What the pre-change check found before any code was written

**`API_CONTRACTS.md` declared three error codes that `ERROR_MODEL.md` does not
define.** Once `.01` made the register generated, those operations became
undeclarable.

| Declared by an operation | Register has | Resolution |
| --- | --- | --- |
| `coverage.insufficient_evidence` | `evidence.insufficient_coverage` | **Transposed words.** Reference corrected |
| `provider.unavailable` | `coverage.provider_degraded` | API-004 is evidence assembly; reference corrected |
| `validation.invalid_party` | *nothing* | §2 declared a Validation class from the beginning and **no code was ever registered for it.** Two added |

Only two `validation.*` codes were registered, not a family:
`validation.invalid_request` (400, schema violation) and
`validation.invalid_party` (422, well-formed and impossible). A register that
anticipates codes nobody raises rots, because nothing fails when a speculative
entry is wrong.

**None of this would have failed anything before.** `API_CONTRACTS.md` is prose
and nothing read it. A client branching on a code the server can never send does
not error — it simply never takes that branch. `TestTheTwoRegistersAgree` now
gates it, and was mutation-tested: a seeded `provider.made_up` fails with the
right message.

## 5. Change inventory

| File | Change |
| --- | --- |
| `contracts/openapi.yaml` | **9 operations, 15 new schemas, 5 parameters, 1 response.** The bulk of this sub-step |
| `docs/product/04-contracts/ERROR_MODEL.md` | `validation.*` family — 2 codes |
| `docs/product/04-contracts/API_CONTRACTS.md` | 2 mis-referenced codes corrected |
| `apps/api/src/conventions/error_codes.py` | Regenerated — 21 → 23 codes |
| `contracts/schemas/error-codes.json` | Regenerated — 17 → 19 client-visible |
| `tests/api/test_api_operations.py` | **New.** 40 assertions |
| `tests/api/test_api_conventions.py` | Cross-register gate; one stale `.01` assertion replaced |
| `CLAUDE.md` | Warning that `gitnexus_query` is degraded |

## 6. Twelve impact categories

| # | Category | Assessment |
| --- | --- | --- |
| 1 | **Callers / call graph** | None. No Python behaviour changed; `error_codes.py` gained two entries |
| 2 | **Public API / contracts** | **This is the change.** 9 operations declared, all `PROPOSED`, none implemented. Additive to `.01`, which declared no paths — so nothing can break |
| 3 | **Database / schema** | None. `DATA-010`/`011` are referenced by the operations and **do not exist in `DATA_CONTRACTS.md`** — a documentation gap owned by STEP-006, noted not fixed |
| 4 | **Events** | `EVT-001`–`004` are referenced in prose. AsyncAPI is `.05` |
| 5 | **Configuration** | None |
| 6 | **Infrastructure** | One dev dependency, `jsonschema`, to validate the examples |
| 7 | **Security** | **Material.** Every resource-scoped operation reuses the indistinguishable denial; no operation declares a bare 403. Both are asserted across all nine, not spot-checked |
| 8 | **Privacy** | `accessibility_needs` is declared-only (`REQ-PRIV-003`) and `Party` is a **closed** object, so an undeclared sensitive attribute cannot arrive through it |
| 9 | **Accessibility** | Not directly. `REQ-A11Y-002`'s table-and-CSV alternative binds to the surfaces, not the contract |
| 10 | **Performance** | The 500 ms job-handle promise is declared for API-004/005. Unverifiable until handlers exist; recorded as a contract obligation, not a met one |
| 11 | **Tenancy** | Tenant comes from the token. **No operation accepts a tenant parameter**, and there is no path or query field through which one could be supplied |
| 12 | **Documentation** | This record, `IMPL-026`, the sub-step record, `REGRESSION_LOG`, `MASTER_TRACKER`, and two corrections to the contract documents |

## 7. Data-flow inspection

No runtime data flows: nothing is implemented. What is being inspected is what
the contract **permits**, which is the only thing that can be got wrong today.

| Hazard | Control | Evidence |
| --- | --- | --- |
| An operation becoming an existence oracle | Every `{id}` operation `$ref`s the shared `NotFoundOrForbidden`; none may define its own 404 | Asserted for all 9; a separate assertion forbids any 403 |
| A tenant supplied by the client | No operation declares a tenant parameter, in path, query or header | Structural — the parameter does not exist |
| A retry creating two trips | `Idempotency-Key` required on every mutating operation | Asserted; **the test found `PUT /brief` missing one** (§8) |
| A lost update | `If-Match` required where state is replaced, and an ETag returned wherever a version is readable — you cannot send a version you were never given | Both asserted |
| An estimate rendered as fact | `Evidenced.status` is required with **no default**, so a caller cannot omit it and get `confirmed` free | Asserted |
| Conflicting sources silently averaged | `Evidenced.conflicts` retains them (`REQ-EVID-002`) | Present in the schema |
| A plausible invalid plan instead of an explanation | The infeasible response **requires** `remediation`, and a conflict set needs **≥2** constraints — a one-item set means the solver failed to explain | Asserted |
| Money as a float | Every cost is `Money`, integer minor units | Asserted on both cost fields |

## 8. What the tests caught in my own contract

**`PUT /trips/{tripId}/brief` required `If-Match` but not `Idempotency-Key`.** My
reasoning had been that a conditional PUT is naturally idempotent. It is not good
enough: if the first attempt succeeds and the response is lost, the retry carries
a now-stale `If-Match` and gets a 409, leaving the client unable to tell whether
its change applied. `If-Match` prevents a lost update; the key prevents a lost
*answer*.

**`.01` guessed the remediation shape and the guess was wrong.** It declared
`conflict_set` and `relaxations` as arrays of strings before any operation needed
one. `.02` needed relaxations that name the constraint they relax — "depart at
15:00 instead" is not actionable unless the reader knows which of three
constraints it addresses. `Problem.remediation` now fixes only `kind` and lets
the composing response supply the shape.

**`allOf` + `additionalProperties: false` rejected a field the same schema
requires.** Each `allOf` branch validates the whole instance independently, so a
closed branch rejects a property another branch declares. `ConflictSet` is built
for composition and cannot be closed; `Party` and `Money` are leaves and are.

All three were found by validating the examples, which is the cheapest possible
place to find them and the entire argument for contract-first.

## 9. Score

| Dimension | Value | Reason |
| --- | --- | --- |
| Reach | Medium | Every handler in STEP-008…014 implements against these |
| Reversibility | High | Declarative only; nothing implemented |
| Detectability | High | 40 assertions over the contract; 440 Python tests total |
| Security exposure | Medium | Enumeration and tenancy fixed here for all nine operations at once |
| Performance | None | No runtime path |
| **Overall** | **MEDIUM** | **Confidence HIGH.** No owner approval required |

## 10. Post-change verification

| Check | Result |
| --- | --- |
| Python suite | **440 passed, 5 skipped** (up from 405) |
| `ruff` / mypy | Clean, 33 source files |
| Every internal `$ref` resolves | Asserted |
| Every example validates against its schema | Asserted, including the external error-code enum |
| `pnpm verify`, `pnpm ci:local`, R1–R7 | Recorded in the regression entry |
