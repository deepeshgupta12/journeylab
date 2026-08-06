---
sub_step_id: STEP-002.07
parent_step: STEP-002
title: Audit event emission and runtime flag primitives
status: VERIFIED
owners: ["Deepesh Kumar Gupta"]
requirement_ids: [REQ-SEC-007, REQ-PLAT-012]
blast_radius_id: BR-017
depends_on: [STEP-002.06]
last_updated: 2026-08-06
---

# STEP-002.07 — Audit event emission and runtime flag primitives

## 1. Outcome
Security and business audit events are written **immutably and separately from application logs**, and feature/model/provider/cohort flags change behavior without a deployment.

## 2. Scope and boundary
**In scope:** audit event writer with redaction, immutable audit store, flag evaluation primitives and admin-settable values.
**Not in this sub-step:** the admin console UI ([STEP-021](../../STEP-021-administration-and-curation-console.md)), dashboards and alerts ([STEP-024](../../STEP-024-observability-sre-and-support-readiness.md)).

## 3. Requirements served
| Requirement | Acceptance criterion | Test ID |
| --- | --- | --- |
| REQ-SEC-007 | Audit events immutable, separate from app logs, redacted | TST-SEC-007 |
| REQ-PLAT-012 | Flags change behavior with no redeploy | TST-PLAT-012 |

## 4. Pre-change analysis
| Field | Value |
| --- | --- |
| Graph status | ✅ **RUNNABLE** — `impact(AuditRecord, upstream, 3)` returned `epistemic: exact`, LOW, 2 direct — **both tests**, confirming there was no production sink |
| Queries run | KG-Q-015; KG-Q-014 (redaction paths) |
| Direct dependents | Every audited operation; every flagged feature |
| Unknown / low-confidence areas | Audit retention periods are **not legally validated** (`DEC-007`) |
| Blast radius | [BR-017](../../../10-logs/blast-radius/BR-017-audit-and-flags.md) — **HIGH** (audit is the evidence trail for everything else) |
| Approval required? | **Yes** — Security Architect |

## 5. Implementation plan
- [x] Audit writer with all seven fields. Naive timestamps rejected at construction — ordering is most of what an investigation depends on
- [x] **Append-only by PRIVILEGE, not convention.** `journeylab_app` holds INSERT + SELECT only; `UPDATE`, `DELETE` and `TRUNCATE` each verified to return `permission denied`. Code can be changed; a privilege cannot be talked around
- [x] Redaction at emission. Redacting on read would mean the raw value was already durably stored in every backup and replica
- [x] Its own table, schema and retention — deliberately a table, not the event bus: an audit trail routed through a queue can be dropped
- [x] Flag evaluation with tenant override → global default → conservative, resolved in one query so precedence cannot drift
- [~] **PARTIAL.** `feature_flags` carries `updated_by`/`updated_at`, and the app role cannot write flags at all. Emitting an audit event on change belongs to the admin console (STEP-021), which is the only writer
- [x] Every failure path returns conservative — unreachable store, missing row, null value, wrong type. `conservative` is a **required** argument with no default, because which direction is safe differs per flag

## 6. Contracts and schema changes
| Artifact | Change | Compatibility |
| --- | --- | --- |
| Audit event schema | New | Additive |
| Flag configuration schema | New | Additive |

## 7. Tests to add
| Test ID | Type | Asserts |
| --- | --- | --- |
| TST-SEC-007 | integration | Audit events immutable; no code path updates or deletes them |
| — | security | Secrets and PII absent from audit payloads |
| TST-PLAT-012 | integration | Flag change alters behavior without restart |
| — | integration | Flag service unavailable ⇒ conservative default |

## 8. Telemetry, security and accessibility
Audit volume and write-failure rate monitored — a silent audit failure is a compliance gap. Redaction failure **blocks emission** rather than leaking.

## 9. Documentation to update
- [x] Sub-step record · `IMPL-014` · `BR-017` · regression entry · tracker
- [x] [SECURITY_PRIVACY_RESPONSIBLE_AI](../../../03-architecture/SECURITY_PRIVACY_RESPONSIBLE_AI.md) `SC-AUDIT-01` marked implemented

## 10. Regression cross-check (R1–R7)
| Check | Result | Detail |
| --- | --- | --- |
| R1 | **PASS** | 335 Python + 41 TypeScript |
| R7 | **PASS** | Shell 12/12; isolation suite 14+5. Both new tables are RLS `ENABLE` + `FORCE` |
| R2–R6 | **PASS / N/A** | R2 N/A; migration 002 is additive. See [REGRESSION_LOG](../../../10-logs/REGRESSION_LOG.md) |

## 11. Rollback
Flag primitives revert cleanly. **Audit records never revert** — they are append-only by design; a bad writer is fixed forward.

## 12. Acceptance criteria
- [x] Append-only, enforced by the database
- [x] Redaction at emission; failure raises and blocks the write
- [x] Separate table and schema
- [~] Flags change behaviour without redeploy (**proven in-process**); **auditing the change** is STEP-021's, since the admin console is the only writer
- [x] Outage yields conservative — mutation-tested by making it fail open

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | 2026-08-06 |
| Implementation | [IMPL-014](../../../10-logs/IMPLEMENTATION_LOG.md) |
| Tests | 29 (335 Python total); 4/4 mutants killed |
| Notes / surprises | The prediction was right and drove the design: `conservative` is a **required** argument with no default, so a flag whose author has not decided which direction is safe cannot be evaluated at all. **Two defects found by tests rather than review:** `PRIMARY KEY (key, organization_id)` made the NULL-means-global row impossible to insert, because PK columns are implicitly `NOT NULL`; and a tuple containing a private key passed through `redact()` untouched, because neither the masker nor the safety sweep traversed tuples — **the fail-closed branch was unreachable until that fix** |
| Carried gaps | Emitters not wired into request paths (STEP-004); write-failure monitoring (STEP-024); flag-change auditing via the admin console (STEP-021); retention policy, blocked on `DEC-007` |
