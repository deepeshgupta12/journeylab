---
blast_radius_id: BR-031
sub_step_id: STEP-004.04
title: Privacy, admin, coverage and job operations (API-015…018)
author: Deepesh Kumar Gupta
date: 2026-08-11
score: MEDIUM
confidence: HIGH
approval_required: false
---

# BR-031 — Privacy, admin, coverage and job operations

> The sub-step record predicts `BR-025`, held by STEP-003.08. This is `BR-031`.

## 1. Graph state

| Field | Value |
| --- | --- |
| Indexed commit | `6ea8436` |
| HEAD at check | `6ea8436` |
| Freshness | ✅ up to date |
| Result | **NOT BLOCKED**, but see §3 — one query returned a confidently wrong answer |
| Confidence | **HIGH** for this change; **reduced** in the tool itself |

## 2. Queries run

| # | Query | Result |
| --- | --- | --- |
| 1 | `impact(CLIENT_VISIBLE)` | **Ambiguous** — same declaration indexed twice. Disambiguated by `target_uid` |
| 2 | `impact(uid=Variable:…CLIENT_VISIBLE)` | **`0 impacted`, `risk: LOW`, `epistemic: exact`** — and it is wrong (§3) |
| 3 | `detect_changes()` | Run pre-commit |

## 3. The graph reported zero, confidently, and was wrong

`CLIENT_VISIBLE` has **five references across two files**:

```
tests/api/test_api_operations.py:19    from conventions.error_codes import CLIENT_VISIBLE
tests/api/test_api_operations.py:329   assert code in CLIENT_VISIBLE
tests/api/test_api_conventions.py:28   from conventions.error_codes import CLIENT_VISIBLE, ERROR_CODES
tests/api/test_api_conventions.py:96   assert set(published["enum"]) == CLIENT_VISIBLE
tests/api/test_api_conventions.py:477  for code in CLIENT_VISIBLE:
```

The graph reports `0 impacted` and labels it **`epistemic: exact`**.

**This is worse than the FTS gap**, and worth stating plainly. The degraded
concept search at least emits a warning. This emits a guarantee. A pre-change
check that targets a module-level constant will report a clean blast radius for a
symbol with real dependents, and `epistemic: exact` invites the reader to stop
looking.

Module-level constants imported with `from x import Y` are not traced. So the
running list of graph limitations is now:

| # | Limitation | First recorded |
| --- | --- | --- |
| 1 | `workspace:*` package aliases are not followed | `BR-024` §3 |
| 2 | React components used as JSX have zero traced dependents | `BR-025` §3 |
| 3 | CSS has no representation at all | `BR-026` §3 |
| 4 | `gitnexus_query` returns empty; `--repair-fts` is not a valid flag | `BR-029` §3 |
| 5 | The same declaration is indexed twice (`Property` and `Variable`) | `BR-030` §3 |
| 6 | **Imported constants report `0 impacted` as `exact`** | here |

Functions are traced correctly, and that is genuinely useful — `impact(problem)`
and `impact(safe_detail)` both returned real callers and processes. The tool is
reliable for one shape of symbol and silently unreliable for several others.

**Consequence for the working agreement:** a `0 impacted` result is only
trustworthy for a Python function. Everywhere else it means "not traced". Carried
to `STEP-026` and already warned about in `CLAUDE.md`.

## 4. A correction to something I said

I stated in the previous hand-off that `auth/errors.py` would migrate to RFC 9457
at `.04`, and that invitation redemption would land here. **Neither is true.**
`.04` is privacy, admin, coverage and jobs — and STEP-004 declares contracts only.
No route handler exists anywhere in the repository, so a migration has nothing to
be verified against.

Both remain carried: the migration needs real handlers, which arrive with the
implementing steps (STEP-008 onward), not with the contract.

## 5. Change inventory

| File | Change |
| --- | --- |
| `contracts/openapi.yaml` | **6 operations, 8 schemas.** API-015…018, with tracking and cancellation as their own operations |
| `tests/api/test_api_operations.py` | 23 new assertions |

No generated file changed; every code these operations reference was registered.

## 6. Twelve impact categories

| # | Category | Assessment |
| --- | --- | --- |
| 1 | Callers / call graph | None |
| 2 | **Public API / contracts** | 6 operations, all `PROPOSED`. Purely additive. **22 operations now declared in total** |
| 3 | Database / schema | None. `DATA-015` still undefined (STEP-006) |
| 4 | Events | None new |
| 5 | Configuration | None |
| 6 | Infrastructure | None |
| 7 | **Security** | **The reason this is MEDIUM.** The first unauthenticated operation in the contract, plus a four-eyes control. See §7 |
| 8 | **Privacy** | The whole of API-015. Per-store deletion tracking makes `REQ-PRIV-006` verifiable by the subject rather than asserted to them |
| 9 | Accessibility | Not directly |
| 10 | Performance | None declared |
| 11 | Tenancy | Unchanged. Coverage is public and **tenant-free by construction** — it has no tenant-scoped field to leak |
| 12 | Documentation | This record, `IMPL-028`, the sub-step record, `REGRESSION_LOG`, `MASTER_TRACKER` |

## 7. Data-flow inspection

### 7.1 The one public operation

`getCoverage` declares `security: []`, overriding the global bearer requirement.
It is the only operation in the contract that does, and a test **counts them** —
so a second one added by accident is visible rather than inherited.

Public is correct here: a traveller must be able to learn their destination is
unsupported without registering to be told no.

| Hazard | Control |
| --- | --- |
| Provider identity leaking to an anonymous caller | `provider_health` is a single aggregate enum. Never a list, never a name, never a count — each of those leaks the shape of the supply chain |
| Quota detail revealing when the product is weakest | No quota, rate-limit or remaining-capacity field exists |
| A future field arriving undeclared | `Coverage` and `CoverageRegion` are **closed** |
| Enumeration of unsupported regions | Nothing to enumerate: the response is a complete list of what *is* supported |

A test asserts eight specific leak-shaped names are absent from the public
response, not merely that the current fields look fine.

### 7.2 Privacy — verifiable, not assertable

`REQ-PRIV-006` requires deletion to traverse **primary, object, vector, graph,
cache, export and token** stores. The record names all seven individually and
carries a per-store state.

A single `complete` boolean goes true when the easy stores finish. `REQ-PRIV-007`
is about the subject being able to *see* the outstanding ones, so
`partially_failed` is a distinct state — six of seven is not complete, and calling
it complete is the specific failure the requirement guards against.

Acceptance is `202`, never `200`: the work continues after the response, and
saying otherwise is a lie the subject acts on. Export URLs are documented as
expiring and single-use, because a permanent link to someone's entire trip
history is a credential.

### 7.3 Four-eyes, and a control that cannot currently be satisfied

`status` is **absent from the request schema**, which is closed. A caller that
could ask for `active` could skip four-eyes; the server decides, and a high-impact
override is created `pending_approval`.

The contract names a **second curator**, matching `AUTHORIZATION_MATRIX` §4.
`DEC-010` has not resolved whether an `ops_admin` may stand in, so the contract
declares only what the matrix states — encoding a guess would be inventing
authorization policy.

**With a single owner, four-eyes is structurally unsatisfiable** (`ADR-010`). The
contract declares the control correctly; satisfying it is an organisational
problem that `STEP-021` cannot ship without.

An override additionally requires a reason of at least ten characters and at least
one piece of evidence. "Fix" is not a reason, and a fact override with no
supporting evidence is an opinion overwriting a source.

### 7.4 Job streaming

`heartbeat` is a declared event type, and that is the operation's central design
decision: without it a client cannot distinguish a job that is thinking from a
connection that died, and a traveller watching a spinner cannot either.

The stream carries **warnings**, not only progress and result — a generation that
succeeded while three providers were degraded is not the same as one that
succeeded cleanly. Events are sequenced so a reconnecting client can tell whether
it missed anything rather than assuming it did.

Cancellation returns `202`, not `204`: a job mid-flight stops at a safe point, and
claiming it has already stopped would be a lie the client acts on. `REQ-NFR-004`
requires the last valid state to survive cancellation.

## 8. Score

| Dimension | Value | Reason |
| --- | --- | --- |
| Reach | Medium | Privacy, admin and platform steps implement against these |
| Reversibility | High | Declarative only |
| Detectability | High | 23 assertions; 492 Python tests total |
| Security exposure | Medium | First public operation; four-eyes control |
| **Overall** | **MEDIUM** | Confidence HIGH in the change; **reduced confidence in the graph tooling** (§3) |

## 9. Post-change verification

| Check | Result |
| --- | --- |
| Python suite | **492 passed, 5 skipped** (up from 469) |
| `ruff` / mypy | Clean |
| Every `$ref` resolves; exactly one unauthenticated operation | Asserted |
| `pnpm verify`, `pnpm ci:local`, R1–R7 | Recorded in the regression entry |
