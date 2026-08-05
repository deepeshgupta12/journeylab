---
sub_step_id: STEP-002.07
parent_step: STEP-002
title: Audit event emission and runtime flag primitives
status: NOT_STARTED
owners: []
requirement_ids: [REQ-SEC-007, REQ-PLAT-012]
blast_radius_id: BR-013
depends_on: [STEP-002.06]
last_updated: 2026-08-05
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
| Graph status | **BLOCKED — static fallback** |
| Queries run | KG-Q-015; KG-Q-014 (redaction paths) |
| Direct dependents | Every audited operation; every flagged feature |
| Unknown / low-confidence areas | Audit retention periods are **not legally validated** (`DEC-007`) |
| Blast radius | BR-013 — HIGH (audit is the evidence trail for everything else) |
| Approval required? | **Yes** — Security Architect |

## 5. Implementation plan
- [ ] Audit writer: actor, tenant, operation, resource, outcome, timestamp, correlation ID
- [ ] **Append-only storage** — no update or delete path exists in code
- [ ] Redaction applied **at emission**, not at query time
- [ ] Separate store/stream from application logs
- [ ] Flag evaluation: feature, model, provider, cohort
- [ ] Flag changes are themselves audited
- [ ] Safe defaults: an unreachable flag service yields the **conservative** value, not the permissive one

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
- [ ] Sub-step record · logs · `BR-013` · parent §21 · tracker
- [ ] [SECURITY_PRIVACY_RESPONSIBLE_AI](../../../03-architecture/SECURITY_PRIVACY_RESPONSIBLE_AI.md) `SC-AUDIT-01` marked implemented

## 10. Regression cross-check (R1–R7)
| Check | Result | Detail |
| --- | --- | --- |
| R1 | | STEP-001 + all 002 sub-steps |
| R7 | | Must pass |
| R2–R6 | | As applicable |

## 11. Rollback
Flag primitives revert cleanly. **Audit records never revert** — they are append-only by design; a bad writer is fixed forward.

## 12. Acceptance criteria
- [ ] Audit store append-only with no update/delete path
- [ ] Redaction at emission; failure blocks rather than leaks
- [ ] Audit separate from application logs
- [ ] Flags change behavior without redeploy and are themselves audited
- [ ] Flag service outage yields conservative defaults

## 13. Completion record
| Field | Value |
| --- | --- |
| Completed | — |
| Notes / surprises | "Fail conservative" on flags is easy to get backwards: a flag service outage that enables a half-built feature is a far worse outcome than one that disables a finished one |
