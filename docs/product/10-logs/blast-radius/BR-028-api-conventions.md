---
blast_radius_id: BR-028
sub_step_id: STEP-004.01
title: Global API conventions — errors, pagination, idempotency, ETags
author: Deepesh Kumar Gupta
date: 2026-08-11
score: MEDIUM
confidence: HIGH
approval_required: false
---

# BR-028 — Global API conventions

> The sub-step record predicts `BR-022`, which STEP-003.05 already holds. This
> record is `BR-028`, continuing from `BR-027`. Corrected in the sub-step file.

## 1. Graph state at the time of the check

| Field | Value |
| --- | --- |
| Tool | `npx gitnexus status`, `gitnexus_impact` (MCP) |
| Indexed commit | `f50d854` |
| HEAD at check | `f50d854` |
| Freshness | ✅ up to date |
| Result | **NOT BLOCKED** — and for the first time the graph traced an execution flow rather than returning zero |
| Confidence | **HIGH** |

## 2. Queries run

| # | Query | Result |
| --- | --- | --- |
| 1 | `impact(opaque_denial, upstream, includeTests)` | **2 direct callers** (`_extract_bearer`, `resolve_context`), **1 affected process** (`resolve_context → opaque_denial`), 1 module (Auth). LOW, `epistemic: exact` |
| 2 | `impact(contrastPairs)` / `impact(renderCss)` — from BR-026, still valid | unchanged |
| 3 | `query("error response problem details status code")` | **Returned nothing, with a warning: "FTS indexes missing — keyword search degraded."** See §3 |
| 4 | `detect_changes()` | Run pre-commit; recorded in the regression entry |

**Query 1 is the first genuinely useful graph answer in this repository.** Python
functions are called with parentheses, so the call graph traces them — unlike
React components (`BR-025` §3) and CSS (`BR-026` §3), which it cannot see at all.
Worth recording that the tool works where the language cooperates.

## 3. A third graph limitation, and this one is fixable

`gitnexus_query` returned no results and warned that its full-text indexes are
missing, suggesting `gitnexus analyze --repair-fts`.

So the concept search — the thing `CLAUDE.md` tells contributors to use *instead
of* grepping — has been silently degraded for an unknown number of sub-steps. It
did not fail; it returned an empty result set, which reads exactly like "no such
concept exists".

Not repaired in this sub-step, because re-indexing with a new flag mid-change
would invalidate the pre-change state this record is written against. Logged as a
follow-up and carried to `STEP-026`, alongside the JSX and CSS gaps.

## 4. Change inventory

**Added**

| File | Purpose |
| --- | --- |
| `tools/error_model_source.py` | Single parser for `ERROR_MODEL.md` §3 |
| `tools/gen_error_codes.py` | Two emitters over it |
| `apps/api/src/conventions/error_codes.py` | **Generated.** 21 codes |
| `apps/api/src/conventions/problem.py` | RFC 9457 problem details |
| `apps/api/src/conventions/pagination.py` | Cursor pagination |
| `apps/api/src/conventions/concurrency.py` | Idempotency, ETag, correlation |
| `contracts/openapi.yaml` | OpenAPI 3.1 — conventions only |
| `contracts/schemas/error-codes.json` | **Generated.** 17 client-visible codes |
| `tests/api/test_api_conventions.py` | 70 assertions |

**Modified**

| File | Change |
| --- | --- |
| `tests/security/test_tenant_isolation.py` | The pending-vector detector now matches **usage, not mention** — see §6 |
| `pyproject.toml` | `types-PyYAML` for the contract tests |

**Not yet modified, deliberately:** `apps/api/src/auth/errors.py` still returns
its STEP-002.02 body. See §7.

## 5. Twelve impact categories

| # | Category | Assessment |
| --- | --- | --- |
| 1 | **Callers / call graph** | Additive. Nothing existing calls the new modules yet — `.02`–`.04` will. `opaque_denial` in `auth/errors.py` is untouched this sub-step (§7) |
| 2 | **Public API / contracts** | **This sub-step IS the contract.** `contracts/openapi.yaml` is created and becomes authoritative for schemas (`ADR-001`). No operations declared, so no operation can break |
| 3 | **Database / schema** | None |
| 4 | **Events** | None. AsyncAPI is `.05` |
| 5 | **Configuration** | None |
| 6 | **Infrastructure** | None. One dev dependency (`types-PyYAML`) |
| 7 | **Security** | **Material, and the reason this is MEDIUM.** Three enumeration and leakage surfaces are defined here rather than per-operation. See §6 |
| 8 | **Privacy** | Positive. `safe_detail` refuses to emit a problem document containing a traceback, connection string, credential or email address — `REQ-PRIV-004` and `ERROR_MODEL.md` §5, enforced rather than documented |
| 9 | **Accessibility** | None |
| 10 | **Performance** | Cursor pagination avoids the re-scan offset pagination costs per page. No runtime cost added |
| 11 | **Tenancy** | **Positive and enforced.** A cursor may not carry a tenant, organization, user, actor, role or scope, and that is checked on **decode** as well as encode |
| 12 | **Documentation** | This record, `IMPL-025`, the sub-step record, `REGRESSION_LOG`, `MASTER_TRACKER` |

## 6. Mandatory data-flow inspection

Three flows, each a surface that would otherwise be re-litigated per operation.

### 6.1 Error responses — what leaves the server

**Flow:** failure → `problem(code, …)` → register lookup → `application/problem+json`.

| Hazard | Control | Evidence |
| --- | --- | --- |
| An invented error shape per service | `problem()` takes a **code**, not strings. Status, title and remediation come from the generated register | An unregistered code raises; test asserts it |
| A stack trace, connection string, credential or email in `detail` | `safe_detail()` **raises**, and deliberately does not redact — redaction turns a developer mistake into a truncated message that still ships | 6 parametrised leak cases |
| A provider identity reaching a client | Never placed in a problem document; `ERROR_MODEL.md` §5 calls it commercially confidential and attack-surface information | Structural — the register carries no provider field |
| An internal condition returned as an error | `ai.injection_detected` and friends have no client status and cannot be emitted | Test asserts the raise; the published enum excludes them |
| A missing correlation ID on exactly the responses support needs | Required parameter, no default | Test asserts the raise |

### 6.2 Enumeration — REQ-SEC-004

**Flow:** unauthorized / missing / cross-tenant → `opaque_denial()` → one response.

The status is **forced to 404**, overriding the register. `ERROR_MODEL.md` writes
`authz.forbidden` as "403/404" — meaning the two are indistinguishable — and does
not say which is sent. The parser took the first and produced a 403, which
silently undid STEP-002.02. A 403 still confirms that *something* is there to be
forbidden.

`opaque_denial` still takes no `reason` parameter, and the `detail` field is
**omitted entirely** rather than set to a constant, so there is no field a future
edit can differentiate. A test asserts the function's signature, so adding one
fails the build.

### 6.3 Cursors — client-controlled state that looks opaque

**Flow:** `cursor` query parameter → base64 decode → JSON → keyset → query.

A cursor is base64, **not encryption**. The client can read and rewrite it.

| Hazard | Control |
| --- | --- |
| A tenant or identity smuggled in a cursor | 14 forbidden keys rejected **on decode**, not only on encode. Encode-side validation catches our mistakes; decode-side catches the attacker's |
| A crafted cursor making the server parse something expensive | 2048-byte cap before any decoding |
| A caller learning why their cursor failed | Every failure raises the identical message, `"invalid cursor"` — the same reasoning as the opaque denial |

## 7. What this sub-step deliberately does NOT do

**`auth/errors.py` is unchanged.** It still returns the STEP-002.02 body
`{"error": {"code": "not_found", …}}`, which is not RFC 9457.

Migrating it means changing a function with two live callers inside a traced
execution flow, and there is no HTTP surface yet to verify the migration against
— `apps/api` has no routes. Doing it here would be a change with no test that
exercises the path it affects.

It is recorded as a carried item for `STEP-004.04`, where the platform routes
land and the migration can be proven end to end. **Until then two error shapes
exist in the repository**, and that is stated rather than left for someone to
discover.

## 8. A test I narrowed, and why that needed its own proof

The cross-tenant ratchet in `test_tenant_isolation.py` fired: it reported that a
cache subsystem had landed. It had not. The word `redis` appears inside a
**prohibition** pattern in `problem.py` — a regex whose only purpose is to stop a
connection string reaching a client — and the detector searched raw source text.

A keyword search finds the warning as readily as the violation.

The detector now strips comments and string literals before matching, and the
cache pattern matches the *shape* of use (`import redis`, `redis.`) rather than
the word. **Narrowing a detector that exists to fail on purpose is dangerous**, so
`test_the_detector_can_still_fire` asserts it still sees real code and still
ignores a literal — and a seeded `import redis` was confirmed to trip it.

## 9. Score

| Dimension | Value | Reason |
| --- | --- | --- |
| Reach | Medium | Every future operation inherits these conventions |
| Reversibility | High | New files plus one narrowed test; no schema, no data |
| Detectability | High | 70 new assertions; 405 Python tests total |
| Security exposure | Medium | Three surfaces defined here — all mitigated and tested (§6) |
| Performance | None | No runtime path yet |
| **Overall** | **MEDIUM** | **Confidence HIGH.** No owner approval required |

## 10. Post-change verification

| Check | Result |
| --- | --- |
| Python suite | **405 passed, 5 skipped** (up from 335) |
| `ruff check` / `ruff format` / mypy | Clean, 32 source files |
| `pnpm verify` | Recorded in the regression entry |
| `pnpm ci:local` | Recorded in the regression entry |
| R1–R7 | Recorded in the regression entry |
