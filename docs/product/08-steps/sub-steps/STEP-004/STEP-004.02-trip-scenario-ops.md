---
sub_step_id: STEP-004.02
parent_step: STEP-004
title: Trip, brief and scenario operations (API-001…009)
status: VERIFIED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-PLAT-005, REQ-PLAT-008]
blast_radius_id: BR-029
depends_on: [STEP-004.01]
last_updated: 2026-08-11
---

# STEP-004.02 — Trip, brief and scenario operations (API-001…009)

## 1. Outcome
The core planning surface is fully specified in OpenAPI with request/response schemas, error cases and examples, before any handler exists.

## 2. Scope and boundary
**In scope:** `API-001`–`API-009`: create/read trip, replace brief, build evidence pack, generate scenarios, list/read scenarios, select, edit.

**Not in this sub-step:** Handler implementations (their owning steps); collaboration and booking operations (`.03`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-PLAT-005, REQ-PLAT-008 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | ✅ **NOT BLOCKED** for impact; `gitnexus_query` remains **unusable** — `--repair-fts` is not a valid flag and `--force` does not rebuild it (`BR-029` §3) |
| HEAD / indexed commit | `c524820` / `c524820` — matched |
| Queries run | `impact(problem)` → 1 direct, **2 processes**, `epistemic: exact`; `query(...)` → empty with an FTS warning; `detect_changes()` |
| Unknown / low-confidence areas | Impact-preview token semantics for API-009 — declared **required and opaque** so the shape cannot change without a version bump; designed with STEP-014. **New:** `DATA-010`/`011` are referenced by these operations and do not exist in `DATA_CONTRACTS.md` (STEP-006 owns it) |
| Blast radius | **[BR-029](../../../10-logs/blast-radius/BR-029-trip-scenario-operations.md) — MEDIUM, confidence HIGH.** The record predicted `BR-023`; that number was already taken by STEP-003.06 |
| Approval required? | **No** — MEDIUM with high confidence |

## 5. Implementation plan
- [x] `API-001`/`API-002` trip create and read with ETag
- [x] `API-003` brief replace with **`If-Match` required** — and `Idempotency-Key`, which a test proved was also needed
- [x] `API-004`/`API-005` async operations returning a **job handle within 500 ms** — declared as a contract obligation; unverifiable until handlers exist
- [x] `API-006`/`API-007` scenario list and detail — provenance enforced by the `Evidenced` **type**, so a bare number cannot be returned for a volatile field
- [x] `API-008` select — owner-only, matching `select_canonical_scenario` in the authorization matrix
- [x] `API-009` typed edit — impact-preview token required and opaque
- [x] `422` responses carrying **minimal conflict sets** — required, with `minItems: 2`

## 6. Contracts and schema changes
Contracts are declared in [STEP-004](../../STEP-004-contract-first-platform-apis.md); this sub-step consumes them. Any change follows [CONTRACT_CHANGE_POLICY](../../../04-contracts/CONTRACT_CHANGE_POLICY.md).

## 7. Tests to add
| Test | Type | Asserts | Status |
| --- | --- | --- | --- |
| TST-PLAT-005 | contract | All examples validate against schemas, **including the external error-code enum** | ✅ |
| TST-CONS-005 | contract | Infeasible response carries a conflict set of **at least two** constraints | ✅ |
| — | contract | Every mutating operation requires `Idempotency-Key`; no read demands one | ✅ **found `PUT /brief` missing it** |
| — | contract | Every `{id}` operation reuses the shared denial; **none declares a 403** | ✅ all 9 |
| — | contract | Every error code named in an example is registered | ✅ |
| — | contract | The operation register and the error register name the same codes | ✅ mutation-tested |

40 assertions in `tests/api/test_api_operations.py`. Python suite: 405 → **440**.

## 8. Telemetry, security and accessibility
Traces carry tenant-safe correlation IDs; no PII in telemetry. Any user-facing surface is keyboard and screen-reader complete (`REQ-A11Y-001`) and completable without the map (`REQ-A11Y-003`).

## 9. Documentation to update
- [ ] Sub-step completion record
- [ ] [IMPLEMENTATION_LOG](../../../10-logs/IMPLEMENTATION_LOG.md) · [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) · [BUG_REGISTER](../../../10-logs/BUG_REGISTER.md) if applicable
- [ ] `BR-023` post-change section
- [ ] Parent step §21 · [MASTER_TRACKER](../../../02-delivery/MASTER_TRACKER.md)

## 10. Regression cross-check (R1–R7)
| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression suite | **PASS** | 440 Python + 61 web + 307 UI + 40 browser |
| R2 contract compatibility | **PASS** | Purely additive; `.01` declared no paths |
| R3 graph diff as expected | **PASS** | Regenerated register only; no Python behaviour changed |
| R4 untested requirements | **PASS — improved** | Seven requirements gain contract-level assertions |
| R5 orphan/unowned nodes | **PASS** | Catch-all owner covers `contracts/` |
| R6 closed-bug regression tests | **PASS** | BUG-001…019; meta-suite 43/43 |
| R7 tenant isolation | **PASS — 12/12** | Plus: **no operation accepts a tenant parameter** |

**Overall:** **PASS**. Full detail in [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md).

## 11. Rollback
Revert this sub-step's commit; prior sub-steps stay intact and `main` stays deployable. Schema work uses expand/contract, so the expand phase is reversible.

## 12. Acceptance criteria
- [x] Nine operations specified with all response codes — and every one declares at least one failure, because an operation with only success responses is an operation nobody has thought about failing
- [x] Async operations declare the job-handle contract — API-004 and API-005 return `JobHandle` with an SSE `events_url`
- [x] Owner-only operations declare it — API-008 matches `select_canonical_scenario`, which the authorization matrix grants to `trip_owner` and denies to `trip_editor`
- [x] Every volatile field carries source, observed time, effective time, confidence — **enforced by the type**, not by convention: the field's schema *is* `Evidenced`, and all five provenance members are required

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | 2026-08-11 |
| Commit SHA | *(this commit)* |
| Pushed | ✅ |
| Graph re-indexed at | post-commit |
| `main` green and deployable | ✅ |
| Bugs found | None logged. **Six defects found and fixed inside the sub-step**, five of them in the contract itself — see the regression entry |
| Notes / surprises | The prediction held exactly: *"encoding provenance in the response schema is what makes REQ-EVID-001 enforceable rather than aspirational — a handler cannot omit what the contract requires."* The `Evidenced` type is that sentence made structural, and `status` has no default so a caller cannot omit it and get `confirmed` free.<br><br>**The pre-change check found a defect before a line was written.** Three error codes declared by operations did not exist in the register — two transposed names and one, `validation.invalid_party`, against a Validation class that had been declared since the document was written and never given a code. None of it would have failed anything: `API_CONTRACTS.md` is prose, nothing read it, and a client branching on a code the server cannot send simply never takes that branch.<br><br>**Five of six failures in this sub-step were the contract catching itself.** `PUT /brief` required `If-Match` but not `Idempotency-Key` — a conditional PUT looks naturally idempotent until a lost response leaves the retry with a stale precondition and a 409, and the client cannot tell whether its change applied. `.01`'s guessed remediation payload turned out wrong the moment a real relaxation needed to name the constraint it relaxes. And `allOf` with `additionalProperties: false` rejected a field the same schema requires two lines later, because each branch validates the whole instance independently.<br><br>Every one of those is cheaper here than at STEP-012 with a solver already written against the wrong shape. |
