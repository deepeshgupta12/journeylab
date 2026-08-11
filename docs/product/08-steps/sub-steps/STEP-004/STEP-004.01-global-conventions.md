---
sub_step_id: STEP-004.01
parent_step: STEP-004
title: Global API conventions: errors, pagination, idempotency, ETags
status: VERIFIED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-PLAT-005]
blast_radius_id: BR-028
depends_on: [STEP-003.08]
last_updated: 2026-08-11
---

# STEP-004.01 — Global API conventions: errors, pagination, idempotency, ETags

## 1. Outcome
One set of conventions governs every endpoint, so no service invents its own error shape, pagination or concurrency semantics.

## 2. Scope and boundary
**In scope:** RFC 9457 problem details with stable `type` URIs; cursor pagination; `Idempotency-Key`; ETag/`If-Match`; correlation headers; rate-limit declarations.

**Not in this sub-step:** Individual operations (`.02`–`.04`); implementations behind them.

## 3. Requirements served
| Requirement | Acceptance criterion | Test |
| --- | --- | --- |
| REQ-PLAT-005 | See §12 | See §7 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | ✅ **NOT BLOCKED** — and for the first time the graph traced an execution flow rather than returning zero |
| HEAD / indexed commit | `f50d854` / `f50d854` — matched |
| Queries run | `impact(opaque_denial)` → **2 direct callers, 1 process, `epistemic: exact`**; `query(...)` → **empty, with "FTS indexes missing"**; `detect_changes()` |
| Unknown / low-confidence areas | Rate-limit values need capacity projections that do not exist (`ASM-002`) — mechanism declared, numbers deferred. **New:** `gitnexus_query` is silently degraded (`BR-028` §3) |
| Blast radius | **[BR-028](../../../10-logs/blast-radius/BR-028-api-conventions.md) — MEDIUM, confidence HIGH.** The record predicted `BR-022`; that number was already taken by STEP-003.05 |
| Approval required? | **No** — MEDIUM with high confidence |

## 5. Implementation plan
- [x] Problem-details schema with the error-code register — **generated** from ERROR_MODEL.md by one parser and two emitters (`ADR-012` for the second time). 21 codes, 17 client-visible
- [x] Cursor pagination envelope — offset is absent *structurally*, and a cursor may not carry identity, checked on decode as well as encode
- [x] `Idempotency-Key` required on all commands — case-insensitive lookup, canonical-JSON replay comparison
- [x] ETag and `If-Match` on mutable resources — strong tags bound to resource **and** version; a missing `If-Match` is refused, not treated as consent
- [x] **403 and 404 share an identical body shape** — forced to 404, with no `detail` field to differentiate and a test on the function signature
- [x] Money as integer minor units; RFC 3339 with explicit IANA zone — both declared in `contracts/openapi.yaml`

## 6. Contracts and schema changes
Contracts are declared in [STEP-004](../../STEP-004-contract-first-platform-apis.md); this sub-step consumes them. Any change follows [CONTRACT_CHANGE_POLICY](../../../04-contracts/CONTRACT_CHANGE_POLICY.md).

## 7. Tests to add
| Test | Type | Asserts | Status |
| --- | --- | --- | --- |
| TST-PLAT-005 | contract | Problem details conform to RFC 9457; the published contract parses | ✅ |
| — | contract | 403 and 404 bodies indistinguishable | ✅ status, body, absent `detail`, **and the function signature** |
| — | unit | An unregistered code cannot be raised | ✅ |
| — | unit | `detail` refuses a traceback, connection string, credential or email | ✅ 6 cases |
| — | unit | A cursor may not carry a tenant, on decode as well as encode | ✅ 7 forbidden keys |
| — | unit | The generated register still matches the markdown | ✅ drift gate |

70 assertions in `tests/api/test_api_conventions.py`. Python suite: 335 → **405**.

## 8. Telemetry, security and accessibility
Traces carry tenant-safe correlation IDs; no PII in telemetry. Any user-facing surface is keyboard and screen-reader complete (`REQ-A11Y-001`) and completable without the map (`REQ-A11Y-003`).

## 9. Documentation to update
- [ ] Sub-step completion record
- [ ] [IMPLEMENTATION_LOG](../../../10-logs/IMPLEMENTATION_LOG.md) · [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) · [BUG_REGISTER](../../../10-logs/BUG_REGISTER.md) if applicable
- [ ] `BR-022` post-change section
- [ ] Parent step §21 · [MASTER_TRACKER](../../../02-delivery/MASTER_TRACKER.md)

## 10. Regression cross-check (R1–R7)
| Check | Result | Detail |
| --- | --- | --- |
| R1 full regression suite | **PASS** | 405 Python + 61 web + 307 UI + 40 browser |
| R2 contract compatibility | **N/A → baselined** | The contract is created here; from `.02` there is something to diff |
| R3 graph diff as expected | **PASS** | New package and generators; one modified test |
| R4 untested requirements | **PASS** | REQ-PLAT-005 newly covered |
| R5 orphan/unowned nodes | **PASS** | Catch-all owner covers `contracts/` |
| R6 closed-bug regression tests | **PASS** | BUG-001…019; meta-suite 43/43 |
| R7 tenant isolation | **PASS — 12/12** | Plus the new cursor assertion |

**Overall:** **PASS**. Full detail in [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md).

## 11. Rollback
Revert this sub-step's commit; prior sub-steps stay intact and `main` stays deployable. Schema work uses expand/contract, so the expand phase is reversible.

## 12. Acceptance criteria
- [x] Conventions documented in OpenAPI and enforced by schema
- [x] Error codes match the register — **by generation**, with a drift gate, so they cannot stop matching
- [x] Idempotency and concurrency semantics declared — as reusable components; per-operation declarations land with the operations in `.02`–`.04`
- [x] Enumeration prevented by identical 403/404 shapes — one status, one body, no `detail` field, and the signature is asserted

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | 2026-08-11 |
| Commit SHA | *(this commit)* |
| Pushed | ✅ |
| Graph re-indexed at | post-commit |
| `main` green and deployable | ✅ |
| Bugs found | None logged. Five defects found and fixed within the sub-step — see the regression entry |
| Notes / surprises | The prediction was right — *"getting 403/404 indistinguishability into the shared convention is far cheaper than retrofitting it across 18 operations"* — and the sub-step nearly proved it the hard way. **The generated register silently returned 403**, because `ERROR_MODEL.md` writes the status as "403/404" and the parser took the first. That would have reversed STEP-002.02 across every operation built on this convention. Caught by a test written from the requirement rather than from the code.<br><br>**Naming the package `http` shadowed the standard library.** `apps/api/src` is on `pythonpath`, so nothing would have failed at import — it would have failed later, somewhere else, when a dependency reached for `http.client`.<br><br>A test that exists to fail on purpose fired for the wrong reason: the cross-tenant ratchet saw the word `redis` inside a regex forbidding connection strings. Narrowing it needed its own test, because the fix for a false positive quietly becomes a permanent false negative.<br><br>**Two error shapes now coexist.** `auth/errors.py` is not RFC 9457 and cannot be migrated until routes exist to verify against (STEP-004.04). Stated rather than deferred silently. |
