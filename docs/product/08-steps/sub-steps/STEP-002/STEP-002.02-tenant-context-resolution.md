---
sub_step_id: STEP-002.02
parent_step: STEP-002
title: Tenant and actor context resolution at the API boundary
status: NOT_STARTED
owners: []
requirement_ids: [REQ-SEC-001, REQ-SEC-004]
blast_radius_id: BR-008
depends_on: [STEP-002.01]
last_updated: 2026-08-05
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
| Blast radius | BR-008 — **HIGH**: security boundary |
| Approval required? | **Yes** — Security Architect |

## 5. Implementation plan
- [ ] `apps/api/src/auth/dependencies.py` — resolve actor and tenant from the validated token
- [ ] **Reject any tenant hint from header, query or body** — token is the only source
- [ ] Bind tenant to the DB session via `SET LOCAL` inside the request transaction
- [ ] Propagate context explicitly into background jobs and workflow activities
- [ ] Stamp `tenant_id` on every emitted event envelope
- [ ] Fail closed with `403` (identical body shape to `404`) when context is absent

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
- [ ] Sub-step record · logs · `BR-008` · parent §21 · tracker

## 10. Regression cross-check (R1–R7)
| Check | Result | Detail |
| --- | --- | --- |
| R1 | | STEP-001 + STEP-002.01 |
| R7 tenant isolation | | **Must still pass** — this sub-step is where it can silently break |
| R2–R6 | | As applicable |

## 11. Rollback
Revert the dependency; endpoints do not yet exist, so blast radius is contained. After endpoints exist, this becomes forward-only.

## 12. Acceptance criteria
- [ ] Actor and tenant derive from the token only
- [ ] Client-supplied tenant hints are ignored
- [ ] Context reaches DB sessions, jobs and event envelopes
- [ ] Missing context fails closed
- [ ] `403`/`404` indistinguishable

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Notes / surprises | Ambient context (thread-locals, contextvars) crossing an async boundary is the classic leak — propagation must be explicit and tested |
