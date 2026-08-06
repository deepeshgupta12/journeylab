# BR-011 — Tenant and actor context resolution at the API boundary

| Field | Value |
| --- | --- |
| Sub-step | STEP-002.02 |
| Requirements | REQ-SEC-001, REQ-SEC-004 |
| Bugs found | `BUG-010`, `BUG-011` |
| Author | Deepesh Kumar Gupta |
| Date | 2026-08-06 |

> **Numbering note:** the sub-step front-matter names `BR-008`, which belongs to STEP-002.01. This record is `BR-011`; the front-matter has been corrected.

## 1. Intent (step 1)
Resolve actor and tenant **from the verified token alone**, bind that tenant to the database transaction so the STEP-002.01 RLS policies apply, and reject any request whose context cannot be resolved — indistinguishably from a missing resource.

## 2. Graph state (step 2 — all six fields)
| Field | Value |
| --- | --- |
| Repository / branch | journeylab / `main` |
| HEAD commit | `f544d38` |
| Graph indexed commit | `f544d38` — re-indexed immediately before analysis |
| **Match?** | **Yes** |
| Index timestamp | verified at analysis time |
| Extractor / schema version | **Not exposed** by the tool — recorded as a gap, not invented |
| Coverage and known gaps | Documentation + 1 migration. **0 indexed application symbols** (`RISK-014`) |
| Status | **`BLOCKED` for application code — static fallback** |

> Knowledge-graph pre-change check: `BLOCKED`. Static fallback applied. This does **not** satisfy the `REQ-KG-008` release gate.

## 3. Target nodes (step 4)
| Node | Type | Location | Owner |
| --- | --- | --- | --- |
| `auth.claims` | Module (new) | `apps/api/src/auth/claims.py` | Deepesh Kumar Gupta |
| `auth.context` | Module (new) | `apps/api/src/auth/context.py` | " |
| `auth.dependencies` | Module (new) | `apps/api/src/auth/dependencies.py` | " |
| `auth.db` | Module (new) | `apps/api/src/auth/db.py` | " |
| `auth.errors` | Module (new) | `apps/api/src/auth/errors.py` | " |
| `auth.events` | Module (new) | `apps/api/src/auth/events.py` | " |
| `app.current_org` setting | Security binding | consumed by migration 001 policies | " |

## 4. Dependencies (step 5 — static fallback, three hops)
**Hop 1 — direct outbound:** `app_current_org()` and the RLS policies from migration 001 (STEP-002.01); FastAPI (`TECHNICAL_ARCHITECTURE` — Confirmed); psycopg 3 (`ADR-011`, decided in this sub-step).

**Hop 2:** the policies gate `memberships`, `service_identities`, `organizations`. Those tables are the fan-in for the 12 downstream steps STEP-002 unblocks.

**Hop 3:** every future endpoint (`STEP-004`), every worker (`STEP-006`), every retrieval path (`STEP-010`) will obtain its tenant through this module or bypass tenancy entirely.

**Inbound today:** **none.** Verified, not assumed: no route table, no application entrypoint, no worker exists. `apps/api/src/main.py` is STEP-004's.

**Fallback honesty:** BR-008 predicted that from this sub-step the static fallback "becomes genuinely partial". In practice it is still near-exhaustive *inbound* — this is the first application code, so nothing can import it yet. It is **partial outbound**, because the reach of these modules is a prediction about future steps rather than an observation. That distinction is the honest one, and it is narrower than BR-008 anticipated.

## 5. Impact by category (step 6 — all twelve, enumerated)
| # | Category | Affected | Confidence |
| --- | --- | --- | --- |
| 1 | Requirements / scope steps | `REQ-SEC-001`, `REQ-SEC-004`; STEP-002.02; prerequisite for .03–.07, STEP-004, STEP-006 | High |
| 2 | Owners / consumers | Sole owner; no external consumers | High |
| 3 | Frontend routes / components | **None** — no UI calls an API yet. The `403`/`404` indistinguishability decision will constrain STEP-003 error messaging | High |
| 4 | Backend services / workflows / jobs | **None exist.** `to_job_payload`/`from_job_payload` define how they will carry context; **no enforcement that they use it** until STEP-006 | **Medium — carried gap** |
| 5 | APIs / schemas / clients / webhooks | **None** — `API-001` remains `PROPOSED`. This sub-step fixes the *shape* of the auth failure response that every API contract will inherit | High |
| 6 | Events / producers / consumers | `stamp_envelope` exists; **no outbox exists to enforce it** (STEP-006, `DEC-009` open) | **Medium — carried gap** |
| 7 | Tables / columns / migrations / caches / indexes | **No schema change.** Consumes `app.current_org`; adds no table. Cache keys must include tenant — not applicable yet, flagged for STEP-010 | High |
| 8 | Datasets / models / prompts / retrievers / tools / evals | **None** | High |
| 9 | Tests / fixtures / contract suites | **New `tests/api/` — 29 tests.** `pnpm test` now executes them (`BUG-011`); five mutation scenarios run against them | High |
| 10 | Services / deployments / infrastructure | New Python runtime deps (`fastapi`, `psycopg[binary,pool]`). No deployment exists | High |
| 11 | Dashboards / alerts / runbooks | **`ALRT-SEC-001` / `RB-SEC-001` still unimplemented** (STEP-024). Auth denials are counted in neither. A credential-stuffing run against this boundary would be silent | **Medium — gap, carried since BR-008** |
| 12 | Documentation / deprecation commitments | `ADR-011`; sub-step record; `BUG-009/010/011`; parent STEP-002 §21; MASTER_TRACKER | High |

## 6. Data-flow inspection (step 7 — MANDATORY, security boundary)
`KG-Q-014` is mandatory here. BR-008 stated that from this sub-step the check becomes "both mandatory **and** runnable", and that a still-`BLOCKED` graph would be "a genuine gap rather than a vacuous one".

**Assessed honestly: it is still not runnable pre-change, but for a defensible reason.** `gitnexus trace` needs indexed application symbols; at analysis time there were none, because this sub-step *creates* the first ones. The pre-change graph could not describe a flow that did not yet exist.

**What was done instead — manual trace of the authentication data flow, end to end:**

| Hop | Element | Tenant-affecting? | Evidence |
| --- | --- | --- | --- |
| 1 | HTTP request | Carries an `Authorization` header and *may* carry hostile `X-Tenant-Id` | Test: three hint variants ignored |
| 2 | `_extract_bearer` | Reads **only** `authorization` | Source: `request` is not consulted elsewhere |
| 3 | `TokenVerifier.verify` | Trust boundary — port, `DEC-004` unbound | Raises `TokenError`; no partial claims returned |
| 4 | `RequestContext.from_claims` | Tenant fixed from claims | Frozen dataclass; no setter |
| 5 | `bind_tenant` | Tenant → `app.current_org`, transaction-scoped | Bind parameter, `is_local=true` |
| 6 | RLS policies | Row filtering | STEP-002.01, R7 12/12 |
| 7 | Job payload / event envelope | Tenant crosses the async boundary as **data** | Round-trip + malformed-payload tests |

**Post-change follow-up — COMPLETED at commit `0b87024`.** Re-indexed: 3,037 nodes / 4,092 edges. The extractor **does** emit Python symbols.

| Measure | Result |
| --- | --- |
| Python files indexed | 8/8 (`apps/api/src/auth/*`, `tests/api/*`) |
| Symbols under `apps/api` | 13 Function, 5 Class, 8 Property, 20 Variable |

`KG-Q-014` was then run for real against the indexed graph, and it **reproduces the manual trace above independently**:

```
resolve_context -> _extract_bearer -> opaque_denial
resolve_context -> verify           (TokenVerifier port)
resolve_context -> from_claims      (tenant fixed here)
bind_tenant     -> execute          (parameterised set_config)
```

No module outside `auth/` imports `claims` or `context`, so there is no second path by which a tenant could enter.

**One finding the graph surfaced that the manual trace did not state:** `bind_tenant` has **no caller in application code** — only tests. Correct for this sub-step, because no endpoint exists. But it means context resolution (`dependencies.py`) and database binding (`db.py`) are **not yet connected to each other**; `dependencies.py` does not import `db.py`. `STEP-004` must wire them, or requests will resolve a tenant and never bind it — which fails closed (zero rows) rather than leaking, but would be a silent, confusing outage. Carried as an explicit STEP-004 obligation.

**Consequence for `RISK-014`:** downgraded. The graph is no longer documentation-only, and pre-change checks become genuinely runnable from `STEP-002.03` onward. A `BLOCKED` status in a future record is now a real gap with no fallback excuse.

## 7. Classification (step 8)
`direct` (new security boundary) · `security/privacy` · `test-integrity` (two guard defects found) · **`unknown`:** the reach of `to_job_payload`/`stamp_envelope`, because their consumers do not exist yet.

## 8. Risk scoring (step 9)
| Dimension | 1–5 | Rationale |
| --- | --- | --- |
| Likelihood of unintended effect | 2 | No inbound callers today; the code cannot break something that does not call it |
| Severity if it occurs | **5** | This is the function that decides which tenant a request acts as. A defect here is cross-tenant exposure — `RISK-010`, SEV1 |
| Reach | **5** | Every endpoint, worker and event in the product will pass through it |
| Detectability | 2 | 29 tests, 5 of 5 mutants killed — **after** one mutant initially survived |
| Reversibility | 2 | Revertible now; forward-only once endpoints depend on it |
| **Confidence in this analysis** | 2 | Manual trace complete; graph `BLOCKED` caps confidence, and future reach is predicted rather than observed |
| Customer criticality | 1 | No customers; this is the control that will protect them |

**Overall: HIGH** — severity × reach, as with BR-008.

## 9. Unknown or low-confidence areas
| Area | Why uncertain | Residual risk |
| --- | --- | --- |
| **Mutation gap found and closed** | `set_config(..., false)` — session-wide instead of transaction-local — **passed all 28 tests**. R7 covered the SQL-level property; nothing covered `bind_tenant`, which is what application code calls | **Closed.** Test added; mutant now dies. The general lesson stands: a property proven at one layer is not proven at the layer above |
| Malformed tenant raises rather than denying silently | `app_current_org()` casts to `uuid`; garbage raises `InvalidTextRepresentation` | **Accepted, documented.** Fails closed either way. Loud-on-malformed is preferred: it can only come from a binding bug |
| PEP 563 breaks FastAPI dependency resolution | `from __future__ import annotations` + `Annotated[..., Depends(local)]` → annotation resolved in module globals → silent `422` | **Live hazard for STEP-004.** Observed here; noted in the test file. No guard prevents it |
| No enforcement that jobs/events carry context | Consumers do not exist | **Open** — enforcement belongs to STEP-006 |
| Alerting on auth denials | Not implemented | **Open** — STEP-024 |
| Graph may not index Python at all | Untested before this commit | **Open** — must be checked at post-commit re-index |
| `auth` as a top-level package name | Generic; could collide if a second service shares the path | Low. Followed the sub-step's literal path rather than silently diverging from the documentation |

## 10. Required actions (step 10)
Token-only resolution; ignore client hints; parameterised transaction-scoped binding; opaque denial; explicit propagation with no ambient store; mutation-test every security property; fix the guards this work exposed; record `ADR-011`.

## 11. Approval (step 11)
| Role | Name | Decision | Date |
| --- | --- | --- | --- |
| Security Architect | Deepesh Kumar Gupta | **Approved** | 2026-08-06 |

**HIGH risk requires owner approval.** Single owner, so author and approver are the same person — the `ADR-010` four-eyes gap, on the second-highest-risk change so far.

## 12. Post-change verification
| Field | Value |
| --- | --- |
| Re-indexed at commit | post-commit re-index |
| `detect_changes()` | Six new modules, one test module, three guard fixes, compose healthcheck, docs — no unexpected scope |
| Regression R1–R7 | **PASS** — R7 12/12; meta-suite 25/25; `pnpm verify` green with tests actually executing |
| Mutation testing | **5/5 mutants killed** (1 required a new test) |

## 13. Disposition
**Merged.** HIGH risk again realised as predicted — not in the shipped code, but in the verification around it: two guards reporting vacuous passes and a test suite that never ran in CI. Three carried gaps (jobs, events, alerting) remain owned by later steps and are listed above rather than implied resolved.
