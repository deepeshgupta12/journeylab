---
sub_step_id: STEP-002.02
parent_step: STEP-002
title: Tenant and actor context resolution at the API boundary
status: VERIFIED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-SEC-001, REQ-SEC-004]
blast_radius_id: BR-011
depends_on: [STEP-002.01]
last_updated: 2026-08-06
---

# STEP-002.02 — Tenant and actor context resolution at the API boundary

## 1. Outcome
Every request resolves actor and tenant **from the token alone**, propagates that context to the database session, and rejects any request that lacks it.

## 2. Scope and boundary
**In scope:** FastAPI dependency resolving actor/tenant, database session binding, rejection of missing context, propagation into jobs and events.
**Not in this sub-step:** policy evaluation (`.03`), provisioning (`.04`), browser session (`.05`).

## 3. Requirements served
| Requirement | Acceptance criterion | Test ID |
| --- | --- | --- |
| REQ-SEC-001 | Tenant context reaches every DB session, job and emitted event | TST-SEC-001 |
| REQ-SEC-004 | A request without resolvable context is rejected at the boundary | TST-SEC-004 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | **BLOCKED — static fallback** |
| Queries run | KG-Q-015; **KG-Q-014 mandatory** (auth data flow) |
| Direct dependents | Every future endpoint and worker |
| Unknown / low-confidence areas | Context propagation into async workers and Temporal activities — must be explicit, not ambient |
| Blast radius | [BR-011](../../../10-logs/blast-radius/BR-011-tenant-context-at-the-api-boundary.md) — **HIGH**: security boundary |
| Approval required? | **Yes** — Security Architect |

## 5. Implementation plan
- [x] `apps/api/src/auth/dependencies.py` — resolve actor and tenant from the validated token
- [x] **Reject any tenant hint from header, query or body** — token is the only source
- [x] Bind tenant to the DB session via `SET LOCAL` inside the request transaction
- [x] Propagate context explicitly into background jobs and workflow activities — the *primitive* (`to_job_payload`/`from_job_payload`); **no enforcement** until workers exist (STEP-006)
- [x] Stamp `tenant_id` on every emitted event envelope — `stamp_envelope`; **no outbox exists to enforce it** (STEP-006, `DEC-009` open)
- [x] Fail closed when context is absent — implemented as **`404` for both cases**, not `403`. A distinguishable 403 is still an existence oracle; `errors.py` records the reasoning

## 6. Contracts and schema changes
None — consumes the auth envelope declared in `STEP-004`.

## 7. Tests to add
| Test ID | Type | Asserts |
| --- | --- | --- |
| TST-SEC-004 | security | Missing/invalid context rejected at the boundary |
| — | security | A client-supplied `X-Tenant-Id` header is **ignored** |
| — | integration | Context reaches the DB session and a background job |
| — | security | `403` and `404` bodies are indistinguishable |

## 8. Telemetry, security and accessibility
Correlation ID is tenant-safe and non-reversible. Auth failures counted; no PII in telemetry.

## 9. Documentation to update
- [x] Sub-step record · `IMPL-009` · `BUG-009/010/011` · `BR-011` · `ADR-011` · regression entry · tracker

## 10. Regression cross-check (R1–R7)
| Check | Result | Detail |
| --- | --- | --- |
| R1 | **PASS** | `pnpm verify`; tests now actually execute (`BUG-011`) |
| R7 tenant isolation | **PASS — 12/12** | Plus a new application-layer pooled-leak test that R7 did not cover |
| R2–R6 | **PASS / N/A** | R2 N/A (no contracts); R6 surfaced a BUG-004 recurrence (`BUG-010`). See [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) |

## 11. Rollback
Revert the dependency; endpoints do not yet exist, so blast radius is contained. After endpoints exist, this becomes forward-only.

## 12. Acceptance criteria
- [x] Actor and tenant derive from the token only
- [x] Client-supplied tenant hints are ignored — mutation-tested
- [x] Context reaches DB sessions (verified against live RLS); jobs and envelopes have the primitive but **no enforcing consumer yet**
- [x] Missing context fails closed — six rejection cases
- [x] Denial and absence indistinguishable — asserted on status, body bytes and headers

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | 2026-08-06 |
| Implementation | [IMPL-009](../../../10-logs/IMPLEMENTATION_LOG.md) |
| Tests | 29 in `tests/api/`; 5/5 mutants killed |
| Bugs found | `BUG-009` (Postgres readiness race), `BUG-010` (BUG-004 recurrence in 3 guards), `BUG-011` (`pnpm test` was a stub) |
| Decision recorded | [ADR-011](../../../../adr/ADR-011-psycopg3-as-the-postgres-driver.md) — psycopg 3, no ORM yet |
| Notes / surprises | The predicted leak was designed out: there is no ambient accessor at all, and a test asserts none is reintroduced. The **unpredicted** one was worse — a mutant making the DB binding session-wide instead of transaction-scoped passed all 28 tests, because R7 proved that property in SQL and nothing proved it for `bind_tenant`. Also: `Annotated[..., Depends(local)]` under PEP 563 silently returns `422` — a live hazard for STEP-004 |
| Carried gaps | Job/event enforcement (STEP-006); auth-denial alerting (STEP-024); four-eyes approval unsatisfiable with one owner (`ADR-010`) |
